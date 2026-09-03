"""
Analyzer — Xây prompt và gọi model qua OpenAI-compatible API.
Hỗ trợ 7 provider: OpenAI, Gemini, Grok, DeepSeek, OpenRouter, KiraAI, Ollama.
Key lấy từ SQLite (lệnh /keys trong bot).
"""

import base64
import logging
import requests
from config import (
    provider_base_url, provider_api_key,
    text_model, vision_model, PROVIDERS,
)
from storage import get_candles, get_api_key, get_current_provider
from indicators import compute_all, format_indicators

log = logging.getLogger("analyzer")


def resolve_provider(preferred=None):
    """
    Xác định provider sẽ dùng:
    - preferred (từ lệnh /model) nếu có
    - provider đã lưu trong DB
    - provider đầu tiên có key
    """
    from config import PROVIDER_PRIORITY
    if preferred:
        return preferred
    saved = get_current_provider()
    if saved:
        return saved
    # Tự chọn provider đầu tiên CÓ KEY (bỏ qua Ollama — chỉ dùng khi chủ động /model)
    for p in PROVIDER_PRIORITY:
        if p == "ollama":
            continue  # Ollama local chỉ dùng khi user chọn /model ollama
        if get_api_key(p):
            return p
    return ""


def _try_provider(prov, messages, model, max_tokens, image_b64, add_disclaimer=True, lang="vi"):
    """Gọi 1 provider. Trả text hoặc None nếu lỗi."""
    info = PROVIDERS.get(prov, {})
    key = provider_api_key(prov)
    if not key:
        log.warning("[%s] bỏ qua — thiếu key", prov)
        return None

    # Model mặc định nếu không truyền — ưu tiên override (admin /setmodel) → config
    if not model:
        from storage import get_model_override
        kind = "vision" if image_b64 else "text"
        mdl = get_model_override(prov, kind) or (vision_model(prov) if image_b64 else text_model(prov))
    else:
        mdl = model
    r = None

    try:
        if prov == "gemini":
            headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
            api_url = f"{provider_base_url(prov)}/chat/completions"
        elif prov == "claude":
            headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
            claude_msgs = []
            system_text = ""
            for m in messages:
                if m["role"] == "system":
                    system_text = m["content"]
                else:
                    claude_msgs.append({"role": m["role"], "content": m["content"]})
            payload = {"model": mdl, "messages": claude_msgs, "max_tokens": max_tokens}
            if system_text:
                payload["system"] = system_text
            if image_b64:
                claude_msgs[-1]["content"] = [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_b64}},
                    {"type": "text", "text": claude_msgs[-1]["content"]},
                ]
            api_url = f"{provider_base_url(prov)}/messages"
        else:
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            if prov == "openrouter":
                headers["HTTP-Referer"] = "https://github.com/"
                headers["X-Title"] = "TNVGold-Telegram"
            api_url = f"{provider_base_url(prov)}/chat/completions"
            if image_b64:
                content = [{"type": "text", "text": m["content"]} for m in messages if m["role"] == "user"]
                content.insert(0, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}})
                payload = {"model": mdl, "messages": [*[m for m in messages if m["role"] != "user"], {"role": "user", "content": content}], "max_tokens": max_tokens}
            else:
                payload = {"model": mdl, "messages": messages, "max_tokens": max_tokens}

        r = requests.post(api_url, headers=headers, json=payload, timeout=90)
        r.raise_for_status()
        data = r.json()
        if prov == "claude":
            text = data["content"][0]["text"].strip()
        else:
            text = data["choices"][0]["message"]["content"].strip()

        # Nếu AI trả text rỗng → KHÔNG nối disclaimer (tránh chỉ còn disclaimer),
        # coi như provider lỗi để _call_chat thử provider khác.
        if not text:
            log.warning("[%s] trả về text rỗng — bỏ qua, thử provider khác", prov)
            return None

        if lang == "en":
            disclaimer = ('\n\n⚠️ _Disclaimer: This analysis is for reference only '
                          'and is not investment advice. Markets carry risk — '
                          'manage your capital carefully._')
        else:
            disclaimer = ('\n\n⚠️ _Disclaimer: Phân tích chỉ mang tính tham khảo, '
                          'không phải lời khuyên đầu tư. Thị trường có rủi ro, '
                          'hãy quản lý vốn chặt chẽ._')
        return (text + disclaimer if add_disclaimer else text)
    except Exception as e:
        log.warning("[%s] lỗi: %s", prov, e)
        if r is not None:
            log.warning("Response: %s", r.text[:200])
        return None


def _call_chat(messages, model=None, max_tokens=900, image_b64=None, provider=None, add_disclaimer=True, lang="vi"):
    """
    Gọi chat completion với auto-fallback.
    Thử provider ưu tiên, nếu lỗi → tự thử provider khác có key.
    """
    # Xác định danh sách provider cần thử
    preferred = resolve_provider(provider)
    if not preferred:
        log.error("Không có provider khả dụng — thêm key bằng lệnh /keys")
        return None

    # Tạo danh sách thử: provider ưu tiên + các provider có key còn lại
    from config import PROVIDER_PRIORITY
    from storage import get_api_key
    providers_to_try = [preferred]
    for p in PROVIDER_PRIORITY:
        if p not in providers_to_try:
            info = PROVIDERS.get(p, {})
            if info.get("no_key") or get_api_key(p):
                providers_to_try.append(p)

    last_error = None
    empty_providers = []
    for prov in providers_to_try:
        if prov == "ollama" and prov != preferred:
            continue  # Ollama chỉ thử nếu được chọn chủ động
        result = _try_provider(prov, messages, model, max_tokens, image_b64,
                                add_disclaimer=add_disclaimer, lang=lang)
        if result is not None:
            return result
        last_error = prov

    log.error("Tất cả provider đều không trả kết quả (thử: %s). "
              "Kiểm tra key (/keys) hoặc đổi provider (/model <tên>).",
              ", ".join(providers_to_try))
    return None


# ── Prompt theo gold-scalp-playbook (M5 focus) ────────────
def build_analysis_prompt(candles, timeframe="M5", detail=False, lang="vi"):
    """Dựng prompt text phân tích từ nến + chỉ báo."""
    ind = compute_all(candles)
    ind_text = format_indicators(ind)

    lang_req = (
        "Trả lời TIẾNG VIỆT, cô đọng, có cấu trúc rõ ràng. "
        if lang == "vi"
        else "Answer in ENGLISH, concise, clearly structured. "
    )

    system = (
        "Bạn là chuyên gia scalping XAUUSD (vàng) trên MT5, chuyên khung M5, "
        "tuân thủ nghiêm ngặt gold-scalp-playbook: "
        "- Chỉ giao dịch cửa sổ thanh khoản (London 08:00-12:00 UTC, London-NY overlap 12:00-16:00 UTC). "
        "- R:R tối thiểu 1:1.5, khuyến nghị 1:2. "
        "- SL đặt theo 1×ATR, sizing = risk / (SL_pips × pip_value). "
        "- Tránh: phiên Asia, 30' trước & 10' sau tin, thứ 6 sau 16:00 UTC. "
        "- Không tự tin tuyệt đối. "
        f"{lang_req}"
    )

    user = f"""Dữ liệu nến M5 XAUUSD gần nhất ({ind['count']} nến):

{ind_text}

Hãy phân tích theo quy trình scalp M5:
1) *Xu hướng & bối cảnh*: trend chính (từ SMA20/50, EMA9/21), đang ở phiên nào (ước theo giờ hiện tại).
2) *Vùng hỗ trợ/kháng cự*: các mức quan trọng gần giá (Fib, BB, recent H/L).
3) *Tín hiệu momentum*: RSI (quá mua/bán?), MACD (crossover?), ATR (biến động).
4) *Setup khuyến nghị*: BUY/SELL/NEUTRAL + lý do ngắn, entry, SL (1×ATR), TP (R:R 1:2).
5) *Rủi ro*: thời điểm tin tức, cảnh báo, điều kiện hủy setup.

Yêu cầu: dưới 250 từ, có dấu ✅/⚠️. KHÔNG thêm disclaimer/phòng tránh rủi ro — bot sẽ tự thêm."""
    if detail:
        user += "\n\nLưu ý: đây là bản phân tích chi tiết, có thể dài hơn và thêm cảnh báo rủi ro sâu."

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def analyze_text(timeframe="M5", detail=False, provider=None, lang="vi"):
    """Phân tích text XAUUSD từ nến trong DB. Trả text hoặc None."""
    candles = get_candles(limit=300)
    if len(candles) < 20:
        return "⚠️ Chưa đủ dữ liệu nến (cần ≥20). Collector đang chạy chưa? (cần ~100 phút để có 20 nến M5)"
    messages = build_analysis_prompt(candles, timeframe=timeframe, detail=detail, lang=lang)
    return _call_chat(messages, max_tokens=900 if not detail else 1400, provider=provider, lang=lang)


def analyze_image(image_path: str, timeframe="M5", provider=None, lang="vi"):
    """Phân tích chart ảnh bằng model vision. Trả text hoặc None."""
    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
    except Exception as e:
        log.error("Đọc ảnh lỗi: %s", e)
        return None

    # Lấy dữ liệu nến kèm
    candles = get_candles(limit=100)
    from indicators import compute_all, format_indicators
    ind = compute_all(candles)
    ind_text = format_indicators(ind) if candles else "Chưa có dữ liệu nến."

    lang_req = (
        "Trả lời TIẾNG VIỆT cô đọng. "
        if lang == "vi"
        else "Answer in ENGLISH, concise. "
    )

    messages = [
        {"role": "system", "content": (
            "Bạn là chuyên gia scalping XAUUSD khung M5. "
            "Phân tích BIỂU ĐỒ ảnh kèm số liệu, xác định: xu hướng, mô hình nến, "
            "vùng S/R, setup entry/SL/TP theo R:R 1:2. "
            f"{lang_req}"
            "KHÔNG thêm disclaimer/phòng tránh rủi ro — bot sẽ tự thêm."
        )},
        {"role": "user", "content": (
            f"Phân tích chart XAUUSD M5 trong ảnh.\n\n"
            f"Số liệu chỉ báo hiện tại:\n{ind_text}\n\n"
            "Đọc chart và cho: 1) xu hướng, 2) pattern nổi bật, 3) S/R, "
            "4) setup entry/SL/TP, 5) cảnh báo. Dưới 200 từ."
        )},
    ]
    return _call_chat(messages, max_tokens=1500, image_b64=b64, provider=provider, lang=lang)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    candles = get_candles(limit=300)
    print(f"Đã có {len(candles)} nến M5 trong DB")
    if len(candles) >= 20:
        print(analyze_text())
    else:
        print("Chưa đủ nến — không thể test phân tích thực.")
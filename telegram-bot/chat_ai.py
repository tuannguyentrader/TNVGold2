"""
chat_ai.py — Chat AI tự do cho bot vàng TNVGold (chỉ nói về XAUUSD).

Người dùng nhắn tin thường (không phải lệnh /...) → bot gọi AI với:
- Dữ liệu thị trường realtime (giá, trend, RSI, ATR, tín hiệu TNV, dự đoán nến)
- Tin tức kinh tế USD hôm nay (Forex Factory)
- Hiệu quả tín hiệu TNV gần đây (7 ngày / 30 ngày)

Prompt theo "Cách A" — bot CHỈ tư vấn vàng, từ chối chủ đề khác.
"""

import logging
from datetime import datetime

log = logging.getLogger("chat_ai")


def _market_data(lang="vi") -> str:
    """Dữ liệu thị trường hiện tại (không gồm BB — người dùng yêu cầu bỏ)."""
    try:
        from storage import get_candles
        from indicators import compute_all
        from tnv_engine import analyze_tnv
        from candle_analysis import analyze_candle_sequence
        from collector import get_last_price

        candles = get_candles(limit=100)
        if not candles or len(candles) < 20:
            return ("Chưa đủ dữ liệu nến M5." if lang == "vi"
                    else "Not enough M5 candle data.")
        ind = compute_all(candles)
        price = get_last_price()
        if price is None:
            price = candles[-1]["close"]

        # Trend so với SMA20
        sma20 = ind.get("sma20")
        if sma20:
            if price < sma20:
                trend = (f"GIẢM (dưới SMA20 ${sma20:.2f})" if lang == "vi"
                         else f"DOWN (below SMA20 ${sma20:.2f})")
            else:
                trend = (f"TĂNG (trên SMA20 ${sma20:.2f})" if lang == "vi"
                         else f"UP (above SMA20 ${sma20:.2f})")
        else:
            trend = ("Không xác định" if lang == "vi" else "Unknown")

        # RSI
        rsi = ind.get("rsi14")
        if rsi is None:
            rsi_txt = "N/A"
        elif rsi < 30:
            rsi_txt = (f"{rsi:.1f} (Quá bán)" if lang == "vi"
                       else f"{rsi:.1f} (Oversold)")
        elif rsi > 70:
            rsi_txt = (f"{rsi:.1f} (Quá mua)" if lang == "vi"
                       else f"{rsi:.1f} (Overbought)")
        else:
            rsi_txt = (f"{rsi:.1f} (Trung tính)" if lang == "vi"
                       else f"{rsi:.1f} (Neutral)")

        # ATR
        atr = ind.get("atr14")
        atr_txt = f"${atr:.2f}" if atr else "N/A"

        # Tín hiệu TNV
        sig_txt = ("CHỜ — không có tín hiệu." if lang == "vi"
                   else "WAIT — no signal.")
        try:
            result = analyze_tnv(candles, use_system1=True, use_system2=False)
            if "error" not in result:
                for sig in result.get("signals", []):
                    if sig.get("type") in ("LONG", "SHORT"):
                        st = sig["type"]
                        sc = sig.get("score", 0)
                        sig_txt = (f"🟢 LONG — Score {sc}/10" if st == "LONG"
                                   else f"🔴 SHORT — Score {sc}/10")
                        break
        except Exception as e:
            log.warning("chat_ai TNV signal lỗi: %s", e)

        # Dự đoán nến tiếp
        pred_txt = "N/A"
        try:
            seq = analyze_candle_sequence(candles, lookback=10)
            pred_txt = seq.get("predicted_direction", "N/A")
        except Exception as e:
            log.warning("chat_ai prediction lỗi: %s", e)

        lines = [
            f"XAUUSD: ${price:.2f}",
            f"{'Trend M5:' if lang == 'vi' else 'M5 Trend:'} {trend}",
            f"{'RSI14:' if lang == 'vi' else 'RSI14:'} {rsi_txt}",
            f"{'ATR14:' if lang == 'vi' else 'ATR14:'} {atr_txt}",
            f"{'Tín hiệu TNV:' if lang == 'vi' else 'TNV signal:'} {sig_txt}",
            f"{'Dự đoán nến M5 tiếp:' if lang == 'vi' else 'Next M5 candle prediction:'} {pred_txt}",
        ]
        return "\n".join(lines)
    except Exception as e:
        log.warning("chat_ai market data lỗi: %s", e)
        return ("Chưa có dữ liệu thị trường." if lang == "vi"
                else "No market data available.")


def _news_data(lang="vi") -> str:
    """Tin tức kinh tế USD hôm nay (Forex Factory)."""
    try:
        from forex_factory import get_calendar, filter_usd_events
        events = get_calendar()
        if not events:
            return ("Không có dữ liệu lịch kinh tế." if lang == "vi"
                    else "No economic calendar data.")
        usd = filter_usd_events(events)
        today = datetime.now().date()
        upcoming = []
        for e in usd:
            t = e.get("time_utc")
            if t and t.date() == today:
                upcoming.append(e)
        upcoming.sort(key=lambda x: x.get("time_utc") or datetime.min)
        if not upcoming:
            return ("Không có tin USD quan trọng hôm nay." if lang == "vi"
                    else "No important USD news today.")
        lines = []
        for e in upcoming[:8]:
            t = e.get("time_utc")
            time_str = t.strftime("%H:%M") if t else "?"
            title = e.get("title", "?")
            impact = e.get("impact", "")
            star = {"High": "🚨", "Medium": "⚠️"}.get(impact, "")
            lines.append(f"• {time_str} — {title} {star}")
        return "\n".join(lines)
    except Exception as e:
        log.warning("chat_ai news lỗi: %s", e)
        return ("Không có dữ liệu tin tức." if lang == "vi"
                else "No news data.")


def _signal_stats(lang="vi") -> str:
    """Hiệu quả tín hiệu TNV gần đây (7 ngày & 30 ngày)."""
    try:
        from signals import get_stats

        def _line(stats):
            total = stats.get("total", 0)
            if total == 0:
                return ("Chưa có tín hiệu." if lang == "vi"
                        else "No signals yet.")
            win = stats.get("win_rate", 0)
            tr = stats.get("total_r", 0)
            return (f"{total} tín hiệu, win {win:.0f}%, tổng R {tr:+.1f}"
                    if lang == "vi"
                    else f"{total} signals, win {win:.0f}%, total R {tr:+.1f}")

        s7 = _line(get_stats(7))
        s30 = _line(get_stats(30))
        if lang == "vi":
            return f"• 7 ngày: {s7}\n• 30 ngày: {s30}"
        return f"• 7d: {s7}\n• 30d: {s30}"
    except Exception as e:
        log.warning("chat_ai stats lỗi: %s", e)
        return ("Không có dữ liệu hiệu quả." if lang == "vi"
                else "No performance data.")


def _system_prompt_vi(market_data: str, news_data: str, signal_stats: str) -> str:
    """System prompt tiếng Việt — luật bắt buộc (đã chốt)."""
    return f"""Bạn là chuyên gia phân tích kỹ thuật Vàng (XAUUSD), làm việc tại một quỹ đầu tư.
Bot này CHỈ phục vụ giao dịch vàng — bạn chỉ trả lời về XAUUSD, thị trường, chỉ báo, tin tức, rủi ro.

=== DỮ LIỆU THỊ TRƯỜNG HIỆN TẠI ===
{market_data}

=== TIN TỨC KINH TẾ USD HÔM NAY ===
{news_data}

=== HIỆU QUẢ TÍN HIỆU GẦN ĐÂY ===
{signal_stats}

=== LUẬT BẮT BUỘC ===
1. Chỉ trả lời về XAUUSD, trading vàng, tin tức liên quan vàng.
   Nếu người dùng hỏi ngoài chủ đề → từ chối lịch sự: "Tôi chuyên về vàng, hãy hỏi về XAUUSD nhé."
2. LUÔN dựa vào dữ liệu thực tế bên trên (giá, RSI, ATR, trend, tín hiệu TNV, tin tức) — không tự suy diễn, không bịa số.
3. Thiếu thông tin → nói "tôi cần thêm dữ liệu" — không đoán bừa.
4. Phân biệt rõ: GIÁ HIỆN TẠI vs DỰ ĐOÁN — không gây nhầm lẫn.
5. KHÔNG khuyến nghị mua/bán. Chỉ phân tích xu hướng, rủi ro, tác động.
6. Kết thúc mỗi trả lời về giao dịch bằng: "⚠️ Không phải lời khuyên tài chính."
7. Trả lời tối đa 3-4 câu, ngắn gọn.
8. Trả lời ĐÚNG NGÔN NGỮ người dùng hỏi (tiếng Việt / tiếng Anh)."""


def _system_prompt_en(market_data: str, news_data: str, signal_stats: str) -> str:
    """System prompt tiếng Anh — cùng luật, dịch tự nhiên."""
    return f"""You are a Gold (XAUUSD) technical analysis expert working at an investment fund.
This bot ONLY serves gold trading — you only answer about XAUUSD, the market, indicators, news, and risk.

=== CURRENT MARKET DATA ===
{market_data}

=== TODAY'S USD ECONOMIC NEWS ===
{news_data}

=== RECENT SIGNAL PERFORMANCE ===
{signal_stats}

=== MANDATORY RULES ===
1. Only answer about XAUUSD, gold trading, and gold-related news.
   If the user asks off-topic → politely refuse: "I specialize in gold — please ask about XAUUSD."
2. ALWAYS base answers on the actual data above (price, RSI, ATR, trend, TNV signal, news) — do not make things up or invent numbers.
3. If information is missing → say "I need more data" — do not guess.
4. Clearly distinguish: CURRENT PRICE vs PREDICTION — do not confuse them.
5. Do NOT recommend buying or selling. Only analyze trends, risk, and impact.
6. End every trading-related answer with: "⚠️ Not financial advice."
7. Answer in at most 3-4 short sentences.
8. Answer in the SAME LANGUAGE the user asks in (Vietnamese / English)."""


def build_chat_prompt(user_msg: str, lang="vi") -> list:
    """Dựng messages [system, user] cho AI chat tự do."""
    market_data = _market_data(lang)
    news_data = _news_data(lang)
    signal_stats = _signal_stats(lang)

    if lang == "en":
        system = _system_prompt_en(market_data, news_data, signal_stats)
    else:
        system = _system_prompt_vi(market_data, news_data, signal_stats)

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]


def chat_with_ai(user_msg: str, lang="vi", provider=None):
    """Gọi AI chat. Trả text hoặc None nếu lỗi/không có provider."""
    try:
        from analyzer import _call_chat
        messages = build_chat_prompt(user_msg, lang)
        # add_disclaimer=False: prompt đã yêu cầu AI tự thêm "⚠️ Không phải lời khuyên tài chính."
        # — tránh trùng 2 dòng cảnh báo với disclaimer tự động của analyzer.
        return _call_chat(messages, max_tokens=500, provider=provider, add_disclaimer=False)
    except Exception as e:
        log.error("chat_with_ai lỗi: %s", e)
        return None


if __name__ == "__main__":
    import sys

    lang = sys.argv[1] if len(sys.argv) > 1 else "vi"
    prompt = build_chat_prompt("Giá vàng hôm nay thế nào?", lang)
    print("=" * 60)
    print(f"  SYSTEM PROMPT ({lang})")
    print("=" * 60)
    print(prompt[0]["content"])
    print()
    print("=" * 60)
    print("  USER MESSAGE")
    print("=" * 60)
    print(prompt[1]["content"])
    print()
    print("=" * 60)
    print("  ✅ Done — built prompt without AI key.")

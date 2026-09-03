"""
Cấu hình tập trung cho TNVGold Telegram Bot.
API keys KHÔNG nằm trong .env — lưu trong SQLite, quản lý qua lệnh /keys.
Hỗ trợ 7 provider: OpenAI, Gemini, Grok, DeepSeek, OpenRouter, KiraAI, Ollama.
"""

import os
from pathlib import Path

# ── Thư mục ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "xau_bot.db"
CHART_DIR = DATA_DIR / "charts"
CHART_DIR.mkdir(exist_ok=True)
REPORT_DIR = DATA_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)

# ── Telegram ─────────────────────────────────────────────
# Lấy token theo thứ tự: env → file telegram_token.txt → yêu cầu nhập
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not TELEGRAM_TOKEN:
    _token_file = BASE_DIR / "telegram_token.txt"
    if _token_file.exists():
        TELEGRAM_TOKEN = _token_file.read_text().strip()

# Whitelist chat id (phân tách bằng dấu phẩy). Rỗng = mọi người dùng được.
ALLOWED_CHAT_IDS = {
    int(x.strip()) for x in os.environ.get("ALLOWED_CHAT_IDS", "").split(",") if x.strip().isdigit()
}

# Admin chat ids — luôn được xem là gói Pro (không cần đặt tier).
# Phân tách bằng dấu phẩy. VD: ADMIN_CHAT_IDS=123456,-100987654
ADMIN_CHAT_IDS = {
    int(x.strip()) for x in os.environ.get("ADMIN_CHAT_IDS", "").split(",") if x.strip().isdigit()
}

# ── Provider registry ────────────────────────────────────
# Mỗi provider: base_url (OpenAI-compatible), model text mặc định, model vision mặc định
PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "text_model": "deepseek-chat",
        "vision_model": "deepseek-v4-flash-vision-exp",
    },
    "gemini": {
        "name": "Gemini (Google)",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "text_model": "gemini-2.0-flash",
        "vision_model": "gemini-2.0-flash",
    },
    "openai": {
        "name": "ChatGPT (OpenAI)",
        "base_url": "https://api.openai.com/v1",
        "text_model": "gpt-4o-mini",
        "vision_model": "gpt-4o",
    },
    "claude": {
        "name": "Claude (Anthropic)",
        "base_url": "https://api.anthropic.com/v1",
        "text_model": "claude-sonnet-4-20250514",
        "vision_model": "claude-sonnet-4-20250514",
    },
    "grok": {
        "name": "Grok (xAI)",
        "base_url": "https://api.x.ai/v1",
        "text_model": "grok-2-latest",
        "vision_model": "grok-2-vision-latest",
    },
    "openrouter": {
        "name": "OpenRouter (nhiều model)",
        "base_url": "https://openrouter.ai/api/v1",
        "text_model": "deepseek/deepseek-chat",
        "vision_model": "deepseek/deepseek-vl2",
    },
    "kiraai": {
        "name": "KiraAI",
        "base_url": "https://kiraai.vn/api/v1",
        "text_model": "glm-5.3-flash",
        "vision_model": "glm-5.3-flash",
    },
    "bai": {
        "name": "Bai",
        "base_url": "https://api.b.ai/v1",
        "text_model": "deepseek-v4-flash",
        "vision_model": "deepseek-v4-flash-vision-exp",
    },
    "ollama": {
        "name": "Ollama (local)",
        "base_url": "http://localhost:11434/v1",
        "text_model": "llama3.2",
        "vision_model": "llama3.2-vision",
        "no_key": True,  # không cần API key
    },
}

# Thứ tự ưu tiên khi tự chọn provider:
# Rẻ + nhanh trước (cho hàng giờ), chất lượng cao sau (cho báo cáo)
# DeepSeek → Gemini → ChatGPT → Claude → Grok → OpenRouter → KiraAI → Bai → Ollama
PROVIDER_PRIORITY = [
    "deepseek", "gemini", "openai", "claude",
    "grok", "openrouter", "kiraai", "bai", "ollama",
]

# ── Gold-API ─────────────────────────────────────────────
GOLD_API_URL = os.environ.get("GOLD_API_URL", "https://api.gold-api.com/price/XAU")
GOLD_API_KEY = os.environ.get("GOLD_API_KEY", "")  # optional
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "60"))  # giây
CANDLE_MINUTES = int(os.environ.get("CANDLE_MINUTES", "5"))  # M5

# ── Lịch báo cáo ─────────────────────────────────────────
DAILY_REPORT_HOURS = os.environ.get(
    "DAILY_REPORT_HOURS", "7,19"
)  # giờ VN (UTC+7), cách dấu phẩy

# ── Feature: tín hiệu TNV tự động (F1) ───────────────────
AUTO_SIGNAL = os.environ.get("AUTO_SIGNAL", "1") == "1"
AUTO_SIGNAL_MIN_SCORE = int(os.environ.get("AUTO_SIGNAL_MIN_SCORE", "5"))
# Lặp lại: không gửi tín hiệu trùng (cùng hướng, cùng vùng giá) trong N phút
AUTO_SIGNAL_DEDUPE_MIN = int(os.environ.get("AUTO_SIGNAL_DEDUPE_MIN", "60"))

# ── Feature: tổng kết cuối ngày (F2) ─────────────────────
EOD_ENABLED = os.environ.get("EOD_ENABLED", "1") == "1"
EOD_HOUR = int(os.environ.get("EOD_HOUR", "22"))      # giờ VN
EOD_MINUTE = int(os.environ.get("EOD_MINUTE", "0"))  # 22:00 VN = 15:00 UTC

# ── TradingView chart ────────────────────────────────────
TV_URL = os.environ.get(
    "TV_URL",
    "https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD&interval=5",
)
CHART_INTERVAL_SECONDS = int(os.environ.get("CHART_INTERVAL_SECONDS", "30"))


# ── Subscription / Redeem code ───────────────────────────
TRIAL_DAYS = int(os.environ.get("TRIAL_DAYS", "7"))        # trial cho khách mới
CODE_PREFIX = os.environ.get("CODE_PREFIX", "XK")          # prefix mã kích hoạt
CODE_LENGTH = int(os.environ.get("CODE_LENGTH", "8"))      # độ dài phần thân mã
EXPIRE_REMIND_DAYS = int(os.environ.get("EXPIRE_REMIND_DAYS", "3"))  # nhắc trước N ngày


# ── Helper API keys (lưu SQLite) ─────────────────────────
def _get_key(provider: str) -> str:
    """Lấy API key từ SQLite (qua storage). Tránh circular import."""
    try:
        from storage import kv_get
        return kv_get(f"api_key_{provider}", "") or ""
    except Exception:
        return os.environ.get(f"{provider.upper()}_API_KEY", "")


def provider_base_url(provider: str) -> str:
    return PROVIDERS.get(provider, {}).get("base_url", "https://openrouter.ai/api/v1")


def provider_api_key(provider: str) -> str:
    """Trả API key cho provider. Ollama không cần key."""
    info = PROVIDERS.get(provider, {})
    if info.get("no_key"):
        return "ollama"
    return _get_key(provider)


def text_model(provider: str) -> str:
    return PROVIDERS.get(provider, {}).get("text_model", "deepseek/deepseek-chat")


def vision_model(provider: str) -> str:
    return PROVIDERS.get(provider, {}).get("vision_model", "deepseek/deepseek-vl2")


def available_providers() -> list:
    """Trả danh sách provider khả dụng (có key hoặc không cần key)."""
    result = []
    from storage import kv_get
    for p in PROVIDER_PRIORITY:
        info = PROVIDERS[p]
        if info.get("no_key"):
            result.append(p)
        else:
            key = kv_get(f"api_key_{p}", "")
            if key:
                result.append(p)
    return result


def is_allowed(chat_id: int) -> bool:
    """Kiểm tra chat id có được phép dùng bot không."""
    return (not ALLOWED_CHAT_IDS) or (chat_id in ALLOWED_CHAT_IDS)


# ── User tiers ───────────────────────────────────────────
# Chỉ 2 gói: free (mặc định) và pro (trả phí qua mã kích hoạt).
# Mức sử dụng tối đa cho từng tier (mỗi ngày, reset 00:00 UTC)
TIER_DAILY_LIMITS = {
    "free": {
        "signals": 5,    # chỉ nhận 5 tín hiệu tự động/ngày
        "ai_calls": 10,  # /xau, chat AI... tối đa 10 lần/ngày
        "chart": 0,      # không có /chart
    },
    "pro": {
        "signals": 9999,
        "ai_calls": 9999,
        "chart": 500,
    },
}

# ── Ngôn ngữ mặc định theo từng chat (channel/nhóm) ─────
# Chat nào nằm trong dict này sẽ nhận báo cáo bằng ngôn ngữ đó
# (ưu tiên: /lang của chat > mặc định theo chat > mặc định chung "vi").
# Ví dụ: DEFAULT_LANG_BY_CHAT = {-1002694704578: "en"}
DEFAULT_LANG_BY_CHAT = {-1001307697872: "en", -1001438511820: "en"}

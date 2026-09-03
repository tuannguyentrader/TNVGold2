"""
i18n.py — Hỗ trợ song ngữ (Tiếng Việt / English) cho TNVGold Telegram Bot.

Ngôn ngữ lưu theo chat_id trong SQLite (kv table):
  lang:vi  (mặc định) | lang:en
"""
from storage import kv_set, kv_get

DEFAULT_LANG = "en"
SUPPORTED = ("vi", "en")

# ── Từ điển song ngữ ─────────────────────────────────────
_STRINGS = {
    # Menu /start — mẫu 3 nhóm (đã chốt)
    "bot_intro": {
        "vi": "🤖 *TNVGold Telegram Bot*\n_Trợ lý AI phân tích XAUUSD thời gian thực (Multi-Timeframe)_",
        "en": "🤖 *TNVGold Telegram Bot*\n_Real-time AI XAUUSD analysis assistant (Multi-Timeframe)_",
    },
    "menu_group_analysis": {
        "vi": "📊 *PHÂN TÍCH & TÍN HIỆU*",
        "en": "📊 *ANALYSIS & SIGNALS*",
    },
    "menu_group_settings": {
        "vi": "⚙️ *CÀI ĐẶT HỆ THỐNG*",
        "en": "⚙️ *SYSTEM SETTINGS*",
    },
    "menu_tip": {
        "vi": "",
        "en": "",
    },
    # Phân tích & Tín hiệu
    "cmd_xau_m5": {
        "vi": "/xau m5 — Báo cáo tổng hợp M5 (Xu hướng + Tín hiệu + Khuyến nghị)",
        "en": "/xau m5 — M5 summary report (Trend + Signal + Recommendation)",
    },
    "cmd_candle_m5": {
        "vi": "/candle m5 — Phân tích chi tiết nến M5 → Dự đoán nến tiếp theo",
        "en": "/candle m5 — Detailed M5 candle analysis → Predict next candle",
    },
    "cmd_price": {
        "vi": "/price — Giá XAUUSD hiện tại",
        "en": "/price — Current XAUUSD price",
    },
    "cmd_news": {
        "vi": "/news — Lịch kinh tế XAUUSD hôm nay",
        "en": "/news — Today's XAUUSD economic calendar",
    },
    "cmd_history": {
        "vi": "/history — Lịch sử tín hiệu TNV gần nhất",
        "en": "/history — Recent TNV signal history",
    },
    "cmd_stats": {
        "vi": "/stats — Thống kê hiệu suất TNV (win rate, tổng R)",
        "en": "/stats — TNV performance stats (win rate, total R)",
    },
    # Cài đặt hệ thống
    "cmd_model": {
        "vi": "/model — Xem hoặc đổi AI đang dùng",
        "en": "/model — View or switch the current AI",
    },
    "cmd_model_ai": {
        "vi": "/model <ai> — Chọn AI",
        "en": "/model <ai> — Select AI",
    },
    "cmd_keys": {
        "vi": "/keys — Xem trạng thái API Key",
        "en": "/keys — View API Key status",
    },
    "cmd_keys_set": {
        "vi": "/keys set <ai> <key> — Lưu API key",
        "en": "/keys set <ai> <key> — Save an API key",
    },
    "cmd_keys_remove": {
        "vi": "/keys remove <ai> — Xóa API key",
        "en": "/keys remove <ai> — Remove an API key",
    },
    "cmd_lang": {
        "vi": "/lang — Chuyển ngôn ngữ (`vi` / `en`)",
        "en": "/lang — Switch language (`vi` / `en`)",
    },
    "cmd_help": {
        "vi": "/help — Hướng dẫn",
        "en": "/help — Help",
    },
    "cmd_settings": {
        "vi": "/settings — Cài đặt cá nhân",
        "en": "/settings — Personal settings",
    },
    # ── Subscription / Register / Redeem ─────────────────
    "help_subscription": {
        "vi": "👤 *TÀI KHOẢN & GÓI*",
        "en": "👤 *ACCOUNT & PLAN*",
    },
    "cmd_register": {
        "vi": "/register — Đăng ký (dùng thử Pro 7 ngày miễn phí)",
        "en": "/register — Sign up (free 7-day Pro trial)",
    },
    "cmd_myplan": {
        "vi": "/myplan — Xem gói hiện tại + hạn dùng",
        "en": "/myplan — View current plan + expiry",
    },
    "cmd_redeem": {
        "vi": "/redeem <mã> — Nạp mã kích hoạt để gia hạn",
        "en": "/redeem <code> — Redeem a code to renew",
    },
    # ── /chart ────────────────────────────────────────────
    "cmd_chart": {
        "vi": "/chart [khung] — Ảnh biểu đồ + phân tích AI (Premium)",
        "en": "/chart [tf] — Chart image + AI analysis (Premium)",
    },
    "chart_thinking": {
        "vi": "🖼️ Đang tạo ảnh biểu đồ và phân tích...",
        "en": "🖼️ Generating chart image and analysis...",
    },
    "chart_error": {
        "vi": "⚠️ Không tạo được ảnh biểu đồ. Thử lại sau.",
        "en": "⚠️ Could not generate chart image. Try again later.",
    },
    "chart_no_vision": {
        "vi": "⚠️ Chưa có AI đọc ảnh (vision). Đặt key vision trước: /keys set <ai> <key>",
        "en": "⚠️ No vision AI available. Set a vision key first: /keys set <ai> <key>",
    },
    "chart_no_data": {
        "vi": "⚠️ Chưa đủ dữ liệu nến.",
        "en": "⚠️ Not enough candle data.",
    },
    "chart_premium_only": {
        "vi": "⭐ */chart là tính năng Pro.*\nNâng cấp để xem ảnh biểu đồ + phân tích AI.\nLiên hệ admin để đăng ký Pro.",
        "en": "⭐ */chart is a Pro feature.*\nUpgrade to view chart images + AI analysis.\nContact admin to subscribe to Pro.",
    },
    "quota_ai_exceeded": {
        "vi": "⚠️ *Hết lượt sử dụng miễn phí*\n\nBạn đã dùng hết hạn mức AI cho ngày hôm nay rồi. Hãy nâng cấp lên *Gói Pro* để tiếp tục trò chuyện không giới hạn và mở khóa các tính năng cao cấp nhé!\n\n🚀 *Đặc quyền Pro:*\n• Không giới hạn tin nhắn mỗi ngày\n• Phản hồi tốc độ cao ưu tiên\n• Truy cập các mô hình AI mới nhất\n\n💎 *Nâng cấp ngay:* Liên hệ admin @TuanNguyenTrader để nhận ưu đãi.",
        "en": "⚠️ *Free daily limit reached*\n\nYou've used up today's AI limit. Upgrade to *Pro* to keep chatting without limits and unlock premium features!\n\n🚀 *Pro benefits:*\n• Unlimited messages per day\n• High-speed priority response\n• Access to the latest AI models\n\n💎 *Upgrade now:* Contact admin @TuanNguyenTrader for special offers.",
    },
    "quota_chart_exceeded": {
        "vi": "⚠️ *Hết lượt chart miễn phí*\n\nBạn đã dùng hết hạn mức chart cho ngày hôm nay. Hãy nâng cấp lên *Gói Pro* để xem ảnh biểu đồ + phân tích AI không giới hạn!\n\n🚀 *Đặc quyền Pro:*\n• Không giới hạn tin nhắn mỗi ngày\n• Phản hồi tốc độ cao ưu tiên\n• Truy cập các mô hình AI mới nhất\n\n💎 *Nâng cấp ngay:* Liên hệ admin @TuanNguyenTrader để nhận ưu đãi.",
        "en": "⚠️ *Free chart limit reached*\n\nYou've used up today's chart limit. Upgrade to *Pro* to view chart images + AI analysis without limits!\n\n🚀 *Pro benefits:*\n• Unlimited messages per day\n• High-speed priority response\n• Access to the latest AI models\n\n💎 *Upgrade now:* Contact admin @TuanNguyenTrader for special offers.",
    },
    "quota_signals_exceeded": {
        "vi": "⚠️ *Hết lượt tín hiệu miễn phí hôm nay*\n\nBạn đã nhận đủ 5 tín hiệu tự động trong ngày. Nâng cấp *Gói Pro* để nhận không giới hạn tín hiệu TNV chất lượng cao!\n\n💎 *Nâng cấp ngay:* Liên hệ admin @TuanNguyenTrader để nhận ưu đãi.",
        "en": "⚠️ *Free signal limit reached for today*\n\nYou've already received 5 auto signals today. Upgrade to *Pro* for unlimited high-quality TNV signals!\n\n💎 *Upgrade now:* Contact admin @TuanNguyenTrader for special offers.",
    },
    # ── /help chi tiết ────────────────────────────────────
    "help_title": {"vi": "📖 *HƯỚNG DẪN SỬ DỤNG TNVGOLD*", "en": "📖 *TNVGOLD USER GUIDE*"},
    "help_analysis": {"vi": "📊 *PHÂN TÍCH & TÍN HIỆU*", "en": "📊 *ANALYSIS & SIGNALS*"},
    "help_settings": {"vi": "⚙️ *CÀI ĐẶT*", "en": "⚙️ *SETTINGS*"},
    "help_tier": {"vi": "⭐ *GÓI DỊCH VỤ*", "en": "⭐ *SERVICE TIERS*"},
    "help_tier_free": {
        "vi": "• *Free*: tín hiệu TNV, /xau, /news, /candle, /stats, /history\n• *Pro*: + /chart ảnh AI, cảnh báo đa mốc, AI không giới hạn",
        "en": "• *Free*: TNV signals, /xau, /news, /candle, /stats, /history\n• *Pro*: + /chart AI image, multi-alerts, unlimited AI",
    },
    "help_admin_table": {
        "vi": "🛠 *BẢNG ADMIN*\n\n/tier <chat_id> <free|pro> — Đặt gói cho user\n/gencode <gói> <ngày> [số lượng] — Tạo mã kích hoạt\n/users [gói] [ngày] — Danh sách user\n/renew <chat_id> <gói> <ngày> — Gia hạn cho user\n/expire <chat_id> — Hạ user về Free\n/reset <chat_id> — Xoá dữ liệu user\n\n🤖 *QUẢN LÝ AI*\n/model — Xem/đổi provider AI\n/keys set <provider> <key> — Lưu API key\n/keys remove <provider> — Xoá key\n/setmodel <provider> text <model> — Đổi model text\n/setmodel <provider> vision <model> — Đổi model vision\n/setmodel <provider> reset — Xoá override, về mặc định",
        "en": "🛠 *ADMIN TABLE*\n\n/tier <chat_id> <free|pro> — Set user tier\n/gencode <tier> <days> [count] — Generate redeem codes\n/users [tier] [days] — List users\n/renew <chat_id> <tier> <days> — Renew user\n/expire <chat_id> — Downgrade user to Free\n/reset <chat_id> — Clear user data\n\n🤖 *AI MANAGEMENT*\n/model — View/switch AI provider\n/keys set <provider> <key> — Save API key\n/keys remove <provider> — Remove key\n/setmodel <provider> text <model> — Set text model\n/setmodel <provider> vision <model> — Set vision model\n/setmodel <provider> reset — Clear override, revert to default",
    },
    # ── Tier (gói dịch vụ) ────────────────────────────────
    "tier_requires": {
        "vi": "⭐ Tính năng này yêu cầu gói *{tier}*.\nBạn đang ở gói *{current}*.\nLiên hệ admin để nâng cấp.",
        "en": "⭐ This feature requires *{tier}* tier.\nYou are on *{current}* tier.\nContact admin to upgrade.",
    },
    "tier_info": {"vi": "⭐ Gói hiện tại: *{tier}*", "en": "⭐ Current tier: *{tier}*"},
    "tier_admin_set": {
        "vi": "✅ Đã đặt gói {tier} cho chat {cid}.",
        "en": "✅ Set tier {tier} for chat {cid}.",
    },
    "tier_admin_usage": {
        "vi": "Cú pháp: /tier <chat_id> <free|pro>\nHiện tại: Free {free} | Pro {pro}",
        "en": "Usage: /tier <chat_id> <free|pro>\nCurrent: Free {free} | Pro {pro}",
    },
    # Price
    "xau_price": {
        "vi": "🪙 *XAUUSD*: *${price:.2f}*/oz",
        "en": "🪙 *XAUUSD*: *${price:.2f}*/oz",
    },
    "price_source": {
        "vi": " (Gold-API)",
        "en": " (Gold-API)",
    },
    "price_error": {
        "vi": "⚠️ Không lấy được giá.",
        "en": "⚠️ Could not fetch price.",
    },
    # Indicators
    "indicators_title": {
        "vi": "📊 *Chỉ báo XAUUSD* (nguồn: {source})",
        "en": "📊 *XAUUSD Indicators* (source: {source})",
    },
    "not_enough_data": {
        "vi": "⚠️ Chưa đủ dữ liệu (cần ≥20 nến).",
        "en": "⚠️ Not enough data (need ≥20 candles).",
    },
    # Candle analysis
    "not_enough_candles": {
        "vi": "⚠️ Chưa đủ dữ liệu nến (cần ≥3).",
        "en": "⚠️ Not enough candle data (need ≥3).",
    },
    "close_high": {
        "vi": "🟢 Nến đóng gần đỉnh → phe mua còn mạnh, có thể tiếp tục tăng",
        "en": "🟢 Candle closed near high → buyers strong, possible continuation up",
    },
    "close_low": {
        "vi": "🔴 Nến đóng gần đáy → phe bán còn mạnh, có thể tiếp tục giảm",
        "en": "🔴 Candle closed near low → sellers strong, possible continuation down",
    },
    "close_mid": {
        "vi": "🟡 Nến đóng ở giữa → thị trường đang do dự, chờ breakout",
        "en": "🟡 Candle closed in middle → market indecisive, wait for breakout",
    },
    # XAU analysis
    "analyzing": {
        "vi": "⏳ Đang phân tích...",
        "en": "⏳ Analyzing...",
    },
    "not_enough_data_xau": {
        "vi": "⚠️ Chưa đủ dữ liệu. Collector đang chạy?",
        "en": "⚠️ Not enough data. Is the collector running?",
    },
    "model_no_response": {
        "vi": "⚠️ Model không phản hồi. Thêm key: /keys set <ai> <key>",
        "en": "⚠️ Model did not respond. Add key: /keys set <ai> <key>",
    },
    "xau_header": {
        "vi": "📊 *XAUUSD — {tf}*\nGiá: ${price:.2f}",
        "en": "📊 *XAUUSD — {tf}*\nPrice: ${price:.2f}",
    },
    # Model
    "ai_not_exist": {
        "vi": "⚠️ AI `{provider}` không tồn tại.\nCó: {providers}",
        "en": "⚠️ AI `{provider}` does not exist.\nAvailable: {providers}",
    },
    "ai_selected": {
        "vi": "✅ Đã chọn AI: *{name}*",
        "en": "✅ AI selected: *{name}*",
    },
    "ai_current": {
        "vi": "🧠 *AI hiện tại:*",
        "en": "🧠 *Current AI:*",
    },
    "ai_auto": {
        "vi": "  → (tự chọn — chưa đặt)",
        "en": "  → (auto — not set)",
    },
    "ai_configured": {
        "vi": "*Provider đã cấu hình key:*",
        "en": "*Providers with keys:*",
    },
    "ai_change_hint": {
        "vi": "Đổi: /model <tên> | Thêm key: /keys set <tên> <key>",
        "en": "Switch: /model <name> | Add key: /keys set <name> <key>",
    },
    # /setmodel (admin)
    "setmodel_syntax": {
        "vi": (
            "⚙️ *Cú pháp /setmodel:*\n"
            "• `/setmodel <provider> text <model>` — đổi model text\n"
            "• `/setmodel <provider> vision <model>` — đổi model vision\n"
            "• `/setmodel <provider> reset` — xoá override\n"
            "• `/setmodel` — xem override hiện tại\n\n"
            "Ví dụ: `/setmodel kiraai text deepseek-chat`"
        ),
        "en": (
            "⚙️ *Usage:*\n"
            "• `/setmodel <provider> text <model>`\n"
            "• `/setmodel <provider> vision <model>`\n"
            "• `/setmodel <provider> reset`\n"
            "• `/setmodel` — list current overrides\n\n"
            "Example: `/setmodel kiraai text deepseek-chat`"
        ),
    },
    "setmodel_none": {
        "vi": "⚙️ Chưa có model override nào. Bot đang dùng model mặc định từ `config.py`.",
        "en": "⚙️ No model overrides. Bot is using defaults from `config.py`.",
    },
    "setmodel_current": {
        "vi": "⚙️ *Model override hiện tại:*",
        "en": "⚙️ *Current model overrides:*",
    },
    "setmodel_ok": {
        "vi": "✅ Đã đặt `{provider}` {kind} → `{model}`",
        "en": "✅ Set `{provider}` {kind} → `{model}`",
    },
    "setmodel_reset": {
        "vi": "♻️ Đã xoá override cho `{provider}`. Trở về mặc định từ `config.py`.",
        "en": "♻️ Cleared override for `{provider}`. Back to `config.py` default.",
    },
    # Keys
    "keys_title": {
        "vi": "🔑 *API Keys đã lưu (SQLite):*",
        "en": "🔑 *Saved API Keys (SQLite):*",
    },
    "keys_no_key": {
        "vi": " (không cần key)",
        "en": " (no key needed)",
    },
    "keys_missing": {
        "vi": "chưa có key",
        "en": "no key yet",
    },
    "keys_hint": {
        "vi": "Thêm: /keys set <ai> <key>\nVD: /keys set openai sk-xxx\nXóa: /keys remove <ai>",
        "en": "Add: /keys set <ai> <key>\nE.g.: /keys set openai sk-xxx\nRemove: /keys remove <ai>",
    },
    "keys_syntax": {
        "vi": "⚠️ Cú pháp: /keys set <ai> <key> hoặc /keys remove <ai>",
        "en": "⚠️ Usage: /keys set <ai> <key> or /keys remove <ai>",
    },
    "keys_saved": {
        "vi": "✅ Đã lưu key cho *{name}*",
        "en": "✅ Key saved for *{name}*",
    },
    "keys_removed": {
        "vi": "🗑️ Đã xóa key `{provider}`",
        "en": "🗑️ Key `{provider}` removed",
    },
    "keys_no_key_needed": {
        "vi": "⚠️ `{provider}` không cần API key (chạy local).",
        "en": "⚠️ `{provider}` does not need an API key (runs locally).",
    },
    # TNV
    "tnv_need_data": {
        "vi": "⚠️ Cần ≥60 nến M5 (bot cần chạy ~5 giờ để có đủ dữ liệu).",
        "en": "⚠️ Need ≥60 M5 candles (bot needs ~5 hours to collect enough data).",
    },
    "tnv_recommendation": {
        "vi": "🤖 *Khuyến nghị:*",
        "en": "🤖 *Recommendation:*",
    },
    # Lang
    "lang_set": {
        "vi": "🌐 Ngôn ngữ đã đặt: *Tiếng Việt*\nDùng /lang en để chuyển sang English.",
        "en": "🌐 Language set: *English*\nUse /lang vi to switch to Vietnamese.",
    },
    "lang_invalid": {
        "vi": "⚠️ Ngôn ngữ không hợp lệ. Dùng /lang vi hoặc /lang en.",
        "en": "⚠️ Invalid language. Use /lang vi or /lang en.",
    },
    "lang_hint": {
        "vi": "🌐 Ngôn ngữ hiện tại: *{language}*\nĐổi: /lang en (English) hoặc /lang vi (Tiếng Việt)",
        "en": "🌐 Current language: *{language}*\nSwitch: /lang en (English) or /lang vi (Vietnamese)",
    },
    # ── Báo cáo tổng /xau ──────────────────────────────
    "report_title": {
        "vi": "📊 *BÁO CÁO XAUUSD — {tf}* (by @TNVGold_bot)",
        "en": "📊 *XAUUSD REPORT — {tf}* (by @TNVGold_bot)",
    },
    "price_label": {
        "vi": "💰 *Giá hiện tại:*",
        "en": "💰 *Current price:*",
    },
    "section_trend": {
        "vi": "📉 *XU HƯỚNG & MOMENTUM*",
        "en": "📉 *TREND & MOMENTUM*",
    },
    "section_reco": {
        "vi": "🎯 *KHUYẾN NGHỊ*",
        "en": "🎯 *RECOMMENDATION*",
    },
    "disclaimer": {
        "vi": "_⚠️ Disclaimer: Chỉ mang tính tham khảo, quản lý vốn chặt chẽ._",
        "en": "_⚠️ Disclaimer: For reference only, manage your capital carefully._",
    },
    "reco_no_data": {
        "vi": "• Không đủ dữ liệu để khuyến nghị.",
        "en": "• Not enough data for a recommendation.",
    },
    "reco_strategy_label": {
        "vi": "Chiến lược:",
        "en": "Strategy:",
    },
    "reco_strategy": {
        "vi": "Ưu tiên *{dir_label}* theo xu hướng {trend} {mark}",
        "en": "Favor *{dir_label}* — aligned with the {trend} trend {mark}",
    },
    "reco_align": {
        "vi": "(khớp tín hiệu TNV)",
        "en": "(aligned with TNV signal)",
    },
    "reco_conflict": {
        "vi": "nhưng NGƯỢC tín hiệu TNV — giảm risk hoặc bỏ qua",
        "en": "but OPPOSES TNV signal — reduce risk or skip",
    },
    "reco_exit": {
        "vi": "Có tín hiệu EXIT *{dir_label}* — ưu tiên chốt lời, chờ tín hiệu mới.",
        "en": "EXIT *{dir_label}* signal — take profit now, wait for a fresh entry.",
    },
    "reco_sideway": {
        "vi": "Thị trường đi ngang / tín hiệu yếu — KHÔNG vào lệnh.",
        "en": "Sideways market / weak signals — *DO NOT enter.*",
    },
    "reco_cancel_label": {
        "vi": "Điều kiện hủy:",
        "en": "Invalidation:",
    },
    "reco_cancel_long": {
        "vi": "Hủy lệnh nếu giá phá vỡ dưới `${lo:.2f}`.",
        "en": "Invalidate setup if price breaks below `${lo:.2f}`.",
    },
    "reco_cancel_short": {
        "vi": "Hủy lệnh nếu giá phá vỡ trên `${hi:.2f}`.",
        "en": "Invalidate setup if price breaks above `${hi:.2f}`.",
    },
    # Feature 1: Tín hiệu tự động
    "auto_signal_title": {"vi": "📡 *TNV — Tín Hiệu Tự Động*", "en": "📡 *TNV — Auto Signal*"},
    "auto_signal_brand": {"vi": "📡 *AUTO SIGNAL* (by @TNVGold_bot)", "en": "📡 *AUTO SIGNAL* (by @TNVGold_bot)"},
    "auto_signal_sig_line": {"vi": "{emoji} *{stype}* | *Score: {score}/10* ✅", "en": "{emoji} *{stype}* | *Score: {score}/10* ✅"},
    "auto_signal_entry": {"vi": "🔹 *Entry:* `{value}`", "en": "🔹 *Entry:* `{value}`"},
    "auto_signal_sl": {"vi": "🔹 *Stop Loss (SL):* `{value}`", "en": "🔹 *Stop Loss (SL):* `{value}`"},
    "auto_signal_tp": {"vi": "🔹 *Take Profit (TP):* `{value}`", "en": "🔹 *Take Profit (TP):* `{value}`"},
    "auto_signal_market_update": {"vi": "📊 *Market Update:*", "en": "📊 *Market Update:*"},
    "auto_signal_current_price": {"vi": "• Giá hiện tại: `{value}`", "en": "• Current Price: `{value}`"},
    "auto_signal_n": {"vi": "• N: `{value}`", "en": "• N: `{value}`"},
    "auto_signal_long": {"vi": "🟢 *LONG* — Score {score}/10 ✅", "en": "🟢 *LONG* — Score {score}/10 ✅"},
    "auto_signal_short": {"vi": "🔴 *SHORT* — Score {score}/10 ✅", "en": "🔴 *SHORT* — Score {score}/10 ✅"},
    # Feature 2: Tổng kết cuối ngày
    "eod_title": {"vi": "📊 *TỔNG KẾT CUỐI NGÀY — XAUUSD* (by @TNVGold_bot)", "en": "📊 *END-OF-DAY SUMMARY — XAUUSD* (by @TNVGold_bot)"},
    "eod_tnv": {"vi": "📡 *TNV Hôm nay:*", "en": "📡 *TNV Today:*"},
    "eod_signals": {"vi": "• Tín hiệu: {total} ({wins} ✅ / {losses} ❌)", "en": "• Signals: {total} ({wins} ✅ / {losses} ❌)"},
    "eod_winrate": {"vi": "• Win rate: {win_rate}%", "en": "• Win rate: {win_rate}%"},
    "eod_r": {"vi": "• Tổng R: {total_r}", "en": "• Total R: {total_r}"},
    # Feature 4: Lịch sử
    "hist_title": {"vi": "📜 *LỊCH SỬ TÍN HIỆU* (by @TNVGold_bot)", "en": "📜 *SIGNAL HISTORY* (by @TNVGold_bot)"},
    "hist_empty": {"vi": "Chưa có tín hiệu nào.", "en": "No signals yet."},
    "hist_status_tp": {"vi": "✅ TP", "en": "✅ TP"},
    "hist_status_sl": {"vi": "❌ SL", "en": "❌ SL"},
    "hist_status_open": {"vi": "⏳ mở", "en": "⏳ open"},
    # Feature 5: Thống kê
    "stats_text": {"vi": "📊 *THỐNG KÊ TNV ({days} ngày)* (by @TNVGold_bot)\n• Tín hiệu: {total} ({long} LONG / {short} SHORT)\n• Win rate: {win_rate}%\n• Tổng R: {total_r}R\n• Đã đóng: {wins} thắng / {losses} thua", "en": "📊 *TNV STATS ({days} days)* (by @TNVGold_bot)\n• Signals: {total} ({long} LONG / {short} SHORT)\n• Win rate: {win_rate}%\n• Total R: {total_r}R\n• Closed: {wins} wins / {losses} losses"},
    # ── Giai đoạn 1: Inline keyboard /start (1.1) ─────────
    "btn_xau": {"vi": "📊 Báo cáo /xau", "en": "📊 /xau Report"},
    "btn_candle": {"vi": "🕯 /candle", "en": "🕯 /candle"},
    "btn_history": {"vi": "📜 Lịch sử", "en": "📜 History"},
    "btn_stats": {"vi": "📈 Thống kê", "en": "📈 Stats"},
    "btn_price": {"vi": "💰 Giá", "en": "💰 Price"},
    "btn_news": {"vi": "📰 Tin tức", "en": "📰 News"},
    "btn_lang": {"vi": "🌐 Ngôn ngữ", "en": "🌐 Language"},
    "btn_settings": {"vi": "⚙️ Cài đặt", "en": "⚙️ Settings"},
    "btn_tf": {"vi": "⏱ Khung thời gian", "en": "⏱ Timeframe"},
    "btn_tf_menu": {"vi": "📊 *Chọn khung thời gian*", "en": "📊 *Choose timeframe*"},
    "btn_m5": {"vi": "M5", "en": "M5"},
    "btn_m15": {"vi": "M15", "en": "M15"},
    "btn_m30": {"vi": "M30", "en": "M30"},
    "btn_h1": {"vi": "H1", "en": "H1"},
    "btn_h4": {"vi": "H4", "en": "H4"},
    "btn_d1": {"vi": "D1", "en": "D1"},
    "btn_back": {"vi": "◀️ Quay lại", "en": "◀️ Back"},
    "btn_lang_menu": {"vi": "🌐 *Chọn ngôn ngữ*", "en": "🌐 *Choose language*"},
    "btn_lang_vi": {"vi": "🇻🇳 Tiếng Việt", "en": "🇻🇳 Vietnamese"},
    "btn_lang_en": {"vi": "🇬🇧 English", "en": "🇬🇧 English"},
    # ── Giai đoạn 1: /settings (1.2) ─────────────────────
    "settings_title": {"vi": "⚙️ *CÀI ĐẶT*", "en": "⚙️ *SETTINGS*"},
    "settings_hint": {"vi": "_Chạm vào nút để bật/tắt._", "en": "_Tap buttons to toggle._"},
    "settings_auto_signal": {"vi": "📡 Tín hiệu tự động", "en": "📡 Auto signals"},
    "settings_news": {"vi": "📰 Cảnh báo tin tức", "en": "📰 News alerts"},
    "settings_eod": {"vi": "📊 Tổng kết cuối ngày", "en": "📊 End-of-day summary"},
    "settings_daily": {"vi": "📰 Báo cáo sáng/tối", "en": "📰 Daily report"},
    "settings_min_score": {"vi": "🎯 Ngưỡng Score", "en": "🎯 Score threshold"},
    "settings_on": {"vi": "🟢 BẬT", "en": "🟢 ON"},
    "settings_off": {"vi": "🔴 TẮT", "en": "🔴 OFF"},
    "settings_saved": {"vi": "✅ Đã lưu: {item} = {value}", "en": "✅ Saved: {item} = {value}"},
    # ── Giai đoạn 1: /ping + /uptime (1.4) ────────────────
    "ping_text": {"vi": "🏓 Pong! Bot đang hoạt động bình thường.", "en": "🏓 Pong! Bot is running normally."},
    "uptime_title": {"vi": "⏱ *THÔNG TIN BOT*", "en": "⏱ *BOT STATUS*"},
    "uptime_runtime": {"vi": "• Thời gian chạy: {uptime}", "en": "• Uptime: {uptime}"},
    "uptime_source": {"vi": "• Nguồn dữ liệu: {source}", "en": "• Data source: {source}"},
    "uptime_signals": {"vi": "• Tín hiệu hôm nay: {signals}", "en": "• Signals today: {signals}"},
    "uptime_price": {"vi": "• Giá hiện tại: `${price:.2f}`", "en": "• Current price: `${price:.2f}`"},
    # ── Báo cáo đầu phiên (Session report) ────────────────
    "settings_session": {"vi": "📊 Báo cáo đầu phiên", "en": "📊 Session report"},
    "settings_session_times": {"vi": "🕑 Giờ gửi", "en": "🕑 Send times"},
    "session_title": {
        "vi": "📊 *BÁO CÁO ĐẦU PHIÊN — {session}* (by @TNVGold_bot)",
        "en": "📊 *SESSION REPORT — {session}* (by @TNVGold_bot)",
    },
    "session_london": {"vi": "London", "en": "LONDON"},
    "session_newyork": {"vi": "New York", "en": "NEW YORK"},
    "session_asia": {"vi": "Châu Á", "en": "ASIA"},
    "session_price": {"vi": "Giá: ${price:.2f}", "en": "Price: ${price:.2f}"},
    "session_trend": {"vi": "• Trend M5: {trend} ➡️ {dir}", "en": "• Trend M5: {trend} ➡️ {dir}"},
    "session_prediction": {"vi": "• Dự đoán phiên: {dir}", "en": "• Session prediction: {dir}"},
    "session_signal": {"vi": "📡 *TNVGold: {signal}*", "en": "📡 *TNVGold: {signal}*"},
    "session_signal_none": {"vi": "CHỜ — không có tín hiệu mới.", "en": "WAIT — no new signal."},
    "session_signal_long": {"vi": "🟢 LONG — Score {score}/10", "en": "🟢 LONG — Score {score}/10"},
    "session_signal_short": {"vi": "🔴 SHORT — Score {score}/10", "en": "🔴 SHORT — Score {score}/10"},
    "session_disclaimer": {
        "vi": "_Báo cáo đầu phiên, tham khảo — không phải lời khuyên tài chính._",
        "en": "_Session report, for reference only — not financial advice._",
    },
    # Trend theo vị trí so SMA (session report)
    "session_trend_below": {
        "vi": "Dưới SMA20 (${s20:.2f}) & SMA50 (${s50:.2f})",
        "en": "Below SMA20 (${s20:.2f}) & SMA50 (${s50:.2f})",
    },
    "session_trend_above": {
        "vi": "Trên SMA20 (${s20:.2f}) & SMA50 (${s50:.2f})",
        "en": "Above SMA20 (${s20:.2f}) & SMA50 (${s50:.2f})",
    },
    "session_trend_between": {
        "vi": "Giữa SMA20 (${s20:.2f}) & SMA50 (${s50:.2f})",
        "en": "Between SMA20 (${s20:.2f}) & SMA50 (${s50:.2f})",
    },
    "session_trend_no_sma": {"vi": "Chưa đủ dữ liệu SMA", "en": "Not enough SMA data"},
    # RSI state
    "rsi_oversold": {"vi": "Quá bán", "en": "Oversold"},
    "rsi_overbought": {"vi": "Quá mua", "en": "Overbought"},
    "rsi_neutral": {"vi": "Trung tính", "en": "Neutral"},
    # RSI/MACD + Range (session report)
    "session_rsi_macd": {
        "vi": "• RSI (14): {rsi:.1f} ({rsi_state}) | MACD: {macd:+.2f}",
        "en": "• RSI (14): {rsi:.1f} ({rsi_state}) | MACD: {macd:+.2f}",
    },
    "session_range": {
        "vi": "• ATR (14): ${atr:.2f} | Phạm vi: ${lo:.0f} - ${hi:.0f}",
        "en": "• ATR (14): ${atr:.2f} | Range: ${lo:.0f} - ${hi:.0f}",
    },
    "session_range_na": {
        "vi": "• ATR (14): ${atr:.2f} | Phạm vi: N/A",
        "en": "• ATR (14): ${atr:.2f} | Range: N/A",
    },
    # ── AI chat (Chat tự do) ──────────────────────────────
    "ai_on": {
        "vi": "💬 *AI CHAT ĐÃ BẬT* — nhắn tin bình thường để hỏi về vàng.",
        "en": "💬 *AI CHAT ENABLED* — send a normal message to ask about gold.",
    },
    "ai_off": {"vi": "💬 AI chat đã tắt.", "en": "💬 AI chat disabled."},
    "ai_usage": {"vi": "Cách dùng: /ai on hoặc /ai off", "en": "Usage: /ai on or /ai off"},
    "ai_error": {"vi": "⚠️ Lỗi kết nối AI. Thử lại sau.", "en": "⚠️ AI connection error. Try again later."},
    "ai_no_key": {
        "vi": "⚠️ Chưa có AI provider khả dụng. Dùng /model và /keys để cấu hình.",
        "en": "⚠️ No AI provider available. Use /model and /keys to configure.",
    },
    "ai_thinking": {"vi": "🤔 Đang phân tích...", "en": "🤔 Analyzing..."},

    # ── Subscription / Register / Redeem ─────────────────
    "reg_welcome_new": {
        "vi": "👋 Chào mừng! Gõ /register để đăng ký tài khoản (dùng thử {days} ngày miễn phí).",
        "en": "👋 Welcome! Type /register to sign up (free {days}-day trial).",
    },
    "reg_already": {
        "vi": "✅ Bạn đã đăng ký rồi. Dùng /myplan để xem gói hiện tại.",
        "en": "✅ You're already registered. Use /myplan to view your plan.",
    },
    "reg_already_trialed": {
        "vi": "⚠️ Bạn đã dùng thử 7 ngày rồi.\n\nLiên hệ admin @TuanNguyenTrader để mua Pro.",
        "en": "⚠️ You've already used your 7-day trial.\n\nContact admin @TuanNguyenTrader to purchase Pro.",
    },
    "reg_success": {
        "vi": "🎉 *Đăng ký thành công!*\n\nGói: *{tier}*\nHạn dùng: {expiry}\nCòn lại: {days_left} ngày\n\nDùng /redeem <mã> để gia hạn bất kỳ lúc nào.",
        "en": "🎉 *Registration successful!*\n\nPlan: *{tier}*\nExpires: {expiry}\nDays left: {days_left}\n\nUse /redeem <code> to renew anytime.",
    },
    "myplan_title": {
        "vi": "📋 *GÓI CỦA BẠN*",
        "en": "📋 *YOUR PLAN*",
    },
    "myplan_tier": {"vi": "Gói", "en": "Plan"},
    "myplan_status": {"vi": "Trạng thái", "en": "Status"},
    "myplan_registered": {"vi": "Đăng ký", "en": "Registered"},
    "myplan_expires": {"vi": "Hết hạn", "en": "Expires"},
    "myplan_renewed": {"vi": "Gia hạn lần cuối", "en": "Last renewed"},
    "myplan_never": {"vi": "Không hết hạn", "en": "Never expires"},
    "myplan_expired": {"vi": "⚠️ Đã hết hạn", "en": "⚠️ Expired"},
    "myplan_active": {"vi": "✅ Đang dùng", "en": "✅ Active"},
    "myplan_days_left": {"vi": "Còn {n} ngày", "en": "{n} days left"},
    "myplan_remind": {
        "vi": "💡 /redeem <mã> để gia hạn.",
        "en": "💡 /redeem <code> to renew.",
    },
    "redeem_usage": {
        "vi": "Cú pháp: /redeem <mã>\nVD: /redeem XK-AB12CD3E",
        "en": "Usage: /redeem <code>\nE.g.: /redeem XK-AB12CD3E",
    },
    "redeem_not_registered": {
        "vi": "⚠️ Bạn cần /register trước khi nạp mã.",
        "en": "⚠️ Please /register before redeeming a code.",
    },
    "redeem_invalid": {
        "vi": "❌ Mã không tồn tại hoặc đã được sử dụng.",
        "en": "❌ Code not found or already used.",
    },
    "redeem_success": {
        "vi": "✅ *Gia hạn thành công!*\n\nMã: `{code}`\nGói: *{tier}* ({days} ngày)\nHạn mới: {expiry}\nCòn lại: {days_left} ngày",
        "en": "✅ *Renewal successful!*\n\nCode: `{code}`\nPlan: *{tier}* ({days} days)\nNew expiry: {expiry}\nDays left: {days_left}",
    },
    "expire_warn": {
        "vi": "⏰ Gói {tier} của bạn sắp hết hạn (còn {days} ngày).\n\n/redeem <mã> để gia hạn ngay.",
        "en": "⏰ Your {tier} plan expires in {days} days.\n\n/redeem <code> to renew now.",
    },
    "expire_done": {
        "vi": "⚠️ Gói {tier} của bạn đã hết hạn. Bạn đã được hạ về gói Free.\n\n/redeem <mã> để tiếp tục dùng Premium/Pro.",
        "en": "⚠️ Your {tier} plan has expired. Downgraded to Free.\n\n/redeem <code> to continue with Premium/Pro.",
    },

    # ── Admin: /gencode, /users, /renew, /expire ─────────
    "admin_only": {
        "vi": "⚠️ Lệnh này chỉ dành cho quản trị viên.",
        "en": "⚠️ Admin only command.",
    },
    "gencode_usage": {
        "vi": "Cú pháp: /gencode <gói> <ngày> [số lượng]\nVD: /gencode pro 30 5\nGói: free | pro",
        "en": "Usage: /gencode <tier> <days> [count]\nE.g.: /gencode pro 30 5\nTiers: free | pro",
    },
    "gencode_invalid_tier": {
        "vi": "❌ Gói không hợp lệ. Dùng: free / pro",
        "en": "❌ Invalid tier. Use: free / pro",
    },
    "gencode_created": {
        "vi": "✅ Đã tạo {n} mã *{tier} {days} ngày*:\n\n{codes}",
        "en": "✅ Created {n} code(s) *{tier} {days} days*:\n\n{codes}",
    },
    "users_list_title": {
        "vi": "👥 *DANH SÁCH USER*",
        "en": "👥 *USER LIST*",
    },
    "users_list_empty": {
        "vi": "Chưa có user nào đăng ký.",
        "en": "No registered users yet.",
    },
    "users_list_line": {
        "vi": "• `{cid}` | {tier} | {status}{days}",
        "en": "• `{cid}` | {tier} | {status}{days}",
    },
    "users_list_footer": {
        "vi": "\nTổng: {free} free | {pro} pro",
        "en": "\nTotal: {free} free | {pro} pro",
    },
    "renew_usage": {
        "vi": "Cú pháp: /renew <chat_id> <gói> <ngày>\nVD: /renew 123456 pro 30",
        "en": "Usage: /renew <chat_id> <tier> <days>\nE.g.: /renew 123456 pro 30",
    },
    "renew_done": {
        "vi": "✅ Đã gia hạn user {cid}: *{tier}* thêm {days} ngày.\nHạn mới: {expiry}",
        "en": "✅ Renewed user {cid}: *{tier}* +{days} days.\nNew expiry: {expiry}",
    },
    "expire_done_admin": {
        "vi": "✅ Đã hạ user {cid} về gói Free.",
        "en": "✅ User {cid} downgraded to Free.",
    },
    "gencode_list_title": {
        "vi": "🎟️ *DANH SÁCH MÃ KÍCH HOẠT*",
        "en": "🎟️ *REDEEM CODE LIST*",
    },
    "gencode_list_line": {
        "vi": "• `{code}` | {tier} {days}d | {used} | {created}",
        "en": "• `{code}` | {tier} {days}d | {used} | {created}",
    },
    "users_list_line_v2": {
        "vi": "• `{cid}` | {tier} | {status}{days} | mã: {code}",
        "en": "• `{cid}` | {tier} | {status}{days} | code: {code}",
    },
    "users_no_code": {
        "vi": "chưa có",
        "en": "none",
    },
    # ── Từ tnv_engine ──
    "error_prefix": {"vi": "⚠️ {}"},
    "no_s1_data": {"vi": "⚠️ Không có dữ liệu SYSTEM 1.", "en": "⚠️ No SYSTEM 1 data."},
    "price_n": {"vi": "Giá: ${:.2f} | N : ${:.2f}", "en": "Price: ${:.2f} | N : ${:.2f}"},
    "htf_not_against": {"vi": "  HTF M15: KHÔNG ngược chiều ✅", "en": "  HTF M15: NOT AGAINST ✅"},
    "htf_against": {"vi": "  HTF M15: ĐANG NGƯỢC CHIỀU ❌", "en": "  HTF M15: AGAINST ❌"},
    "htf_against_note": {"vi": " *Chỉ vào lệnh 50% risk, hoặc chờ M15 đảo chiều.*", "en": " *Enter with 50% risk, or wait for M15 reversal.*"},
    "exit_target_reached": {"vi": "  Đã đạt {:.0f}% mục tiêu — cân nhắc chốt lời sớm", "en": "  Reached {:.0f}% of target — consider taking profit early"},
    "below_threshold": {"vi": "  Dưới ngưỡng 5 — bỏ qua", "en": "  Below threshold 5 — skip"},
    "below_threshold_note": {"vi": "*Tín hiệu dưới ngưỡng Score 5. Không vào lệnh.*", "en": "*Signal below Score 5 threshold. No entry.*"},
    "sideway_range": {"vi": "⬜ *CHỜ* — Thị trường đi ngang, giá trong biên độ ${:.2f} - ${:.2f} không vào lệnh.", "en": "⬜ *WAIT* — Market sideways, price within ${:.2f} - ${:.2f} range, no entry."},
    "sideway_no_breakout": {"vi": "⬜ *CHỜ* — Chưa có tín hiệu breakout.", "en": "⬜ *WAIT* — No breakout signal yet."},
    "signal_long": {"vi": "TÍN HIỆU LONG", "en": "LONG SIGNAL"},
    "signal_short": {"vi": "TÍN HIỆU SHORT", "en": "SHORT SIGNAL"},
    "signal_exit_long": {"vi": "TÍN HIỆU EXIT LONG", "en": "EXIT LONG SIGNAL"},
    "signal_exit_short": {"vi": "TÍN HIỆU EXIT SHORT", "en": "EXIT SHORT SIGNAL"},
    "signal_below": {"vi": "TÍN HIỆU {}", "en": "{} SIGNAL"},
    "htf_not_against_dot": {"vi": "• *HTF M15:* Không ngược chiều ✅", "en": "• *HTF M15:* Not against ✅"},
    "htf_against_dot": {"vi": "• *HTF M15:* Đang ngược chiều ❌ — chỉ vào lệnh 50% risk", "en": "• *HTF M15:* Against ❌ — enter with 50% risk only"},
    "exit_target_reached_dot": {"vi": "• Đã đạt {:.0f}% mục tiêu — cân nhắc chốt lời sớm.", "en": "• Reached {:.0f}% of target — consider taking profit early."},
    "below_threshold_dot": {"vi": "• Dưới ngưỡng 5 — bỏ qua", "en": "• Below threshold 5 — skip"},
    "below_threshold_note_italic": {"vi": "_Tín hiệu dưới ngưỡng Score 5. Không vào lệnh._", "en": "_Signal below Score 5 threshold. No entry._"},
    "sideway_range_dot": {"vi": "⬜ *CHỜ* — Thị trường đi ngang, giá trong biên độ `${:.2f}` - `${:.2f}` không vào lệnh.", "en": "⬜ *WAIT* — Market sideways, price within `${:.2f}` - `${:.2f}`, no entry."},
    "sideway_no_breakout_dot": {"vi": "⬜ *CHỜ* — Chưa có tín hiệu breakout.", "en": "⬜ *WAIT* — No breakout signal yet."},
    "wait_no_signal": {"vi": "⏳ *CHỜ* — chưa có tín hiệu đủ điều kiện.", "en": "⏳ *WAIT* — no qualifying signal yet."},
    # ── Từ report ──
    "session_asia_rep": {"vi": "Phiên Asia", "en": "Asia session"},
    "session_london_rep": {"vi": "Phiên London", "en": "London session"},
    "session_overlap": {"vi": "Phiên London/NY overlap", "en": "London/NY overlap"},
    "session_ny": {"vi": "Phiên New York", "en": "New York Session"},
    "trend_down": {"vi": "GIẢM", "en": "DOWN"},
    "trend_up": {"vi": "TĂNG", "en": "UP"},
    "trend_sideways": {"vi": "ĐI NGANG", "en": "SIDEWAYS"},
    "pos_below_rep": {
        "vi": "Dưới SMA20 (`${s20:.2f}`) & SMA50 (`${s50:.2f}`) ➡️ GIẢM",
        "en": "Below SMA20 (`${s20:.2f}`) & SMA50 (`${s50:.2f}`) ➡️ DOWN",
    },
    "pos_above_rep": {
        "vi": "Trên SMA20 (`${s20:.2f}`) & SMA50 (`${s50:.2f}`) ➡️ TĂNG",
        "en": "Above SMA20 (`${s20:.2f}`) & SMA50 (`${s50:.2f}`) ➡️ UP",
    },
    "pos_between_rep": {
        "vi": "Giữa SMA20 (`${s20:.2f}`) & SMA50 (`${s50:.2f}`) ➡️ ĐI NGANG",
        "en": "Between SMA20 (`${s20:.2f}`) & SMA50 (`${s50:.2f}`) ➡️ SIDEWAYS",
    },
    "pos_no_sma": {"vi": "Chưa đủ dữ liệu SMA", "en": "Not enough SMA data"},
    "rsi_oversold": {"vi": "Quá bán", "en": "Oversold"},
    "rsi_overbought": {"vi": "Quá mua", "en": "Overbought"},
    "rsi_neutral": {"vi": "Trung tính", "en": "Neutral"},
    "pred_up": {"vi": "TĂNG", "en": "UP"},
    "pred_down": {"vi": "GIẢM", "en": "DOWN"},
    "pred_slight_up": {"vi": "TĂNG NHẸ", "en": "SLIGHTLY BULLISH"},
    "pred_slight_down": {"vi": "GIẢM NHẸ", "en": "SLIGHTLY BEARISH"},
    "pred_sideways": {"vi": "ĐI NGANG", "en": "SIDEWAYS"},
    "pred_line": {
        "vi": "• Dự đoán nến {tf} tiếp theo:",
        "en": "• Next {tf} candle prediction:",
    },
    "news_title": {"vi": "📰 *TIN TỨC SẮP TỚI (USD)*", "en": "📰 *UPCOMING NEWS (USD)*"},
    "news_forecast": {"vi": "Dự báo:", "en": "Forecast:"},
    "news_previous": {"vi": "Trước:", "en": "Previous:"},
    "news_empty": {"vi": "• Không có tin USD quan trọng trong 4h tới.", "en": "• No major USD news in the next 4 hours."},
    "tnv_no_data": {"vi": "⚠️ Không có dữ liệu TNV.", "en": "⚠️ No TNV data."},
    "atr_range": {
        "vi": "• ATR (14): {atr} | Phạm vi: {rng}",
        "en": "• ATR (14): {atr} | Range: {rng}",
    },
    # ── Từ scheduler ──
    "daily_title": {
        "vi": "📰 *XAUUSD Daily Report* — {time} (by @TNVGold_bot)",
        "en": "📰 *XAUUSD Daily Report* — {time} (by @TNVGold_bot)",
    },
    "price_rsi_atr": {
        "vi": "Giá: *${price:.2f}* | RSI: {rsi:.0f} | ATR: ${atr:.2f}",
        "en": "Price: *${price:.2f}* | RSI: {rsi:.0f} | ATR: ${atr:.2f}",
    },
    "m5_candles": {
        "vi": "10 nến M5: 🟢{bull} / 🔴{bear}",
        "en": "10 M5 candles: 🟢{bull} / 🔴{bear}",
    },
    "prediction": {
        "vi": "🎯 Dự đoán: *{dir}*",
        "en": "🎯 Prediction: *{dir}*",
    },
    "price_simple": {
        "vi": "Giá: *${price:.2f}*",
        "en": "Price: *${price:.2f}*",
    },
    "m5_indicators": {"vi": "*Chỉ báo M5:*", "en": "*M5 Indicators:*"},
    "candle_analysis": {"vi": "*Phân tích nến:*", "en": "*Candle analysis:*"},
    "close_position": {
        "vi": "Vị trí đóng: {pos:.0%}",
        "en": "Close position: {pos:.0%}",
    },
    "disclaimer": {
        "vi": "_Báo cáo tự động, tham khảo — không phải lời khuyên tài chính._",
        "en": "_Auto-generated report, for reference only — not financial advice._",
    },
    "no_data": {"vi": "⚠️ Chưa có dữ liệu.", "en": "⚠️ No data available."},
    "session_range": {
        "vi": "• ATR (14): ${atr:.2f} | Range: `${lo:.0f}` - `${hi:.0f}`",
        "en": "• ATR (14): ${atr:.2f} | Range: `${lo:.0f}` - `${hi:.0f}`",
    },
    "dir_up": {"vi": "UP (tăng)", "en": "UP"},
    "dir_down": {"vi": "DOWN (giảm)", "en": "DOWN"},
    "dir_slight_up": {"vi": "TĂNG NHẸ (cẩn thận)", "en": "SLIGHTLY BULLISH"},
    "dir_slight_down": {"vi": "GIẢM NHẸ (cẩn thận)", "en": "SLIGHTLY BEARISH"},
    "dir_side": {"vi": "SIDE WAYS (đi ngang, chờ breakout)", "en": "SIDEWAYS (wait for breakout)"},
    # ── Từ candle_analysis ──
    "cand_header": {"vi": "📊 *PHÂN TÍCH NẾN ({tf})* (by @TNVGold_bot)", "en": "📊 *CANDLESTICK ANALYSIS ({tf})* (by @TNVGold_bot)"},
    "last_candle": {"vi": "• *Nến cuối:*", "en": "• *Last candle:*"},
    "close_pos": {"vi": "• *Vị trí đóng:*", "en": "• *Close position:*"},
    "range_pct": {"vi": "({pct} chiều cao nến)", "en": "({pct} of candle height)"},
    "chain": {"vi": "• *Chuỗi {n} nến:* 🟢 {b} xanh / 🔴 {r} đỏ / ⚪ {d} doji (Momentum: {m})", "en": "• *Last {n} candles:* 🟢 {b} green / 🔴 {r} red / ⚪ {d} doji (Momentum: {m})"},
    "reversal": {"vi": "• *Tín hiệu đảo chiều:*", "en": "• *Reversal signal:*"},
    "reversal_bull": {"vi": "Nến xanh bứt phá sau chuỗi đỏ, đóng cửa cao", "en": "Green breakout candle after a red streak, closed high"},
    "reversal_bear": {"vi": "Nến đỏ bứt phá sau chuỗi xanh, đóng cửa thấp", "en": "Red breakout candle after a green streak, closed low"},
    "predict": {"vi": "• 🔮 *Dự đoán nến tiếp:*", "en": "• 🔮 *Next candle prediction:*"},
    "pos_high": {"vi": "Đóng cửa sát đỉnh", "en": "Closed near high"},
    "pos_low": {"vi": "Đóng cửa sát đáy", "en": "Closed near low"},
    "pos_above_c": {"vi": "Đóng cửa trên thân nến", "en": "Closed above the body"},
    "pos_below_c": {"vi": "Đóng cửa dưới thân nến", "en": "Closed below the body"},
    "pos_mid": {"vi": "Đóng cửa giữa thân nến", "en": "Closed in the middle"},
    "side_bull": {"vi": "Phe mua còn lực", "en": "Buyers still have momentum"},
    "side_bear": {"vi": "Phe bán còn lực", "en": "Sellers still have momentum"},
    "side_buy": {"vi": "Phe mua chiếm ưu thế", "en": "Buyers in control"},
    "side_sell": {"vi": "Phe bán chiếm ưu thế", "en": "Sellers in control"},
    "side_mid": {"vi": "Do dự", "en": "Indecisive"},
    "dir_slight_up_c": {"vi": "TĂNG NHẸ", "en": "SLIGHTLY BULLISH"},
    "dir_slight_down_c": {"vi": "GIẢM NHẸ", "en": "SLIGHTLY BEARISH"},
    "dir_up_c": {"vi": "TĂNG", "en": "UP"},
    "dir_down_c": {"vi": "GIẢM", "en": "DOWN"},
    "dir_side_c": {"vi": "ĐI NGANG", "en": "SIDEWAYS"},
    "note_caution": {"vi": "(⚠️ Cẩn thận nhịp hồi)", "en": "(⚠️ *Watch out for pullbacks*)"},
    "note_breakout": {"vi": "(⚠️ Chờ breakout rõ ràng)", "en": "(⚠️ *Wait for a clear breakout*)"},
}


def t(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    """Lấy chuỗi theo ngôn ngữ, format với kwargs."""
    entry = _STRINGS.get(key, {})
    text = entry.get(lang) or entry.get(DEFAULT_LANG) or key
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError):
        return text


# Hiển thị tier cho đẹp: "pro" → "Pro", "free" → "Free"
_TIER_DISPLAY = {"free": "Free", "pro": "Pro"}


def pretty_tier(tier: str) -> str:
    """Format tier viết hoa chữ cái đầu cho hiển thị đẹp."""
    if not tier:
        return "Free"
    return _TIER_DISPLAY.get(tier.lower(), tier.title())


def get_lang(chat_id) -> str:
    """Lấy ngôn ngữ của chat.

    Ưu tiên: /lang đặt riêng → DEFAULT_LANG_BY_CHAT (theo kênh/nhóm) → mặc định "en".
    """
    lang = kv_get(f"lang:{chat_id}", None)
    if lang in SUPPORTED:
        return lang
    # Chưa đặt riêng → dùng mặc định theo chat (nếu có cấu hình)
    try:
        from config import DEFAULT_LANG_BY_CHAT
        lang = DEFAULT_LANG_BY_CHAT.get(chat_id, DEFAULT_LANG)
    except Exception:
        lang = DEFAULT_LANG
    if lang not in SUPPORTED:
        lang = DEFAULT_LANG
    return lang


def set_lang(chat_id, lang: str) -> bool:
    """Đặt ngôn ngữ cho chat. Trả True nếu hợp lệ."""
    lang = lang.lower().strip()
    if lang not in SUPPORTED:
        return False
    kv_set(f"lang:{chat_id}", lang)
    return True

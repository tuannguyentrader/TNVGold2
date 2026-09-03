"""
bot.py — TNVGold Telegram Bot: phân tích nến XAUUSD + chỉ báo + tín hiệu TNV.
"""

import os
import sys
import logging
import threading
import time
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# Import local modules
sys.path.insert(0, os.path.dirname(__file__))
import config
from storage import (
    init_db, get_candles,
    set_api_key, remove_api_key, list_api_keys,
    set_current_provider, get_current_provider,
    kv_get, kv_set,
)
from collector import get_last_price
from candle_analysis import analyze_candle_sequence, format_sequence_report
from mt5_connector import get_rates, get_mt5_mode
from tnv_engine import analyze_tnv
from report import build_xau_report
from signals import get_history, format_history, get_stats, format_stats

# Helper Markdown + gửi tin an toàn (dùng chung toàn project)
from telegram_safe import escape_md as _escape_md, send as _ts_send
from i18n import t, get_lang, set_lang, pretty_tier
log = logging.getLogger("bot")

# Thời điểm module được nạp — dùng cho /ping (thời gian chạy)
_BOOT_TS = time.time()

# ── Khởi tạo DB ──────────────────────────────────────────
init_db()

# ── Helpers ──────────────────────────────────────────────
# _escape_md đã import từ telegram_safe ở đầu file (DRY)


async def _send(update: Update, text: str, parse_mode="Markdown", reply_markup=None):
    """Gửi text với Markdown.

    - Mặc định parse_mode=Markdown → in đậm/nghiêng hoạt động.
    - Nếu text có ký tự Markdown lẻ (gây lỗi parse) → escape trước khi gửi.
    - Nếu vẫn lỗi → gửi plain text.
    """
    # Escape ký tự Markdown lẻ (tránh lỗi "Can't parse entities")
    safe_text = _escape_md(text)

    # Log chẩn đoán: parse_mode, độ dài, và có escape hay không
    if log.isEnabledFor(logging.DEBUG):
        log.debug("_send parse_mode=%s len=%d escaped=%s text[:60]=%r",
                  parse_mode, len(text), safe_text != text, text[:60])

    try:
        await update.message.reply_text(safe_text, parse_mode=parse_mode, reply_markup=reply_markup)
    except Exception as e:
        log.error("_send Markdown lỗi: %s (parse_mode=%s) — fallback plain", e, parse_mode)
        # Markdown fail → gửi plain
        try:
            await update.message.reply_text(text, reply_markup=reply_markup)
        except Exception as e2:
            log.error("Send lỗi hoàn toàn: %s", e2)


async def _edit(query, text: str, parse_mode="Markdown", reply_markup=None):
    """Edit message với Markdown — có escape + fallback plain text.

    Dùng cho inline keyboard callback. Tránh tình trạng nút bấm không
    phản hồi khi text có ký tự Markdown lẻ (vd: _ trong Gold_bot).
    """
    safe_text = _escape_md(text)
    try:
        await query.edit_message_text(safe_text, parse_mode=parse_mode, reply_markup=reply_markup)
    except Exception as e:
        # Markdown fail → thử plain
        try:
            await query.edit_message_text(text, reply_markup=reply_markup)
        except Exception as e2:
            log.error("Edit lỗi hoàn toàn: %s", e2)


def _main_menu_kb(lang: str) -> InlineKeyboardMarkup:
    """Keyboard chính: full menu, dùng cho cả Free + Pro.

    - Free và Pro đều thấy đầy đủ nút.
    - Chỉ khi bấm nút mới phân biệt tier (Pro-only sẽ báo "tính năng Pro").
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_xau", lang), callback_data="xau:M5"),
            InlineKeyboardButton(t("btn_candle", lang), callback_data="candle:M5"),
        ],
        [
            InlineKeyboardButton(t("btn_history", lang), callback_data="history"),
            InlineKeyboardButton(t("btn_stats", lang), callback_data="stats"),
        ],
        [
            InlineKeyboardButton(t("btn_price", lang), callback_data="price"),
            InlineKeyboardButton(t("btn_news", lang), callback_data="news"),
        ],
        [
            InlineKeyboardButton(t("btn_tf", lang), callback_data="tf"),
            InlineKeyboardButton(t("btn_lang", lang), callback_data="lang"),
            InlineKeyboardButton(t("btn_settings", lang), callback_data="settings"),
        ],
    ])


def _tf_menu_kb(lang: str) -> InlineKeyboardMarkup:
    """Keyboard chọn khung thời gian."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_m5", lang), callback_data="tf:M5"),
            InlineKeyboardButton(t("btn_m15", lang), callback_data="tf:M15"),
            InlineKeyboardButton(t("btn_m30", lang), callback_data="tf:M30"),
        ],
        [
            InlineKeyboardButton(t("btn_h1", lang), callback_data="tf:H1"),
            InlineKeyboardButton(t("btn_h4", lang), callback_data="tf:H4"),
            InlineKeyboardButton(t("btn_d1", lang), callback_data="tf:D1"),
        ],
        [
            InlineKeyboardButton(t("btn_back", lang), callback_data="back"),
        ],
    ])


def _lang_menu_kb(lang: str) -> InlineKeyboardMarkup:
    """Keyboard chọn ngôn ngữ."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_lang_vi", lang), callback_data="lang:vi"),
            InlineKeyboardButton(t("btn_lang_en", lang), callback_data="lang:en"),
        ],
        [
            InlineKeyboardButton(t("btn_back", lang), callback_data="back"),
        ],
    ])


def _settings_text_and_kb(chat_id: int, lang: str):
    """Xây text + keyboard cho menu settings."""
    try:
        from scheduler import get_runtime_settings  # lazy import
        settings = get_runtime_settings(chat_id)
    except Exception as e:
        log.warning("Settings: chưa có runtime settings (%s) — dùng mặc định", e)
        settings = {}
    on_label = t("settings_on", lang)
    off_label = t("settings_off", lang)

    toggle_keys = [
        ("auto_signal", t("settings_auto_signal", lang)),
        ("news", t("settings_news", lang)),
        ("eod", t("settings_eod", lang)),
    ]

    lines = [t("settings_title", lang), "", t("settings_hint", lang), ""]
    buttons = []
    for key, label in toggle_keys:
        is_on = settings.get(key, False)
        status = on_label if is_on else off_label
        lines.append(f"{label}: {status}")
        cb = f"set:{key}"
        btn_label = f"{'🟢' if is_on else '🔴'} {label}"
        buttons.append([InlineKeyboardButton(btn_label, callback_data=cb)])

    # min_score row
    min_score = settings.get("min_score", 5)
    lines.append("")
    lines.append(f"{t('settings_min_score', lang)}: {min_score}/10")
    score_btns = [
        InlineKeyboardButton(str(s), callback_data=f"set:min_score:{s}")
        for s in (5, 6, 7, 8)
    ]
    buttons.append(score_btns)

    buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data="back")])

    return "\n".join(lines), InlineKeyboardMarkup(buttons)


def check_allowed(update: Update) -> bool:
    """Kiểm tra chat id có được phép không."""
    if not config.is_allowed(update.effective_chat.id):
        return False
    return True


async def _is_chat_admin(update: Update) -> bool:
    """Kiểm tra user có phải admin/creator của group/channel không.
    Chat private luôn trả True (không có khái niệm admin).
    Group/channel: fail closed — lỗi hoặc thiếu user → False."""
    chat = update.effective_chat
    user = update.effective_user
    if chat is None or user is None:
        return False
    if chat.type == "private":
        return True
    try:
        member = await chat.get_member(user.id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        log.warning("Admin check lỗi (chat %s, user %s): %s", chat.id, user.id, e)
        return False


# ── Handlers ─────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not check_allowed(update):
        return
    chat = update.effective_chat
    # Public: tự động đăng ký chat RIÊNG (private) nhận tin tự động
    # (LONG/SHORT, EOD...) — không cần khai báo XAU_CHAT_IDS thủ công.
    # Chỉ đăng ký private; group/channel vẫn theo XAU_CHAT_IDS.
    if chat is not None and chat.type == "private":
        try:
            from scheduler import add_active_chat
            add_active_chat(chat.id)
        except Exception as e:
            log.warning("Tự đăng ký chat %s lỗi: %s", chat.id, e)
    lang = get_lang(update.effective_chat.id)
    from storage import get_tier
    user_tier = get_tier(update.effective_chat.id)
    await _send(update, _main_menu_text(lang), reply_markup=_main_menu_kb(lang))


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """📖 /help — hướng dẫn chi tiết."""
    if not check_allowed(update):
        return
    await cmd_help_detail(update, ctx)


async def cmd_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    price = get_last_price()
    if price:
        await _send(update, t("xau_price", lang, price=price))
    else:
        # Thử fetch trực tiếp
        from collector import fetch_gold_price
        data = fetch_gold_price()
        if data:
            await _send(update, t("xau_price", lang, price=data['price']) + t("price_source", lang))
        else:
            await _send(update, t("price_error", lang))


async def cmd_news(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """⏰ /news — lịch kinh tế XAUUSD hôm nay (Forex Factory)."""
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    # Quota check (ai_calls)
    try:
        from storage import check_quota
        chat_id = update.effective_chat.id
        if not check_quota(chat_id, "ai_calls"):
            await _send(update, t("quota_ai_exceeded", lang))
            return
    except Exception:
        pass
    await _send(update, t("analyzing", lang))

    try:
        from forex_factory import get_calendar, filter_usd_events, format_news
        events = get_calendar()
        usd_events = filter_usd_events(events)
        text = format_news(usd_events, lang=lang)
        await _send(update, text)
        try:
            from storage import incr_usage
            incr_usage(update.effective_chat.id, "ai_calls", 1)
        except Exception:
            pass
    except Exception as e:
        log.warning("News lỗi: %s", e)
        await _send(update, "⚠️ Không lấy được lịch kinh tế. Thử lại sau." if lang == "vi" else "⚠️ Could not fetch economic calendar. Try again later.")


async def cmd_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """📜 /history — lịch sử tín hiệu TNV gần nhất."""
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    # Quota check (ai_calls)
    try:
        from storage import check_quota
        chat_id = update.effective_chat.id
        if not check_quota(chat_id, "ai_calls"):
            await _send(update, t("quota_ai_exceeded", lang))
            return
    except Exception:
        pass

    limit = 10
    if ctx.args:
        try:
            limit = int(ctx.args[0])
            if limit < 1:
                limit = 1
            elif limit > 30:
                limit = 30
        except ValueError:
            pass

    try:
        sigs = get_history(limit)
        text = format_history(sigs, lang)
        await _send(update, text)
        try:
            from storage import incr_usage
            incr_usage(update.effective_chat.id, "ai_calls", 1)
        except Exception:
            pass
    except Exception as e:
        log.error("history lỗi: %s", e)
        await _send(update, "⚠️ Không lấy được lịch sử tín hiệu." if lang == "vi" else "⚠️ Could not fetch signal history.")


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """📊 /stats — thống kê hiệu suất tín hiệu TNV."""
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    # Quota check (ai_calls)
    try:
        from storage import check_quota
        chat_id = update.effective_chat.id
        if not check_quota(chat_id, "ai_calls"):
            await _send(update, t("quota_ai_exceeded", lang))
            return
    except Exception:
        pass

    days = 30
    if ctx.args:
        try:
            days = int(ctx.args[0])
            if days < 1:
                days = 1
            elif days > 90:
                days = 90
        except ValueError:
            pass

    try:
        stats = get_stats(days)
        text = format_stats(stats, lang)
        await _send(update, text)
        try:
            from storage import incr_usage
            incr_usage(update.effective_chat.id, "ai_calls", 1)
        except Exception:
            pass
    except Exception as e:
        log.error("stats lỗi: %s", e)
        await _send(update, "⚠️ Không lấy được thống kê." if lang == "vi" else "⚠️ Could not fetch stats.")


async def _candle_for(update: Update, timeframe: str = "M5") -> str:
    """Xây báo cáo /candle cho khung thời gian đã chọn. Trả None nếu thiếu dữ liệu."""
    lang = get_lang(update.effective_chat.id)

    # Đọc nến từ MT5 (ưu tiên) hoặc DB
    if get_mt5_mode() == "local":
        candles = get_rates("XAUUSD", timeframe, count=20)
    else:
        candles = get_candles(limit=20)

    if not candles or len(candles) < 3:
        return None

    # Phân tích chuỗi nến
    result = analyze_candle_sequence(candles, lookback=min(10, len(candles)))
    return format_sequence_report(result, timeframe=timeframe, lang=lang)


async def cmd_candle_analysis(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /candle — phân tích từng nến (O/H/L/C + vị trí đóng) → dự đoán nến tiếp theo.
    /candle m15 / m30 / h1 / h4 / d1 — chọn khung. Mặc định M5.
    Alias cũ: /nhan
    """
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    # Quota check (ai_calls)
    try:
        from storage import check_quota
        chat_id = update.effective_chat.id
        if not check_quota(chat_id, "ai_calls"):
            await _send(update, t("quota_ai_exceeded", lang))
            return
    except Exception:
        pass

    args = " ".join(ctx.args or []).lower()
    timeframe = "M5"
    if "h1" in args:
        timeframe = "H1"
    elif "h4" in args:
        timeframe = "H4"
    elif "d1" in args:
        timeframe = "D1"
    elif "m15" in args:
        timeframe = "M15"
    elif "m30" in args:
        timeframe = "M30"

    report = await _candle_for(update, timeframe)
    if report is None:
        await _send(update, t("not_enough_candles", lang))
        return

    await _send(update, report)
    try:
        from storage import incr_usage
        incr_usage(update.effective_chat.id, "ai_calls", 1)
    except Exception:
        pass


async def _xau_for(update: Update, timeframe: str = "M5", detail: bool = False) -> str:
    """Xây báo cáo /xau cho khung thời gian đã chọn. Trả None nếu thiếu dữ liệu."""
    lang = get_lang(update.effective_chat.id)

    # Lấy nến
    candles = None
    candles_htf = None
    if get_mt5_mode() == "local":
        candles = get_rates("XAUUSD", timeframe, count=300)
        # HTF cho TNV: M15 cho M5, H1 cho M15/M30, H4 cho H1
        htf_tf = {"M5": "M15", "M15": "H1", "M30": "H1", "H1": "H4"}.get(timeframe, "M15")
        candles_htf = get_rates("XAUUSD", htf_tf, count=30)
    else:
        candles = get_candles(limit=300)

    if not candles or len(candles) < 20:
        return None

    # Chạy TNV cho phần tín hiệu
    tnv_result = None
    try:
        tnv_result = analyze_tnv(
            candles,
            candles_htf=candles_htf,
            use_system1=True,
            use_system2=False,  # chỉ System 1
        )
    except Exception as e:
        log.warning("TNV lỗi: %s", e)

    # Dựng báo cáo tổng
    report = build_xau_report(candles, tnv_result, lang=lang, timeframe=timeframe)

    # Nếu /xau chi tiet → thêm phân tích LLM chi tiết
    if detail:
        from analyzer import build_analysis_prompt, _call_chat
        messages = build_analysis_prompt(candles, timeframe=timeframe, detail=True, lang=lang)
        llm = _call_chat(messages, max_tokens=900, lang=lang)
        if llm:
            llm_title = "🤖 *LLM Phân tích sâu*" if lang == "vi" else "🤖 *Deep LLM Analysis*"
            report += f"\n\n━━━━━━━━━━━━\n{llm_title}\n━━━━━━━━━━━━\n{llm}"

    return report


async def cmd_xau(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /xau — báo cáo tổng (xu hướng + chỉ báo + TNV + khuyến nghị)
    /xau m5 m15 m30 h1 h4 d1 — chọn khung (mặc định M5)
    """
    if not check_allowed(update):
        return

    lang = get_lang(update.effective_chat.id)
    # Quota check (ai_calls)
    try:
        from storage import check_quota
        chat_id = update.effective_chat.id
        if not check_quota(chat_id, "ai_calls"):
            await _send(update, t("quota_ai_exceeded", lang))
            return
    except Exception:
        pass
    args = " ".join(ctx.args or []).lower()
    detail = "chi tiet" in args or "detail" in args
    timeframe = "M5"

    if "h1" in args:
        timeframe = "H1"
    elif "h4" in args:
        timeframe = "H4"
    elif "d1" in args:
        timeframe = "D1"
    elif "m15" in args:
        timeframe = "M15"
    elif "m30" in args:
        timeframe = "M30"

    await _send(update, t("analyzing", lang))

    report = await _xau_for(update, timeframe, detail=detail)
    if report is None:
        await _send(update, t("not_enough_data_xau", lang))
        return

    await _send(update, report)
    try:
        from storage import incr_usage
        incr_usage(update.effective_chat.id, "ai_calls", 1)
    except Exception:
        pass


async def cmd_model(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Xem/đổi AI đang dùng. /model để xem, /model <ai> để chọn. Admin only."""
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    # Chỉ admin được dùng
    if update.effective_chat.id not in config.ADMIN_CHAT_IDS:
        await _send(update, t("admin_only", lang))
        return
    args = ctx.args
    if args:
        # Đổi provider
        provider = args[0].lower().replace("chatgpt", "openai")
        if provider not in config.PROVIDERS:
            await _send(update, t("ai_not_exist", lang, provider=provider, providers=", ".join(config.PROVIDERS.keys())))
            return
        set_current_provider(provider)
        await _send(update, t("ai_selected", lang, name=config.PROVIDERS[provider]['name']))
        return

    # Xem trạng thái
    current = get_current_provider()
    keys = list_api_keys()
    lines = [t("ai_current", lang)]
    if current:
        lines.append(f"  → *{config.PROVIDERS.get(current, {}).get('name', current)}*")
    else:
        lines.append(t("ai_auto", lang))
    lines.append("")
    lines.append(t("ai_configured", lang))
    for p, info in config.PROVIDERS.items():
        has = "✅" if keys.get(p) or info.get("no_key") else "❌"
        lines.append(f"  {has} `{p}` — {info['name']}")
    lines.append("")
    lines.append(t("ai_change_hint", lang))
    await _send(update, "\n".join(lines))


async def cmd_setmodel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Đổi model cho provider — chỉ admin.
    /setmodel <provider> text <model_name>    — đổi model text
    /setmodel <provider> vision <model_name>  — đổi model vision
    /setmodel <provider> reset                — xoá override, về mặc định config.py
    /setmodel                                 — xem tất cả override hiện tại
    """
    if not check_allowed(update):
        return
    chat_id = update.effective_chat.id
    lang = get_lang(chat_id)

    # Chỉ admin mới được đổi
    if chat_id not in config.ADMIN_CHAT_IDS:
        await _send(update, t("admin_only", lang))
        return

    from storage import set_model_override, clear_model_override, list_model_overrides

    args = ctx.args or []

    # Không có arg → xem trạng thái override hiện tại
    if not args:
        overrides = list_model_overrides()
        if not overrides:
            await _send(update, t("setmodel_none", lang))
            return
        lines = [t("setmodel_current", lang), ""]
        for prov, models in overrides.items():
            prov_name = config.PROVIDERS.get(prov, {}).get("name", prov)
            text_m = models.get("text", "—")
            vision_m = models.get("vision", "—")
            lines.append(f"  *{prov}* ({prov_name})")
            lines.append(f"    text: `{text_m}`")
            lines.append(f"    vision: `{vision_m}`")
        await _send(update, "\n".join(lines))
        return

    provider = args[0].lower()
    if provider not in config.PROVIDERS:
        await _send(update, t("ai_not_exist", lang,
                              provider=provider,
                              providers=", ".join(config.PROVIDERS.keys())))
        return

    # /setmodel <provider> reset — xoá override
    if len(args) == 2 and args[1].lower() == "reset":
        clear_model_override(provider)
        await _send(update, t("setmodel_reset", lang, provider=provider))
        return

    # /setmodel <provider> <text|vision> <model_name>
    if len(args) < 3:
        await _send(update, t("setmodel_syntax", lang))
        return

    kind = args[1].lower()
    if kind not in ("text", "vision"):
        await _send(update, t("setmodel_syntax", lang))
        return

    model_name = " ".join(args[2:]).strip()
    if not model_name:
        await _send(update, t("setmodel_syntax", lang))
        return

    set_model_override(provider, kind, model_name)
    await _send(update, t("setmodel_ok", lang,
                          provider=provider, kind=kind, model=model_name))


async def cmd_keys(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Quản lý API key qua SQLite — admin only.
    /keys — xem trạng thái
    /keys set <ai> <key> — lưu key
    /keys remove <ai> — xóa key
    """
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    # Chỉ admin
    if update.effective_chat.id not in config.ADMIN_CHAT_IDS:
        await _send(update, t("admin_only", lang))
        return
    args = ctx.args
    if not args:
        # Xem trạng thái
        keys = list_api_keys()
        lines = [t("keys_title", lang)]
        for p, info in config.PROVIDERS.items():
            if info.get("no_key"):
                lines.append(f"  ⚙️ `{p}` — {info['name']} {t('keys_no_key', lang)}")
                continue
            k = keys.get(p)
            if k:
                masked = k[:6] + "..." + k[-4:] if len(k) > 12 else "***"
                lines.append(f"  ✅ `{p}` — {info['name']}: `{masked}`")
            else:
                lines.append(f"  ❌ `{p}` — {info['name']}: {t('keys_missing', lang)}")
        lines.append("")
        lines.append(t("keys_hint", lang))
        await _send(update, "\n".join(lines))
        return

    action = args[0].lower()
    if action == "set" and len(args) >= 3:
        provider = args[1].lower().replace("chatgpt", "openai")
        key = args[2]
        if provider not in config.PROVIDERS:
            await _send(update, t("ai_not_exist", lang, provider=provider, providers=", ".join(config.PROVIDERS.keys())))
            return
        if config.PROVIDERS[provider].get("no_key"):
            await _send(update, t("keys_no_key_needed", lang, provider=provider))
            return
        set_api_key(provider, key)
        # Tự chọn provider này nếu chưa có
        if not get_current_provider():
            set_current_provider(provider)
        await _send(update, t("keys_saved", lang, name=config.PROVIDERS[provider]['name']))
        return

    if action == "remove" and len(args) >= 2:
        provider = args[1].lower().replace("chatgpt", "openai")
        remove_api_key(provider)
        if get_current_provider() == provider:
            set_current_provider("")
        await _send(update, t("keys_removed", lang, provider=provider))
        return

    await _send(update, t("keys_syntax", lang))


async def cmd_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Đổi ngôn ngữ: /lang, /lang vi, /lang en."""
    if not check_allowed(update):
        return
    chat_id = update.effective_chat.id
    args = ctx.args
    if args:
        ok = set_lang(chat_id, args[0])
        if ok:
            new_lang = get_lang(chat_id)
            await _send(update, t("lang_set", new_lang))
        else:
            await _send(update, t("lang_invalid", get_lang(chat_id)))
        return

    # Không có đối số → xem ngôn ngữ hiện tại
    cur = get_lang(chat_id)
    label = "Tiếng Việt" if cur == "vi" else "English"
    await _send(update, t("lang_hint", cur, language=label))


async def cmd_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """⚙️ /settings — bật/tắt tính năng tự động + ngưỡng Score."""
    chat = update.effective_chat
    if chat.type == "private":
        if not check_allowed(update):
            return
    else:
        if not await _is_chat_admin(update):
            lang = get_lang(chat.id)
            msg = "⚠️ Chỉ admin mới đổi được cài đặt." if lang == "vi" else "⚠️ Only admins can change settings."
            await _send(update, msg)
            return
    lang = get_lang(chat.id)
    text, kb = _settings_text_and_kb(chat.id, lang)
    await _send(update, text, reply_markup=kb)


async def cmd_ping(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """🏓 /ping — kiểm tra bot + thông tin cơ bản."""
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)

    # Thời gian chạy
    elapsed = int(time.time() - _BOOT_TS)
    days, rem = divmod(elapsed, 86400)
    hours, rem = divmod(rem, 3600)
    mins = rem // 60
    uptime = f"{days}d {hours}h {mins}m" if days else f"{hours}h {mins}m"

    # Nguồn dữ liệu
    source = "MT5" if get_mt5_mode() == "local" else "Gold-API"

    text = (
        t("ping_text", lang) + "\n"
        + t("uptime_title", lang) + "\n"
        + t("uptime_runtime", lang, uptime=uptime) + "\n"
        + t("uptime_source", lang, source=source)
    )
    await _send(update, text)


async def cmd_chart(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """🖼️ /chart [khung] — ảnh biểu đồ + phân tích AI (Premium)."""
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    chat_id = update.effective_chat.id

    # Kiểm tra tier
    from storage import get_tier, require_tier
    user_tier = get_tier(chat_id)
    if not require_tier("pro", user_tier):
        await _send(update, t("chart_premium_only", lang))
        return

    # Quota check (chart) — free=0 sẽ fail ngay; pro có 500/ngày
    try:
        from storage import check_quota
        if not check_quota(chat_id, "chart"):
            await _send(update, t("quota_chart_exceeded", lang))
            return
    except Exception:
        pass

    args = " ".join(ctx.args or []).lower()
    timeframe = "M5"
    if "h1" in args:
        timeframe = "H1"
    elif "h4" in args:
        timeframe = "H4"
    elif "d1" in args:
        timeframe = "D1"
    elif "m15" in args:
        timeframe = "M15"
    elif "m30" in args:
        timeframe = "M30"

    await _send(update, t("chart_thinking", lang))

    # Tạo ảnh từ dữ liệu MT5 (matplotlib, nhanh, không cần Playwright)
    from chartgen import generate_chart
    img_path = generate_chart(timeframe=timeframe)
    if not img_path or not os.path.isfile(img_path):
        await _send(update, t("chart_error", lang))
        return

    # Gửi ảnh
    try:
        from telegram import InputFile
        app = get_app()
        if app is None:
            await _send(update, t("chart_error", lang))
            return
        with open(img_path, "rb") as f:
            await app.bot.send_photo(chat_id=chat_id, photo=InputFile(f, filename="chart.png"))
    except Exception as e:
        log.warning("chart send photo lỗi: %s", e)
        await _send(update, t("chart_error", lang))
        return

    # Phân tích AI vision (nếu có)
    try:
        from analyzer import analyze_image
        # Kiểm tra có provider vision nào khả dụng không
        from config import available_providers, PROVIDERS
        vision_ok = False
        for p in available_providers():
            if PROVIDERS.get(p, {}).get("vision_model"):
                vision_ok = True
                break
        if not vision_ok:
            note = ("ℹ️ *Biểu đồ:* ✅\n\n_Chưa cấu hình AI đọc ảnh (vision). "
                    "Thiết lập key để có phân tích tự động: liên hệ admin._"
                    if lang == "vi" else
                    "ℹ️ *Chart:* ✅\n\n_Vision AI not configured. Contact admin._")
            await _ts_send(app.bot, chat_id, note)
            return

        ai_text = analyze_image(img_path, timeframe=timeframe, lang=lang)
        if ai_text:
            await _ts_send(app.bot, chat_id, ai_text)
            try:
                from storage import incr_usage
                incr_usage(chat_id, "ai_calls", 1)
                incr_usage(chat_id, "chart", 1)
            except Exception:
                pass
        else:
            note = ("ℹ️ AI vision không trả kết quả. Vui lòng thử lại sau."
                    if lang == "vi" else
                    "ℹ️ Vision AI returned nothing. Please try again later.")
            await _ts_send(app.bot, chat_id, note)
    except Exception as e:
        log.warning("chart AI vision lỗi: %s", e)
        try:
            note = ("⚠️ Phân tích AI lỗi: %s" % str(e)[:100]
                    if lang == "vi" else "⚠️ AI analysis error: %s" % str(e)[:100])
            await _ts_send(app.bot, chat_id, note)
        except Exception:
            pass


async def cmd_help_detail(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """📖 /help — hướng dẫn chi tiết (bảng USER + bảng ADMIN cho admin)."""
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    from storage import get_tier
    from config import ADMIN_CHAT_IDS

    chat_id = update.effective_chat.id
    tier = get_tier(chat_id)
    is_admin = chat_id in ADMIN_CHAT_IDS

    # ── Bảng USER ──
    user_table = (
        f"{t('help_title', lang)}\n\n"
        f"{t('help_analysis', lang)}\n\n"
        f"{t('cmd_xau_m5', lang)}\n"
        f"{t('cmd_candle_m5', lang)}\n"
        f"{t('cmd_price', lang)}\n"
        f"{t('cmd_news', lang)}\n"
        f"{t('cmd_history', lang)}\n"
        f"{t('cmd_stats', lang)}\n\n"
        f"{t('help_settings', lang)}\n\n"
        f"{t('cmd_lang', lang)}\n"
        f"{t('cmd_settings', lang)}\n\n"
        f"{t('help_subscription', lang)}\n\n"
        f"{t('cmd_register', lang)}\n"
        f"{t('cmd_myplan', lang)}\n"
        f"{t('cmd_redeem', lang)}\n\n"
        f"{t('help_tier', lang)}\n\n"
        f"{t('help_tier_free', lang)}\n\n"
        f"{t('tier_info', lang, tier=_pretty_tier(tier))}"
    )

    # ── Bảng ADMIN (chỉ admin) ──
    text = user_table
    if is_admin:
        text += f"\n\n━━━━━━━━━━━━\n\n{t('help_admin_table', lang)}"

    await _send(update, text)


async def cmd_tier(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """⭐ /tier [chat_id <tier>] — quản lý gói dịch vụ (admin)."""
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    chat_id = update.effective_chat.id
    from storage import get_tier, set_tier, count_premium_users
    from config import TIER_DAILY_LIMITS, ADMIN_CHAT_IDS

    # Là admin không?
    is_admin = chat_id in ADMIN_CHAT_IDS

    if not ctx.args:
        # Xem tier của bản thân
        tier = get_tier(chat_id)
        limits = TIER_DAILY_LIMITS.get(tier, {})
        lines = [
            t("tier_info", lang, tier=_pretty_tier(tier)),
            f"🆔 Chat ID: `{chat_id}`",
            "",
            "📊 *Hạn mức hàng ngày:*" if lang == "vi" else "📊 *Daily limits:*",
        ]
        for k, v in limits.items():
            lines.append(f"  • {k}: {v}")
        if is_admin:
            note = "✅ Bạn là ADMIN — tự động gói Pro." if lang == "vi" else "✅ You are ADMIN — automatically Pro tier."
            lines.append("")
            lines.append(note)
        await _send(update, "\n".join(lines))
        return

    # Chỉ admin mới được đặt tier cho người khác
    if not is_admin:
        await _send(update, "⚠️ Chỉ admin mới đặt được gói cho người khác." if lang == "vi" else "⚠️ Only admins can set tiers for others.")
        return

    # Admin: đặt tier cho user
    try:
        target = int(ctx.args[0])
        new_tier = ctx.args[1].lower() if len(ctx.args) >= 2 else ""
        if new_tier not in ("free", "pro"):
            counts = count_premium_users()
            await _send(update, t("tier_admin_usage", lang, **counts))
            return
        set_tier(target, new_tier)
        await _send(update, t("tier_admin_set", lang, tier=new_tier, cid=target))
    except (ValueError, IndexError):
        counts = count_premium_users()
        await _send(update, t("tier_admin_usage", lang, **counts))


# ── Subscription / Register / Redeem ─────────────────────
def _pretty_tier(tier: str) -> str:
    """Format tier cho đẹp: 'pro' → 'Pro', 'free' → 'Free'."""
    return pretty_tier(tier)

def _fmt_date(ts: int, lang: str) -> str:
    """Format epoch -> dd/mm/yyyy theo ngôn ngữ (mặc định 'en' dùng yyyy-mm-dd)."""
    from datetime import datetime, timezone
    if not ts:
        return t("myplan_never", lang)
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    if lang == "vi":
        return dt.strftime("%d/%m/%Y")
    return dt.strftime("%Y-%m-%d")


def _fmt_days_left(ts: int, lang: str) -> str:
    """Số ngày còn lại đến expiry. Trả chuỗi rỗng nếu không hết hạn."""
    if not ts:
        return ""
    now = int(time.time())
    days = max(0, (ts - now) // 86400)
    return f" ({t('myplan_days_left', lang, n=days)})" if days > 0 else ""


async def cmd_register(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """📝 /register — đăng ký tài khoản (trial 7 ngày free, CHỈ 1 LẦN)."""
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    chat_id = update.effective_chat.id
    from storage import is_registered, has_ever_registered, register_user, get_subscription
    from config import TRIAL_DAYS

    # Đã từng đăng ký (register_logs không bao giờ bị xoá) → chặn vĩnh viễn
    if has_ever_registered(chat_id):
        await _send(update, t("reg_already_trialed", lang))
        return

    if is_registered(chat_id):
        await _send(update, t("reg_already", lang))
        return

    expiry = register_user(chat_id, tier="pro", days=TRIAL_DAYS)
    expiry_str = _fmt_date(expiry, lang)
    days_left = (expiry - int(time.time())) // 86400 if expiry else 0
    text = t("reg_success", lang, tier="free", expiry=expiry_str, days_left=days_left)
    await _send(update, text)


async def cmd_myplan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """📋 /myplan — xem gói hiện tại + hạn dùng."""
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    chat_id = update.effective_chat.id
    from storage import get_subscription, is_registered, has_ever_registered, get_active_tier

    if not is_registered(chat_id):
        # Chưa có tài khoản → phân biệt: mới (chưa từng thử) vs đã dùng thử
        if has_ever_registered(chat_id):
            await _send(update, t("reg_already_trialed", lang))
        else:
            await _send(update, t("reg_welcome_new", lang, days=7))
        return

    sub = get_subscription(chat_id)
    tier = get_active_tier(chat_id)
    expiry = sub.get("expiry_ts", 0) or 0
    registered = sub.get("registered_ts", 0) or 0
    renewed = sub.get("last_renew_ts", 0) or 0

    now = int(time.time())
    if expiry == 0:
        status = t("myplan_active", lang)
    elif expiry > now:
        status = t("myplan_active", lang)
    else:
        status = t("myplan_expired", lang)

    lines = [
        t("myplan_title", lang),
        f"  • {t('myplan_tier', lang)}: *{_pretty_tier(tier)}*",
        f"  • {t('myplan_status', lang)}: {status}{_fmt_days_left(expiry, lang)}",
        f"  • {t('myplan_expires', lang)}: {_fmt_date(expiry, lang)}",
        f"  • {t('myplan_registered', lang)}: {_fmt_date(registered, lang)}",
    ]
    if renewed and renewed != registered:
        lines.append(f"  • {t('myplan_renewed', lang)}: {_fmt_date(renewed, lang)}")

    # Nếu sắp hết hạn, gợi ý redeem
    if expiry and expiry > now and (expiry - now) < 3 * 86400:
        lines.append("")
        lines.append(t("myplan_remind", lang))
    await _send(update, "\n".join(lines))


async def cmd_redeem(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """🔑 /redeem <mã> — nạp mã kích hoạt để gia hạn gói."""
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    chat_id = update.effective_chat.id
    from storage import is_registered, redeem_code

    if not ctx.args:
        await _send(update, t("redeem_usage", lang))
        return

    if not is_registered(chat_id):
        await _send(update, t("redeem_not_registered", lang))
        return

    code = " ".join(ctx.args).strip().upper()
    ok, msg, info = redeem_code(chat_id, code)

    if not ok:
        await _send(update, t("redeem_invalid", lang))
        return

    new_expiry = info.get("new_expiry", 0) or 0
    expiry_str = _fmt_date(new_expiry, lang)
    days_left = max(0, (new_expiry - int(time.time())) // 86400) if new_expiry else 0
    text = t("redeem_success", lang,
             code=info.get("code", code),
             tier=_pretty_tier(info.get("tier", "?")),
             days=info.get("days", 0),
             expiry=expiry_str,
             days_left=days_left)
    await _send(update, text)


# ── Admin: /gencode, /users, /renew, /expire ─────────────
async def _is_admin(chat_id: int) -> bool:
    from config import ADMIN_CHAT_IDS
    return chat_id in ADMIN_CHAT_IDS


async def cmd_gencode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """🎟️ /gencode <gói> <ngày> [số_lượng] — admin tạo mã kích hoạt.
    /gencode list — xem danh sách mã đã tạo.
    """
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    chat_id = update.effective_chat.id
    if not await _is_admin(chat_id):
        await _send(update, t("admin_only", lang))
        return

    # ── /gencode list ──
    if ctx.args and ctx.args[0].lower() == "list":
        from storage import list_codes
        codes = list_codes(limit=50)
        from datetime import datetime
        lines = [t("gencode_list_title", lang)]
        if not codes:
            lines.append(t("users_list_empty", lang))
        else:
            for c in codes:
                used = "✅ used" if c["used_by"] else "🆕 unused"
                if c["used_by"]:
                    used += f" → {c['used_by']}"
                created = datetime.fromtimestamp(c["created_at"]).strftime("%d/%m")
                lines.append(
                    t("gencode_list_line", lang,
                      code=c["code"],
                      tier=_pretty_tier(c["tier"]),
                      days=c["days"],
                      used=used,
                      created=created)
                )
        await _send(update, "\n".join(lines))
        return

    if len(ctx.args) < 2:
        await _send(update, t("gencode_usage", lang))
        return

    tier = ctx.args[0].lower()
    if tier not in ("free", "pro"):
        await _send(update, t("gencode_invalid_tier", lang))
        return
    try:
        days = int(ctx.args[1])
        if days < 1 or days > 3650:
            await _send(update, t("gencode_usage", lang))
            return
    except ValueError:
        await _send(update, t("gencode_usage", lang))
        return

    count = 1
    if len(ctx.args) >= 3:
        try:
            count = int(ctx.args[2])
            count = max(1, min(count, 50))  # giới hạn 50 mã/lần
        except ValueError:
            count = 1

    from storage import create_codes_bulk
    codes = create_codes_bulk(tier, days, count, created_by=chat_id)
    code_text = "\n".join(f"`{c}`" for c in codes)
    await _send(update, t("gencode_created", lang, n=len(codes), tier=_pretty_tier(tier), days=days, codes=code_text))


async def cmd_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """👥 /users [gói] [expire_within_days] — admin xem danh sách user."""
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    chat_id = update.effective_chat.id
    if not await _is_admin(chat_id):
        await _send(update, t("admin_only", lang))
        return

    tier_filter = None
    exp_days = 0
    for arg in ctx.args:
        a = arg.lower()
        if a in ("free", "pro"):
            tier_filter = a
        else:
            try:
                exp_days = int(a)
            except ValueError:
                pass

    from storage import list_users, count_users_by_tier
    users = list_users(tier=tier_filter, expiring_within_days=exp_days)
    counts = count_users_by_tier()

    lines = [t("users_list_title", lang)]
    if not users:
        lines.append(t("users_list_empty", lang))
    else:
        from storage import get_user_codes
        # Giới hạn hiển thị 30 user để tránh quá dài
        for u in users[:30]:
            expiry = u.get("expiry_ts", 0) or 0
            if expiry == 0:
                days_str = ""
            else:
                days = max(0, (expiry - int(time.time())) // 86400)
                days_str = f" ({days}d)" if days >= 0 else " (expired)"
            # Lấy mã user đã dùng (mới nhất)
            used_codes = get_user_codes(u["chat_id"], limit=1)
            code_str = used_codes[0]["code"] if used_codes else t("users_no_code", lang)
            lines.append(t("users_list_line_v2", lang,
                           cid=u["chat_id"],
                           tier=_pretty_tier(u.get("tier", "free")),
                           status=t("myplan_active", lang) if expiry == 0 or expiry > int(time.time()) else t("myplan_expired", lang),
                           days=days_str,
                           code=code_str))
        if len(users) > 30:
            lines.append(f"... +{len(users) - 30} more")
    lines.append(t("users_list_footer", lang, **counts))
    await _send(update, "\n".join(lines))


async def cmd_renew(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """🔄 /renew <chat_id> <gói> <ngày> — admin gia hạn cho user."""
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    chat_id = update.effective_chat.id
    if not await _is_admin(chat_id):
        await _send(update, t("admin_only", lang))
        return

    if len(ctx.args) < 3:
        await _send(update, t("renew_usage", lang))
        return

    try:
        target = int(ctx.args[0])
        tier = ctx.args[1].lower()
        days = int(ctx.args[2])
        if tier not in ("free", "pro") or days < 1:
            await _send(update, t("renew_usage", lang))
            return
    except ValueError:
        await _send(update, t("renew_usage", lang))
        return

    from storage import renew_subscription
    new_expiry = renew_subscription(target, tier, days)
    expiry_str = _fmt_date(new_expiry, lang)
    await _send(update, t("renew_done", lang, cid=target, tier=_pretty_tier(tier), days=days, expiry=expiry_str))


async def cmd_expire(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """⏬ /expire <chat_id> — admin hạ user về free ngay."""
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    chat_id = update.effective_chat.id
    if not await _is_admin(chat_id):
        await _send(update, t("admin_only", lang))
        return

    if not ctx.args:
        note = ("Cú pháp: /expire <chat_id>\nVD: /expire 332965032"
                if lang == "vi" else "Usage: /expire <chat_id>\nE.g.: /expire 332965032")
        await _send(update, note)
        return
    try:
        target = int(ctx.args[0])
    except ValueError:
        note = ("Cú pháp: /expire <chat_id>" if lang == "vi" else "Usage: /expire <chat_id>")
        await _send(update, note)
        return

    from storage import expire_user_now
    expire_user_now(target)
    await _send(update, t("expire_done_admin", lang, cid=target))


async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """♻️ /reset <chat_id> — admin xoá dữ liệu user, cho đăng ký lại."""
    if not check_allowed(update):
        return
    lang = get_lang(update.effective_chat.id)
    chat_id = update.effective_chat.id
    if not await _is_admin(chat_id):
        await _send(update, t("admin_only", lang))
        return

    if not ctx.args:
        note = ("Cú pháp: /reset <chat_id>\nVD: /reset 332965032"
                if lang == "vi" else "Usage: /reset <chat_id>\nE.g.: /reset 332965032")
        await _send(update, note)
        return
    try:
        target = int(ctx.args[0])
    except ValueError:
        note = ("Cú pháp: /reset <chat_id>" if lang == "vi" else "Usage: /reset <chat_id>")
        await _send(update, note)
        return

    from storage import reset_user
    reset_user(target)
    note = (f"✅ Đã xoá dữ liệu user {target}."
            if lang == "vi" else
            f"✅ User {target} data cleared.")
    await _send(update, note)


async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Xử lý mọi nút inline keyboard."""
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        log.warning("query.answer lỗi: %s", e)

    chat_id = update.effective_chat.id
    lang = get_lang(chat_id)
    data = query.data or ""
    log.info("Callback nhận: chat_id=%s data=%s", chat_id, data)

    try:

        # ── Báo cáo /xau theo khung ──
        if data.startswith("xau:"):
            tf = data.split(":", 1)[1].upper()
            report = await _xau_for(update, tf)
            if report is None:
                await _edit(query, t("not_enough_data_xau", lang), parse_mode="Markdown")
            else:
                await _edit(query, report, parse_mode="Markdown")
            return

        # ── Báo cáo /candle theo khung ──
        if data.startswith("candle:"):
            tf = data.split(":", 1)[1].upper()
            report = await _candle_for(update, tf)
            if report is None:
                await _edit(query, t("not_enough_candles", lang), parse_mode="Markdown")
            else:
                await _edit(query, report, parse_mode="Markdown")
            return

        # ── Các lệnh đơn giản ──
        if data == "history":
            try:
                limit = 10
                sigs = get_history(limit)
                text = format_history(sigs, lang)
            except Exception as e:
                log.error("history btn lỗi: %s", e)
                text = "⚠️ Không lấy được lịch sử tín hiệu." if lang == "vi" else "⚠️ Could not fetch signal history."
            await _edit(query, text, parse_mode="Markdown")
            return

        if data == "stats":
            try:
                days = 30
                stats = get_stats(days)
                text = format_stats(stats, lang)
            except Exception as e:
                log.error("stats btn lỗi: %s", e)
                text = "⚠️ Không lấy được thống kê." if lang == "vi" else "⚠️ Could not fetch stats."
            await _edit(query, text, parse_mode="Markdown")
            return

        if data == "price":
            price = get_last_price()
            if price:
                text = t("xau_price", lang, price=price)
            else:
                from collector import fetch_gold_price
                data_price = fetch_gold_price()
                if data_price:
                    text = t("xau_price", lang, price=data_price['price']) + t("price_source", lang)
                else:
                    text = t("price_error", lang)
            await _edit(query, text, parse_mode="Markdown")
            return

        if data == "news":
            try:
                from forex_factory import get_calendar, filter_usd_events, format_news
                events = get_calendar()
                usd_events = filter_usd_events(events)
                text = format_news(usd_events, lang=lang)
            except Exception as e:
                log.warning("News btn lỗi: %s", e)
                text = "⚠️ Không lấy được lịch kinh tế. Thử lại sau." if lang == "vi" else "⚠️ Could not fetch economic calendar. Try again later."
            await _edit(query, text, parse_mode="Markdown")
            return

        # ── Menu con: khung thời gian ──
        if data == "tf":
            await _edit(query, 
                t("btn_tf_menu", lang), parse_mode="Markdown",
                reply_markup=_tf_menu_kb(lang),
            )
            return

        if data.startswith("tf:"):
            tf = data.split(":", 1)[1].upper()
            # Gửi báo cáo /xau theo TF đã chọn
            report = await _xau_for(update, tf)
            if report is None:
                await _edit(query, t("not_enough_data_xau", lang), parse_mode="Markdown")
                return
            await _edit(query, f"⏱ {tf}\n\n{report}", parse_mode="Markdown")
            return

        # ── Menu con: ngôn ngữ ──
        if data == "lang":
            await _edit(query, 
                t("btn_lang_menu", lang), parse_mode="Markdown",
                reply_markup=_lang_menu_kb(lang),
            )
            return

        if data.startswith("lang:"):
            new_lang = data.split(":", 1)[1]
            ok = set_lang(chat_id, new_lang)
            if ok:
                lang = get_lang(chat_id)
                text = t("lang_set", lang)
            else:
                text = t("lang_invalid", lang)
            from storage import get_tier
            cb_tier = get_tier(chat_id)
            await _edit(query,
                text, parse_mode="Markdown",
                reply_markup=_main_menu_kb(lang),
            )
            return

        # ── Menu cài đặt ──
        if data == "settings":
            text, kb = _settings_text_and_kb(chat_id, lang)
            await _edit(query, text, parse_mode="Markdown", reply_markup=kb)
            return

        if data.startswith("set:"):
            # Admin gate cho group/channel — member không đổi được cài đặt
            if update.effective_chat.type != "private" and not await _is_chat_admin(update):
                await update.callback_query.answer("Chỉ admin mới đổi được cài đặt", show_alert=True)
                return

            try:
                from scheduler import get_runtime_settings, set_runtime_setting  # lazy import
            except Exception as e:
                log.warning("Settings scheduler chưa sẵn sàng: %s", e)
                await query.answer("⚠️ Settings chưa khả dụng", show_alert=True)
                return

            payload = data.split(":", 1)[1]
            if payload.startswith("min_score:"):
                try:
                    value = int(payload.split(":", 1)[1])
                except ValueError:
                    value = 5
                set_runtime_setting(chat_id, "min_score", value)
            else:
                # Bật/tắt toggle
                settings = get_runtime_settings(chat_id)
                current = settings.get(payload, False)
                set_runtime_setting(chat_id, payload, not current)

            text, kb = _settings_text_and_kb(chat_id, lang)
            await _edit(query, text, parse_mode="Markdown", reply_markup=kb)
            return

        # ── Quay lại menu chính ──
        if data == "back":
            from storage import get_tier
            cb_tier = get_tier(chat_id)
            await _edit(query,
                _main_menu_text(lang),
                parse_mode="Markdown",
                reply_markup=_main_menu_kb(lang),
            )
            return

        # Callback không biết
        log.warning("Callback không nhận diện: %s", data)
        await _edit(query, "⚠️ Thao tác không hợp lệ.", parse_mode="Markdown")

    except Exception as e:
        import traceback
        log.error("Callback lỗi chi tiết: %s\n%s", e, traceback.format_exc())
        try:
            await update.callback_query.answer(f"⚠️ Lỗi: {str(e)[:50]}", show_alert=True)
        except Exception:
            pass


def _main_menu_text(lang: str) -> str:
    """Text menu chính (dùng khi quay lại từ submenu).

    - Hiển thị full cho cả Free + Pro.
    - Chỉ khi dùng chức năng Pro mới phân biệt tier.
    """
    return (
        f"{t('bot_intro', lang)}\n\n"
        f"{t('menu_group_analysis', lang)}\n\n"
        f"{t('cmd_xau_m5', lang)}\n"
        f"{t('cmd_candle_m5', lang)}\n"
        f"{t('cmd_price', lang)}\n"
        f"{t('cmd_news', lang)}\n"
        f"{t('cmd_history', lang)}\n"
        f"{t('cmd_stats', lang)}\n"
        f"{t('cmd_chart', lang)}\n\n"
        f"{t('menu_group_settings', lang)}\n\n"
        f"{t('cmd_lang', lang)}\n"
        f"{t('cmd_help', lang)}"
    )


# ── Khởi động bot ────────────────────────────────────────
_app = None
_bot_loop = None  # event loop của bot thread (để gửi tin thread-safe từ scheduler)


async def on_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Khách tự gửi ảnh chart → bot phân tích bằng AI vision (nếu có key).

    Hỗ trợ: ảnh/chart, chụp màn hình app giao dịch.
    """
    if not check_allowed(update):
        return
    chat_id = update.effective_chat.id
    lang = get_lang(chat_id)

    # Quota check (ai_calls)
    try:
        from storage import check_quota, incr_usage, get_tier
        if not check_quota(chat_id, "ai_calls"):
            note = t("quota_ai_exceeded", lang)
            await _send(update, note)
            return
    except Exception:
        pass

    photo = update.message.photo[-1]
    file = await photo.get_file()
    tmp_dir = os.path.join(config.DATA_DIR, "user_imgs")
    os.makedirs(tmp_dir, exist_ok=True)
    img_path = os.path.join(tmp_dir, f"u_{chat_id}_{int(time.time())}.jpg")
    await file.download_to_drive(img_path)

    thinking = ("🔍 Đang phân tích ảnh..."
                if lang == "vi" else "🔍 Analyzing image...")
    await _send(update, thinking)

    try:
        from analyzer import analyze_image
        ai_text = analyze_image(img_path, timeframe="M5", lang=lang)
        if ai_text:
            # Escape Markdown lẻ + fallback plain
            safe_text = _escape_md(ai_text)
            sent_ok = False
            try:
                await update.message.reply_text(safe_text, parse_mode="Markdown")
                sent_ok = True
            except Exception:
                try:
                    await update.message.reply_text(ai_text, parse_mode="Markdown")
                    sent_ok = True
                except Exception:
                    try:
                        await update.message.reply_text(ai_text)
                        sent_ok = True
                    except Exception:
                        pass
            if sent_ok:
                try:
                    from storage import incr_usage
                    incr_usage(chat_id, "ai_calls", 1)
                except Exception:
                    pass
        else:
            note = ("ℹ️ AI không trả kết quả. Vui lòng thử lại sau."
                    if lang == "vi" else "ℹ️ No result from vision AI. Please try again later.")
            await _send(update, note)
    except Exception as e:
        log.warning("photo analyze lỗi: %s", e)
        note = ("⚠️ Phân tích ảnh lỗi: %s\nVui lòng thử lại sau." % str(e)[:100]
                if lang == "vi" else "⚠️ Image analysis error: %s\nPlease try again later." % str(e)[:100])
        await _send(update, note)
    finally:
        try:
            os.remove(img_path)
        except Exception:
            pass


def get_app():
    """Trả Application instance (None nếu chưa khởi động)."""
    return _app


def get_bot_loop():
    """Trả event loop của bot thread (None nếu chưa khởi động)."""
    return _bot_loop


def run_bot(stop_event: threading.Event):
    """Chạy Telegram bot polling."""
    global _app, _bot_loop
    if not config.TELEGRAM_TOKEN:
        log.error("Thiếu TELEGRAM_BOT_TOKEN")
        return

    # Tạo + set event loop riêng cho bot thread — PTB dùng asyncio.get_event_loop()
    # trong chính thread này, nên ta bắt được loop để gửi tin thread-safe từ scheduler.
    _bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_bot_loop)

    app = Application.builder().token(config.TELEGRAM_TOKEN).build()
    _app = app

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("price", cmd_price))
    app.add_handler(CommandHandler("candle", cmd_candle_analysis))
    app.add_handler(CommandHandler("xau", cmd_xau))
    app.add_handler(CommandHandler("news", cmd_news))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("model", cmd_model))
    app.add_handler(CommandHandler("setmodel", cmd_setmodel, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("keys", cmd_keys))
    app.add_handler(CommandHandler("lang", cmd_lang))
    app.add_handler(CommandHandler("settings", cmd_settings))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("chart", cmd_chart))
    app.add_handler(CommandHandler("tier", cmd_tier))
    app.add_handler(CommandHandler("register", cmd_register))
    app.add_handler(CommandHandler("myplan", cmd_myplan))
    app.add_handler(CommandHandler("redeem", cmd_redeem))
    app.add_handler(CommandHandler("gencode", cmd_gencode))
    app.add_handler(CommandHandler("users", cmd_users))
    app.add_handler(CommandHandler("renew", cmd_renew))
    app.add_handler(CommandHandler("expire", cmd_expire))
    app.add_handler(CommandHandler("reset", cmd_reset))

    # Callback cho inline keyboard
    app.add_handler(CallbackQueryHandler(on_callback))

    # Nhận ảnh do khách gửi → phân tích AI vision (quota: ai_calls)
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))

    log.info("✅ Bot Telegram đang chạy...")
    app.run_polling(stop_signals=None)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_bot(threading.Event())
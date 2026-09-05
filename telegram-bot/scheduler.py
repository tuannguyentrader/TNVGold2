"""
Scheduler — Lịch báo cáo cố định:
- Mỗi giờ: brief ngắn M5 (nến + xu hướng + setup nhanh)
- Sáng/Tối (mặc định 7h, 19h giờ VN): báo cáo chi tiết + đa khung
- Feature 1: tín hiệu TNV tự động (AUTO_SIGNAL) + theo dõi TP/SL
- Feature 2: tổng kết cuối ngày (EOD)
- Feature 3: cảnh báo tin tức chủ động (NEWS)

Chạy trong thread riêng, dùng timezone VN (UTC+7).
"""

import logging
import os
import time
import threading
from datetime import datetime, timedelta, timezone

# Load .env ở local (VPS Windows CMD dùng `set` thủ công cũng OK)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import config
from storage import get_candles, save_report, kv_get, kv_set, get_tier, check_quota, incr_usage
from candle_analysis import analyze_candle_sequence, format_sequence_report
from indicators import compute_all, format_indicators

log = logging.getLogger("scheduler")

# UTC+7 (Việt Nam)
VN_TZ = timezone(timedelta(hours=7))

# Callback gửi tin nhắn (set từ main)
_send_callback = None
_active_chat_ids = []  # chat id được phép nhận báo cáo tự động

# Cảnh báo tin tức: theo dõi event đã gửi (tránh lặp)
_sent_news = {}  # {"type|cid:khung_gio": giờ_utc_đã_gửi} — type="30m" hoặc "5m"
NEWS_CHECK_MINUTES = 5  # kiểm tra mỗi 5 phút

# ── Feature 1: tín hiệu TNV tự động ─────────────────────
# Dedupe trong bộ nhớ: {chat_id: {type|date: timestamp}} — tránh spam cùng hướng.
# Dedupe bền vững (chống trùng khi bot khởi động lại): kv key "last_sig:{type}".
_sent_auto = {}  # {"cid:LONG|YYYY-MM-DD": epoch_giây_đã_gửi}

# ── Feature 2: tổng kết cuối ngày ────────────────────────
_last_eod_day = {}  # {chat_id: ngày_đã_gửi}

# ── Song ngữ: dùng chung từ i18n ──────────────────────────
from i18n import t as _L


def _direction_label(direction: str, lang: str) -> str:
    """Map predicted_direction (từ candle_analysis, dùng chữ Việt) → nhãn theo lang."""
    d = direction.lower()
    if "tăng" in d and "nhẹ" in d:
        return _L("dir_slight_up", lang)
    if "tăng" in d:
        return _L("dir_up", lang)
    if "giảm" in d and "nhẹ" in d:
        return _L("dir_slight_down", lang)
    if "giảm" in d:
        return _L("dir_down", lang)
    if "side" in d or "ngang" in d:
        return _L("dir_side", lang)
    return direction


def set_send_callback(fn):
    global _send_callback
    _send_callback = fn


def set_active_chats(chat_ids):
    global _active_chat_ids
    _active_chat_ids = list(chat_ids)


def add_active_chat(chat_id: int):
    """Thêm một chat vào danh sách nhận tin tự động (nếu chưa có)."""
    global _active_chat_ids
    if chat_id not in _active_chat_ids:
        _active_chat_ids.append(chat_id)
        log.info("➕ Đã đăng ký chat %s nhận tin tự động", chat_id)


def _send_all(text: str):
    if not _send_callback:
        return
    for cid in _active_chat_ids:
        try:
            _send_callback(chat_id=cid, text=text)
        except Exception as e:
            log.error("Send %d lỗi: %s", cid, e)


def _send_lang(text_fn):
    """For each active chat, get its language, build text via text_fn(lang), and send."""
    if not _send_callback:
        return
    from i18n import get_lang
    for cid in _active_chat_ids:
        try:
            lang = get_lang(cid)
            text = text_fn(lang)
            if text:
                _send_callback(chat_id=cid, text=text)
        except Exception as e:
            log.error("Send %d lỗi: %s", cid, e)


# ── Runtime settings (per-chat overrides from kv) ──────────
_SETTING_KEYS = {"auto_signal", "news", "eod", "min_score"}


def get_runtime_settings(chat_id) -> dict:
    """Return per-chat runtime settings with config defaults."""
    return {
        "auto_signal": kv_get(f"set:{chat_id}:auto_signal", config.AUTO_SIGNAL),
        "eod": kv_get(f"set:{chat_id}:eod", config.EOD_ENABLED),
        
        "news": kv_get(f"set:{chat_id}:news", True),
        "min_score": kv_get(f"set:{chat_id}:min_score", config.AUTO_SIGNAL_MIN_SCORE),
    }


def set_runtime_setting(chat_id, key, value):
    """Set a per-chat runtime setting in kv."""
    if key not in _SETTING_KEYS:
        raise ValueError(f"Unknown setting key: {key}")
    # Normalize bool/int/float from string
    if isinstance(value, str):
        if value.lower() in ("true", "1", "yes"):
            value = True
        elif value.lower() in ("false", "0", "no"):
            value = False
        else:
            try:
                value = float(value) if "." in value else int(value)
            except ValueError:
                pass
    kv_set(f"set:{chat_id}:{key}", value)


def check_news_alerts(enabled_chats=None):
    """
    Kiểm tra lịch kinh tế: có sự kiện USD High/Medium sắp tới.

    Gửi 2 lần cho mỗi đợt tin:
      • Lần 1: ~30 phút trước giờ tin (cửa sổ 30-60 phút tới)
      • Lần 2: ~5 phút trước giờ tin (cửa sổ 5-15 phút tới)

    Mỗi lần gửi 1 tin DUY NHẤT gộp tất cả events sắp tới (dạng /news).
    Dedupe riêng cho từng loại ("30m", "5m") theo khung giờ để không gửi trùng.

    enabled_chats: list chat_id được gửi (tôn trọng settings per-chat "news").
    Mỗi chat nhận đúng ngôn ngữ của mình (vi/en).
    """
    try:
        from forex_factory import get_calendar, filter_usd_events, events_in_window, format_news_alert
        from i18n import get_lang
        events = get_calendar()
        if not events:
            return
        usd_events = filter_usd_events(events)
        if not usd_events:
            return
        now = datetime.now(timezone.utc)
        # Chỉ events sắp tới
        upcoming = [e for e in usd_events if e["time_utc"] > now]
        if not upcoming:
            return
        # Chỉ gửi cho chat được phép
        if enabled_chats is None:
            enabled_chats = _active_chat_ids
        enabled_chats = [c for c in enabled_chats if get_runtime_settings(c).get("news", True)]
        if not enabled_chats:
            return

        # Định nghĩa 2 cửa sổ cảnh báo
        alerts = [
            ("30m", 30, 60),   # ~30 phút trước: cửa sổ [30, 60) phút
            ("5m",  5,  15),   # ~5 phút trước:  cửa sổ [5, 15) phút
        ]
        for alert_type, min_before, max_before in alerts:
            # Lọc events trong cửa sổ này
            window_events = [
                e for e in upcoming
                if min_before <= (e["time_utc"] - now).total_seconds() / 60 < max_before
            ]
            if not window_events:
                continue

            # Dedupe: dùng khung giờ của event đầu tiên
            first_time = window_events[0]["time_utc"]
            dedupe_key = f"{alert_type}|{first_time.strftime('%H:%M')}"
            if dedupe_key in _sent_news and (now - _sent_news[dedupe_key]).total_seconds() < 5400:
                log.info("📰 Tin %s: đã gửi %s, bỏ qua", alert_type, first_time.strftime('%H:%M'))
                continue
            _sent_news[dedupe_key] = now

            # Số phút còn lại làm tròn
            minutes_left = max(0, round((first_time - now).total_seconds() / 60))

            for cid in enabled_chats:
                lang = get_lang(cid)
                text = format_news_alert(window_events, lang=lang, minutes_left=minutes_left)
                try:
                    _send_callback(chat_id=cid, text=text)
                except Exception as e:
                    log.error("News send %d lỗi: %s", cid, e)
                log.info("📰 Cảnh báo %s: %d events, khung %s → %d (%s)",
                         alert_type, len(window_events), first_time.strftime('%H:%M'), cid, lang)

        # Dọn cache cũ (> 90 phút)
        for k in [k for k, v in _sent_news.items() if (now - v).total_seconds() > 5400]:
            _sent_news.pop(k, None)
    except Exception as e:
        log.warning("News alert lỗi: %s", e)


def check_auto_signals(enabled_chats=None):
    """
    Feature 1 — Tín hiệu TNV tự động.

    Mỗi 5 phút (khi nến M5 mới đóng): chạy analyze_tnv (System 1),
    lọc tín hiệu LONG/SHORT có score >= AUTO_SIGNAL_MIN_SCORE,
    tính SL/TP theo N (SL=1.5N, TP=2N), gửi cảnh báo + lưu vào
    bảng signals (cho /stats, /history và đánh giá TP/SL tự động).

    enabled_chats: list of chat_ids to send to (respects per-chat auto_signal setting).
    Signal is always recorded for stats regardless of enabled_chats.

    Dedupe: mỗi hướng chỉ gửi 1 lần trong AUTO_SIGNAL_DEDUPE_MIN phút.
    """
    if not config.AUTO_SIGNAL:
        return
    if not enabled_chats:
        return
    try:
        from tnv_engine import analyze_tnv
        from i18n import t as t_, get_lang
        import signals

        # Determine min_score: use the minimum among enabled chats
        min_score = config.AUTO_SIGNAL_MIN_SCORE
        for cid in enabled_chats:
            chat_min = get_runtime_settings(cid).get("min_score", config.AUTO_SIGNAL_MIN_SCORE)
            if isinstance(chat_min, (int, float)):
                min_score = min(min_score, chat_min)

        candles = get_candles(limit=100)
        if not candles:
            return

        # ── Đồng bộ nến vừa đóng với collector (tránh race 60s) ──
        # Collector chạy mỗi 60s; nếu scheduler chạy đúng lúc nến M5 đóng mà
        # collector chưa kịp UPSERT nến mới, ta chờ tối đa 10s để lấy đúng nến.
        for _ in range(5):
            now_vn2 = datetime.now(VN_TZ)
            current_period = int(now_vn2.timestamp()) // 300 * 300
            last_ts = candles[-1]["ts"]
            # Nến mới đóng = ts của kỳ vừa kết thúc (current_period - 300)
            closed_period = current_period - 300
            if last_ts >= closed_period:
                time.sleep(2)
                candles = get_candles(limit=100)
                if not candles:
                    return
            else:
                break
        # Bỏ nến đang hình thành (nếu có) — chỉ phân tích nến ĐÃ ĐÓNG
        now_vn2 = datetime.now(VN_TZ)
        current_period = int(now_vn2.timestamp()) // 300 * 300
        if candles[-1]["ts"] >= current_period:
            candles = candles[:-1]
        if len(candles) < 22:
            log.info("Auto signal: mới %d nến, cần ≥22", len(candles))
            return

        result = analyze_tnv(candles, use_system1=True, use_system2=False)
        if "error" in result:
            log.info("Auto signal bỏ qua: %s", result["error"])
            return

        n_val = result.get("n_value") or 0
        if n_val <= 0:
            log.info("Auto signal bỏ qua: N (ATR) không hợp lệ")
            return

        price = result.get("current_price")
        now = datetime.now(VN_TZ)
        now_ts = time.time()
        day_key = now.strftime("%Y-%m-%d")
        sent_any = False

        for sig in result.get("signals", []):
            stype = sig["type"]
            if stype not in ("LONG", "SHORT", "EXIT_LONG", "EXIT_SHORT"):
                continue
            score = sig.get("score", 0)
            # Exit KHÔNG bị chặn bởi min_score (giống indicator TNV: exit luôn báo)
            if stype in ("LONG", "SHORT") and score < min_score:
                continue
            # Bỏ thông báo EXIT tự động — chỉ giữ LONG/SHORT (theo yêu cầu)
            if stype in ("EXIT_LONG", "EXIT_SHORT"):
                continue

            dedupe_minutes = config.AUTO_SIGNAL_DEDUPE_MIN

            # Dedupe bền vững (SQLite): bỏ qua nếu đã gửi cùng loại
            # trong dedupe_minutes, kể cả sau khi bot khởi động lại.
            last_ts = kv_get(f"last_sig:{stype}")
            if isinstance(last_ts, (int, float)) and (now_ts - float(last_ts)) < dedupe_minutes * 60:
                continue
            kv_set(f"last_sig:{stype}", now_ts)

            if stype in ("LONG", "SHORT"):
                # Entry: ưu tiên mức breakout của chính tín hiệu, fallback giá hiện tại
                entry = sig.get("entry_level") or price
                if stype == "LONG":
                    sl = entry - 1.5 * n_val
                    tp = entry + 2.0 * n_val
                else:
                    sl = entry + 1.5 * n_val
                    tp = entry - 2.0 * n_val
                sl = round(sl, 2)
                tp = round(tp, 2)

                # Lưu vào bảng signals (luôn ghi nhận bất kể enabled_chats)
                signals.record_signal({
                    "type": stype,
                    "score": score,
                    "price": price,
                    "entry": round(entry, 2),
                    "sl": sl,
                    "tp": tp,
                })

                # Tin nhắn song ngữ (vi/en) — template mới theo yêu cầu
                emoji = "🟢" if stype == "LONG" else "🔴"
                texts = {}
                for lang in ("vi", "en"):
                    texts[lang] = (
                        t_("auto_signal_brand", lang) + "\n"
                        + t_("auto_signal_sig_line", lang, emoji=emoji, stype=stype, score=score) + "\n\n"
                        + t_("auto_signal_entry", lang, value=f"${entry:.2f}") + "\n"
                        + t_("auto_signal_sl", lang, value=f"${sl:.2f}") + "\n"
                        + t_("auto_signal_tp", lang, value=f"${tp:.2f}") + "\n\n"
                        + t_("auto_signal_market_update", lang) + "\n"
                        + t_("auto_signal_current_price", lang, value=f"${price:.2f}") + "\n"
                        + t_("auto_signal_n", lang, value=f"${n_val:.2f}")
                    )
            else:
                # EXIT_LONG / EXIT_SHORT — báo đóng lệnh, không cần SL/TP
                is_exit_long = stype == "EXIT_LONG"
                emoji = "🔴" if is_exit_long else "🟢"
                exit_level = sig.get("exit_level") or price
                entry = exit_level  # cho log thống nhất
                sl = tp = None
                texts = {}
                for lang in ("vi", "en"):
                    texts[lang] = (
                        t_("auto_signal_brand", lang) + "\n"
                        + t_("auto_signal_sig_line", lang, emoji=emoji, stype=stype, score=score) + "\n\n"
                        + t_("auto_signal_current_price", lang, value=f"${price:.2f}") + "\n"
                        + t_("auto_signal_n", lang, value=f"${n_val:.2f}")
                    )

            # Gửi đến từng chat (per-chat dedupe + ngôn ngữ riêng + quota)
            # Quota: free chỉ nhận giới hạn signals/ngày (config.TIER_DAILY_LIMITS),
            # pro gửi bình thường. Signal ĐÃ được lưu bảng signals cho mọi tier ở trên —
            # chỉ giới hạn VIỆC GỬI qua _send_callback.
            for cid in enabled_chats:
                tier = get_tier(cid)
                if tier != "pro" and not check_quota(cid, "signals"):
                    continue  # free hết quota hôm nay → bỏ qua chat này cho signal này
                mem_key = f"{cid}:{stype}|{day_key}"
                last_mem = _sent_auto.get(mem_key)
                if last_mem and (now_ts - last_mem) < dedupe_minutes * 60:
                    continue
                _sent_auto[mem_key] = now_ts
                if _send_callback:
                    try:
                        chat_lang = get_lang(cid)
                        text = texts.get(chat_lang, texts.get("vi", ""))
                        _send_callback(chat_id=cid, text=text)
                        if tier != "pro":
                            incr_usage(cid, "signals", 1)  # trừ quota sau khi gửi thành công
                    except Exception as e:
                        log.error("Send auto signal %d lỗi: %s", cid, e)

            log.info("📡 Auto signal %s score=%.1f entry=%.2f sl=%.2f tp=%.2f",
                     stype, score, entry, sl, tp)
            sent_any = True

        if not sent_any:
            log.debug("Auto signal: không có tín hiệu đủ điều kiện")
    except Exception as e:
        log.warning("Auto signal lỗi: %s", e)


def check_eod(enabled_chats=None):
    """
    Feature 2 — Tổng kết cuối ngày (EOD).

    Mỗi ngày 1 lần, khi giờ VN đạt EOD_HOUR:EOD_MINUTE:
    - Thống kê tín hiệu hôm nay (signals.get_stats(days=1))
    - Giá đóng hiện tại
    Gửi qua _send_all.

    enabled_chats: list of chat_ids to send to (respects per-chat eod setting).
    """
    if not config.EOD_ENABLED:
        return
    if not enabled_chats:
        return
    try:
        from i18n import t, get_lang
        import signals

        now_vn = datetime.now(VN_TZ)
        # Chỉ gửi khi đúng giờ (trong cửa sổ 5 phút) và 1 lần/ngày
        if now_vn.hour != config.EOD_HOUR or now_vn.minute < config.EOD_MINUTE:
            return
        if now_vn.minute > config.EOD_MINUTE + 5:
            return

        stats = signals.get_stats(days=1)
        total = stats.get("total", 0)
        wins = stats.get("wins", 0)
        losses = stats.get("losses", 0)
        win_rate = stats.get("win_rate", 0.0)
        total_r = stats.get("total_r", 0.0)

        date_str = now_vn.strftime("%d/%m/%Y")

        for cid in enabled_chats:
            # Per-chat dedupe
            if _last_eod_day.get(cid) == now_vn.day:
                continue
            _last_eod_day[cid] = now_vn.day

            lang = get_lang(cid)
            lines = [
                t("eod_title", lang),
                f"📅 {date_str}",
                "",
                t("eod_tnv", lang),
                t("eod_signals", lang, total=total, wins=wins, losses=losses),
                t("eod_winrate", lang, win_rate=win_rate),
                t("eod_r", lang, total_r=total_r),
            ]
            text = "\n".join(lines)
            if _send_callback:
                try:
                    _send_callback(chat_id=cid, text=text)
                except Exception as e:
                    log.error("Send EOD %d lỗi: %s", cid, e)

        log.info("📊 Tổng kết cuối ngày đã gửi (%s)", date_str)
    except Exception as e:
        log.warning("EOD lỗi: %s", e)


def build_daily_report(lang="vi"):
    """Báo cáo sáng/tối chi tiết: đa khung + chỉ báo + dự đoán."""
    candles = get_candles(limit=120)
    if not candles:
        return _L("no_data", lang)
    price = candles[-1]["close"]
    seq = analyze_candle_sequence(candles, lookback=10)
    ind = compute_all(candles)

    lines = [
        _L("daily_title", lang, time=datetime.now(VN_TZ).strftime('%H:%M %d/%m/%Y')),
        _L("price_simple", lang, price=price),
        "",
        _L("m5_indicators", lang),
        format_indicators(ind),
        "",
        _L("candle_analysis", lang),
        f"`{seq['last_candle']['class'].replace('_', ' ').title().replace(' ', '')}`",
        _L("close_position", lang, pos=seq['last_candle']['close_pos']),
        _L("prediction", lang, dir=_direction_label(seq['predicted_direction'], lang)),
        "",
        _L("disclaimer", lang),
    ]
    return "\n".join(lines)





def _publish_pulse_to_redis():
    """
    Tính pulse từ candles hiện tại + ghi lên Upstash Redis để Web đọc.
    Chạy mỗi 5 phút (cùng pha với auto_signals).
    """
    try:
        from tnv_engine import analyze_tnv
        from redis_writer import write_pulse
        from indicators import compute_all

        candles = get_candles(limit=100)
        if not candles or len(candles) < 22:
            return

        result = analyze_tnv(candles, use_system1=True, use_system2=False)
        if "error" in result:
            return

        price = result.get("current_price")
        if not price or price <= 0:
            return

        # Lấy signal LONG/SHORT/EXIT đầu tiên (nếu có) để suy ra bias
        signals_list = result.get("signals", []) or []
        bias = "NEUTRAL"
        score = 0.0
        entry_price = None
        sl_price = None
        tp_price = None

        for sig in signals_list:
            stype = sig.get("type", "")
            if stype in ("LONG", "SHORT"):
                bias = stype
                score = float(sig.get("score", 0) or 0)
                if "entry_level" in sig and sig["entry_level"]:
                    entry_price = float(sig["entry_level"])
                break

        # N-value: volatility thật của TNV (dùng cho SL/TP, giống auto_signals)
        n_val = result.get("n_value") or 0

        # Tính indicators thật từ candles (cho TechnicalGrid)
        ind = compute_all(candles) if candles else {}
        rsi_val = ind.get("rsi14") or 50.0
        atr_val = ind.get("atr14") or 0.0
        adx_val = ind.get("adx14")
        vwap_val = ind.get("vwap")
        spread_val = ind.get("spread")
        ema9 = ind.get("ema9") or 0.0
        ema21 = ind.get("ema21") or 0.0
        ema_gap = (ema9 - ema21) if (ema9 and ema21) else 0.0

        # Tính SL/TP theo đúng logic TNVGold:
        #   SL = entry ∓ 1.5 × N
        #   TP = entry ± 2.0 × N
        # Giống scheduler.py auto_signals (line 320-330)
        n_use = float(n_val) if n_val else 0.0
        if entry_price and n_use > 0:
            if bias == "LONG":
                sl_price = round(entry_price - 1.5 * n_use, 2)
                tp_price = round(entry_price + 2.0 * n_use, 2)
            elif bias == "SHORT":
                sl_price = round(entry_price + 1.5 * n_use, 2)
                tp_price = round(entry_price - 2.0 * n_use, 2)

        # Khi NEUTRAL: ENTRY hiển thị giá hiện tại, EXIT hiển thị range Low-High
        # (kênh Donchian 20 của S1 — 2 ngưỡng breakout bot đang theo dõi)
        range_low = None
        range_high = None
        if bias == "NEUTRAL":
            entry_price = float(price)
            s1 = result.get("systems", {}).get("S1") or {}
            range_low = s1.get("entry_low")
            range_high = s1.get("entry_high")

        write_pulse(
            price=float(price),
            bias=bias,
            score=score,
            # volatility = N-value (ATR 20 của TNVGold) — dùng cho SL/TP
            volatility=float(n_val) if n_val else None,
            entry_price=entry_price,
            range_low=range_low,
            range_high=range_high,
            sl_price=sl_price,
            tp_price=tp_price,
            rsi=float(rsi_val) if rsi_val else None,
            ema_gap=float(ema_gap),
            adx=adx_val,
            atr_14=float(atr_val) if atr_val else None,  # ATR 14 tách riêng
            vwap=vwap_val,
            spread=spread_val,
        )
    except Exception as e:
        log.warning("publish_pulse_to_redis lỗi: %s", e)


def scheduler_loop(stop_event: threading.Event):
    """Vòng lặp scheduler: tín hiệu TNV, tin, EOD, expiry check."""
    while not stop_event.is_set():
        now_vn = datetime.now(VN_TZ)

        # Cảnh báo tin tức chủ động (mỗi 5 phút)
        if now_vn.minute % NEWS_CHECK_MINUTES == 0:
            news_enabled = [c for c in _active_chat_ids if get_runtime_settings(c)["news"]]
            if news_enabled:
                check_news_alerts(news_enabled)

        # ── Feature 1: tín hiệu TNV tự động (mỗi 5 phút = nến M5 mới) ──
        if now_vn.minute % 5 == 0:
            enabled = [c for c in _active_chat_ids if get_runtime_settings(c)["auto_signal"]]
            if enabled:
                check_auto_signals(enabled)
            # Ghi pulse lên Upstash Redis (chia sẻ với Web dashboard)
            _publish_pulse_to_redis()
            # Theo dõi tín hiệu đang mở: tự đóng khi chạm TP/SL
            try:
                import signals
                candles = get_candles(limit=100)
                closed = signals.evaluate_open_signals(candles)
                if closed:
                    log.info("✅ Auto-close %d tín hiệu chạm TP/SL", closed)
            except Exception as e:
                log.warning("evaluate_open_signals lỗi: %s", e)

        # ── Feature 2: tổng kết cuối ngày (tự kiểm tra giờ/phút) ──
        enabled = [c for c in _active_chat_ids if get_runtime_settings(c)["eod"]]
        if enabled:
            check_eod(enabled)

        # ── Feature 4: nhắc gia hạn / hạ gói (mỗi ngày 08:00 VN) ──
        if now_vn.hour == 8 and now_vn.minute == 0:
            try:
                check_expiring_subs()
            except Exception as e:
                log.warning("check_expiring_subs lỗi: %s", e)

        stop_event.wait(60)


# ── Feature 4: nhắc gia hạn / hạ gói hết hạn ──────────
_last_expiry_day = None  # chống gửi trùng trong cùng ngày


def check_expiring_subs():
    """Mỗi ngày quét 1 lần:
    - User sắp hết hạn (≤ EXPIRE_REMIND_DAYS) → nhắc /redeem
    - User đã hết hạn → hạ về free + thông báo
    """
    global _last_expiry_day
    today = datetime.now(VN_TZ).date()
    if _last_expiry_day == today:
        return
    _last_expiry_day = today

    from storage import list_users, get_active_tier
    remind_days = config.EXPIRE_REMIND_DAYS
    expiring = list_users(expiring_within_days=remind_days)

    for u in expiring:
        cid = u["chat_id"]
        tier = u.get("tier", "free")
        expiry = u.get("expiry_ts", 0) or 0
        if expiry == 0:
            continue  # không hết hạn

        now = int(time.time())
        days_left = (expiry - now) // 86400
        lang = get_lang(cid)

        try:
            if days_left < 0:
                # Đã hết hạn → hạ về free + thông báo
                import storage
                with storage.db() as c:
                    c.execute("UPDATE subscriptions SET tier = 'free' WHERE chat_id = ?", (cid,))
                msg = t("expire_done", lang, tier=tier)
                log.info("Subscription expired: cid=%s tier=%s", cid, tier)
            else:
                # Sắp hết hạn → nhắc
                msg = t("expire_warn", lang, tier=tier, days=days_left)
                log.info("Expiring soon: cid=%s tier=%s days=%d", cid, tier, days_left)

            if _send_callback:
                _send_callback(cid, msg)
        except Exception as e:
            log.warning("send expiry notify to %s lỗi: %s", cid, e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(build_daily_report())
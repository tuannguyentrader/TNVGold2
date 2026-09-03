"""
report.py — Dựng báo cáo tổng XAUUSD (/xau) theo mẫu Gemini đã chốt.
Không gọi LLM — tính toán từ nến MT5 + TNV + phân tích nến (nhanh, ổn định).

Cấu trúc:
  📊 BÁO CÁO XAUUSD — M5
  Phiên London/overlap | 21:00 UTC
  Giá hiện tại
  📉 XU HƯỚNG & MOMENTUM
  📡 TNVGold — SYSTEM 1
  🎯 KHUYẾN NGHỊ HÀNH ĐỘNG
  Disclaimer
"""
from datetime import datetime, timedelta, timezone

VN_TZ = timezone(timedelta(hours=7))

from indicators import compute_all
from candle_analysis import analyze_candle_sequence
from tnv_engine import donchian_high, donchian_low, format_tnv_gemini
from i18n import t
_L = t


def _session_label(hour_utc: int, lang: str = "vi") -> str:
    """Nhận diện phiên giao dịch theo giờ UTC."""
    if 8 <= hour_utc < 12:
        return _L("session_london_rep", lang)
    if 12 <= hour_utc < 16:
        return _L("session_overlap", lang)
    if 16 <= hour_utc < 21:
        return _L("session_ny", lang)
    return _L("session_asia_rep", lang)


def _trend_text(price, s20, s50, lang: str = "vi"):
    """Xác định trend theo vị trí giá so SMA20/SMA50."""
    if s20 is None or s50 is None:
        return "n/a", 0
    if price < s20 and price < s50:
        return _L("trend_down", lang), -1
    if price > s20 and price > s50:
        return _L("trend_up", lang), 1
    return _L("trend_sideways", lang), 0


def _rsi_state(rsi, lang: str = "vi"):
    if rsi is None:
        return "n/a"
    if rsi < 30:
        return _L("rsi_oversold", lang)
    if rsi > 70:
        return _L("rsi_overbought", lang)
    return _L("rsi_neutral", lang)


def _prediction(seq, lang: str = "vi"):
    """Map dự đoán nến + confidence giả từ score của candle engine."""
    direction = seq.get("predicted_direction", "SIDE WAYS (đi ngang, chờ breakout)")
    score = seq.get("score", 0)
    conf = min(85, 50 + abs(score) * 7)  # confidence ước lượng

    mapping = {
        "UP (tăng)": ("🟢", _L("pred_up", lang)),
        "DOWN (giảm)": ("🔴", _L("pred_down", lang)),
        "TĂNG NHẸ (cẩn thận)": ("🟢", _L("pred_slight_up", lang)),
        "GIẢM NHẸ (cẩn thận)": ("🔴", _L("pred_slight_down", lang)),
        "SIDE WAYS (đi ngang, chờ breakout)": ("⚪", _L("pred_sideways", lang)),
    }
    emoji, label = mapping.get(direction, ("⚪", _L("pred_sideways", lang)))
    return emoji, label, conf


def build_xau_report(candles, tnv_result, lang="vi", timeframe="M5"):
    """
    Dựng báo cáo tổng /xau.
    candles: nến M5 (hoặc khung yêu cầu).
    tnv_result: dict từ analyze_tnv(candles, candles_htf=...).
    """
    if not candles or len(candles) < 20:
        return t("not_enough_data_xau", lang)

    ind = compute_all(candles)
    price = ind.get("last_close") or candles[-1]["close"]

    # ── Thời gian + phiên ────────────────────────────────
    now_utc = datetime.now(timezone.utc)
    now_vn = now_utc.astimezone(VN_TZ)
    hour = now_vn.hour  # giờ VN để hiển thị
    session = _session_label(now_utc.hour, lang)  # phiên tính theo giờ UTC
    time_str = f"{hour:02d}:{now_vn.minute:02d} VN"

    # ── Xu hướng & momentum ─────────────────────────────
    s20, s50 = ind.get("sma20"), ind.get("sma50")
    trend, trend_dir = _trend_text(price, s20, s50, lang)

    # Vị trí so SMA cho dòng Trend M5
    if s20 is not None and s50 is not None:
        if trend_dir == -1:
            pos_text = _L("pos_below_rep", lang, s20=s20, s50=s50)
        elif trend_dir == 1:
            pos_text = _L("pos_above_rep", lang, s20=s20, s50=s50)
        else:
            pos_text = _L("pos_between_rep", lang, s20=s20, s50=s50)
    else:
        pos_text = _L("pos_no_sma", lang)

    rsi = ind.get("rsi14")
    rsi_state = _rsi_state(rsi, lang)
    rsi_txt = f"`{rsi:.1f}`" if rsi is not None else "`n/a`"

    macd_line, _, macd_hist = ind.get("macd", (None, None, None))
    macd_txt = f"`{macd_hist:+.2f}`" if macd_hist is not None else "`n/a`"

    atr_v = ind.get("atr14")
    atr_txt = f"`${atr_v:.2f}`" if atr_v else "`n/a`"

    dc_hi = donchian_high(candles, 20, offset=1)
    dc_lo = donchian_low(candles, 20, offset=1)
    if dc_hi is not None and dc_lo is not None:
        range_txt = f"`${dc_lo:.0f}` - `${dc_hi:.0f}`"
    else:
        range_txt = "`n/a`"

    # ── Dự đoán nến ─────────────────────────────────────
    seq = analyze_candle_sequence(candles, lookback=10)
    p_emoji, p_label, p_conf = _prediction(seq, lang)

    # ── TNV signal ──────────────────────────────────────
    tnv_section = format_tnv_gemini(tnv_result, lang=lang) if tnv_result else _L("tnv_no_data", lang)

    # ── Khuyến nghị ─────────────────────────────────────
    reco_lines = _build_reco(tnv_result, trend, trend_dir, lang)

    lines = [
        t("report_title", lang, tf=timeframe),
        f"_{session} | {time_str}_",
        "",
        f"{t('price_label', lang)} `${price:.2f}`",
        "",
        "━━━━━━━━━━━━",
        t("section_trend", lang),
        "",
        f"• Trend {timeframe}: {pos_text}",
        f"• RSI (14): {rsi_txt} ({rsi_state}) | MACD: {macd_txt}",
        _L("atr_range", lang, atr=atr_txt, rng=range_txt),
        f"{_L('pred_line', lang, tf=timeframe)} {p_emoji} {p_label} ({p_conf}%)",
        "",
        tnv_section,
        "",
        "━━━━━━━━━━━━",
        t("section_reco", lang),
        "",
    ]
    lines += reco_lines
    lines.append("")

    # ── Tin tức kinh tế sắp tới ──────────────────────────
    try:
        from forex_factory import get_calendar, filter_usd_events, events_in_window
        _events = get_calendar()
        if _events:
            usd = filter_usd_events(_events)
            now = datetime.now(timezone.utc)
            upcoming = events_in_window(usd, minutes=240)  # tin trong 4h tới
        else:
            upcoming = []

        news_block = [
            "━━━━━━━━━━━━",
            _L("news_title", lang),
            "",
        ]

        if upcoming:
            for ev in upcoming:
                ev_time = ev["time_utc"]
                ev_time_vn = ev_time.astimezone(VN_TZ) if isinstance(ev_time, datetime) else ev_time
                impact_icon = "🔴" if ev["impact"] == "High" else "🟡"
                title = ev.get("title", "")
                news_block.append(f"• `{ev_time_vn.strftime('%H:%M')}` {impact_icon} 🇺🇸 *{title}*")
                parts = []
                if ev.get("forecast"):
                    parts.append(f"{_L('news_forecast', lang)} `{ev['forecast']}`")
                if ev.get("previous"):
                    parts.append(f"{_L('news_previous', lang)} `{ev['previous']}`")
                if parts:
                    news_block.append("  " + " | ".join(parts))
        else:
            news_block.append(_L("news_empty", lang))

        lines += news_block

    except Exception:
        pass  # Không có news thì bỏ qua, không crash

    lines.append("")
    lines.append(t("disclaimer", lang))

    return "\n".join(lines)


def _build_reco(tnv_result, trend, trend_dir, lang):
    """Dựng phần KHUYẾN NGHỊ HÀNH ĐỘNG."""
    if not tnv_result or "error" in tnv_result:
        return [t("reco_no_data", lang)]

    s1 = tnv_result.get("systems", {}).get("S1") or {}
    signals = tnv_result.get("signals", [])
    actives = [s for s in signals if s["type"] in ("LONG", "SHORT")]
    exits = [s for s in signals if s["type"] in ("EXIT_LONG", "EXIT_SHORT")]

    # Lấy entry_high / entry_low cho điều kiện hủy
    cancel_hi = s1.get("entry_high")
    cancel_lo = s1.get("entry_low")

    lines = []

    # ── Có tín hiệu active → ưu tiên hướng (khớp TNV block) ──
    if actives:
        sig = actives[0]
        is_long = sig["type"] == "LONG"
        dir_label = "LONG" if is_long else "SHORT"
        if (is_long and trend_dir == 1) or (not is_long and trend_dir == -1):
            mark = "✅"
        else:
            mark = "⚠️"
        strategy = f"{t('reco_strategy', lang, dir_label=dir_label, trend=trend, mark=mark)}"
        lines.append(f"• *{t('reco_strategy_label', lang)}* {strategy}")
        # Điều kiện hủy theo hướng lệnh: LONG → phá vỡ dưới entry_low;
        # SHORT → phá vỡ trên entry_high. Không nêu mức cùng chiều (không phải hủy).
        if is_long and cancel_lo is not None:
            lines.append(
                f"• *{t('reco_cancel_label', lang)}* {t('reco_cancel_long', lang, lo=cancel_lo)}"
            )
        elif not is_long and cancel_hi is not None:
            lines.append(
                f"• *{t('reco_cancel_label', lang)}* {t('reco_cancel_short', lang, hi=cancel_hi)}"
            )
    # ── EXIT → chốt lời (chỉ khi không có entry mới) ──────
    elif exits:
        ex = exits[0]
        is_long_exit = ex["type"] == "EXIT_LONG"
        dir_label = "LONG" if is_long_exit else "SHORT"
        lines.append(f"• *{t('reco_strategy_label', lang)}* {t('reco_exit', lang, dir_label=dir_label)}")
    else:
        # Sideway hoặc dưới ngưỡng → không vào
        lines.append(f"• *{t('reco_strategy_label', lang)}* {t('reco_sideway', lang)}")

    return lines

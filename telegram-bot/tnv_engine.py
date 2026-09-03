"""
TNV Engine — Port chính xác từ TNV_Indicator v3.26 (MQL5 → Python)
Chiến lược:
- System 1: Donchian 20/10 (nhanh, cho scalp M5)
- System 2: Donchian 55/20 (dài hạn, lọc trend)
- N = ATR(20) Wilder — sizing
- Breakout Quality Filter (Score 0-10): body ratio, đóng 1/3, range, HTF, buffer
"""

from indicators import atr, compute_all


# ── Bilingual support: dùng chung từ i18n ────────────────
from i18n import t as _t


# ── N (ATR Wilder) ────────────────────────────────────────
def compute_n(candles, period=20):
    """
    Tính N = ATR(20) Wilder.
    Giống hệt ComputeN() trong TNV_Indicator.mq5.
    """
    if len(candles) < period + 2:
        return None
    trs = []
    for i in range(1, len(candles)):
        h = candles[i]["high"]
        l = candles[i]["low"]
        pc = candles[i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    # Wilder smoothing
    seed = sum(trs[:period]) / period
    n = seed
    for i in range(period, len(trs)):
        n = (n * (period - 1) + trs[i]) / period
    return n


# ── Donchian ─────────────────────────────────────────────
def donchian_high(candles, period, offset=0):
    """Highest high trong period nến, tính từ offset."""
    if len(candles) < offset + period:
        return None
    return max(c["high"] for c in candles[-(offset + period):len(candles) - offset])


def donchian_low(candles, period, offset=0):
    """Lowest low trong period nến, tính từ offset."""
    if len(candles) < offset + period:
        return None
    return min(c["low"] for c in candles[-(offset + period):len(candles) - offset])


# ── HTF Filter (Higher Timeframe) ─────────────────────────
def get_higher_tf(minutes: int) -> str:
    """Tra từ khung thời gian phút → khung lớn hơn (giống GetHigherTimeframe)."""
    if minutes <= 5:
        return "M15"
    elif minutes <= 15:
        return "H1"
    elif minutes <= 30:
        return "H1"
    elif minutes <= 60:
        return "H4"
    elif minutes <= 240:
        return "D1"
    else:
        return "H1"


def is_htf_not_against(candles_htf, is_long: bool, lookback=5):
    """
    Kiểm tra Higher Timeframe không chống lại hướng giao dịch.
    Giống IsHTFNotAgainst trong MQL5.
    Trả True nếu HTF ủng hộ hoặc trung lập, False nếu chống lại.
    """
    if len(candles_htf) < lookback:
        return True  # không đủ dữ liệu → không filter

    htf_candles = candles_htf[-(lookback + 1):-1]  # bỏ nến đang hình thành
    if len(htf_candles) < 4:
        return True

    lower_highs = 0
    lower_lows = 0
    higher_highs = 0
    higher_lows = 0

    for i in range(1, min(4, len(htf_candles))):
        if htf_candles[i]["high"] < htf_candles[i - 1]["high"]:
            lower_highs += 1
        if htf_candles[i]["low"] < htf_candles[i - 1]["low"]:
            lower_lows += 1
        if htf_candles[i]["high"] > htf_candles[i - 1]["high"]:
            higher_highs += 1
        if htf_candles[i]["low"] > htf_candles[i - 1]["low"]:
            higher_lows += 1

    if is_long:
        # Nếu 2/4 nến gần đều đỉnh thấp hơn và đáy thấp hơn → downtrend HTF
        if lower_highs >= 2 and lower_lows >= 2:
            return False
        return True
    else:
        if higher_highs >= 2 and higher_lows >= 2:
            return False
        return True


# ── Quality Score (giống hệt CalculateScore) ─────────────
def calculate_score(
    is_long: bool,
    bar_open, bar_high, bar_low, bar_close,
    n_value,
    candles_htf=None,
    # Parameters (giống input TNV)
    use_quality_filter=True,
    min_body_ratio=0.50,
    require_close_third=True,
    range_mult=0.70,
    bonus_range=2,
    bonus_htf=2,
    bonus_n=1,
):
    """
    Tính điểm chất lượng breakout.
    Score 0-10. Score < 5 = không đủ điều kiện.
    """
    if not use_quality_filter:
        return 10

    if n_value is None or n_value <= 0:
        return 0

    bar_range = bar_high - bar_low
    if bar_range <= 0:
        return 0

    body = abs(bar_close - bar_open)
    body_ratio = body / bar_range if bar_range > 0 else 0

    # Body ratio threshold
    if body_ratio < min_body_ratio:
        return 0

    # Close in top/bottom 1/3
    if require_close_third:
        third = bar_range / 3.0
        if is_long:
            if bar_close < (bar_high - third):
                return 0
        else:
            if bar_close > (bar_low + third):
                return 0

    # Base score
    score = 5

    # Range bonus
    if bar_range >= range_mult * n_value:
        score += bonus_range

    # HTF bonus
    if candles_htf is not None and is_htf_not_against(candles_htf, is_long):
        score += bonus_htf

    # N bonus
    if body_ratio >= min_body_ratio and bar_range >= (range_mult * 0.8 * n_value):
        score += bonus_n

    return min(score, 10)


# ── Phân tích TNV trên nến ──────────────────────────────
def analyze_tnv(
    candles,
    candles_htf=None,  # nến khung cao hơn để HTF filter
    # System 1 params
    s1_entry=20,
    s1_exit=10,
    use_system1=True,
    # System 2 params
    s2_entry=55,
    s2_exit=20,
    use_system2=False,
    # Quality Filter params
    buffer_mult=0.15,
    min_body_ratio=0.50,
    require_close_third=True,
    range_mult=0.70,
    min_score=5,
    atr_period=20,
):
    """
    Phân tích TNV trên nến hiện tại.
    Trả dict đầy đủ tín hiệu.
    """
    # Chỉ cần đủ nến cho System 1 (s1_entry=20) + ATR (atr_period+2=22)
    # — không cần s2_entry=55 khi use_system2=False.
    need = max((s1_entry if use_system1 else 0), atr_period + 2)
    if len(candles) < need:
        return {"error": f"Cần ≥{need} nến"}

    # N value
    n_val = compute_n(candles, period=atr_period)
    if n_val is None or n_val <= 0:
        return {"error": "Không tính được N (ATR)"}

    # Nến hiện tại (nến cuối đã đóng)
    bar = candles[-1]
    bar_open = bar["open"]
    bar_high = bar["high"]
    bar_low = bar["low"]
    bar_close = bar["close"]

    # Nến trước (để kiểm tra first break)
    prev = candles[-2] if len(candles) >= 2 else None

    result = {
        "n_value": round(n_val, 2),
        "current_price": bar_close,
        "signals": [],
        "systems": {},
    }

    # ── System 1 ─────────────────────────────────
    if use_system1:
        e_high = donchian_high(candles, s1_entry, offset=1)  # bỏ nến hiện tại
        e_low = donchian_low(candles, s1_entry, offset=1)
        x_high = donchian_high(candles, s1_exit, offset=1)
        x_low = donchian_low(candles, s1_exit, offset=1)

        prev_e_high = donchian_high(candles, s1_entry, offset=2)
        prev_e_low = donchian_low(candles, s1_entry, offset=2)
        prev_x_low = donchian_low(candles, s1_exit, offset=2)
        prev_x_high = donchian_high(candles, s1_exit, offset=2)

        s1 = {
            "entry_high": round(e_high, 2) if e_high else None,
            "entry_low": round(e_low, 2) if e_low else None,
            "exit_high": round(x_high, 2) if x_high else None,
            "exit_low": round(x_low, 2) if x_low else None,
            "long_signal": False,
            "short_signal": False,
            "exit_long": False,
            "exit_short": False,
            "long_score": 0,
            "short_score": 0,
            "exit_score": 0,
            # HTF filter status (per direction)
            "htf_long_ok": is_htf_not_against(candles_htf, True) if candles_htf else None,
            "htf_short_ok": is_htf_not_against(candles_htf, False) if candles_htf else None,
        }

        buffer = buffer_mult * n_val if n_val > 0 else 0

        # Long Entry
        if e_high and bar_high > e_high:
            buffer_ok = (n_val <= 0) or (bar_close > e_high + buffer)
            first_break = True
            if prev and prev_e_high:
                first_break = not (prev["high"] > prev_e_high)
            if buffer_ok:
                score = calculate_score(
                    True, bar_open, bar_high, bar_low, bar_close, n_val,
                    candles_htf=candles_htf,
                    min_body_ratio=min_body_ratio,
                    require_close_third=require_close_third,
                    range_mult=range_mult,
                )
                s1["long_signal"] = score >= min_score
                s1["long_score"] = score
                if score >= min_score and first_break:
                    result["signals"].append({
                        "system": "S1",
                        "type": "LONG",
                        "price": bar_close,
                        "entry_level": e_high,
                        "score": score,
                        "first_break": first_break,
                    })

        # Short Entry
        if e_low and bar_low < e_low:
            buffer_ok = (n_val <= 0) or (bar_close < e_low - buffer)
            first_break = True
            if prev and prev_e_low:
                first_break = not (prev["low"] < prev_e_low)
            if buffer_ok:
                score = calculate_score(
                    False, bar_open, bar_high, bar_low, bar_close, n_val,
                    candles_htf=candles_htf,
                    min_body_ratio=min_body_ratio,
                    require_close_third=require_close_third,
                    range_mult=range_mult,
                )
                s1["short_signal"] = score >= min_score
                s1["short_score"] = score
                if score >= min_score and first_break:
                    result["signals"].append({
                        "system": "S1",
                        "type": "SHORT",
                        "price": bar_close,
                        "entry_level": e_low,
                        "score": score,
                        "first_break": first_break,
                    })

        # Exit Long
        if x_low and bar_close < x_low:
            first_break = True
            if prev and prev_x_low:
                first_break = not (prev["close"] < prev_x_low)
            score = calculate_score(
                False, bar_open, bar_high, bar_low, bar_close, n_val,
                candles_htf=candles_htf,
                min_body_ratio=min_body_ratio,
                require_close_third=require_close_third,
                range_mult=range_mult,
            )
            s1["exit_long"] = True
            s1["exit_score"] = score
            # Exit KHÔNG bị chặn bởi min_score (giống TNV: exit luôn được alert)
            if first_break:
                result["signals"].append({
                    "system": "S1",
                    "type": "EXIT_LONG",
                    "price": bar_close,
                    "exit_level": x_low,
                    "score": score,
                    "first_break": first_break,
                })

        # Exit Short
        if x_high and bar_close > x_high:
            first_break = True
            if prev and prev_x_high:
                first_break = not (prev["close"] > prev_x_high)
            score = calculate_score(
                True, bar_open, bar_high, bar_low, bar_close, n_val,
                candles_htf=candles_htf,
                min_body_ratio=min_body_ratio,
                require_close_third=require_close_third,
                range_mult=range_mult,
            )
            s1["exit_short"] = True
            s1["exit_score"] = score
            # Exit KHÔNG bị chặn bởi min_score (giống TNV: exit luôn được alert)
            if first_break:
                result["signals"].append({
                    "system": "S1",
                    "type": "EXIT_SHORT",
                    "price": bar_close,
                    "exit_level": x_high,
                    "score": score,
                    "first_break": first_break,
                })

        result["systems"]["S1"] = s1

    # ── System 2 ─────────────────────────────────
    if use_system2:
        e_high = donchian_high(candles, s2_entry, offset=1)
        e_low = donchian_low(candles, s2_entry, offset=1)
        x_high = donchian_high(candles, s2_exit, offset=1)
        x_low = donchian_low(candles, s2_exit, offset=1)

        prev_e_high = donchian_high(candles, s2_entry, offset=2)
        prev_e_low = donchian_low(candles, s2_entry, offset=2)
        prev_x_low = donchian_low(candles, s2_exit, offset=2)
        prev_x_high = donchian_high(candles, s2_exit, offset=2)

        s2 = {
            "entry_high": round(e_high, 2) if e_high else None,
            "entry_low": round(e_low, 2) if e_low else None,
            "exit_high": round(x_high, 2) if x_high else None,
            "exit_low": round(x_low, 2) if x_low else None,
            "long_signal": False,
            "short_signal": False,
            "exit_long": False,
            "exit_short": False,
            "long_score": 0,
            "short_score": 0,
            "exit_score": 0,
        }

        buffer = buffer_mult * n_val if n_val > 0 else 0

        if e_high and bar_high > e_high:
            buffer_ok = (n_val <= 0) or (bar_close > e_high + buffer)
            first_break = True
            if prev and prev_e_high:
                first_break = not (prev["high"] > prev_e_high)
            if buffer_ok:
                score = calculate_score(
                    True, bar_open, bar_high, bar_low, bar_close, n_val,
                    candles_htf=candles_htf,
                    min_body_ratio=min_body_ratio,
                    require_close_third=require_close_third,
                    range_mult=range_mult,
                )
                s2["long_signal"] = score >= min_score
                s2["long_score"] = score
                if score >= min_score and first_break:
                    result["signals"].append({
                        "system": "S2",
                        "type": "LONG",
                        "price": bar_close,
                        "entry_level": e_high,
                        "score": score,
                        "first_break": first_break,
                    })

        if e_low and bar_low < e_low:
            buffer_ok = (n_val <= 0) or (bar_close < e_low - buffer)
            first_break = True
            if prev and prev_e_low:
                first_break = not (prev["low"] < prev_e_low)
            if buffer_ok:
                score = calculate_score(
                    False, bar_open, bar_high, bar_low, bar_close, n_val,
                    candles_htf=candles_htf,
                    min_body_ratio=min_body_ratio,
                    require_close_third=require_close_third,
                    range_mult=range_mult,
                )
                s2["short_signal"] = score >= min_score
                s2["short_score"] = score
                if score >= min_score and first_break:
                    result["signals"].append({
                        "system": "S2",
                        "type": "SHORT",
                        "price": bar_close,
                        "entry_level": e_low,
                        "score": score,
                        "first_break": first_break,
                    })

        if x_low and bar_close < x_low:
            first_break = True
            if prev and prev_x_low:
                first_break = not (prev["close"] < prev_x_low)
            score = calculate_score(
                False, bar_open, bar_high, bar_low, bar_close, n_val,
                candles_htf=candles_htf,
                min_body_ratio=min_body_ratio,
                require_close_third=require_close_third,
                range_mult=range_mult,
            )
            s2["exit_long"] = True
            s2["exit_score"] = score
            if score >= min_score and first_break:
                result["signals"].append({
                    "system": "S2",
                    "type": "EXIT_LONG",
                    "price": bar_close,
                    "exit_level": x_low,
                    "score": score,
                    "first_break": first_break,
                })

        if x_high and bar_close > x_high:
            first_break = True
            if prev and prev_x_high:
                first_break = not (prev["close"] > prev_x_high)
            score = calculate_score(
                True, bar_open, bar_high, bar_low, bar_close, n_val,
                candles_htf=candles_htf,
                min_body_ratio=min_body_ratio,
                require_close_third=require_close_third,
                range_mult=range_mult,
            )
            s2["exit_short"] = True
            s2["exit_score"] = score
            if score >= min_score and first_break:
                result["signals"].append({
                    "system": "S2",
                    "type": "EXIT_SHORT",
                    "price": bar_close,
                    "exit_level": x_high,
                    "score": score,
                    "first_break": first_break,
                })

        result["systems"]["S2"] = s2

    return result


def _format_tnv_block(result, lang="vi"):
    """
    Format thân tín hiệu TNV (SYSTEM 1) theo mẫu đã chốt.
    Trả list dòng (chưa có header) để tái sử dụng cho /tnvgold và /xau.
    """
    if "error" in result:
        return [f"⚠️ {result['error']}"]

    n_val = result.get("n_value", 0)
    price = result.get("current_price", 0)
    s1 = result.get("systems", {}).get("S1")
    if not s1:
        return [_t("no_s1_data", lang)]

    sl_dist = 1.5 * n_val
    tp_dist = 2.0 * n_val

    signals = result.get("signals", [])
    actives = [s for s in signals if s["type"] in ("LONG", "SHORT")]
    exits = [s for s in signals if s["type"] in ("EXIT_LONG", "EXIT_SHORT")]

    lines = []

    # ── 1. Ưu tiên tín hiệu entry active (mẫu 1, 2, 5) ───
    # Khi có entry mới, KHÔNG hiện EXIT để tránh tín hiệu ngược nhau
    if actives:
        for sig in actives:
            is_long = sig["type"] == "LONG"
            entry = sig.get("entry_level") or s1.get("entry_high" if is_long else "entry_low")
            score = sig.get("score", 0)
            if is_long:
                sl = (entry - sl_dist) if entry else None
                tp = (entry + tp_dist) if entry else None
                htf_ok = s1.get("htf_long_ok")
            else:
                sl = (entry + sl_dist) if entry else None
                tp = (entry - tp_dist) if entry else None
                htf_ok = s1.get("htf_short_ok")

            emoji = "🟢" if is_long else "🔴"
            label = "LONG" if is_long else "SHORT"
            mark = "✅" if score >= 7 else "⚠️" if score >= 5 else "❌"

            lines.append(f"{emoji} *{label}* — Score {score}/10 {mark}")
            if entry is not None:
                lines.append(f"  Entry: ${entry:.2f}")
            if sl is not None and tp is not None:
                lines.append(f"  SL: ${sl:.2f} | TP: ${tp:.2f} (R:R 1:2)")
            # HTF line
            if htf_ok is True:
                lines.append(_t("htf_not_against", lang))
            elif htf_ok is False:
                lines.append(_t("htf_against", lang))
                lines.append(_t("htf_against_note", lang))
        return lines

    # ── 2. EXIT signal (mẫu 4) ──────────────────────────
    if exits:
        for ex in exits:
            is_long_exit = ex["type"] == "EXIT_LONG"
            label = "EXIT LONG" if is_long_exit else "EXIT SHORT"
            score = ex.get("score", 0)
            mark = "✅" if score >= 7 else "⚠️"
            # % mục tiêu: khoảng cách giá đã đi từ entry level cùng hướng về TP (2N)
            if is_long_exit:
                base = s1.get("entry_low") or price
                pct = (price - base) / tp_dist * 100 if tp_dist > 0 else 0
            else:
                base = s1.get("entry_high") or price
                pct = (base - price) / tp_dist * 100 if tp_dist > 0 else 0
            pct = max(0, min(100, pct))
            lines.append(f"🔵 *{label}* — Score {score}/10 {mark}")
            lines.append(_t("exit_target_reached", lang, pct))
        return lines

    # ── 3. Có breakout nhưng dưới ngưỡng (mẫu 6) ─────────
    below = []
    if s1.get("long_score", 0) > 0:
        below.append(("LONG", s1.get("long_score"), s1.get("entry_high")))
    if s1.get("short_score", 0) > 0:
        below.append(("SHORT", s1.get("short_score"), s1.get("entry_low")))
    if below:
        for label, score, entry in below:
            emoji = "🟢" if label == "LONG" else "🔴"
            lines.append(f"{emoji} *{label}* — Score {score}/10 ❌")
            if entry is not None:
                lines.append(f"  Entry: ${entry:.2f}")
            lines.append(_t("below_threshold", lang))
        lines.append("")
        lines.append(_t("below_threshold_note", lang))
        return lines

    # ── 4. Sideway — không breakout (mẫu 3) ─────────────
    el = s1.get("entry_low")
    eh = s1.get("entry_high")
    if el is not None and eh is not None:
        lines.append(_t("sideway_range", lang, el, eh))
    else:
        lines.append(_t("sideway_no_breakout", lang))
    return lines


def format_tnv_signal(result, lang="vi"):
    """Format tin nhắn đầy đủ /tnvgold — chỉ SYSTEM 1, theo mẫu đã chốt."""
    if "error" in result:
        return f"⚠️ {result['error']}"

    header = [
        "📡 *TNVGold — XAUUSD M5*",
        f"{_t('price_n', lang, result.get('current_price', 0), result.get('n_value', 0))}",
        "━━━━━━━━━━━━",
    ]
    return "\n".join(header + _format_tnv_block(result, lang=lang))


def format_tnv_section(result, lang="vi"):
    """
    Format riêng phần TNV cho /xau (báo cáo tổng).
    """
    if "error" in result:
        return f"⚠️ {result['error']}"
    lines = [
        "━━━━━━━━━━━━",
        "📡 TNVGold",
        "━━━━━━━━━━━━",
    ]
    return "\n".join(lines + _format_tnv_block(result, lang=lang))


def format_tnv_gemini(result, lang="vi"):
    """
    Format phần TNV cho /xau — giống auto signal, bỏ SYSTEM 1, separator ngắn.
    """
    if "error" in result:
        return f"⚠️ {result['error']}"

    n_val = result.get("n_value", 0)
    sl_dist = 1.5 * n_val
    tp_dist = 2.0 * n_val

    lines = ["━━━━━━━━━━━━", "📡 *TNVGold*", ""]

    signals = result.get("signals", [])
    actives = [s for s in signals if s["type"] in ("LONG", "SHORT")]

    # ── 1. Có tín hiệu active ──
    if actives:
        for sig in actives:
            is_long = sig["type"] == "LONG"
            score = sig.get("score", 0)
            emoji = "🟢" if is_long else "🔴"
            entry = sig.get("entry_level")

            if is_long:
                sl = (entry - sl_dist) if entry else None
                tp = (entry + tp_dist) if entry else None
            else:
                sl = (entry + sl_dist) if entry else None
                tp = (entry - tp_dist) if entry else None

            lines.append(f"{emoji} *{'LONG' if is_long else 'SHORT'}* | *Score: {score}/10* ✅")
            lines.append("")
            if entry is not None:
                lines.append(f"🔹 *Entry:* `{entry:.2f}`")
            if sl is not None:
                lines.append(f"🔹 *Stop Loss (SL):* `{sl:.2f}`")
            if tp is not None:
                lines.append(f"🔹 *Take Profit (TP):* `{tp:.2f}`")
        return "\n".join(lines)

    # ── 2. Không có tín hiệu ──
    lines.append(_t("wait_no_signal", lang))
    return "\n".join(lines)


if __name__ == "__main__":
    # Demo với dữ liệu mẫu
    import random
    random.seed(42)
    base = 2930.0
    candles = []
    for i in range(100):
        direction = random.choice([-1, 1]) * random.uniform(0.5, 3.0)
        o = base
        c = o + direction
        h = max(o, c) + random.uniform(0.2, 1.5)
        l = min(o, c) - random.uniform(0.2, 1.5)
        candles.append({
            "open": round(o, 2), "high": round(h, 2),
            "low": round(l, 2), "close": round(c, 2),
            "volume": random.randint(10, 100),
        })
        base = c

    result = analyze_tnv(candles, use_system1=True, use_system2=False)
    print(format_tnv_signal(result))
    print("✅ tnv_engine OK")
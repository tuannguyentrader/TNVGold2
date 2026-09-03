"""
Candle Analysis — Phân tích TỪNG NẾN (O/H/L/C + vị trí đóng cửa)
để dự đoán xu hướng tiếp theo. Trái tim của bot scalp M5.

Nguyên tắc:
- Mỗi nến cho biết "bên nào thắng" (bull/bear) qua vị trí đóng so với thân nến.
- Vị trí đóng (close position) trong thân nến → lực lượng phe còn lại.
- Chuỗi nến liên tiếp → momentum & khả năng đảo chiều.
"""

# ── Vị trí đóng cửa trong nến ─────────────────────────────
def close_position(candle):
    """
    Trả vị trí đóng trong khoảng [0,1]:
    0 = đóng sát đáy nến (bear mạnh), 1 = đóng sát đỉnh (bull mạnh),
    0.5 = đóng giữa (do dự).
    Nếu high==low (nến đứng yên) → 0.5.
    """
    h = candle["high"]
    l = candle["low"]
    c = candle["close"]
    o = candle["open"]
    if h == l:
        return 0.5
    return (c - l) / (h - l)


def candle_body(candle):
    """Thân nến: |close - open|."""
    return abs(candle["close"] - candle["open"])


def candle_range(candle):
    """Phạm vi nến: high - low."""
    return candle["high"] - candle["low"]


def is_bull(candle):
    return candle["close"] > candle["open"]


def is_bear(candle):
    return candle["close"] < candle["open"]


# ── Phân loại 1 nến ─────────────────────────────────────
def classify_candle(candle):
    """
    Phân loại nến theo:
    - Hướng (bull/bear/doji)
    - Độ mạnh (strong/weak/normal)
    - Vị trí đóng (upper/lower/middle)
    """
    o, h, l, c = candle["open"], candle["high"], candle["low"], candle["close"]
    cp = close_position(candle)
    body = candle_body(candle)
    rng = candle_range(candle)

    if rng == 0:
        return "doji_flat"

    # Doji: thân rất nhỏ so với range
    body_ratio = body / rng if rng > 0 else 0
    if body_ratio < 0.1:
        return "doji"

    if is_bull(candle):
        if cp >= 0.8:
            strength = "strong"
        elif cp >= 0.5:
            strength = "normal"
        else:
            strength = "weak"  # bull nhưng đóng thấp → bị kéo xuống
        return f"bull_{strength}"
    else:
        if cp <= 0.2:
            strength = "strong"
        elif cp <= 0.5:
            strength = "normal"
        else:
            strength = "weak"  # bear nhưng đóng cao → bị đẩy lên
        return f"bear_{strength}"


# ── Phân tích chuỗi nến → dự đoán xu hướng ───────────────
def analyze_candle_sequence(candles, lookback=10):
    """
    Phân tích chuỗi nến gần nhất và dự đoán xu hướng tiếp theo.
    Trả dict gồm: bias, momentum, signals, detail, predicted_direction.
    """
    if not candles:
        return {"error": "Không có nến"}

    seq = candles[-lookback:]
    classes = [classify_candle(c) for c in seq]
    closes = [c["close"] for c in seq]

    bull_count = sum(1 for c in seq if is_bull(c))
    bear_count = sum(1 for c in seq if is_bear(c))
    doji_count = len(seq) - bull_count - bear_count

    # Momentum: tỷ lệ nến xanh/đỏ (không dùng body_sum vì nến xanh nhỏ + nến đỏ to làm sai lệch)
    body_sum = sum(candle_body(c) * (1 if is_bull(c) else -1) for c in seq)

    # Độ dốc: nến gần nhất cao/thấp hơn trước?
    last = seq[-1]
    prev = seq[-2] if len(seq) >= 2 else None

    # Vị trí đóng hiện tại
    cp = close_position(last)

    # Phát hiện đảo chiều (reversal) tiềm năng
    reversal_signals = []
    if len(seq) >= 3:
        c3 = seq[-3]
        c2 = seq[-2]
        c1 = seq[-1]
        # Bullish reversal: bear → bull với đóng cao
        if is_bear(c2) and is_bull(c1) and close_position(c1) >= 0.6:
            reversal_signals.append("bullish_reversal (nến xanh sau nến đỏ, đóng cao)")
        if is_bull(c2) and is_bear(c1) and close_position(c1) <= 0.4:
            reversal_signals.append("bearish_reversal (nến đỏ sau nến xanh, đóng thấp)")

    # Phát hiện momentum mạnh — dùng tỷ lệ nến xanh/đỏ, không dùng body_sum
    momentum = "neutral"
    if bull_count >= 7 and bear_count <= 2:
        momentum = "strong_bullish"
    elif bull_count >= 5 and bear_count <= 4:
        momentum = "bullish"
    elif bear_count >= 7 and bull_count <= 2:
        momentum = "strong_bearish"
    elif bear_count >= 5 and bull_count <= 4:
        momentum = "bearish"

    # Dự đoán hướng tiếp theo (heuristic)
    # Nến cuối đóng vị trí cao + momentum bull → khả năng tiếp tục lên
    score = 0
    if is_bull(last):
        score += 1
    else:
        score -= 1
    if cp >= 0.7:
        score += 1
    elif cp <= 0.3:
        score -= 1
    if momentum.startswith("strong_bull"):
        score += 2
    elif momentum.startswith("strong_bear"):
        score -= 2
    elif momentum.startswith("bull"):
        score += 1
    elif momentum.startswith("bear"):
        score -= 1
    if reversal_signals:
        # Đảo chiều tăng xác suất ngược
        if "bullish_reversal" in reversal_signals[0]:
            score += 1
        elif "bearish_reversal" in reversal_signals[0]:
            score -= 1

    if score >= 3:
        direction = "UP (tăng)"
    elif score <= -3:
        direction = "DOWN (giảm)"
    elif score >= 1:
        direction = "TĂNG NHẸ (cẩn thận)"
    elif score <= -1:
        direction = "GIẢM NHẸ (cẩn thận)"
    else:
        direction = "SIDE WAYS (đi ngang, chờ breakout)"

    return {
        "lookback": len(seq),
        "bull_count": bull_count,
        "bear_count": bear_count,
        "doji_count": doji_count,
        "body_sum": round(body_sum, 2),
        "momentum": momentum,
        "reversal_signals": reversal_signals,
        "last_candle": {
            "open": last["open"],
            "high": last["high"],
            "low": last["low"],
            "close": last["close"],
            "class": classes[-1],
            "close_pos": round(cp, 2),
        },
        "score": score,
        "predicted_direction": direction,
    }


def _class_display(class_name):
    """Chuyển class nến (bull_strong) → hiển thị (BullStrong)."""
    parts = class_name.split("_")
    return "".join(p.capitalize() for p in parts)


def _reversal_display(signal, last_class, lang="vi"):
    """Format tín hiệu đảo chiều theo mẫu mới (song ngữ vi/en).

    - Tiếng Anh: bọc tên class trong backtick (code span) → underscore an toàn,
      không cần escape (Telegram không parse code span).
    - Tiếng Việt: để trần → lưu ý underscore nếu có sẽ bị Telegram parse thành italic
    """
    if "bullish_reversal" in signal:
        raw = f"{_class_display(last_class)}_reversal"
        desc = _cl("reversal_bull", lang)
    elif "bearish_reversal" in signal:
        raw = f"{_class_display(last_class)}_reversal"
        desc = _cl("reversal_bear", lang)
    else:
        raw = signal
        desc = signal

    if lang == "en":
        base = f"`{raw}`"
    else:
        base = f"`{raw}`"
    return base, desc


def _close_position_text(cp, lang="vi"):
    """Mô tả vị trí đóng (song ngữ vi/en)."""
    if cp >= 0.8:
        return _cl("pos_high", lang), _cl("side_bull", lang)
    if cp <= 0.2:
        return _cl("pos_low", lang), _cl("side_bear", lang)
    if cp >= 0.6:
        return _cl("pos_above_c", lang), _cl("side_buy", lang)
    if cp <= 0.4:
        return _cl("pos_below_c", lang), _cl("side_sell", lang)
    return _cl("pos_mid", lang), _cl("side_mid", lang)


def _direction_emoji_and_note(direction, lang="vi"):
    """Emoji + ghi chú cho dự đoán (trả key theo bản đồ _C, không phụ thuộc ngôn ngữ)."""
    d = direction.lower()
    if "tăng" in d and "nhẹ" in d:
        return "dir_slight_up_c", "🟢", "note_caution"
    if "tăng" in d:
        return "dir_up_c", "🟢", ""
    if "giảm" in d and "nhẹ" in d:
        return "dir_slight_down_c", "🔴", "note_caution"
    if "giảm" in d:
        return "dir_down_c", "🔴", ""
    if "side" in d or "ngang" in d:
        return "dir_side_c", "⚪", "note_breakout"
    return "dir_side_c", "⚪", ""


# ── Song ngữ vi/en: dùng chung từ i18n ────────────────────
from i18n import t as _cl


def format_sequence_report(analysis, timeframe="M5", lang="vi"):
    """Format kết quả phân tích chuỗi nến → mẫu /candle mới (song ngữ vi/en)."""
    if "error" in analysis:
        return analysis["error"]

    lc = analysis["last_candle"]
    cp = lc["close_pos"]
    pos_text, phe_text = _close_position_text(cp, lang)
    class_display = _class_display(lc["class"])
    pct = f"{cp:.0%}"

    # Số xanh/đỏ
    bull = analysis["bull_count"]
    bear = analysis["bear_count"]
    doji = analysis["doji_count"]
    momentum = analysis["momentum"]

    # Đảo chiều
    reversal_line = ""
    if analysis["reversal_signals"]:
        sig = analysis["reversal_signals"][0]
        base, desc = _reversal_display(sig, lc["class"], lang)
        reversal_line = f"{_cl('reversal', lang)} {base} ({desc})"

    # Dự đoán
    dir_key, dir_emoji, note_key = _direction_emoji_and_note(analysis["predicted_direction"], lang)
    pred_text = f"{dir_emoji} {_cl(dir_key, lang)}"
    if note_key:
        pred_text += f" {_cl(note_key, lang)}"

    # O/H/L/C: tiếng Anh bọc backtick từng ký tự (khớp mẫu EN), tiếng Việt để trần
    if lang == "en":
        ohlc = f"`O`={lc['open']:.2f} | `H`={lc['high']:.2f} | `L`={lc['low']:.2f} | `C`={lc['close']:.2f}"
    else:
        ohlc = f"O={lc['open']:.2f} | H={lc['high']:.2f} | L={lc['low']:.2f} | C={lc['close']:.2f}"

    # Vị trí đóng: tiếng Anh đậm cả câu phe (khớp mẫu EN), tiếng Việt giữ nguyên
    if lang == "en":
        close_pos_line = f"{_cl('close_pos', lang)} {pos_text} {_cl('range_pct', lang, pct=pct)} ➡️ *{phe_text}.*"
    else:
        close_pos_line = f"{_cl('close_pos', lang)} {pos_text} {_cl('range_pct', lang, pct=pct)} ➡️ {phe_text}."

    lines = [
        _cl("cand_header", lang, tf=timeframe),
        "",
        f"{_cl('last_candle', lang)} {class_display} ({ohlc})",
        close_pos_line,
        _cl("chain", lang, n=analysis["lookback"], b=bull, r=bear, d=doji, m=f"`{momentum}`"),
    ]
    if reversal_line:
        lines.append(reversal_line)
    # Dự đoán: tiếng Anh đậm hướng (khớp mẫu EN), tiếng Việt giữ nguyên
    if lang == "en":
        lines.append(f"{_cl('predict', lang)} {dir_emoji} *{_cl(dir_key, lang)}* {_cl(note_key, lang) if note_key else ''}".rstrip())
    else:
        lines.append(f"{_cl('predict', lang)} {pred_text}")

    return "\n".join(lines)


if __name__ == "__main__":
    # Demo với dữ liệu mẫu
    import random
    random.seed(42)
    base = 2900.0
    candles = []
    for i in range(12):
        direction = random.choice([-1, 1])
        o = base
        c = o + direction * random.uniform(0.5, 2.5)
        h = max(o, c) + random.uniform(0.2, 1.0)
        l = min(o, c) - random.uniform(0.2, 1.0)
        candles.append({"open": o, "high": h, "low": l, "close": c})
        base = c
    result = analyze_candle_sequence(candles)
    print("=" * 60)
    print("  ENGLISH:")
    print("=" * 60)
    print(format_sequence_report(result, lang="en"))
    print()
    print("=" * 60)
    print("  VIETNAMESE:")
    print("=" * 60)
    print(format_sequence_report(result, lang="vi"))

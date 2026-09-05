"""
Indicators — Tính RSI, MACD, ATR, SMA, EMA, Fibonacci từ nến M5.
Thuần Python, không cần thư viện nặng.
"""


# ── SMA ─────────────────────────────────────────────────
def sma(values, period):
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def sma_series(values, period):
    out = []
    for i in range(len(values)):
        if i + 1 < period:
            out.append(None)
        else:
            out.append(sum(values[i + 1 - period: i + 1]) / period)
    return out


# ── EMA ─────────────────────────────────────────────────
def ema_series(values, period):
    if not values:
        return []
    k = 2 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def ema(values, period):
    s = ema_series(values, period)
    return s[-1] if s else None


# ── RSI ─────────────────────────────────────────────────
def rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    # Chỉ lấy period gần nhất
    gains, losses = gains[-period:], losses[-period:]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# ── MACD ────────────────────────────────────────────────
def macd(closes, fast=12, slow=26, signal=9):
    if len(closes) < slow + signal:
        return None, None, None
    ema_fast = ema_series(closes, fast)
    ema_slow = ema_series(closes, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = ema_series(macd_line, signal)
    hist = [m - s for m, s in zip(macd_line, signal_line)]
    return macd_line[-1], signal_line[-1], hist[-1]


# ── ATR ─────────────────────────────────────────────────
def atr(candles, period=14):
    """ATR từ list nến (dict có high/low/close)."""
    if len(candles) < period + 1:
        return None
    trs = []
    for i in range(1, len(candles)):
        h, l, pc = candles[i]["high"], candles[i]["low"], candles[i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs[-period:]) / period


# ── Bollinger ───────────────────────────────────────────
def bollinger(closes, period=20, mult=2):
    if len(closes) < period:
        return None, None, None
    mid = sma(closes, period)
    window = closes[-period:]
    var = sum((x - mid) ** 2 for x in window) / period
    sd = var ** 0.5
    return mid + mult * sd, mid, mid - mult * sd


# ── Fibonacci ───────────────────────────────────────────
def fib_levels(high, low):
    """Trả các mức Fibonacci từ low→high (uptrend) hoặc high→low."""
    diff = high - low
    if diff <= 0:
        return {}
    levels = {
        "0%": low,
        "23.6%": low + 0.236 * diff,
        "38.2%": low + 0.382 * diff,
        "50%": low + 0.5 * diff,
        "61.8%": low + 0.618 * diff,
        "78.6%": low + 0.786 * diff,
        "100%": high,
    }
    return levels


def adx(candles, period: int = 14) -> float | None:
    """
    Average Directional Index (ADX) — đo sức mạnh xu hướng (0-100).
    Không phụ thuộc vào hướng, chỉ đo độ mạnh.
    ADX >= 25: xu hướng mạnh; ADX < 20: thị trường đi ngang.
    """
    if len(candles) < period * 2 + 1:
        return None
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    closes = [c["close"] for c in candles]

    # True Range
    trs = []
    for i in range(1, len(candles)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)

    # +DM, -DM
    plus_dm = []
    minus_dm = []
    for i in range(1, len(candles)):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        if up > down and up > 0:
            plus_dm.append(up)
        else:
            plus_dm.append(0)
        if down > up and down > 0:
            minus_dm.append(down)
        else:
            minus_dm.append(0)

    # Wilder smoothing (14 periods)
    def wilder_smooth(values, period):
        if len(values) < period:
            return None
        smoothed = [sum(values[:period])]
        for v in values[period:]:
            smoothed.append(smoothed[-1] - smoothed[-1] / period + v)
        return smoothed

    tr_smooth = wilder_smooth(trs, period)
    plus_dm_smooth = wilder_smooth(plus_dm, period)
    minus_dm_smooth = wilder_smooth(minus_dm, period)

    if not tr_smooth or not plus_dm_smooth or not minus_dm_smooth:
        return None

    # +DI, -DI
    plus_di = []
    minus_di = []
    dx = []
    for i in range(len(tr_smooth)):
        if tr_smooth[i] == 0:
            continue
        pdi = 100 * plus_dm_smooth[i] / tr_smooth[i]
        mdi = 100 * minus_dm_smooth[i] / tr_smooth[i]
        plus_di.append(pdi)
        minus_di.append(mdi)
        if (pdi + mdi) == 0:
            dx.append(0)
        else:
            dx.append(100 * abs(pdi - mdi) / (pdi + mdi))

    # ADX = smoothed DX
    if len(dx) < period:
        return None
    adx_smooth = [sum(dx[:period]) / period]
    for v in dx[period:]:
        adx_smooth.append((adx_smooth[-1] * (period - 1) + v) / period)

    return adx_smooth[-1] if adx_smooth else None


def vwap(candles) -> float | None:
    """
    Volume-Weighted Average Price — giá trung bình có trọng số volume.
    Cần candles có key 'volume'. Trả về None nếu không đủ data.
    """
    if not candles:
        return None
    total_pv = 0.0
    total_v = 0.0
    for c in candles:
        v = c.get("volume", 0) or 0
        if v <= 0:
            continue
        typical = (c["high"] + c["low"] + c["close"]) / 3
        total_pv += typical * v
        total_v += v
    if total_v == 0:
        return None
    return total_pv / total_v


def spread_estimate(candles) -> float | None:
    """
    Spread ước lượng (pips) = (high - low) trung bình 5 nến gần nhất.
    Lưu ý: Đây là "price range" (độ biến động) chứ KHÔNG phải bid-ask spread
    thật. Bid-ask spread chỉ có từ MT5 broker.

    XAUUSD: 1 pip = 0.01 USD
    Trả về range trung bình (USD) chia 0.01 = pips
    Ví dụ: nến có high-low = 0.05 USD → 5 pips
    """
    if len(candles) < 5:
        return None
    recent = candles[-5:]
    diffs = [c["high"] - c["low"] for c in recent]
    avg_range = sum(diffs) / len(diffs)
    pips = avg_range / 0.01  # XAUUSD: 1 pip = 0.01 USD
    return round(pips, 1)


# ── Tổng hợp tất cả chỉ báo ─────────────────────────────
def compute_all(candles):
    """Tính toàn bộ chỉ báo từ list nến (đã có open/high/low/close)."""
    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    result = {
        "count": len(candles),
        "last_close": closes[-1] if closes else None,
        "sma20": sma(closes, 20),
        "sma50": sma(closes, 50),
        "sma200": sma(closes, 200),
        "ema9": ema(closes, 9),
        "ema21": ema(closes, 21),
        "rsi14": rsi(closes, 14),
        "atr14": atr(candles, 14),
        "adx14": adx(candles, 14),
        "vwap": vwap(candles),
        "spread": spread_estimate(candles),
        "macd": macd(closes),
        "boll": bollinger(closes),
        "fib": fib_levels(max(highs[-50:]), min(lows[-50:])),
        "recent_high": max(highs[-50:]),
        "recent_low": min(lows[-50:]),
    }
    return result


def format_indicators(ind):
    """Format chỉ báo thành text ngắn gọn cho bot."""
    if not ind or ind.get("last_close") is None:
        return "Chưa đủ dữ liệu."
    lines = [
        f"Giá: ${ind['last_close']:.2f}",
        f"SMA20: {fmt(ind['sma20'])} | SMA50: {fmt(ind['sma50'])}",
        f"EMA9: {fmt(ind['ema9'])} | EMA21: {fmt(ind['ema21'])}",
        f"RSI14: {ind['rsi14']:.1f}" if ind["rsi14"] is not None else "RSI: n/a",
    ]
    if ind["atr14"]:
        lines.append(f"ATR14: ${ind['atr14']:.2f}")
    if ind["macd"][0] is not None:
        m, s, h = ind["macd"]
        lines.append(f"MACD: {m:.2f} / Signal: {s:.2f} / Hist: {h:+.2f}")
    if ind["boll"][0]:
        up, mid, lo = ind["boll"]
        lines.append(f"BB: {lo:.2f} | {mid:.2f} | {up:.2f}")
    lines.append(f"50 nến: H ${ind['recent_high']:.2f} / L ${ind['recent_low']:.2f}")
    return "\n".join(lines)


def fmt(v, digits=2):
    return f"${v:.{digits}f}" if v is not None else "n/a"

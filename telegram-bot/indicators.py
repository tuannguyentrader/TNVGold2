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

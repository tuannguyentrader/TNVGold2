# -*- coding: utf-8 -*-
"""
chartgen.py — Vẽ nến candlestick XAUUSD từ dữ liệu MT5 bằng matplotlib.

Nhanh, gọn, không cần Playwright/Chrome.
- Lấy nến từ MT5 (live) hoặc storage (DB) tuỳ chế độ.
- Vẽ nến candlestick thuần matplotlib (không cần mplfinance).
- Hỗ trợ M5/M15/M30/H1/H4/D1.

Hàm chính:
    generate_chart(timeframe="M5", out_path=None) -> str | None
        Trả đường dẫn file PNG, None nếu lỗi.
"""

import os
import logging
from datetime import datetime

log = logging.getLogger("chartgen")

# Thư mục chứa ảnh tạm
_TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "charts")
os.makedirs(_TMP_DIR, exist_ok=True)

# Map khung thời gian → MT5 timeframe
TF_MAP = {
    "M5": "M5", "M15": "M15", "M30": "M30",
    "H1": "H1", "H4": "H4", "D1": "D1",
}


def _get_candles(timeframe: str, count: int = 100):
    """Lấy nến từ MT5 nếu có, fallback từ storage.

    Args:
        timeframe: M5/M15/M30/H1/H4/D1.
        count: số nến cần lấy.

    Returns:
        list dict {ts, open, high, low, close} hoặc [].
    """
    tf = TF_MAP.get(timeframe.upper(), "M5")
    # Ưu tiên MT5 (live, đầy đủ hơn)
    try:
        from mt5_connector import get_rates, get_mt5_mode
        if get_mt5_mode() == "local":
            candles = get_rates("XAUUSD", tf, count=count)
            if candles and len(candles) >= 5:
                return candles
    except Exception as e:
        log.debug("MT5 get_rates lỗi: %s", e)

    # Fallback: storage (DB)
    try:
        from storage import get_candles
        return get_candles(limit=count) or []
    except Exception as e:
        log.warning("storage get_candles lỗi: %s", e)
        return []


def generate_chart(timeframe="M5", out_path=None, count=100):
    """Vẽ biểu đồ nến candlestick từ dữ liệu MT5.

    Args:
        timeframe: M5/M15/M30/H1/H4/D1.
        out_path: đường dẫn PNG đích. None → tự tạo trong data/charts.
        count: số nến (mặc định 100).

    Returns:
        str | None: đường dẫn file PNG, None nếu lỗi.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
    except ImportError:
        log.warning("generate_chart: thiếu matplotlib — chạy: pip install matplotlib")
        return None

    candles = _get_candles(timeframe, count=count)
    if not candles or len(candles) < 5:
        log.warning("generate_chart: quá ít nến (%s)", len(candles) if candles else 0)
        return None

    if out_path is None:
        out_path = os.path.join(_TMP_DIR, f"chart_{int(datetime.now().timestamp())}.png")
    else:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Sắp xếp theo thời gian tăng dần
    data = sorted(candles, key=lambda c: c.get("ts", 0))

    # Vẽ nến
    fig, ax = plt.subplots(figsize=(12, 7), dpi=100)
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    bar_width = 0.6
    bull_color = "#26a69a"
    bear_color = "#ef5350"

    for i, c in enumerate(data):
        o = float(c["open"])
        h = float(c["high"])
        l = float(c["low"])
        cl = float(c["close"])
        is_bull = cl >= o
        color = bull_color if is_bull else bear_color

        # Bấc (wick)
        ax.plot([i, i], [l, h], color=color, linewidth=1.2)

        # Thân nến (body)
        body_bottom = min(o, cl)
        body_height = abs(cl - o)
        if body_height < 0.01:  # doji
            body_height = (h - l) * 0.05
        rect = Rectangle(
            (i - bar_width / 2, body_bottom), bar_width, body_height,
            facecolor=color, edgecolor=color, linewidth=0.5,
        )
        ax.add_patch(rect)

    # Auto scale Y
    all_prices = [float(c["high"]) for c in data] + [float(c["low"]) for c in data]
    ax.set_xlim(-0.5, len(data) - 0.5)
    margin = (max(all_prices) - min(all_prices)) * 0.05 or 2
    ax.set_ylim(min(all_prices) - margin, max(all_prices) + margin)

    # Trục X — chỉ hiện 6-8 mốc giờ
    step = max(1, len(data) // 8)
    tick_positions = list(range(0, len(data), step))
    tick_labels = []
    for idx in tick_positions:
        ts = data[idx].get("ts")
        try:
            dt = datetime.fromtimestamp(ts)
            tick_labels.append(dt.strftime("%m/%d %H:%M"))
        except Exception:
            tick_labels.append("")
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, fontsize=8, color="#cccccc", rotation=15)

    # Title
    price = float(data[-1]["close"])
    ax.set_title(
        f"XAUUSD {timeframe.upper()} — ${price:.2f}",
        fontsize=14, fontweight="bold", color="#ffffff",
    )
    ax.grid(True, alpha=0.2, color="#555555")
    ax.tick_params(colors="#cccccc")
    ax.spines["bottom"].set_color("#555555")
    ax.spines["left"].set_color("#555555")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    fig.savefig(out_path, dpi=100, facecolor=fig.get_facecolor())
    plt.close(fig)
    log.info("generate_chart: đã lưu %s (%d nến)", out_path, len(data))
    return out_path


if __name__ == "__main__":
    path = generate_chart(timeframe="M5")
    print("Chart:", path)
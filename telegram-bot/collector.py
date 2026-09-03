"""
Collector — Poll giá Gold-API mỗi 60s, tự gom nến M5, lưu SQLite.
"""

import time
import logging
import threading
import requests
from config import GOLD_API_URL, GOLD_API_KEY, POLL_INTERVAL, CANDLE_MINUTES
from storage import insert_candle, kv_get, kv_set, get_candles

log = logging.getLogger("collector")

# Nến đang xây dựng (trong khoảng thời gian hiện tại)
_current_candle = {
    "ts": None,  # Unix timestamp đầu kỳ
    "open": None,
    "high": None,
    "low": None,
    "close": None,
    "volume": 0,
}

_last_price = {"price": None, "ts": 0, "raw": None}


def fetch_gold_price():
    """Lấy giá XAU realtime. Không giới hạn, không cần key."""
    global _last_price
    try:
        headers = {}
        if GOLD_API_KEY:
            headers["x-api-key"] = GOLD_API_KEY
        r = requests.get(GOLD_API_URL, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        price = data.get("price")
        if price is not None:
            _last_price.update(price=price, ts=time.time(), raw=data)
        return data
    except Exception as e:
        log.warning("[Gold-API] %s", e)
        if _last_price["price"] is not None:
            return _last_price["raw"]
        return None


def _candle_key(ts=None):
    """Trả Unix timestamp đầu kỳ nến cho CANDLE_MINUTES."""
    if ts is None:
        ts = time.time()
    return int(ts) // (CANDLE_MINUTES * 60) * (CANDLE_MINUTES * 60)


def process_tick(price: float, ts: float = None):
    """Nhận 1 tick giá → cập nhật nến hiện tại."""
    global _current_candle
    if ts is None:
        ts = time.time()
    ck = _candle_key(ts)

    # Nếu sang kỳ nến mới → đóng nến cũ, mở nến mới
    if _current_candle["ts"] is not None and _current_candle["ts"] != ck:
        insert_candle(
            _current_candle["ts"],
            _current_candle["open"],
            _current_candle["high"],
            _current_candle["low"],
            _current_candle["close"],
            _current_candle["volume"],
        )
        # Reset
        _current_candle = {"ts": None, "open": None, "high": None, "low": None, "close": None, "volume": 0}

    if _current_candle["ts"] is None:
        _current_candle["ts"] = ck
        _current_candle["open"] = price
        _current_candle["high"] = price
        _current_candle["low"] = price
        _current_candle["close"] = price
        _current_candle["volume"] = 1
    else:
        _current_candle["high"] = max(_current_candle["high"], price)
        _current_candle["low"] = min(_current_candle["low"], price)
        _current_candle["close"] = price
        _current_candle["volume"] += 1


def poll_loop(stop_event: threading.Event):
    """Vòng lặp chính: poll Gold-API mỗi POLL_INTERVAL giây."""
    log.info("Collector bắt đầu (poll %ds, gom %d phút)", POLL_INTERVAL, CANDLE_MINUTES)
    while not stop_event.is_set():
        data = fetch_gold_price()
        if data and data.get("price") is not None:
            process_tick(data["price"])
        # Sleep theo interval, có check stop_event
        stop_event.wait(POLL_INTERVAL)


def get_last_price() -> float | None:
    """Trả giá XAU gần nhất."""
    if _last_price["price"] is not None:
        return _last_price["price"]
    # Fallback: lấy từ nến cuối
    candles = get_candles(limit=1)
    if candles:
        return candles[-1]["close"]
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Fetch thử 1 lần
    d = fetch_gold_price()
    if d:
        print(f"Giá XAU: ${d['price']:.2f} (lúc {d.get('updatedAtReadable','')})")
        process_tick(d["price"])
        print("Nến hiện tại:", _current_candle)
    else:
        print("❌ Không lấy được giá")
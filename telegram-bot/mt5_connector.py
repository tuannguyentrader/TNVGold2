"""
MT5 Connector — Đọc nến XAUUSD trực tiếp từ MetaTrader 5.

Hỗ trợ 3 chế độ:
1. MT5_LOCAL: MT5 chạy trên cùng VPS (qua Wine hoặc Windows VPS)
   → dùng thư viện MetaTrader5 Python
2. MT5_BRIDGE: MT5 chạy máy khác → gửi dữ liệu qua webhook (HTTP POST)
   → bot chạy server nhỏ để nhận
3. FALLBACK: tự gom từ Gold-API (khi MT5 không có)

Cách dùng:
   export MT5_MODE=local        # dùng MT5 trên VPS (cần Wine + MT5)
   export MT5_MODE=bridge       # nhận dữ liệu từ MT5 WebBridge
   export MT5_MODE=fallback     # dùng Gold-API (mặc định)
"""

import os
import json
import logging
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

from config import DATA_DIR, CANDLE_MINUTES
from storage import insert_candle, upsert_candle, get_candles, kv_get, kv_set
from collector import fetch_gold_price, process_tick

# Token xác thực cho MT5 Bridge server (đặt qua biến môi trường BRIDGE_TOKEN).
# Nếu rỗng → không yêu cầu xác thực (tương thích cấu hình cũ).
BRIDGE_TOKEN = os.environ.get("BRIDGE_TOKEN", "")

log = logging.getLogger("mt5")

MT5_MODE = None  # Được set từ main.py; bot.py dùng get_mt5_mode()


def get_mt5_mode():
    """
    Trả MT5 mode hiện tại:
    1. Nếu main.py đã set → dùng giá trị đó
    2. Nếu chưa → đọc từ env MT5_MODE
    3. Mặc định fallback
    """
    global MT5_MODE
    if MT5_MODE is None:
        mode = os.environ.get("MT5_MODE", "fallback").lower()
        if mode == "local":
            MT5_MODE = "local"
        elif mode == "bridge":
            MT5_MODE = "bridge"
        else:
            MT5_MODE = "fallback"
    return MT5_MODE

# ── Cấu hình khung thời gian MT5 ─────────────────────────
MT5_TIMEFRAMES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}

# Cache nến đọc từ MT5
_candle_cache = {}


def mt5_available() -> bool:
    """Kiểm tra MT5 có sẵn không (thử import MetaTrader5)."""
    try:
        import MetaTrader5
        return True
    except ImportError:
        return False


def init_mt5():
    """Khởi tạo kết nối MT5. Cần Wine + MT5 chạy trên VPS."""
    if not mt5_available():
        log.warning("Thiếu thư viện MetaTrader5. Chạy: pip install MetaTrader5")
        return False
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            log.error("MT5 init thất bại: %s", mt5.last_error())
            return False
        log.info("✅ MT5 kết nối thành công")
        return True
    except Exception as e:
        log.error("MT5 lỗi: %s", e)
        return False


def get_rates(symbol="XAUUSD", timeframe="M5", count=500):
    """
    Đọc nến từ MT5.
    symbol: mã MT5 (vd XAUUSD)
    timeframe: M1/M5/M15/M30/H1/H4/D1
    count: số nến tối đa
    Trả list dict hoặc None nếu lỗi.
    """
    if not mt5_available():
        log.warning("MetaTrader5 chưa được cài")
        return None
    try:
        import MetaTrader5 as mt5
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }
        tf = tf_map.get(timeframe.upper())
        if not tf:
            log.error("Timeframe không hợp lệ: %s", timeframe)
            return None

        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        if rates is None:
            log.error("MT5 copy_rates lỗi: %s", mt5.last_error())
            return None

        # Chuyển thành list dict (numpy record array → dict)
        candles = []
        for r in rates:
            # r là numpy.void — truy cập bằng r["field"], KHÔNG dùng r.get()
            vol = r["tick_volume"] if "tick_volume" in r.dtype.names else r["real_volume"] if "real_volume" in r.dtype.names else 0
            candles.append({
                "ts": int(r["time"]),
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": int(vol),
            })
        return candles
    except Exception as e:
        log.error("MT5 get_rates lỗi: %s", e)
        return None


def get_multi_timeframe(symbol="XAUUSD"):
    """Đọc nhiều khung thời gian cùng lúc."""
    result = {}
    for tf in ["M5", "M15", "M30", "H1"]:
        candles = get_rates(symbol, tf, count=200)
        if candles:
            result[tf] = candles
            _candle_cache[tf] = candles
    return result


# ── Bridge Server (nhận dữ liệu từ MT5 WebBridge) ────────
class BridgeHandler(BaseHTTPRequestHandler):
    """HTTP server nhận webhook từ MT5 WebBridge (TNVGold style)."""

    def do_POST(self):
        # Xác thực token (nếu BRIDGE_TOKEN được cấu hình) — kiểm tra TRƯỚC khi xử lý dữ liệu.
        if BRIDGE_TOKEN:
            token = self.headers.get("X-Bridge-Token", "")
            if token != BRIDGE_TOKEN:
                log.warning("Bridge POST bị từ chối: token thiếu/sai")
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b'{"status":"unauthorized"}')
                return
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
            self._process_bridge_data(data)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        except Exception as e:
            log.error("Bridge POST lỗi: %s", e)
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"status":"error"}')

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"MT5 Bridge server running")

    def _process_bridge_data(self, data):
        """Xử lý dữ liệu từ MT5 WebBridge."""
        # Hỗ trợ format: {"symbol":"XAUUSD","timeframe":"M5","candles":[...]}
        # Hoặc: {"symbol":"XAUUSD","price":4456.2}
        if "candles" in data:
            for c in data["candles"]:
                insert_candle(
                    c["ts"], c["open"], c["high"],
                    c["low"], c["close"], c.get("volume", 0),
                )
            log.info("Bridge: nhận %d nến %s", len(data["candles"]), data.get("symbol", "XAU"))
        elif "price" in data:
            process_tick(float(data["price"]))
            log.info("Bridge: tick %.2f", float(data["price"]))

    def log_message(self, format, *args):
        log.debug("Bridge: %s", format % args)


def start_bridge_server(port=5005):
    """Chạy bridge server trong thread riêng."""
    server = HTTPServer(("0.0.0.0", port), BridgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    log.info("✅ Bridge server listening on port %d", port)
    return server


# ── Collector chính (chọn nguồn dữ liệu) ─────────────────
def mt5_collect_loop(stop_event: threading.Event):
    """
    Vòng lặp collector: ưu tiên MT5, fallback Gold-API.
    Chạy mỗi 60s, nếu MT5 có → đọc nến mới, nếu không → poll Gold-API.
    """
    current_mode = get_mt5_mode()
    log.info("MT5 Collector bắt đầu (mode=%s)", current_mode)

    # Nếu MT5 local, thử kết nối
    use_mt5 = False
    if current_mode == "local":
        use_mt5 = init_mt5()
        if not use_mt5:
            log.warning("MT5 local không khả dụng → fallback Gold-API")

    while not stop_event.is_set():
        try:
            if use_mt5:
                # Đọc nến M5 từ MT5 và lưu — BỎ nến đang hình thành (index 0),
                # chỉ lưu nến đã ĐÓNG HẲN để phân tích đúng như indicator MQL5.
                # Dùng UPSERT để nến đóng cập nhật lại đúng giá trị thật.
                candles = get_rates("XAUUSD", "M5", count=6)
                if candles:
                    # copy_rates_from_pos(index 0) = nến đang chạy → bỏ đi
                    closed = candles[:-1]
                    for c in closed:
                        upsert_candle(c["ts"], c["open"], c["high"],
                                      c["low"], c["close"], c["volume"])
                    if closed:
                        log.info("📊 MT5: %d nến M5 đã đóng", len(closed))
                    # Nến hiện tại (đang chạy) → cập nhật "live" cho báo cáo giá
                    live = candles[-1]
                    upsert_candle(live["ts"], live["open"], live["high"],
                                  live["low"], live["close"], live["volume"])
                else:
                    # MT5 mất kết nối → fallback
                    log.warning("MT5 mất kết nối, fallback Gold-API")
                    data = fetch_gold_price()
                    if data:
                        process_tick(data["price"])
            else:
                # Fallback: Gold-API
                data = fetch_gold_price()
                if data:
                    process_tick(data["price"])
        except Exception as e:
            log.error("Collector lỗi: %s", e)

        stop_event.wait(60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    MT5_MODE = "local"

    # Thử MT5
    ok = init_mt5()
    if ok:
        print("✅ MT5 connected")
        data = get_multi_timeframe("XAUUSD")
        for tf, candles in data.items():
            print(f"  {tf}: {len(candles)} nến, giá gần nhất: {candles[-1]['close']:.2f}")
    else:
        print("❌ MT5 không khả dụng")
        print("   Cài: pip install MetaTrader5")
        print("   Cần MT5 terminal chạy qua Wine trên VPS")
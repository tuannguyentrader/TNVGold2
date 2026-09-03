"""
main.py — Khởi động toàn bộ TNVGold Telegram Bot:
1. Collector (MT5 ưu tiên, fallback Gold-API)
2. Telegram Bot
3. Scheduler (báo cáo định kỳ)

Chạy: python3 main.py
"""

import os
import sys
import time
import asyncio
import logging
import signal
import threading
import shutil
from datetime import datetime
from logging.handlers import RotatingFileHandler

sys.path.insert(0, os.path.dirname(__file__))
import config
from storage import init_db
from mt5_connector import start_bridge_server, mt5_collect_loop
from collector import poll_loop

log = logging.getLogger("main")

# ── Thư mục log (cạnh main.py) ───────────────────────────
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_PATH = os.path.join(LOGS_DIR, "bot.log")


def setup_file_logging():
    """Gắn RotatingFileHandler vào root logger để mọi module ghi log ra file."""
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        handler = RotatingFileHandler(
            LOG_PATH, maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logging.getLogger().addHandler(handler)
        log.info("File log: %s", LOG_PATH)
    except Exception as e:
        logging.getLogger().warning("Không thể tạo file log: %s", e)


# ── Backup DB tự động ────────────────────────────────────
BACKUP_DIR = os.path.join(str(config.DATA_DIR), "backups")
_last_backup_day = None
_backup_lock = threading.Lock()


def backup_db():
    """Backup file sqlite + news_cache.json sang thư mục backups, giữ tối đa 7 bản."""
    try:
        db_src = str(config.DB_PATH)
        if not os.path.exists(db_src):
            log.warning("Backup bỏ qua: DB không tồn tại %s", db_src)
            return
        os.makedirs(BACKUP_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Không ghi đè nếu 2 backup cùng giây
        if os.path.exists(os.path.join(BACKUP_DIR, f"xau_bot_{stamp}.db")):
            time.sleep(1)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_dst = os.path.join(BACKUP_DIR, f"xau_bot_{stamp}.db")
        shutil.copy2(db_src, db_dst)
        log.info("Backup DB → %s (%s bytes)", db_dst, os.path.getsize(db_dst))

        # Backup news_cache.json nếu tồn tại
        news_src = os.path.join(os.path.dirname(db_src), "news_cache.json")
        if os.path.exists(news_src):
            news_dst = os.path.join(BACKUP_DIR, f"news_cache_{stamp}.json")
            shutil.copy2(news_src, news_dst)
            log.info("Backup news_cache → %s", news_dst)

        # Giữ tối đa 7 backup gần nhất (chỉ đếm file .db)
        backups = sorted(
            f for f in os.listdir(BACKUP_DIR) if f.startswith("xau_bot_") and f.endswith(".db")
        )
        for old in backups[:-7]:
            try:
                os.remove(os.path.join(BACKUP_DIR, old))
            except OSError as e:
                log.warning("Không xóa được backup cũ %s: %s", old, e)
        log.info("Backup hoàn tất. Giữ %d/%d bản", min(len(backups), 7), len(backups))
    except Exception as e:
        log.exception("Backup DB lỗi: %s", e)


def backup_loop(stop_event):
    """Chờ tới 00:05 giờ địa phương mỗi ngày, backup 1 lần rồi ngủ tiếp."""
    while not stop_event.is_set():
        try:
            now = datetime.now()
            day_key = (now.year, now.month, now.day)
            if now.hour == 0 and now.minute == 5 and _last_backup_day != day_key:
                with _backup_lock:
                    if _last_backup_day != day_key:
                        _last_backup_day = day_key
                        backup_db()
            time.sleep(60)
        except Exception as e:
            log.exception("Backup loop lỗi: %s", e)
            time.sleep(60)


def load_mt5_mode():
    """Chọn chế độ MT5 từ env. Trả 'local' | 'bridge' | 'fallback'."""
    mode = os.environ.get("MT5_MODE", "fallback").lower()
    if mode not in ("local", "bridge", "fallback"):
        mode = "fallback"
    log.info("MT5 mode: %s", mode)
    return mode


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    setup_file_logging()  # Ghi log ra file (logs/bot.log)

    # Khởi tạo DB
    init_db()
    from signals import init_signal_table
    init_signal_table()
    log.info("DB sẵn sàng tại %s", config.DB_PATH)

    # Chọn nguồn dữ liệu
    mode = load_mt5_mode()

    stop_event = threading.Event()

    # Backup DB thread (hàng ngày 00:05)
    backup_thread = threading.Thread(target=backup_loop, args=(stop_event,), daemon=True)
    backup_thread.start()
    log.info("Backup DB thread đã khởi động (hàng ngày 00:05)")

    # Collector thread
    if mode == "local":
        collector_thread = threading.Thread(
            target=mt5_collect_loop, args=(stop_event,), daemon=True
        )
        log.info("MT5 local: bot sẽ đọc nến trực tiếp từ MT5 trên VPS")
    elif mode == "bridge":
        # MT5 trên máy khác gửi qua webhook
        bridge = start_bridge_server(int(os.environ.get("BRIDGE_PORT", "5005")))
        collector_thread = threading.Thread(
            target=poll_loop, args=(stop_event,), daemon=True
        )
        log.info("MT5 bridge: nhận dữ liệu từ MT5 WebBridge trên port 5005")
    else:
        # Fallback: Gold-API realtime
        collector_thread = threading.Thread(
            target=poll_loop, args=(stop_event,), daemon=True
        )
        log.info("Fallback: poll Gold-API mỗi %ds", config.POLL_INTERVAL)
    collector_thread.start()

    # Import bot + scheduler (cần sau khi có collector)
    import bot
    from scheduler import scheduler_loop, set_send_callback, set_active_chats

    # Active chats từ env (chấp nhận cả chat_id âm: group/channel Telegram)
    active_chats = []
    for x in os.environ.get("XAU_CHAT_IDS", "").split(","):
        x = x.strip()
        if not x:
            continue
        try:
            active_chats.append(int(x))
        except ValueError:
            log.warning("Bỏ qua XAU_CHAT_IDS không hợp lệ: %r", x)
    set_active_chats(active_chats)

    # Chạy bot trong thread (run_polling blocking)
    bot_thread = threading.Thread(target=bot.run_bot, args=(stop_event,), daemon=True)
    bot_thread.start()
    log.info("Bot đang chạy (thread)")

    # Chờ bot sẵn sàng để lấy app.bot cho scheduler
    for _ in range(30):
        if bot.get_app() is not None:
            break
        time.sleep(1)

    app = bot.get_app()

    def send_sync(chat_id, text):
        """Gửi tin từ thread scheduler → event loop của bot (thread-safe, PTB v20+)."""
        loop = bot.get_bot_loop()
        if app is None or loop is None:
            log.warning("Scheduler send bỏ qua: app/loop chưa sẵn sàng (chat %s)", chat_id)
            return
        try:
            from telegram_safe import send as ts_send
            async def _send():
                await ts_send(app.bot, chat_id, text)
            asyncio.run_coroutine_threadsafe(_send(), loop)
        except Exception as e:
            log.error("Scheduler send lỗi: %s", e)

    set_send_callback(send_sync)
    log.info("Scheduler đã gắn callback gửi tin")

    # Scheduler thread
    scheduler_thread = threading.Thread(target=scheduler_loop, args=(stop_event,), daemon=True)
    scheduler_thread.start()
    log.info("Scheduler đang chạy")

    # Đợi bot thread kết thúc
    try:
        while bot_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Dừng...")
    finally:
        stop_event.set()
        log.info("Bot đã dừng")


if __name__ == "__main__":
    main()
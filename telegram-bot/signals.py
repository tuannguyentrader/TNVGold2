"""
signals.py — Lưu trữ & theo dõi tín hiệu TNV tự động (Feature 1/4/5).

- Lưu mỗi tín hiệu LONG/SHORT/EXIT (kèm entry/SL/TP) vào SQLite.
- Tự động đánh giá tín hiệu đã đạt TP hay bị SL quét (mô phỏng theo giá thực).
- Cung cấp /history (F4) và /stats (F5).

API thống nhất cho các module khác:
    record_signal(sig)            -> int  (id)
    evaluate_open_signals(candles) -> int  (số tín hiệu vừa được đóng)
    get_history(limit)            -> list[dict]
    get_stats(days)               -> dict
    pending_signals()             -> list[dict]
"""

import logging
import time
from datetime import datetime, timedelta, timezone

from storage import db

log = logging.getLogger("signals")

SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL,              -- giây epoch lúc tín hiệu phát
    type TEXT NOT NULL,               -- LONG | SHORT | EXIT_LONG | EXIT_SHORT | WAIT
    score REAL,                       -- điểm chất lượng (0-10)
    price REAL,                       -- giá đóng cửa lúc phát
    entry REAL,                       -- mức entry (nếu có)
    sl REAL,                          -- stop loss (nếu có)
    tp REAL,                          -- take profit (nếu có)
    status TEXT DEFAULT 'open',       -- open | hit_tp | hit_sl | expired
    close_price REAL,                 -- giá khi đóng (đánh giá)
    closed_at INTEGER,                -- giây epoch khi đóng
    detail TEXT                       -- JSON chi tiết (hướng, first_break...)
);
CREATE INDEX IF NOT EXISTS idx_signals_ts ON signals(ts);
CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
"""


def init_signal_table():
    with db() as c:
        c.executescript(SCHEMA)


def record_signal(sig: dict) -> int:
    """Lưu một tín hiệu mới. Trả id (0 nếu lỗi)."""
    try:
        with db() as c:
            c.execute("SELECT 1 FROM signals LIMIT 1")
    except Exception:
        init_signal_table()
    try:
        with db() as c:
            cur = c.execute(
                "INSERT INTO signals (ts, type, score, price, entry, sl, tp, status, detail) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    int(time.time()),
                    sig.get("type", "WAIT"),
                    sig.get("score"),
                    sig.get("price"),
                    sig.get("entry"),
                    sig.get("sl"),
                    sig.get("tp"),
                    "open",
                    None,
                ),
            )
            return cur.lastrowid
    except Exception as e:
        log.error("record_signal lỗi: %s", e)
        return 0


def _close_signal(sig_id: int, status: str, close_price: float):
    """Đóng một tín hiệu với trạng thái hit_tp/hit_sl."""
    try:
        with db() as c:
            c.execute(
                "UPDATE signals SET status=?, close_price=?, closed_at=? WHERE id=?",
                (status, close_price, int(time.time()), sig_id),
            )
    except Exception as e:
        log.error("close_signal lỗi: %s", e)


def pending_signals() -> list[dict]:
    """Tất cả tín hiệu đang mở (chưa đóng)."""
    with db() as c:
        rows = c.execute(
            "SELECT * FROM signals WHERE status='open' ORDER BY ts"
        ).fetchall()
    return [dict(r) for r in rows]


def evaluate_open_signals(candles) -> int:
    """Đánh giá tín hiệu đang mở dựa trên nến mới.

    Mỗi tín hiệu LONG có TP ở trên / SL ở dưới; SHORT ngược lại.
    Nếu giá đã vượt TP → hit_tp; chạm SL → hit_sl.
    Chỉ xét giá trong các nến MỚI NHẤT (kể từ lúc tín hiệu phát).
    Trả số tín hiệu vừa được đóng.
    """
    if not candles:
        return 0
    opened = 0
    for sig in pending_signals():
        # Bỏ qua nếu chưa đủ dữ liệu entry
        if not sig.get("sl") or not sig.get("tp"):
            continue
        # Giá cao/thấp của các nến sau khi tín hiệu phát
        sig_ts = sig.get("ts", 0)
        post = [c for c in candles if c.get("ts", 0) >= sig_ts]
        if not post:
            # Tất cả nến đều cũ hơn tín hiệu — bỏ qua (không thể đánh giá)
            continue
        highs = [c.get("high", c["close"]) for c in post]
        lows = [c.get("low", c["close"]) for c in post]

        # LONG: TP trên, SL dưới
        if sig["type"] == "LONG":
            if any(h >= sig["tp"] for h in highs):
                _close_signal(sig["id"], "hit_tp", sig["tp"])
                opened += 1
            elif any(l <= sig["sl"] for l in lows):
                _close_signal(sig["id"], "hit_sl", sig["sl"])
                opened += 1
        # SHORT: TP dưới, SL trên
        elif sig["type"] == "SHORT":
            if any(l <= sig["tp"] for l in lows):
                _close_signal(sig["id"], "hit_tp", sig["tp"])
                opened += 1
            elif any(h >= sig["sl"] for h in highs):
                _close_signal(sig["id"], "hit_sl", sig["sl"])
                opened += 1
    return opened


def get_history(limit: int = 10) -> list[dict]:
    """Lịch sử tín hiệu gần nhất (mới nhất trước)."""
    with db() as c:
        rows = c.execute(
            "SELECT * FROM signals ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_stats(days: int = 30) -> dict:
    """Thống kê hiệu suất trong N ngày qua."""
    now = int(time.time())
    since = now - days * 86400
    with db() as c:
        rows = c.execute(
            "SELECT * FROM signals WHERE ts >= ? AND ts <= ? AND type IN ('LONG','SHORT')",
            (since, now),
        ).fetchall()
    sigs = [dict(r) for r in rows]
    total = len(sigs)
    wins = sum(1 for s in sigs if s["status"] == "hit_tp")
    losses = sum(1 for s in sigs if s["status"] == "hit_sl")
    open_n = sum(1 for s in sigs if s["status"] == "open")
    long_n = sum(1 for s in sigs if s["type"] == "LONG")
    short_n = sum(1 for s in sigs if s["type"] == "SHORT")

    # Tổng R: mỗi lệnh thắng +2R (TP=2N), thua -1R (SL=1.5N quy về -1R)
    total_r = wins * 2.0 - losses * 1.0
    decided = wins + losses
    win_rate = (wins / decided * 100) if decided else 0.0

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "open": open_n,
        "long": long_n,
        "short": short_n,
        "win_rate": round(win_rate, 1),
        "total_r": round(total_r, 1),
        "days": days,
    }


def format_history(sigs: list[dict], lang="vi") -> str:
    """Format danh sách tín hiệu cho /history."""
    from i18n import t

    if not sigs:
        return t("hist_empty", lang)
    lines = [t("hist_title", lang)]
    for i, s in enumerate(sigs, 1):
        ts = datetime.fromtimestamp(s["ts"], tz=timezone(timedelta(hours=7)))
        ts_str = ts.strftime("%d/%m %H:%M")
        st = s["status"]
        if st == "hit_tp":
            status = t("hist_status_tp", lang)
        elif st == "hit_sl":
            status = t("hist_status_sl", lang)
        elif st == "open":
            status = t("hist_status_open", lang)
        else:
            status = st
        sig_txt = f"#{i} {ts_str} {s['type']}"
        if s.get("score") is not None:
            sig_txt += f" Score {s['score']:.0f}"
        lines.append(f"• {sig_txt} → {status}")
    return "\n".join(lines)


def format_stats(stats: dict, lang="vi") -> str:
    """Format thống kê cho /stats."""
    from i18n import t

    return t("stats_text", lang, **stats)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_signal_table()
    print("✅ signals table ready")
    print(get_stats())

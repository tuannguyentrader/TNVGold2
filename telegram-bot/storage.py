"""
Storage — SQLite: lưu nến M5, price alerts, báo cáo, config.
"""

import sqlite3
import json
import time
from contextlib import contextmanager
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS candles (
    ts INTEGER PRIMARY KEY,          -- Unix timestamp đầu kỳ nến (giây)
    symbol TEXT NOT NULL DEFAULT 'XAU',
    open REAL, high REAL, low REAL, close REAL,
    volume REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    kind TEXT,                        -- hourly | daily | manual
    ts INTEGER,
    content TEXT
);
CREATE TABLE IF NOT EXISTS subscriptions (
    chat_id INTEGER PRIMARY KEY,
    tier TEXT DEFAULT 'free',
    expiry_ts INTEGER DEFAULT 0,       -- 0 = không hết hạn
    registered_ts INTEGER DEFAULT 0,
    last_renew_ts INTEGER DEFAULT 0,
    notes TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS redeem_codes (
    code TEXT PRIMARY KEY,
    tier TEXT NOT NULL,
    days INTEGER NOT NULL,
    used_by INTEGER DEFAULT 0,         -- 0 = chưa dùng
    used_at INTEGER DEFAULT 0,
    created_at INTEGER DEFAULT 0,
    created_by INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS register_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    tier TEXT,
    days INTEGER,
    ts INTEGER
);
CREATE INDEX IF NOT EXISTS idx_candles_ts ON candles(ts);
CREATE INDEX IF NOT EXISTS idx_redeem_codes_used ON redeem_codes(used_by);
"""


@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db() as c:
        c.executescript(SCHEMA)


# ── Candles ──────────────────────────────────────────────
def insert_candle(ts: int, o, h, l, c_, v=0, symbol="XAU"):
    with db() as c:
        c.execute(
            "INSERT OR IGNORE INTO candles (ts, symbol, open, high, low, close, volume) "
            "VALUES (?,?,?,?,?,?,?)",
            (ts, symbol, o, h, l, c_, v),
        )


def upsert_candle(ts: int, o, h, l, c_, v=0, symbol="XAU"):
    """Thêm mới HOẶC cập nhật nến theo ts (UPSERT).

    Dùng cho nguồn MT5: nến cùng ts (cùng phiên M5) có thể thay đổi
    khi nến đang hình thành → cần cập nhật lại High/Low/Close thay vì IGNORE.
    PK là (ts, symbol) — nếu chưa có UNIQUE, schema sẽ tự tạo.
    """
    with db() as c:
        c.execute(
            "INSERT INTO candles (ts, symbol, open, high, low, close, volume) "
            "VALUES (?,?,?,?,?,?,?) "
            "ON CONFLICT(ts) DO UPDATE SET "
            "open=excluded.open, high=excluded.high, low=excluded.low, "
            "close=excluded.close, volume=excluded.volume",
            (ts, symbol, o, h, l, c_, v),
        )


def get_candles(symbol="XAU", limit=300, interval_minutes=5):
    """Lấy nến đã gom (từ bảng candles — ta lưu M5 theo ts=5 phút)."""
    with db() as c:
        rows = c.execute(
            "SELECT * FROM candles WHERE symbol=? ORDER BY ts DESC LIMIT ?",
            (symbol, limit),
        ).fetchall()
    return list(reversed([dict(r) for r in rows]))


def get_candle_series(interval_minutes=5, limit=500):
    return get_candles(limit=limit)


# ── Reports ──────────────────────────────────────────────
def save_report(chat_id, kind, content):
    with db() as c:
        c.execute(
            "INSERT INTO reports (chat_id, kind, ts, content) VALUES (?,?,?,?)",
            (chat_id, kind, int(time.time()), content),
        )


# ── KV config ────────────────────────────────────────────
def kv_set(key: str, value):
    with db() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)"
        )
        c.execute(
            "INSERT INTO kv (key, value) VALUES (?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value)),
        )


def kv_get(key: str, default=None):
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)")
        r = c.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
    if not r:
        return default
    try:
        return json.loads(r["value"])
    except Exception:
        return r["value"]


def kv_delete(key: str):
    """Xoá 1 key trong kv (nếu có)."""
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)")
        c.execute("DELETE FROM kv WHERE key=?", (key,))


# ── API Keys (lưu SQLite) ────────────────────────────────
def set_api_key(provider: str, key: str):
    """Lưu API key cho provider vào SQLite."""
    kv_set(f"api_key_{provider}", key)


def get_api_key(provider: str) -> str:
    """Lấy API key cho provider từ SQLite."""
    return kv_get(f"api_key_{provider}", "") or ""


def remove_api_key(provider: str):
    """Xóa API key của provider."""
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)")
        c.execute("DELETE FROM kv WHERE key=?", (f"api_key_{provider}",))


def list_api_keys() -> dict:
    """Trả dict {provider: key} của tất cả provider đã lưu."""
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)")
        rows = c.execute("SELECT key, value FROM kv WHERE key LIKE 'api_key_%'").fetchall()
    result = {}
    for r in rows:
        provider = r["key"].replace("api_key_", "")
        result[provider] = json.loads(r["value"]) if r["value"] else ""
    return result


# ── Provider hiện tại (chọn AI dùng) ────────────────────
def set_current_provider(provider: str):
    kv_set("current_provider", provider)


def get_current_provider() -> str:
    """Trả provider hiện tại. Rỗng = chưa đặt → config tự chọn."""
    return kv_get("current_provider", "") or ""


# ── Model override (admin đổi model từ Telegram) ──────────
def get_model_override(provider: str, kind: str = "text") -> str:
    """
    Lấy model override cho provider.
    kind: "text" | "vision"
    Trả chuỗi rỗng nếu chưa override (fallback về config).
    """
    return kv_get(f"model_override_{provider}_{kind}", "") or ""


def set_model_override(provider: str, kind: str, model_name: str):
    """Lưu model override (admin)."""
    kv_set(f"model_override_{provider}_{kind}", model_name)


def clear_model_override(provider: str, kind: str = None):
    """
    Xoá override.
    kind=None → xoá cả text + vision của provider.
    """
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)")
        if kind:
            c.execute("DELETE FROM kv WHERE key=?", (f"model_override_{provider}_{kind}",))
        else:
            c.execute(
                "DELETE FROM kv WHERE key IN (?, ?)",
                (f"model_override_{provider}_text", f"model_override_{provider}_vision"),
            )


def list_model_overrides() -> dict:
    """Trả {provider: {"text": "...", "vision": "..."}} cho tất cả provider có override."""
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)")
        rows = c.execute(
            "SELECT key, value FROM kv WHERE key LIKE 'model_override_%'"
        ).fetchall()
    result = {}
    for r in rows:
        # key: model_override_<provider>_<kind>
        parts = r["key"].split("_")
        if len(parts) < 4:
            continue
        provider = "_".join(parts[2:-1])
        kind = parts[-1]
        result.setdefault(provider, {})[kind] = r["value"]
    return result


# ── User tiers ───────────────────────────────────────────
TIERS = ("free", "pro")

def get_tier(chat_id: int) -> str:
    """Trả tier hiệu lực của user: 'free' | 'pro'.

    Nguồn: subscriptions (hệ mới — /register, /redeem).
    Fallback: kv user_tier:* (dữ liệu cũ từ /tier) nếu chưa có subscription.
    Tự động hạ 'free' nếu đã hết hạn.
    Admin (ADMIN_CHAT_IDS) luôn 'pro'.

    ⚠️ Hàm DUY NHẤT nên dùng để kiểm tra quyền tier trong toàn bộ codebase.
    """
    try:
        from config import ADMIN_CHAT_IDS
        if chat_id in ADMIN_CHAT_IDS:
            return "pro"
    except Exception:
        pass

    # Ưu tiên subscriptions (hệ mới)
    sub = get_subscription(chat_id)
    if sub is not None:
        tier = sub.get("tier", "free")
        expiry = sub.get("expiry_ts", 0) or 0
        if expiry == 0:
            # Không hết hạn → giữ tier
            return tier if tier in TIERS else "free"
        if expiry > int(time.time()):
            return tier if tier in TIERS else "free"
        # Đã hết hạn → hạ về free trong DB
        try:
            with db() as c:
                c.execute("UPDATE subscriptions SET tier = 'free' WHERE chat_id = ?", (chat_id,))
        except Exception:
            pass
        return "free"

    # Chưa có subscription → fallback kv (cũ)
    tier = kv_get(f"user_tier:{chat_id}", "free")
    if tier not in TIERS:
        tier = "free"
    return tier

def set_tier(chat_id: int, tier: str) -> bool:
    """Đặt tier cho user (đồng bộ cả 2 hệ: subscriptions + kv).

    Nếu user chưa đăng ký → chỉ lưu kv (tier tĩnh, không hết hạn).
    Nếu đã đăng ký → cập nhật subscriptions (không đổi expiry hiện tại).
    """
    if tier not in TIERS:
        return False
    # Đồng bộ kv (cũ)
    kv_set(f"user_tier:{chat_id}", tier)
    # Đồng bộ subscriptions (nếu tồn tại)
    try:
        with db() as c:
            c.execute("""
                INSERT INTO subscriptions (chat_id, tier, expiry_ts, registered_ts, last_renew_ts)
                VALUES (?, ?, 0, ?, 0)
                ON CONFLICT(chat_id) DO UPDATE SET tier = excluded.tier
            """, (chat_id, tier, int(time.time())))
    except Exception:
        pass
    return True

def get_tier_expiry(chat_id: int) -> int:
    """Trả timestamp hết hạn tier (0 = không hết hạn)."""
    # Ưu tiên subscriptions
    sub = get_subscription(chat_id)
    if sub is not None:
        return sub.get("expiry_ts", 0) or 0
    return kv_get(f"user_tier_expiry:{chat_id}", 0) or 0

def set_tier_expiry(chat_id: int, expiry_ts: int):
    """Đặt thời gian hết hạn tier (epoch giây)."""
    kv_set(f"user_tier_expiry:{chat_id}", expiry_ts)
    # Đồng bộ subscriptions nếu tồn tại
    try:
        with db() as c:
            c.execute("UPDATE subscriptions SET expiry_ts = ? WHERE chat_id = ?",
                      (expiry_ts, chat_id))
    except Exception:
        pass

def require_tier(min_tier: str, user_tier: str) -> bool:
    """Kiểm tra user_tier có >= min_tier không. free < pro."""
    levels = {"free": 0, "pro": 1}
    return levels.get(user_tier, 0) >= levels.get(min_tier, 0)

def count_premium_users() -> dict:
    """Đếm số user theo tier (cho admin)."""
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)")
        rows = c.execute("SELECT key, value FROM kv WHERE key LIKE 'user_tier:%' AND key NOT LIKE 'user_tier_expiry:%'").fetchall()
    counts = {"free": 0, "pro": 0}
    for r in rows:
        tier = json.loads(r["value"]) if r["value"] else "free"
        if tier in counts:
            counts[tier] += 1
    return counts


# ── Quota (hạn mức sử dụng hàng ngày) ─────────────────────
def _usage_day_key() -> str:
    """Khóa ngày hiện tại (UTC) cho quota — tự reset mỗi ngày."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_usage(chat_id: int, resource: str) -> int:
    """Số lần đã dùng resource (ai_calls, alerts, chart, signals) hôm nay."""
    return kv_get(f"usage:{chat_id}:{resource}:{_usage_day_key()}", 0) or 0


def incr_usage(chat_id: int, resource: str, amount: int = 1) -> int:
    """Tăng bộ đếm usage hôm nay, trả giá trị mới."""
    key = f"usage:{chat_id}:{resource}:{_usage_day_key()}"
    cur = kv_get(key, 0) or 0
    kv_set(key, cur + amount)
    return cur + amount


def check_quota(chat_id: int, resource: str) -> bool:
    """Kiểm tra còn quota cho resource hôm nay không (dùng config.TIER_DAILY_LIMITS)."""
    from config import TIER_DAILY_LIMITS
    tier = get_tier(chat_id)
    limit = TIER_DAILY_LIMITS.get(tier, {}).get(resource, 0)
    if limit <= 0:
        return False  # không được phép dùng
    return get_usage(chat_id, resource) < limit


def quota_remaining(chat_id: int, resource: str) -> int:
    """Số lần còn lại trong hạn mức hôm nay."""
    from config import TIER_DAILY_LIMITS
    tier = get_tier(chat_id)
    limit = TIER_DAILY_LIMITS.get(tier, {}).get(resource, 0)
    used = get_usage(chat_id, resource)
    return max(0, limit - used)


if __name__ == "__main__":
    init_db()
    print(f"✅ DB initialized at {DB_PATH}")
    # Test chèn nến
    insert_candle(int(time.time()) - int(time.time()) % 300, 2900, 2910, 2895, 2905)
    print("Candles:", len(get_candles(limit=5)))


# ── Subscriptions + Redeem codes ────────────────────────
def is_registered(chat_id: int) -> bool:
    """User đã đăng ký chưa."""
    with db() as c:
        row = c.execute("SELECT 1 FROM subscriptions WHERE chat_id = ?", (chat_id,)).fetchone()
    return row is not None


def has_ever_registered(chat_id: int) -> bool:
    """User đã TỪNG đăng ký chưa (kể cả khi row subscriptions đã bị xoá).

    Dùng register_logs (KHÔNG bao giờ bị xoá) để chặn /register nhiều lần.
    """
    with db() as c:
        row = c.execute(
            "SELECT 1 FROM register_logs WHERE chat_id = ? LIMIT 1", (chat_id,)
        ).fetchone()
    return row is not None


def register_user(chat_id: int, tier: str = "free", days: int = 0) -> int:
    """Đăng ký user mới. Trả expiry_ts (epoch giây). 0 = không hết hạn."""
    now = int(time.time())
    expiry = now + days * 86400 if days > 0 else 0
    with db() as c:
        c.execute("""
            INSERT INTO subscriptions (chat_id, tier, expiry_ts, registered_ts, last_renew_ts)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                tier = excluded.tier,
                expiry_ts = excluded.expiry_ts,
                last_renew_ts = excluded.last_renew_ts
        """, (chat_id, tier, expiry, now, now if tier != "free" else 0))
        c.execute("INSERT INTO register_logs (chat_id, tier, days, ts) VALUES (?, ?, ?, ?)",
                  (chat_id, tier, days, now))
    return expiry


def get_subscription(chat_id: int) -> dict | None:
    """Lấy thông tin subscription. Trả None nếu chưa đăng ký."""
    with db() as c:
        row = c.execute(
            "SELECT chat_id, tier, expiry_ts, registered_ts, last_renew_ts, notes "
            "FROM subscriptions WHERE chat_id = ?", (chat_id,)
        ).fetchone()
    if not row:
        return None
    return dict(row)


# Backward-compat alias. Code mới nên dùng get_tier() thay vì get_active_tier().
get_active_tier = get_tier


def renew_subscription(chat_id: int, tier: str, days: int) -> int:
    """Gia hạn thêm `days` ngày cho user (cộng dồn nếu còn hạn).

    Trả expiry_ts mới.
    """
    sub = get_subscription(chat_id)
    now = int(time.time())
    if not sub:
        # Chưa đăng ký → tự đăng ký
        return register_user(chat_id, tier=tier, days=days)

    current_expiry = sub.get("expiry_ts", 0) or 0
    # Nếu còn hạn → cộng dồn, nếu đã hết → tính từ bây giờ
    base = max(current_expiry, now)
    new_expiry = base + days * 86400
    with db() as c:
        c.execute("""
            UPDATE subscriptions
            SET tier = ?, expiry_ts = ?, last_renew_ts = ?
            WHERE chat_id = ?
        """, (tier, new_expiry, now, chat_id))
    return new_expiry


def expire_user_now(chat_id: int) -> bool:
    """Hạ user về free ngay lập tức (admin dùng)."""
    with db() as c:
        cur = c.execute("UPDATE subscriptions SET tier = 'free', expiry_ts = 0 WHERE chat_id = ?",
                        (chat_id,))
    return cur.rowcount > 0


def reset_user(chat_id: int) -> bool:
    """Xoá hoàn toàn dữ liệu subscription của user + kv cũ.

    Dùng khi user bị lỗi (tier sai, hết hạn sai, ...).
    Admin gọi /reset <chat_id> → user đó có thể /register lại từ đầu.
    """
    with db() as c:
        c.execute("DELETE FROM subscriptions WHERE chat_id = ?", (chat_id,))
    kv_delete(f"user_tier:{chat_id}")
    kv_delete(f"user_tier_expiry:{chat_id}")
    return True


def list_users(tier: str | None = None, expiring_within_days: int = 0) -> list[dict]:
    """Danh sách user, lọc theo tier và/hoặc còn hạn dưới N ngày.

    Args:
        tier: 'free' | 'pro' | None = tất cả
        expiring_within_days: 0 = không lọc; >0 = còn hạn dưới N ngày (gồm đã hết hạn)
    """
    sql = "SELECT chat_id, tier, expiry_ts, registered_ts, last_renew_ts, notes FROM subscriptions"
    args = []
    conditions = []
    if tier:
        conditions.append("tier = ?")
        args.append(tier)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY expiry_ts ASC"

    with db() as c:
        rows = c.execute(sql, args).fetchall()
    users = [dict(r) for r in rows]

    if expiring_within_days > 0:
        now = int(time.time())
        threshold = now + expiring_within_days * 86400
        users = [u for u in users if u["expiry_ts"] == 0 or u["expiry_ts"] <= threshold]

    return users


def count_users_by_tier() -> dict:
    """Đếm user theo tier (dựa trên tier hiệu lực, đã trừ user hết hạn)."""
    with db() as c:
        rows = c.execute("SELECT tier, COUNT(*) as n FROM subscriptions GROUP BY tier").fetchall()
    counts = {"free": 0, "pro": 0}
    for r in rows:
        if r["tier"] in counts:
            counts[r["tier"]] = r["n"]
    return counts


# ── Mã kích hoạt (redeem codes) ──────────────────────────
import secrets
import string


def _make_code(length: int = 8, prefix: str = "XK") -> str:
    """Tạo mã dạng 'XK-AB12CD3E' (prefix-8 ký tự chữ+ số)."""
    alphabet = string.ascii_uppercase + string.digits
    # Loại bỏ ký tự dễ nhầm: 0/O, 1/I/L
    alphabet = alphabet.translate(str.maketrans("", "", "O0I1L"))
    body = "".join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}-{body}"


def create_code(tier: str, days: int, created_by: int = 0) -> str:
    """Tạo 1 mã mới. Trả mã."""
    code = _make_code()
    now = int(time.time())
    with db() as c:
        c.execute("""
            INSERT INTO redeem_codes (code, tier, days, used_by, used_at, created_at, created_by)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (code, tier, days, now, created_by))
    return code


def create_codes_bulk(tier: str, days: int, count: int, created_by: int = 0) -> list[str]:
    """Tạo nhiều mã một lúc. Trả list mã."""
    return [create_code(tier, days, created_by) for _ in range(count)]


def get_code(code: str) -> dict | None:
    """Tra cứu mã (không phân biệt hoa/thường)."""
    code = code.strip().upper()
    with db() as c:
        row = c.execute(
            "SELECT * FROM redeem_codes WHERE code = ?", (code,)
        ).fetchone()
    return dict(row) if row else None


def redeem_code(chat_id: int, code: str) -> tuple[bool, str, dict]:
    """Nạp mã cho user. Trả (success, message, code_info).

    Atomic: nếu mã đã dùng → fail, không gia hạn.
    """
    code_info = get_code(code)
    if not code_info:
        return False, "Mã không tồn tại.", {}

    if code_info["used_by"] != 0:
        return False, "Mã đã được sử dụng.", code_info

    # Đánh dấu đã dùng + gia hạn (cùng 1 transaction — tránh lock)
    now = int(time.time())
    tier = code_info["tier"]
    days = code_info["days"]
    with db() as c:
        # Đánh dấu mã đã dùng (atomic — kiểm tra lại trong transaction)
        cur = c.execute("""
            UPDATE redeem_codes
            SET used_by = ?, used_at = ?
            WHERE code = ? AND used_by = 0
        """, (chat_id, now, code_info["code"]))
        if cur.rowcount == 0:
            return False, "Mã đã được sử dụng (race).", code_info

        # Gia hạn trong cùng transaction (không gọi hàm mở db mới)
        sub = c.execute(
            "SELECT expiry_ts FROM subscriptions WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        if sub is None:
            # Chưa đăng ký → tự đăng ký với gói của mã
            c.execute("""
                INSERT INTO subscriptions (chat_id, tier, expiry_ts, registered_ts, last_renew_ts)
                VALUES (?, ?, ?, ?, ?)
            """, (chat_id, tier, now + days * 86400, now, now))
            new_expiry = now + days * 86400
        else:
            current_expiry = sub["expiry_ts"] or 0
            base = max(current_expiry, now)
            new_expiry = base + days * 86400
            c.execute("""
                UPDATE subscriptions
                SET tier = ?, expiry_ts = ?, last_renew_ts = ?
                WHERE chat_id = ?
            """, (tier, new_expiry, now, chat_id))

        c.execute("INSERT INTO register_logs (chat_id, tier, days, ts) VALUES (?, ?, ?, ?)",
                  (chat_id, tier, days, now))

    return True, f"Nạp mã thành công: {tier} {days} ngày.", {
        **code_info, "new_expiry": new_expiry
    }


def list_codes(unused_only: bool = False, limit: int = 50) -> list[dict]:
    """Liệt kê mã (cho admin)."""
    sql = "SELECT * FROM redeem_codes"
    if unused_only:
        sql += " WHERE used_by = 0"
    sql += " ORDER BY created_at DESC LIMIT ?"
    with db() as c:
        rows = c.execute(sql, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_user_codes(chat_id: int, limit: int = 5) -> list[dict]:
    """Lấy danh sách mã user này đã dùng (mới nhất trước)."""
    with db() as c:
        rows = c.execute(
            "SELECT code, tier, days, used_at FROM redeem_codes "
            "WHERE used_by = ? ORDER BY used_at DESC LIMIT ?",
            (chat_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]

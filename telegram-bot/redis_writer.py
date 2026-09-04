"""
redis_writer.py — Ghi pulse data từ bot lên Upstash Redis (chia sẻ với Web).

Mục đích: Web dashboard (/goldpulse) đọc pulse từ Redis. Thay vì đợi MT5 EA
(như thiết kế cũ), bot Python có thể tự ghi pulse lên Redis mỗi khi có tín hiệu.

Schema ở Web (src/lib/pulse-store.ts):
  PulseSnapshot = {
    symbol, time, price, bias, score, volatility,
    entry: { high, low, gain },
    exit, exitSignal?, signalAge?, htf,
    multiTf: { m15, m30, h1 },
    indicators: { rsi, atr, emaGap, adx, vwap, spread }
  }

Tên key Redis: 'tnv:current_pulse' (giống Web dùng)
TTL: 60 giây (giống Web đặt)
"""

import json
import logging
import os
import time
from typing import Any, Optional

import requests

log = logging.getLogger("redis_writer")

# Load .env ở local (VPS Windows CMD dùng `set` thủ công cũng OK)
try:
    from dotenv import load_dotenv
    load_dotenv()  # tự tìm .env cạnh main.py
except ImportError:
    pass  # production không cần python-dotenv

# Cấu hình — đọc từ environment (file .env ở local, hoặc `set` trong CMD)
UPSTASH_URL = os.environ.get("KV_REST_API_URL", "").rstrip("/")
UPSTASH_TOKEN = os.environ.get("KV_REST_API_TOKEN", "")

# Key & TTL — phải khớp với web/src/lib/pulse-store.ts
REDIS_KEY = "tnv:current_pulse"
REDIS_TTL_SECONDS = 60  # giống web đặt


def _redis_set(key: str, value: dict, ttl: int = REDIS_TTL_SECONDS) -> bool:
    """Ghi 1 key vào Upstash Redis qua REST API."""
    if not UPSTASH_URL or not UPSTASH_TOKEN:
        log.warning("redis_writer: missing KV_REST_API_URL or KV_REST_API_TOKEN")
        return False
    try:
        url = f"{UPSTASH_URL}/set/{key}"
        params = {"EX": ttl}
        # Upstash REST API nhận value là string (JSON)
        r = requests.post(
            url,
            params=params,
            headers={
                "Authorization": f"Bearer {UPSTASH_TOKEN}",
                "Content-Type": "application/json",
            },
            data=json.dumps(value),
            timeout=10,
        )
        if r.status_code != 200:
            log.warning("redis_writer: set failed status=%s body=%s", r.status_code, r.text[:200])
            return False
        return True
    except Exception as e:
        log.warning("redis_writer: set exception: %s", e)
        return False


def write_pulse(
    price: float,
    bias: str,           # "LONG" | "SHORT" | "NEUTRAL"
    score: float,
    volatility: Optional[float] = None,   # ATR
    exit_price: Optional[float] = None,   # TP target
    rsi: Optional[float] = None,
    ema_gap: Optional[float] = None,
) -> bool:
    """
    Ghi pulse snapshot lên Redis. Bot gọi hàm này mỗi khi có tín hiệu mới
    (mỗi 5 phút từ scheduler_loop).

    Tất cả các trường optional đều có default 0/an toàn nếu không có.
    """
    if price is None or price <= 0:
        log.debug("redis_writer: skip write — price invalid (%s)", price)
        return False

    snapshot = {
        "symbol": "XAUUSD",
        "time": time.strftime("%H:%M:%S"),
        "price": float(price),
        "bias": bias if bias in ("LONG", "SHORT", "NEUTRAL") else "NEUTRAL",
        "score": float(score) if score is not None else 0.0,
        "volatility": float(volatility) if volatility is not None else 0.0,
        "entry": {
            "high": float(exit_price) if exit_price else float(price),
            "low": float(price),
            "gain": 0.0,
        },
        "exit": float(exit_price) if exit_price else float(price),
        "htf": bias,
        "multiTf": {
            "m15": {"bias": bias, "score": float(score) if score else 0},
            "m30": {"bias": bias, "score": float(score) if score else 0},
            "h1": {"bias": bias, "score": float(score) if score else 0},
        },
        "indicators": {
            "rsi": float(rsi) if rsi is not None else 50.0,
            "atr": float(volatility) if volatility is not None else 0.0,
            "emaGap": float(ema_gap) if ema_gap is not None else 0.0,
            "adx": 0.0,
            "vwap": 0.0,
            "spread": 0.0,
        },
    }

    ok = _redis_set(REDIS_KEY, snapshot)
    if ok:
        log.info(
            "✅ pulse → Redis: bias=%s price=%.2f score=%.1f",
            bias, price, score,
        )
    return ok

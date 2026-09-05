"""
redis_writer.py — Ghi pulse data từ bot lên Upstash Redis (chia sẻ với Web).

Mục đích: Web dashboard (/goldpulse) đọc pulse từ Redis. Thay vì đợi MT5 EA
(như thiết kế cũ), bot Python có thể tự ghi pulse lên Redis mỗi khi có tín hiệu.

Schema ở Web (src/lib/pulse-store.ts):
  PulseSnapshot = {
    symbol, time, price, bias, score, volatility,
    entry: { price, gain },   // entry price breakout (chỉ có khi LONG/SHORT)
    sl, tp,                    // SL = entry ∓ 1.5N, TP = entry ± 2.0N (TNV logic)
    htf, multiTf, indicators
  }

TNVGold logic (Donchian 20/10 + N-value):
  Entry: e_high / e_low (Donchian 20 nến)
  SL:    entry ∓ 1.5 × N
  TP:    entry ± 2.0 × N (CHỈ 1 TP, không có TP1/TP2/TP3)
  N:     n_value (volatility thật của TNV)

Khi bias = NEUTRAL: entry/sl/tp = null
Khi bias = LONG/SHORT: có đủ 3 giá trị từ signal

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
    volatility: Optional[float] = None,   # N-value (ATR 20 của TNV, dùng cho SL/TP)
    entry_price: Optional[float] = None,   # Donchian breakout price
    sl_price: Optional[float] = None,      # SL = entry ∓ 1.5N
    tp_price: Optional[float] = None,      # TP = entry ± 2.0N (CHỈ 1 TP)
    rsi: Optional[float] = None,
    ema_gap: Optional[float] = None,
    adx: Optional[float] = None,
    vwap: Optional[float] = None,
    spread: Optional[float] = None,
    atr_14: Optional[float] = None,        # ATR 14 (chuẩn, tách riêng)
    range_low: Optional[float] = None,     # Donchian low 20 (kênh dưới) — dùng khi NEUTRAL
    range_high: Optional[float] = None,    # Donchian high 20 (kênh trên) — dùng khi NEUTRAL
) -> bool:
    """
    Ghi pulse snapshot lên Redis. Bot gọi hàm này mỗi khi có tín hiệu mới
    (mỗi 5 phút từ scheduler_loop).

    TNVGold logic:
      Entry: Donchian 20 nến (e_high/e_low từ tnv_engine)
      SL:    entry ∓ 1.5 × N (1.5 lần N-value)
      TP:    entry ± 2.0 × N (2.0 lần N-value, CHỈ 1 TP)

    Khi bias = NEUTRAL: entry/sl/tp = None (không có tín hiệu)
    Khi bias = LONG/SHORT: truyền đủ 3 giá trị entry/sl/tp
    """
    if price is None or price <= 0:
        log.debug("redis_writer: skip write — price invalid (%s)", price)
        return False

    # Tính gain: (current_price - entry_price) / entry_price * 100
    gain = 0.0
    if entry_price and entry_price > 0:
        gain = round(((price - entry_price) / entry_price) * 100, 2)

    snapshot = {
        "symbol": "XAUUSD",
        "time": time.strftime("%H:%M:%S"),
        "price": float(price),
        "bias": bias if bias in ("LONG", "SHORT", "NEUTRAL") else "NEUTRAL",
        "score": float(score) if score is not None else 0.0,
        "volatility": float(volatility) if volatility is not None else 0.0,
        # ENTRY — chỉ có giá trị khi LONG/SHORT
        "entry": {
            "price": float(entry_price) if entry_price else None,
            "gain": gain if entry_price else None,
        },
        # SL + TP — TNV logic 1.5N/2.0N, chỉ 1 TP duy nhất
        "sl": float(sl_price) if sl_price else None,
        "tp": float(tp_price) if tp_price else None,
        "htf": bias,
        "multiTf": {
            "m15": {"bias": bias, "score": float(score) if score else 0},
            "m30": {"bias": bias, "score": float(score) if score else 0},
            "h1": {"bias": bias, "score": float(score) if score else 0},
        },
        "indicators": {
            "rsi": float(rsi) if rsi is not None else 50.0,
            # atr = ATR 14 (tách riêng khỏi volatility/N)
            "atr": float(atr_14) if atr_14 is not None else 0.0,
            "emaGap": float(ema_gap) if ema_gap is not None else 0.0,
            "adx": float(adx) if adx is not None else 0.0,
            "vwap": float(vwap) if vwap is not None else 0.0,
            "spread": float(spread) if spread is not None else 0.0,
        },
    }

    ok = _redis_set(REDIS_KEY, snapshot)
    if ok:
        log.info(
            "✅ pulse → Redis: bias=%s price=%.2f score=%.1f",
            bias, price, score,
        )
    return ok

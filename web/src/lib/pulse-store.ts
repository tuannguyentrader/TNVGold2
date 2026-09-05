import { Redis } from "@upstash/redis";

// Hỗ trợ cả Vercel KV env và Upstash Redis env
const redisUrl =
  process.env.KV_REST_API_URL ||
  process.env.UPSTASH_REDIS_REST_URL;
const redisToken =
  process.env.KV_REST_API_TOKEN ||
  process.env.UPSTASH_REDIS_REST_TOKEN;

const redis = redisUrl && redisToken
  ? new Redis({ url: redisUrl, token: redisToken })
  : null;

export interface MultiTfData {
  bias: "LONG" | "SHORT" | "NEUTRAL";
  score: number;
  high: number;
  low: number;
  exit: number;
  htf: string;
  volatility: number;
}

export interface TechnicalIndicators {
  rsi: number;
  atr: number;
  emaGap: number;
  adx: number;
  vwap: number;
  spread: number;
}

export interface PulseSnapshot {
  symbol: string;
  time: string;
  price: number;
  bias: "LONG" | "SHORT" | "NEUTRAL";
  score: number;
  volatility: number;       // N-value (TNV volatility)
  // ENTRY: chỉ có khi bias = LONG/SHORT (null khi NEUTRAL)
  entry: {
    price: number | null;   // Donchian 20 breakout price
    gain: number | null;     // % thay đổi từ entry đến hiện tại
  };
  // SL + TP theo logic TNVGold: SL = entry ∓ 1.5N, TP = entry ± 2.0N
  // CHỈ 1 TP duy nhất (không có TP1/TP2/TP3)
  sl: number | null;
  tp: number | null;
  // Range Donchian 20 (hiển thị ở EXIT card khi NEUTRAL)
  rangeLow: number | null;
  rangeHigh: number | null;
  exitSignal?: boolean;
  signalAge?: number;
  htf: string;
  multiTf: {
    m15: MultiTfData;
    m30: MultiTfData;
    h1: MultiTfData;
  };
  indicators: TechnicalIndicators;
  analysisText?: {
    en: string;
    vi: string;
  };
}

const KV_KEY_PULSE = "tnv:current_pulse";
const KV_KEY_HISTORY = "tnv:pulse_history";

// Initial neutral state (no demo data)
const defaultSnapshot: PulseSnapshot = {
  symbol: "XAUUSD",
  time: "—",
  price: 0,
  bias: "NEUTRAL",
  score: 0,
  volatility: 0,
  entry: {
    price: null,
    gain: null,
  },
  sl: null,
  tp: null,
  rangeLow: null,
  rangeHigh: null,
  exitSignal: false,
  signalAge: 0,
  htf: "—",
  multiTf: {
    m15: { bias: "NEUTRAL", score: 0, high: 0, low: 0, exit: 0, htf: "—", volatility: 0 },
    m30: { bias: "NEUTRAL", score: 0, high: 0, low: 0, exit: 0, htf: "—", volatility: 0 },
    h1:  { bias: "NEUTRAL", score: 0, high: 0, low: 0, exit: 0, htf: "—", volatility: 0 },
  },
  indicators: {
    rsi: 0,
    atr: 0,
    emaGap: 0,
    adx: 0,
    vwap: 0,
    spread: 0,
  },
};

// Fallback in-memory cache for when KV is not available (local dev)
let localCache: PulseSnapshot | null = null;
let localHistoryCache: PulseSnapshot[] | null = null;

// Đảm bảo snapshot đọc từ Redis luôn có đủ field mới (rangeLow/rangeHigh)
// — data cũ ghi trước khi có field này sẽ được tính fallback từ price ± volatility
function normalizeSnapshot(raw: PulseSnapshot): PulseSnapshot {
  const price = raw?.price ?? 0;
  const vol = raw?.volatility ?? 0;
  return {
    ...raw,
    rangeLow: raw?.rangeLow ?? (price > 0 && vol > 0 ? Number((price - vol).toFixed(2)) : null),
    rangeHigh: raw?.rangeHigh ?? (price > 0 && vol > 0 ? Number((price + vol).toFixed(2)) : null),
  };
}

export async function getLatestPulse(): Promise<PulseSnapshot> {
  try {
    if (!redis) return localCache ? normalizeSnapshot(localCache) : defaultSnapshot;
    const data = await redis.get<PulseSnapshot>(KV_KEY_PULSE);
    if (data) {
      localCache = data;
      return normalizeSnapshot(data);
    }
  } catch {
    // fallback
  }
  return localCache ? normalizeSnapshot(localCache) : defaultSnapshot;
}

export async function getPulseHistory(limit: number = 10): Promise<PulseSnapshot[]> {
  try {
    if (!redis) return localHistoryCache || [];
    const data = await redis.get<PulseSnapshot[]>(KV_KEY_HISTORY);
    if (data && Array.isArray(data)) {
      localHistoryCache = data;
      return data.slice(0, limit);
    }
  } catch {
    // fallback
  }
  return localHistoryCache?.slice(0, limit) || [];
}

// Helper chống trùng/idempotency: hai snapshot là cùng một lần ghi nếu cùng thời điểm,
// cùng giá và cùng bias/score. Một nến M5 đóng hoặc một lần POST lặp sẽ không tạo bản ghi mới.
function isDuplicateSnapshot(a: PulseSnapshot, b: PulseSnapshot): boolean {
  return (
    a.time === b.time &&
    a.price === b.price &&
    a.bias === b.bias &&
    a.score === b.score
  );
}

export async function updatePulse(newSnapshot: PulseSnapshot): Promise<void> {
  // Validate: reject invalid snapshots
  if (typeof newSnapshot.price !== "number" || newSnapshot.price <= 0) {
    return; // ignore invalid price
  }
  if (!newSnapshot.symbol) {
    return; // require symbol
  }

  const snapshot: PulseSnapshot = {
    ...newSnapshot,
    time: newSnapshot.time || new Date().toLocaleTimeString("en-GB", { hour12: false }),
  };

  localCache = snapshot;

  try {
    if (redis) {
      // Save current pulse (TTL 60s — tránh stale data nếu EA ngừng gửi)
      await redis.set(KV_KEY_PULSE, snapshot, { ex: 60 });

      // Update history (idempotent: không ghi snapshot trùng với bản mới nhất)
      const history = (await redis.get<PulseSnapshot[]>(KV_KEY_HISTORY)) || [];
      if (history.length === 0 || !isDuplicateSnapshot(history[0], snapshot)) {
        history.unshift(snapshot);
      }
      const trimmed = history.slice(0, 15);
      localHistoryCache = trimmed;
      // History giữ 7 ngày
      await redis.set(KV_KEY_HISTORY, trimmed, { ex: 7 * 24 * 60 * 60 });
    } else {
      // Local fallback
      if (!localHistoryCache) localHistoryCache = [];
      if (localHistoryCache.length === 0 || !isDuplicateSnapshot(localHistoryCache[0], snapshot)) {
        localHistoryCache.unshift(snapshot);
      }
      if (localHistoryCache.length > 15) {
        localHistoryCache = localHistoryCache.slice(0, 15);
      }
    }
  } catch {
    // ignore
  }
}

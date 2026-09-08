"use client";

import React, { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import type { PulseSnapshot } from "./pulse-store";

interface LivePulseContextType {
  pulse: PulseSnapshot;
  history: PulseSnapshot[];
  isLiveConnected: boolean;
  lastUpdated: string;
}

// Dữ liệu mặc định trung tính, không còn demo
const defaultSnapshot: PulseSnapshot = {
  symbol: "XAUUSD",
  time: "—",
  price: 0,
  bias: "NEUTRAL",
  score: 0,
  volatility: 0,
  entry: { price: null, gain: null },
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
  indicators: { rsi: 0, atr: 0, emaGap: 0, adx: 0, vwap: 0, spread: 0 },
};

const LivePulseContext = createContext<LivePulseContextType>({
  pulse: defaultSnapshot,
  history: [defaultSnapshot],
  isLiveConnected: false,
  lastUpdated: "—",
});

const CACHE_KEY = "tnv_pulse_cache";
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 phút

interface CachedPulse {
  pulse: PulseSnapshot;
  history: PulseSnapshot[];
  isLiveConnected: boolean;
  lastUpdated: string;
  cachedAt: number;  // timestamp
}

/**
 * Load cache từ localStorage.
 * Trả về null nếu:
 *   - Không có cache
 *   - Cache quá cũ (> 5 phút)
 *   - Cache chứa data rỗng (price = 0) — bỏ qua, hiển thị default
 */
function loadCache(): CachedPulse | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const cache = JSON.parse(raw) as CachedPulse;
    // Bỏ qua cache quá cũ
    if (Date.now() - cache.cachedAt > CACHE_TTL_MS) return null;
    // Bỏ qua cache rỗng (price=0) — tránh hiển thị '0' nhảy giữa chừng
    if (!cache.pulse || cache.pulse.price <= 0) return null;
    return cache;
  } catch {
    return null;
  }
}

function saveCache(data: CachedPulse) {
  if (typeof window === "undefined") return;
  // Chỉ lưu cache khi có data thật (price > 0)
  if (!data.pulse || data.pulse.price <= 0) return;
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(data));
  } catch {
    // localStorage có thể đầy hoặc bị chặn — bỏ qua
  }
}

interface LivePulseProviderProps {
  children: ReactNode;
  initialPulse?: PulseSnapshot;    // từ server (SSR)
  initialHistory?: PulseSnapshot[]; // từ server (SSR)
}

export function LivePulseProvider({
  children,
  initialPulse,
  initialHistory,
}: LivePulseProviderProps) {
  // Thứ tự ưu tiên:
  //   1. localStorage cache (nếu có data thật, còn TTL)
  //   2. SSR initial data từ server (nếu có data thật)
  //   3. defaultSnapshot (rỗng)
  const getInitialPulse = (): PulseSnapshot => {
    const cache = loadCache();
    if (cache?.pulse) return cache.pulse;
    if (initialPulse && initialPulse.price > 0) return initialPulse;
    return defaultSnapshot;
  };
  const getInitialHistory = (): PulseSnapshot[] => {
    const cache = loadCache();
    if (cache?.history) return cache.history;
    if (initialHistory && initialHistory.length > 0) return initialHistory;
    return [defaultSnapshot];
  };
  const getInitialConnected = (): boolean => {
    const cache = loadCache();
    if (cache) return cache.isLiveConnected;
    return getInitialPulse().price > 0;
  };
  const getInitialLastUpdated = (): string => {
    const cache = loadCache();
    if (cache) return cache.lastUpdated;
    return getInitialPulse().price > 0 ? getInitialPulse().time : "—";
  };

  const [pulse, setPulse] = useState<PulseSnapshot>(getInitialPulse);
  const [history, setHistory] = useState<PulseSnapshot[]>(getInitialHistory);
  const [isLiveConnected, setIsLiveConnected] = useState<boolean>(getInitialConnected);
  const [lastUpdated, setLastUpdated] = useState<string>(getInitialLastUpdated);

  const fetchLivePulse = async () => {
    try {
      const res = await fetch("/api/pulse", { cache: "no-store" });
      if (res.ok) {
        const json = await res.json();
        if (json.success && json.data) {
          const newPulse = json.data;
          const newConnected = newPulse.price > 0;
          const newLastUpdated = new Date().toLocaleTimeString("en-GB", { hour12: false });

          // Redis hết TTL (price=0, giữa 2 lần bot ghi): KHÔNG ghi đè pulse/history
          // (tránh "data hiện → bị xóa → trống" mỗi 10s) NHƯNG phải hạ cờ LIVE —
          // bot đang không ghi, badge "Live" là sai lệch với sản phẩm tín hiệu.
          if (newPulse.price <= 0) {
            setIsLiveConnected(false);
            return;
          }

          // Merge history: /api/pulse chỉ trả 25 bản gần nhất (payload nhẹ),
          // SSR đã load đầy đủ 500 bản. Gộp: bản mới từ API + phần cũ của prev
          // mà API không có (so theo time+price+bias), giữ tối đa 500.
          const apiHistory: PulseSnapshot[] = Array.isArray(json.history)
            ? json.history
            : [];
          setHistory((prev) => {
            if (apiHistory.length === 0) return prev;
            const seen = new Set(
              apiHistory.map((r) => `${r.time}|${r.price}|${r.bias}`)
            );
            const older = prev.filter(
              (r) => !seen.has(`${r.time}|${r.price}|${r.bias}`)
            );
            return [...apiHistory, ...older].slice(0, 500);
          });
          setIsLiveConnected(newConnected);
          setLastUpdated(newLastUpdated);

          // Lưu cache để lần load sau hiển thị ngay (chỉ giữ 50 bản cache)
          setHistory((merged) => {
            saveCache({
              pulse: newPulse,
              history: merged.slice(0, 50),
              isLiveConnected: newConnected,
              lastUpdated: newLastUpdated,
              cachedAt: Date.now(),
            });
            return merged;
          });
        }
      }
    } catch {
      // Fetch fail (mạng/API lỗi) — hạ cờ LIVE vì không xác nhận được data mới
      setIsLiveConnected(false);
    }
  };

  // Fetch ngay khi mount, polling 10 giây
  useEffect(() => {
    fetchLivePulse();
    const interval = setInterval(fetchLivePulse, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <LivePulseContext.Provider value={{ pulse, history, isLiveConnected, lastUpdated }}>
      {children}
    </LivePulseContext.Provider>
  );
}

export function useLivePulse() {
  return useContext(LivePulseContext);
}

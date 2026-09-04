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
  entry: { high: 0, low: 0, gain: 0 },
  exit: 0,
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

export function LivePulseProvider({ children }: { children: ReactNode }) {
  const [pulse, setPulse] = useState<PulseSnapshot>(defaultSnapshot);
  const [history, setHistory] = useState<PulseSnapshot[]>([defaultSnapshot]);
  const [isLiveConnected, setIsLiveConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState("—");

  const fetchLivePulse = async () => {
    try {
      const res = await fetch("/api/pulse", { cache: "no-store" });
      if (res.ok) {
        const json = await res.json();
        // Luôn update state khi API trả success — dù price=0 hay >0
        // Logic cũ: skip khi price=0 → gây stuck "—" vĩnh viễn
        if (json.success && json.data) {
          setPulse(json.data);
          if (Array.isArray(json.history) && json.history.length > 0) {
            setHistory(json.history);
          }
          // isLiveConnected: true khi có data thật (price > 0)
          setIsLiveConnected(json.data.price > 0);
          setLastUpdated(new Date().toLocaleTimeString("en-GB", { hour12: false }));
        }
      }
    } catch {
      // Fallback — giữ state cũ
    }
  };

  // Fetch ngay lập tức khi mount, sau đó polling 10 giây
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

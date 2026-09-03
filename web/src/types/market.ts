export type MarketBias = "BULLISH" | "BEARISH" | "NEUTRAL";
export type ActionState = "WAITING" | "LONG_READY" | "SHORT_READY" | "BLOCKED";
export type SessionName = "Tokyo" | "London" | "New York" | "Sydney";

export interface TimeframeValue {
  tf: "15m" | "1h" | "4h" | "1D";
  value: string;
  bias?: MarketBias;
}

export interface MetricCardData {
  label: string;
  value: string;
  badge?: string;
  footer?: string;
  tooltip: string;
  flipRows?: TimeframeValue[];
}

export interface HistoryRecord {
  time: string;
  price: string;
  pulse: number;
  bias: MarketBias;
  confidence: number;
  readiness: string;
  adx: number;
  volatility: string;
}

export interface ChartDataPoint {
  time: string;
  timestamp: number;
  price: number;
  pulse: number;
  session: SessionName;
  open: number;
  high: number;
  low: number;
  close: number;
  ema9: number;
  ema21: number;
}

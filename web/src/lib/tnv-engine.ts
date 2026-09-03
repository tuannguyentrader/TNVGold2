/**
 * TNV Engine (v3.26)
 * Quantitative Signal & Breakout Quality Calculation Engine
 * Multi-Timeframe Matrix: M5 (Primary) • M15 • M30 • H1
 */

export type TNVSystemType = "SYSTEM_1" | "SYSTEM_2" | "BOTH";
export type TNVSignalType = "S1_LONG" | "S1_SHORT" | "S1_EXIT_L" | "S1_EXIT_S" | "S2_LONG" | "S2_SHORT" | "IN_CHANNEL";

export interface Candle {
  time: string;
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface TNVScoreBreakdown {
  score: number; // 0 - 10
  passedMandatory: boolean;
  bodyRatio: number;
  isCloseInThird: boolean;
  range: number;
  rangeToN: number;
  htfStatus: "BULLISH" | "BEARISH" | "NEUTRAL";
  isHTFNotAgainst: boolean;
  bonusRange: number;
  bonusHTF: number;
  bonusN: number;
}

export interface TimeframeSignalState {
  tf: "M5" | "M15" | "M30" | "H1";
  signal: TNVSignalType;
  signalLabel: string;
  badgeType: "up" | "down" | "neutral";
  price: number;
  volatility: number;
  score: number;
  high: number;
  low: number;
  exitHigh: number;
  exitLow: number;
}

/**
 * Compute Wilder's Volatility on 20 bars
 */
export function computeWilderVolatility(candles: Candle[], period = 20): number {
  if (candles.length < period + 2) return 0;
  
  const trs: number[] = [];
  for (let i = 1; i < candles.length; i++) {
    const high = candles[i].high;
    const low = candles[i].low;
    const prevClose = candles[i - 1].close;
    const tr = Math.max(high - low, Math.abs(high - prevClose), Math.abs(low - prevClose));
    trs.push(tr);
  }

  // Initial seed
  let seed = 0;
  for (let i = 0; i < period; i++) {
    seed += trs[i];
  }
  seed /= period;

  let n = seed;
  for (let i = period; i < trs.length; i++) {
    n = (n * (period - 1) + trs[i]) / period;
  }

  return Number(n.toFixed(2));
}

/**
 * Get Highest High in the last `period` bars (excluding current bar)
 */
export function getHighest(candles: Candle[], period: number, offset = 1): number {
  if (candles.length < offset + period) return 0;
  const slice = candles.slice(candles.length - offset - period, candles.length - offset);
  return Math.max(...slice.map((c) => c.high));
}

/**
 * Get Lowest Low in the last `period` bars (excluding current bar)
 */
export function getLowest(candles: Candle[], period: number, offset = 1): number {
  if (candles.length < offset + period) return 0;
  const slice = candles.slice(candles.length - offset - period, candles.length - offset);
  return Math.min(...slice.map((c) => c.low));
}

/**
 * Check if Higher Timeframe (M15, M30, H1) is NOT clearly against direction
 */
export function isHTFNotAgainst(isLong: boolean, htfCandles: Candle[]): boolean {
  if (htfCandles.length < 5) return true;

  const last4 = htfCandles.slice(-4);
  let lowerHighs = 0;
  let lowerLows = 0;
  let higherHighs = 0;
  let higherLows = 0;

  for (let i = 1; i < last4.length; i++) {
    if (last4[i].high < last4[i - 1].high) lowerHighs++;
    if (last4[i].low < last4[i - 1].low) lowerLows++;
    if (last4[i].high > last4[i - 1].high) higherHighs++;
    if (last4[i].low > last4[i - 1].low) higherLows++;
  }

  if (isLong) {
    if (lowerHighs >= 2 && lowerLows >= 2) return false;
    return true;
  } else {
    if (higherHighs >= 2 && higherLows >= 2) return false;
    return true;
  }
}

/**
 * Calculate Quality Score for a Signal Candle (0 - 10)
 */
export function calculateQualityScore(
  isLong: boolean,
  candle: Candle,
  volatility: number,
  htfCandles: Candle[],
  options = {
    minBodyRatio: 0.5,
    requireCloseThird: true,
    rangeMult: 0.7,
    bonusRange: 2,
    bonusHTF: 2,
    bonusN: 1,
  }
): TNVScoreBreakdown {
  const range = candle.high - candle.low;
  if (range <= 0 || volatility <= 0) {
    return {
      score: 0,
      passedMandatory: false,
      bodyRatio: 0,
      isCloseInThird: false,
      range: 0,
      rangeToN: 0,
      htfStatus: "NEUTRAL",
      isHTFNotAgainst: false,
      bonusRange: 0,
      bonusHTF: 0,
      bonusN: 0,
    };
  }

  const body = Math.abs(candle.close - candle.open);
  const bodyRatio = body / range;

  // 1. Mandatory condition: Min Body Ratio >= 0.50
  if (bodyRatio < options.minBodyRatio) {
    return {
      score: 0,
      passedMandatory: false,
      bodyRatio,
      isCloseInThird: false,
      range,
      rangeToN: range / volatility,
      htfStatus: "NEUTRAL",
      isHTFNotAgainst: false,
      bonusRange: 0,
      bonusHTF: 0,
      bonusN: 0,
    };
  }

  // 2. Mandatory condition: Close in Top/Bottom 1/3
  const third = range / 3.0;
  let isCloseInThird = false;
  if (isLong) {
    isCloseInThird = candle.close >= candle.high - third;
  } else {
    isCloseInThird = candle.close <= candle.low + third;
  }

  if (options.requireCloseThird && !isCloseInThird) {
    return {
      score: 0,
      passedMandatory: false,
      bodyRatio,
      isCloseInThird: false,
      range,
      rangeToN: range / volatility,
      htfStatus: "NEUTRAL",
      isHTFNotAgainst: false,
      bonusRange: 0,
      bonusHTF: 0,
      bonusN: 0,
    };
  }

  // Base score after passing mandatory criteria
  let score = 5;
  let bonusRange = 0;
  let bonusHTF = 0;
  let bonusN = 0;

  // Bonus 1: Range >= 0.70 * Volatility
  if (range >= options.rangeMult * volatility) {
    bonusRange = options.bonusRange;
    score += bonusRange;
  }

  // Bonus 2: HTF Not Against
  const htfNotAgainst = isHTFNotAgainst(isLong, htfCandles);
  if (htfNotAgainst) {
    bonusHTF = options.bonusHTF;
    score += bonusHTF;
  }

  // Bonus 3: Good Volatility Level
  if (bodyRatio >= options.minBodyRatio && range >= options.rangeMult * 0.8 * volatility) {
    bonusN = options.bonusN;
    score += bonusN;
  }

  if (score > 10) score = 10;

  return {
    score,
    passedMandatory: true,
    bodyRatio,
    isCloseInThird,
    range,
    rangeToN: range / volatility,
    htfStatus: htfNotAgainst ? (isLong ? "BULLISH" : "BEARISH") : "NEUTRAL",
    isHTFNotAgainst: htfNotAgainst,
    bonusRange,
    bonusHTF,
    bonusN,
  };
}

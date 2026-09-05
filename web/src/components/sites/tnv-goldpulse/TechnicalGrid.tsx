"use client";

import { TechCard } from "./TechCard";
import { useLanguage } from "@/lib/language-context";
import { useLivePulse } from "@/lib/live-pulse-context";

export function TechnicalGrid() {
  const { t } = useLanguage();
  const { pulse } = useLivePulse();
  const ind = pulse.indicators;

  const rangeBar = (
    zones: { flex: number; className: string }[],
    needlePositionPercent: number
  ) => (
    <div className="relative w-full h-[5px] rounded-full bg-white/10 overflow-hidden mt-1.5">
      <div className="flex w-full h-full">
        {zones.map((z, i) => (
          <span key={i} className={z.className} style={{ flex: z.flex }} />
        ))}
      </div>
      <div
        className="absolute top-0 bottom-0 w-[2.5px] bg-white shadow-sm"
        style={{ left: `calc(${Math.min(100, Math.max(0, needlePositionPercent))}% - 1px)` }}
      />
    </div>
  );

  const rsiVal = ind.rsi.toFixed(1);
  const atrVal = `$${ind.atr.toFixed(2)}`;
  const emaGapVal = ind.emaGap >= 0 ? `+$${ind.emaGap.toFixed(2)}` : `-$${Math.abs(ind.emaGap).toFixed(2)}`;
  const adxVal = ind.adx.toFixed(1);
  const vwapVal = ind.vwap >= 0 ? `+$${ind.vwap.toFixed(2)}` : `-$${Math.abs(ind.vwap).toFixed(2)}`;
  const spreadVal = `${ind.spread.toFixed(1)} Pips`;

  // Note động theo data thật
  const rsiNote = ind.rsi >= 70
    ? "Overbought / Quá mua"
    : ind.rsi >= 50
    ? "Bullish Zone / Vùng tăng"
    : ind.rsi >= 30
    ? "Bearish Zone / Vùng giảm"
    : "Oversold / Quá bán";
  const atrNote = pulse.price > 0
    ? `${((ind.atr / pulse.price) * 100).toFixed(2)}% of Price / Giá trị`
    : "—";
  const emaGapNote = ind.emaGap > 0
    ? "Bullish Expansion / Mở rộng tăng"
    : ind.emaGap < 0
    ? "Bearish Expansion / Mở rộng giảm"
    : "Neutral / Trung lập";
  const adxNote = ind.adx >= 40
    ? "Strong Trend / Xu hướng mạnh"
    : ind.adx >= 20
    ? "Moderate Trend / Xu hướng vừa"
    : "Weak Trend / Xu hướng yếu";
  const vwapNote = ind.vwap > 0
    ? "Above VWAP / Trên VWAP"
    : ind.vwap < 0
    ? "Below VWAP / Dưới VWAP"
    : "At VWAP / Tại VWAP";
  const spreadNote = `${(ind.spread * 0.01).toFixed(2)} USD`;

  return (
    <section
      id="technical-grid"
      className="qx-tech-grid my-4 overflow-x-auto"
      aria-label={t.techTitle}
    >
      {/* 1. RSI (14) */}
      <TechCard
        label={t.rsiLabel}
        value={rsiVal}
        note={rsiNote}
        tooltip={t.rsiTooltip}
      >
        {rangeBar(
          [
            { flex: 30, className: "bg-[#ff8383]/40" },
            { flex: 40, className: "bg-white/20" },
            { flex: 30, className: "bg-[#61e294]/40" },
          ],
          ind.rsi
        )}
      </TechCard>

      {/* 2. ATR (14) */}
      <TechCard
        label={t.atrLabel}
        value={atrVal}
        note={atrNote}
        tooltip={t.atrTooltip}
      >
        <div className="w-full h-[4px] rounded-full bg-white/10 overflow-hidden mt-1.5">
          <div className="h-full bg-[#f5c542] rounded-full" style={{ width: `${Math.min(100, (ind.atr / 20) * 100)}%` }} />
        </div>
      </TechCard>

      {/* 3. EMA GAP (9/21) */}
      <TechCard
        label={t.emaGapLabel}
        value={
          <span className={ind.emaGap >= 0 ? "text-[#61e294] font-bold" : "text-[#ff8383] font-bold"}>
            {emaGapVal}
          </span>
        }
        note={emaGapNote}
        tooltip={t.emaGapTooltip}
      >
        <div className="w-full h-[4px] rounded-full bg-white/10 overflow-hidden mt-1.5">
          <div
            className={`h-full rounded-full ${ind.emaGap >= 0 ? "bg-[#61e294]" : "bg-[#ff8383]"}`}
            style={{ width: `${Math.min(100, Math.abs(ind.emaGap) * 15)}%` }}
          />
        </div>
      </TechCard>

      {/* 4. ADX (14) */}
      <TechCard
        label={t.adxLabel}
        value={adxVal}
        note={adxNote}
        tooltip={t.adxTooltip}
      >
        {rangeBar(
          [
            { flex: 25, className: "bg-white/10" },
            { flex: 25, className: "bg-[#f5c542]/40" },
            { flex: 50, className: "bg-[#61e294]/50" },
          ],
          ind.adx * 2
        )}
      </TechCard>

      {/* 5. VWAP */}
      <TechCard
        label={t.vwapLabel}
        value={
          <span className={ind.vwap >= 0 ? "text-[#61e294] font-bold" : "text-[#ff8383] font-bold"}>
            {vwapVal}
          </span>
        }
        note={vwapNote}
        tooltip={t.vwapTooltip}
      >
        <div className="text-[0.65rem] text-[#61e294] font-mono mt-1 flex items-center gap-1">
          <span>&bull; {ind.vwap >= 0 ? "Bullish Flow" : "Bearish Flow"}</span>
        </div>
      </TechCard>

      {/* 6. SPREAD */}
      <TechCard
        label={t.spreadLabel}
        value={spreadVal}
        note={spreadNote}
        tooltip={t.spreadTooltip}
      >
      </TechCard>
    </section>
  );
}

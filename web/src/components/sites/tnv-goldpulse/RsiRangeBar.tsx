"use client";

interface RsiRangeBarProps {
  value: number; // 0-100
}

export function RsiRangeBar({ value = 41.2 }: RsiRangeBarProps) {
  const safeVal = Math.min(100, Math.max(0, value));

  return (
    <div className="qx-range-bar" role="meter" aria-valuenow={safeVal} aria-valuemin={0} aria-valuemax={100}>
      <div className="qx-range-zones">
        {/* Oversold zone (<30) */}
        <span className="qx-zone-green" style={{ flex: 30 }} title="Oversold (< 30)" />
        {/* Neutral zone (30-70) */}
        <span className="qx-zone-yellow" style={{ flex: 40 }} title="Neutral (30 - 70)" />
        {/* Overbought zone (>70) */}
        <span className="qx-zone-red" style={{ flex: 30 }} title="Overbought (> 70)" />
      </div>
      <div
        className="qx-range-needle"
        style={{ left: `calc(${safeVal}% - 2px)` }}
        title={`RSI Needle: ${safeVal}`}
      />
    </div>
  );
}

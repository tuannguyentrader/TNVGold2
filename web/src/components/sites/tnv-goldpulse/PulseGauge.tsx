"use client";

interface PulseGaugeProps {
  value: number; // 0 - 100
  bandLabel?: string;
  note?: string;
  color?: string;
}

export function PulseGauge({
  value = 80,
  bandLabel = "PULSE",
  note = "Pulse:80 | Body:68% | Range:Strong | HTF:Pass",
  color,
}: PulseGaugeProps) {
  const size = 104;
  const strokeWidth = 7.5;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const arcLength = circumference * 0.75;
  const strokeDashoffset = arcLength - (Math.min(100, Math.max(0, value)) / 100) * arcLength;

  // Compute theme color if not explicitly provided
  const computedColor =
    color ||
    (value >= 60 ? "#61e294" : value >= 40 ? "#f5c542" : "#ff8383");

  return (
    <div className="flex flex-col items-center justify-center text-center">
      <div className="relative w-[104px] h-[104px] flex items-center justify-center">
        <svg
          width={size}
          height={size}
          className="transform -rotate-135"
          viewBox={`0 0 ${size} ${size}`}
          aria-hidden="true"
        >
          {/* Background Arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeLinecap="round"
          />

          {/* Active Gradient/Color Arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={computedColor}
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
          />
        </svg>

        {/* Center Text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none pt-0.5">
          <span
            className="text-2xl font-bold font-mono tracking-tight leading-none"
            style={{ color: computedColor }}
          >
            {value}
          </span>
          <span className="text-[0.55rem] font-bold tracking-wider text-gray-400 uppercase mt-0.5">
            {bandLabel}
          </span>
        </div>
      </div>

      {/* Compact Note Line */}
      {note && (
        <div className="text-[0.62rem] text-gray-300 font-mono mt-1 text-center">
          {note}
        </div>
      )}
    </div>
  );
}

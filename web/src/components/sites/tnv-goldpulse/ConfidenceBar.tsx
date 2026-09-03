"use client";

interface ConfidenceBarProps {
  value: number; // 0-100
}

export function ConfidenceBar({ value = 42 }: ConfidenceBarProps) {
  const safeVal = Math.min(100, Math.max(0, value));

  return (
    <div className="qx-bar-track">
      <div
        className="qx-bar-fill"
        style={{ width: `${safeVal}%` }}
        role="progressbar"
        aria-valuenow={safeVal}
        aria-valuemin={0}
        aria-valuemax={100}
      />
    </div>
  );
}

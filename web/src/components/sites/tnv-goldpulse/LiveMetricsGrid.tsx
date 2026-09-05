"use client";

import { MetricCard } from "./MetricCard";
import { FlipBackContent } from "./FlipBackContent";
import { ConfidenceBar } from "./ConfidenceBar";
import { TrendingUp, TrendingDown, Minus, ShieldCheck } from "lucide-react";
import { useLanguage } from "@/lib/language-context";
import { useLivePulse } from "@/lib/live-pulse-context";

export function LiveMetricsGrid() {
  const { language, t } = useLanguage();
  const { pulse } = useLivePulse();

  const isLong = pulse.bias === "LONG";
  const isShort = pulse.bias === "SHORT";
  const isNeutral = pulse.bias === "NEUTRAL";

  // NEUTRAL không mang ý nghĩa tín hiệu: đưa score về 0 khi hiển thị để tránh
  // mâu thuẫn "NEUTRAL + score cao" (Pulse/ConfidenceBar luôn nhất quán với BIAS).
  const pulseScore = isNeutral ? 0 : pulse.score;

  // Mặt sau các thẻ TẠM hiển thị M15/M30/H1 = 0 (placeholder — người dùng chưa có ý tưởng, sẽ cập nhật sau).
  const tfPlaceholderRows = [
    { tf: "M15", value: "0" },
    { tf: "M30", value: "0" },
    { tf: "H1", value: "0" },
  ];

  return (
    <div className="grid grid-cols-2 gap-2 w-full min-w-0">
      {/* 1. BIAS */}
      <MetricCard
        label={t.biasLabel}
        tooltip={t.biasTooltip}
        footer={
          <div className="text-[0.65rem] text-gray-400">
            {language === "vi"
              ? `Cách ${pulse.signalAge ?? 0} phút`
              : `${pulse.signalAge ?? 0} min ago`}
          </div>
        }
        flipBack={
          <FlipBackContent label={t.biasLabel} rows={tfPlaceholderRows} />
        }
      >
        <div
          className={`flex items-center gap-1 ${
            isLong || isShort
              ? "text-lg sm:text-2xl font-bold tracking-tight"
              : "text-base sm:text-lg font-normal text-gray-500"
          } ${
            isLong
              ? "text-[#61e294]"
              : isShort
              ? "text-[#ff8383]"
              : ""
          }`}
        >
          {isLong ? (
            <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5" />
          ) : isShort ? (
            <TrendingDown className="w-4 h-4 sm:w-5 sm:h-5" />
          ) : (
            <Minus className="w-3 h-3 sm:w-4 sm:h-4" />
          )}
          <span>{isLong || isShort ? pulse.bias : "—"}</span>
        </div>
      </MetricCard>

      {/* 2. PULSE */}
      <MetricCard
        label="PULSE"
        tooltip={t.scoreTooltip}
        footer={<ConfidenceBar value={pulseScore * 10} />}
        flipBack={<FlipBackContent label="PULSE" rows={tfPlaceholderRows} />}
      >
        <div className="flex items-center justify-center h-full">
          <span
            className={`text-2xl sm:text-4xl font-bold font-mono ${
              pulseScore >= 8
                ? "text-[#61e294]"
                : pulseScore >= 5
                ? "text-[#f5c542]"
                : "text-gray-400"
            }`}
          >
            {pulseScore * 10}
          </span>
        </div>
      </MetricCard>

      {/* 3. VOLATILITY */}
      <MetricCard
        label={t.volatilityLabel}
        tooltip={t.volatilityTooltip}
        footer={
          <div className="flex items-center justify-between text-[0.65rem] text-gray-400">
            <span>Status:</span>
            <span className="text-[#61e294] font-medium">{t.volatilityStatus}</span>
          </div>
        }
        flipBack={
          <FlipBackContent label={t.volatilityLabel} rows={tfPlaceholderRows} />
        }
      >
        <div className="text-lg sm:text-2xl font-bold text-white font-mono tracking-tight">
          ${pulse.volatility.toFixed(2)} <span className="text-[0.65rem] sm:text-xs text-gray-400 font-normal">USD</span>
        </div>
      </MetricCard>

      {/* 4. ENTRY */}
      <MetricCard
        label="ENTRY"
        tooltip={t.entryTooltip}
        flipBack={<FlipBackContent label="ENTRY" rows={tfPlaceholderRows} />}
      >
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center justify-between text-[0.7rem]">
            <span className="text-gray-400 font-sans">Price:</span>
            <span className="text-white font-mono font-bold text-xs sm:text-sm">
              {pulse.entry.price != null ? `$${pulse.entry.price.toFixed(2)}` : "—"}
            </span>
          </div>
          <div className="flex items-center justify-between text-[0.7rem]">
            <span className="text-gray-400 font-sans">Gain:</span>
            <span
              className={`font-mono font-semibold text-xs sm:text-sm ${
                pulse.entry.gain != null && pulse.entry.gain >= 0 ? "text-[#61e294]" : "text-[#ff8383]"
              }`}
            >
              {pulse.entry.gain != null
                ? (pulse.entry.gain >= 0 ? `+${pulse.entry.gain.toFixed(2)}%` : `${pulse.entry.gain.toFixed(2)}%`)
                : "—"}
            </span>
          </div>
        </div>
      </MetricCard>

      {/* 5. EXIT */}
      <MetricCard
        label="EXIT"
        tooltip={t.exitTooltip}
        flipBack={<FlipBackContent label="EXIT" rows={tfPlaceholderRows} />}
      >
        {pulse.sl != null && pulse.tp != null ? (
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between text-[0.7rem] leading-tight">
              <span className="text-gray-400 font-sans">SL <span className="text-[0.55rem] text-gray-500">(1.5N)</span>:</span>
              <span className="text-[#ff8383] font-mono font-semibold">${pulse.sl.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between text-[0.7rem] leading-tight">
              <span className="text-gray-400 font-sans">TP <span className="text-[0.55rem] text-gray-500">(2.0N)</span>:</span>
              <span className="text-[#61e294] font-mono font-semibold">${pulse.tp.toFixed(2)}</span>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500 text-sm font-mono">
            —
          </div>
        )}
      </MetricCard>

      {/* 6. HTF FILTER */}
      <MetricCard
        label={t.htfLabel}
        tooltip={t.htfTooltip}
        footer={
          <div className="flex items-center justify-between text-[0.65rem] text-gray-400">
            <span className="text-gray-400">{t.htfFooter}</span>
            <span className="text-[#61e294] font-semibold">{pulse.htf}</span>
          </div>
        }
        flipBack={<FlipBackContent label={t.htfLabel} rows={tfPlaceholderRows} />}
      >
        <div className="flex items-center gap-1.5 sm:gap-2.5 my-0.5">
          <div className="p-1 sm:p-1.5 rounded-lg bg-[rgba(97,226,148,0.15)] text-[#61e294] border border-[rgba(97,226,148,0.3)] shrink-0">
            <ShieldCheck className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div className="min-w-0">
            <div className="text-xs sm:text-base font-bold text-[#61e294] tracking-tight leading-tight truncate">
              {pulse.htf}
            </div>
            <div className="text-[0.65rem] text-gray-400 font-mono mt-0.5 truncate">
              M15 · M30 · H1
            </div>
          </div>
        </div>
      </MetricCard>
    </div>
  );
}

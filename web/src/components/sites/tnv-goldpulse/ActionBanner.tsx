"use client";

import { useState } from "react";
import { Share2, Check, Zap, Clock, Radio } from "lucide-react";
import { useLanguage } from "@/lib/language-context";
import { useLivePulse } from "@/lib/live-pulse-context";

export function ActionBanner() {
  const { language } = useLanguage();
  const { pulse, isLiveConnected, lastUpdated } = useLivePulse();
  const [copied, setCopied] = useState(false);

  const isLong = pulse.bias === "LONG";
  const isShort = pulse.bias === "SHORT";
  const isNeutral = pulse.bias === "NEUTRAL";
  const hasData = pulse.price > 0;

  const gainStr = pulse.entry.gain >= 0 ? `+${pulse.entry.gain.toFixed(2)}` : pulse.entry.gain.toFixed(2);

  let actionText: string;
  if (!hasData) {
    actionText = language === "vi"
      ? "Đang chờ dữ liệu từ hệ thống..."
      : "Waiting for data from system...";
  } else if (isNeutral) {
    actionText =
      language === "vi"
        ? `XAUUSD TRUNG LẬP • Giá: $${pulse.price.toFixed(2)} • Biên độ: ${pulse.entry.low.toFixed(2)}–${pulse.entry.high.toFixed(2)}`
        : `XAUUSD NEUTRAL • Price: $${pulse.price.toFixed(2)} • Range: ${pulse.entry.low.toFixed(2)}–${pulse.entry.high.toFixed(2)}`;
  } else {
    actionText =
      language === "vi"
        ? `XAUUSD ${pulse.bias} • Giá vào: $${pulse.entry.high.toFixed(2)} • Hiện tại: $${pulse.price.toFixed(2)} (${gainStr}) • Dừng lỗ: $${pulse.exit.toFixed(2)}`
        : `XAUUSD ${pulse.bias} • Entry: $${pulse.entry.high.toFixed(2)} • Now: $${pulse.price.toFixed(2)} (${gainStr}) • Stop: $${pulse.exit.toFixed(2)}`;
  }

  const handleShare = async () => {
    const shareText = `TNV SIGNAL | ${actionText}`;
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(shareText);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    } catch {
      // Fallback
    }
  };

  return (
    <div
      className={`flex items-center justify-between gap-3 px-4 py-2.5 mb-4 rounded-xl border text-xs shadow-md ${
        !hasData
          ? "border-[rgba(255,255,255,0.1)] bg-[#0b0f16]"
          : isLong
          ? "border-[rgba(97,226,148,0.35)] bg-[#070e12]"
          : isShort
          ? "border-[rgba(255,96,96,0.35)] bg-[#130707]"
          : "border-[rgba(245,197,66,0.25)] bg-[#0b0f16]"
      }`}
    >
      {/* Left: Signal Badge + Alert message */}
      <div className="flex items-center gap-2.5 overflow-hidden flex-1 min-w-0">
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-bold text-[0.68rem] border shrink-0 ${
            !hasData
              ? "bg-white/5 text-gray-400 border-white/10"
              : isLong
              ? "bg-[rgba(97,226,148,0.18)] text-[#61e294] border-[rgba(97,226,148,0.3)]"
              : isShort
              ? "bg-[rgba(255,96,96,0.18)] text-[#ff8383] border-[rgba(255,96,96,0.3)]"
              : "bg-[rgba(245,197,66,0.12)] text-[#f5c542] border-[rgba(245,197,66,0.25)]"
          }`}
        >
          <Zap className="w-3 h-3 fill-current" />
          {!hasData ? "TNV IDLE" : isNeutral ? "TNV NEUTRAL" : "TNV SIGNAL"}
        </span>
        <div className="truncate text-gray-200 font-medium font-mono text-[0.74rem]">
          {actionText}
        </div>
      </div>

      {/* Middle: Status badge (Live / Waiting) + timestamp */}
      <div className="flex items-center gap-3 shrink-0">
        <div
          className={`flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[0.66rem] font-semibold ${
            isLiveConnected
              ? "bg-[rgba(97,226,148,0.12)] text-[#61e294] border border-[rgba(97,226,148,0.25)]"
              : "bg-white/5 text-gray-400 border border-white/10"
          }`}
          title={isLiveConnected
            ? (language === "vi" ? "Đang nhận dữ liệu trực tiếp" : "Receiving live data")
            : (language === "vi" ? "Đang chờ dữ liệu..." : "Waiting for data...")}
        >
          <Radio className={`w-3 h-3 ${isLiveConnected ? "animate-pulse" : ""}`} />
          <span className="uppercase tracking-wider">
            {isLiveConnected
              ? "Live"
              : (language === "vi" ? "Chờ" : "Idle")}
          </span>
        </div>

        {/* Last update timestamp */}
        {lastUpdated && lastUpdated !== "—" && (
          <div className="hidden sm:flex items-center gap-1 text-[0.66rem] text-gray-400 font-mono">
            <Clock className="w-3 h-3" />
            <span>{lastUpdated}</span>
          </div>
        )}

        {/* Right: Clean Circular Share Button */}
        <button
          onClick={handleShare}
          className="w-7 h-7 rounded-full bg-black/60 border border-white/10 flex items-center justify-center text-gray-400 hover:text-[#f5c542] hover:border-[#f5c542]/40 transition-all cursor-pointer"
          title="Share Signal Alert"
          aria-label="Share Signal Alert"
        >
          {copied ? (
            <Check className="w-3.5 h-3.5 text-[#61e294]" />
          ) : (
            <Share2 className="w-3.5 h-3.5" />
          )}
        </button>
      </div>
    </div>
  );
}

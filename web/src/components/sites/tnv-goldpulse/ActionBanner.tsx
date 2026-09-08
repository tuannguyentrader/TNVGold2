"use client";

import { useState } from "react";
import { Share2, Check, Zap } from "lucide-react";
import { useLanguage } from "@/lib/language-context";
import { useLivePulse } from "@/lib/live-pulse-context";
import { DataAgeBadge } from "./DataAgeBadge";

export function ActionBanner() {
  const { language } = useLanguage();
  const { pulse } = useLivePulse();
  const [copied, setCopied] = useState(false);

  const isLong = pulse.bias === "LONG";
  const isShort = pulse.bias === "SHORT";
  const isNeutral = pulse.bias === "NEUTRAL";
  const hasData = pulse.price > 0;

  const gainStr = pulse.entry.gain != null
    ? (pulse.entry.gain >= 0 ? `+${pulse.entry.gain.toFixed(2)}%` : `${pulse.entry.gain.toFixed(2)}%`)
    : "—";

  let actionTextLine1: string;
  let actionTextLine2: string = "";
  if (!hasData) {
    actionTextLine1 = language === "vi"
      ? "Đang chờ dữ liệu từ hệ thống..."
      : "Waiting for data from system...";
  } else if (isNeutral) {
    const rangeLow = (pulse.price - pulse.volatility).toFixed(2);
    const rangeHigh = (pulse.price + pulse.volatility).toFixed(2);
    actionTextLine1 =
      language === "vi"
        ? `XAUUSD TRUNG LẬP • $${pulse.price.toFixed(2)}`
        : `XAUUSD NEUTRAL • $${pulse.price.toFixed(2)}`;
    actionTextLine2 =
      language === "vi"
        ? `Biên độ: $${rangeLow}–$${rangeHigh}`
        : `Range: $${rangeLow}–$${rangeHigh}`;
  } else {
    const entryRef = pulse.entry.price != null ? `$${pulse.entry.price.toFixed(2)}` : "—";
    const slRef = pulse.sl != null ? `$${pulse.sl.toFixed(2)}` : "—";
    actionTextLine1 =
      language === "vi"
        ? `XAUUSD ${pulse.bias} • $${pulse.price.toFixed(2)} (${gainStr})`
        : `XAUUSD ${pulse.bias} • $${pulse.price.toFixed(2)} (${gainStr})`;
    actionTextLine2 =
      language === "vi"
        ? `Vào: ${entryRef} • Dừng lỗ: ${slRef}`
        : `Entry: ${entryRef} • Stop: ${slRef}`;
  }

  const handleShare = async () => {
    const shareText = `TNV SIGNAL | ${actionTextLine1}${actionTextLine2 ? " | " + actionTextLine2 : ""}`;
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
      className={`flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-3 px-3 sm:px-4 py-2.5 mb-4 rounded-xl border text-xs sm:text-sm shadow-md overflow-hidden ${
        isLong
          ? "border-[rgba(97,226,148,0.35)] bg-[#070e12]"
          : isShort
          ? "border-[rgba(255,96,96,0.35)] bg-[#130707]"
          : "border-[rgba(245,197,66,0.25)] bg-[#0b0f16]"
      }`}
    >
      {/* Left: Signal Badge + Alert message */}
      <div className="flex items-start sm:items-center gap-2.5 overflow-hidden flex-1 min-w-0">
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-bold text-[0.68rem] border shrink-0 ${
            isLong
              ? "bg-[rgba(97,226,148,0.18)] text-[#61e294] border-[rgba(97,226,148,0.3)]"
              : isShort
              ? "bg-[rgba(255,96,96,0.18)] text-[#ff8383] border-[rgba(255,96,96,0.3)]"
              : "bg-[rgba(245,197,66,0.12)] text-[#f5c542] border-[rgba(245,197,66,0.25)]"
          }`}
        >
          <Zap className="w-3 h-3 fill-current" />
          TNV SIGNAL
        </span>
        {/* Text: 2 dòng trên mobile, 1 dòng (cách nhau bằng •) trên tablet+ */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:gap-1.5 text-gray-200 font-medium font-mono text-[0.74rem] min-w-0 flex-1">
          <span className="truncate">{actionTextLine1}</span>
          {actionTextLine2 && (
            <>
              <span className="hidden sm:inline text-gray-500">•</span>
              <span className="truncate text-gray-400">{actionTextLine2}</span>
            </>
          )}
        </div>
      </div>

      {/* Middle: Data-age badge — tuổi thật của data = now − Date(pulse.time), tự tick mỗi 30s.
          (lastUpdated của context là giờ client fetch, KHÔNG phải tuổi data — không hiển thị nữa.) */}
      <div className="flex items-center gap-3 shrink-0">
        <DataAgeBadge />

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

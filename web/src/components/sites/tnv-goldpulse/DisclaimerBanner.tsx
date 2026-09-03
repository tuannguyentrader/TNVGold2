"use client";

import { useState } from "react";
import { AlertTriangle, X } from "lucide-react";
import { useLanguage } from "@/lib/language-context";

export function DisclaimerBanner() {
  const { language, t } = useLanguage();
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div
      className="flex items-center justify-between gap-3 px-3.5 py-2 mb-3.5 rounded-xl border border-[rgba(245,197,66,0.2)] bg-[rgba(245,197,66,0.04)] text-[0.76rem] text-[rgba(230,230,230,0.85)] leading-relaxed shadow-sm transition-all"
    >
      <div className="flex items-center gap-2">
        <AlertTriangle className="w-3.5 h-3.5 text-[#f5c542] shrink-0" />
        <span>
          <strong className="text-[#f5c542] font-semibold">
            {language === "vi" ? "Lưu ý rủi ro:" : "Risk Notice:"}
          </strong>{" "}
          {t.disclaimerText}{" "}
          <a
            href="#footer"
            className="text-[#f5c542] hover:underline underline-offset-2 ml-1"
          >
            {language === "vi" ? "Chi tiết miễn trừ →" : "Full disclaimer →"}
          </a>
        </span>
      </div>
      <button
        onClick={() => setDismissed(true)}
        className="text-[rgba(255,255,255,0.4)] hover:text-white transition-colors p-1 cursor-pointer"
        title="Dismiss notice"
        aria-label="Dismiss notice"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

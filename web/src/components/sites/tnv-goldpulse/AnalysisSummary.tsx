"use client";

import { PulseGauge } from "./PulseGauge";
import { useLanguage } from "@/lib/language-context";
import { useLivePulse } from "@/lib/live-pulse-context";
import { buildAnalysisText } from "@/lib/analysis-text";

export function AnalysisSummary() {
  const { language, t } = useLanguage();
  const { pulse } = useLivePulse();

  const scrollToTechnical = () => {
    const el =
      document.getElementById("technical-grid") ||
      document.querySelector(".qx-tech-grid");
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const gaugeValue = pulse.score * 10; // 0-100 cho kim đồng hồ
  const gaugeColor = gaugeValue >= 60 ? "#61e294" : gaugeValue >= 40 ? "#f5c542" : "#ff8383";

  // Câu phân tích được sinh bởi hàm thuần trong lib/analysis-text.ts
  // (tách ra để test được; xem ghi chú lỗi số liệu tại đó).
  const analysisText = buildAnalysisText(pulse, language as "vi" | "en");

  return (
    <aside className="flex flex-col justify-between h-full p-3.5 bg-[#080c14] rounded-xl border border-white/5 shadow-inner">
      {/* 1. Top Header: TNV ANALYSIS */}
      <div className="pb-1">
        <div className="flex items-center justify-between pb-1">
          <span className="text-[0.72rem] font-bold uppercase tracking-wider text-[#f5c542]">
            {t.analysisTitle}
          </span>
          <span className="text-[0.6rem] font-bold px-2 py-0.5 rounded bg-[#18392b] text-[#61e294] border border-[#61e294]/30 uppercase">
            {t.liveSignalBadge}
          </span>
        </div>
        {/* Yellow Separator Line */}
        <div className="w-full h-[1.5px] bg-[#f5c542]/70" />
      </div>

      {/* 2. Centered Middle Section: Radial Score Gauge + Narrative Description */}
      <div className="flex flex-col items-center justify-center text-center my-auto py-1 flex-1 gap-2">
        {/* Radial Score Gauge (Scaled 104px) */}
        <div className="transform transition-transform hover:scale-105 duration-200">
          <PulseGauge
            value={gaugeValue}
            displayValue={`${pulse.score}`}
            bandLabel="PULSE /10"
            note={`Pulse ${pulse.score}/10 | RSI: ${pulse.indicators?.rsi?.toFixed(1) ?? "—"} | HTF:${pulse.htf}`}
            color={gaugeColor}
          />
        </div>

        {/* Narrative Description */}
        <p className="text-[0.74rem] text-gray-200 leading-snug font-normal max-w-[98%] text-center m-0">
          {analysisText}
        </p>

        {/* Link to Technical Grid */}
        <div className="flex flex-col items-center justify-center pt-0.5 text-center">
          <button
            onClick={scrollToTechnical}
            className="text-[0.68rem] text-gray-400 hover:text-[#f5c542] transition-colors cursor-pointer underline-offset-4 hover:underline"
          >
            {t.viewTechnical}
          </button>
        </div>
      </div>
    </aside>
  );
}

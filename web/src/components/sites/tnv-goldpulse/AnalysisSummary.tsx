"use client";

import { PulseGauge } from "./PulseGauge";
import { useLanguage } from "@/lib/language-context";
import { useLivePulse } from "@/lib/live-pulse-context";

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

  const gaugeValue = pulse.score * 10; // 0-100 for gauge
  const gaugeColor = gaugeValue >= 60 ? "#61e294" : gaugeValue >= 40 ? "#f5c542" : "#ff8383";

  // Generate live analysis text dynamically based on pulse data
  const genAnalysis = (): string => {
    if (pulse.analysisText?.[language]) return pulse.analysisText[language]!;

    const pulseVal = gaugeValue;
    const gainText = pulse.entry.gain >= 0
      ? `+$${pulse.entry.gain.toFixed(2)}`
      : `-$${Math.abs(pulse.entry.gain).toFixed(2)}`;

    // NEUTRAL case
    if (pulse.bias === "NEUTRAL") {
      if (language === "vi") {
        return `Vàng đang giao dịch đi ngang với xung lực Pulse đạt ${pulseVal}, giá ổn định trong biên độ $${pulse.entry.low.toFixed(2)} – $${pulse.entry.high.toFixed(2)}. Cấu trúc đa khung thời gian chưa có sự đồng thuận rõ ràng. Theo dõi: phá vỡ trên $${pulse.entry.high.toFixed(2)} để xác nhận đà tăng, hoặc thủng $${pulse.entry.low.toFixed(2)} để kích hoạt xu hướng giảm.`;
      }
      return `Gold is trading sideways with Pulse reaching ${pulseVal}, price holding within a range of $${pulse.entry.low.toFixed(2)} – $${pulse.entry.high.toFixed(2)}. Multi-timeframe structure is not providing clear directional alignment. Watch for: a breakout above $${pulse.entry.high.toFixed(2)} to confirm upside momentum, or a breakdown below $${pulse.entry.low.toFixed(2)} to trigger bearish bias.`;
    }

    const direction = pulse.bias === "LONG"
      ? (language === "vi" ? "tăng" : "bullish")
      : (language === "vi" ? "giảm" : "bearish");

    const dirAdj = pulse.bias === "LONG"
      ? (language === "vi" ? "mạnh mẽ" : "strong")
      : (language === "vi" ? "mạnh mẽ" : "strong");

    const alignment = pulse.bias === "LONG"
      ? (language === "vi" ? "tăng" : "bullish")
      : (language === "vi" ? "giảm" : "bearish");

    const resistance = pulse.bias === "LONG"
      ? pulse.entry.high
      : pulse.entry.low;
    const support = pulse.exit;

    // SHORT bias
    if (pulse.bias === "SHORT") {
      if (language === "vi") {
        return `Vàng đang duy trì đà giảm mạnh mẽ với xung lực Pulse đạt ${pulseVal}, giá giảm ${gainText.replace("+", "").replace("-", "")} dưới mức $${resistance.toFixed(2)} cùng cấu trúc đa khung thời gian đồng thuận mà không gặp cản trở. Theo dõi: đà giảm tiếp diễn dưới $${resistance.toFixed(2)} hướng tới các mục tiêu mở rộng, hoặc nhịp hồi kiểm tra lại ngưỡng kháng cự $${support.toFixed(2)} trước khi hình thành nhịp giảm mới.`;
      }
      return `Gold is displaying strong ${direction} momentum as Pulse reaches ${pulseVal} and the price sits ${gainText.replace("+", "").replace("-", " -$")} below the $${resistance.toFixed(2)} level, with higher-timeframe structure providing clean directional alignment without overhead resistance. Watch for: continuation below $${resistance.toFixed(2)} toward lower expansion targets, or a pullback toward the $${support.toFixed(2)} resistance to test supply before the next leg lower.`;
    }

    // LONG bias (default)
    if (language === "vi") {
      return `Vàng đang duy trì đà tăng mạnh mẽ với xung lực Pulse đạt ${pulseVal}, giá bứt phá vượt ${gainText} trên mức $${resistance.toFixed(2)} cùng cấu trúc đa khung thời gian đồng thuận mà không gặp cản trở. Theo dõi: đà tăng tiếp diễn vượt $${resistance.toFixed(2)} hướng tới các mục tiêu mở rộng, hoặc nhịp điều chỉnh kiểm tra lại ngưỡng hỗ trợ $${support.toFixed(2)} trước khi hình thành nhịp tăng mới.`;
    }
    return `Gold is displaying strong ${direction} momentum as Pulse reaches ${pulseVal} and the price sits ${gainText} above the $${resistance.toFixed(2)} level, with higher-timeframe structure providing clean directional alignment without overhead resistance. Watch for: continuation above $${resistance.toFixed(2)} toward upper expansion targets, or a pullback toward the $${support.toFixed(2)} support to test demand before the next leg higher.`;
  };

  const analysisText = genAnalysis();

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
            bandLabel="PULSE"
            note={`Pulse ${gaugeValue} | RSI: ${pulse.indicators.rsi.toFixed(1)} | HTF:${pulse.htf}`}
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

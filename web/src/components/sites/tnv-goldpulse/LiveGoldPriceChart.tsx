"use client";

import { useState } from "react";

type DateRange = "1D" | "1M" | "1Y" | "ALL";

export function LiveGoldPriceChart() {
  // Mặc định khởi tạo là khung thời gian 1M (1 Month)
  const [dateRange, setDateRange] = useState<DateRange>("1M");

  const widgetConfig = encodeURIComponent(
    JSON.stringify({
      symbol: "OANDA:XAUUSD",
      width: "100%",
      height: "100%",
      locale: "en",
      dateRange: dateRange,
      colorTheme: "dark",
      isTransparent: true,
      autosize: true,
      largeChartUrl: "",
      trendLineColor: "rgba(245, 197, 66, 1)",
      underLineColor: "rgba(245, 197, 66, 0.18)",
      underLineBottomColor: "rgba(245, 197, 66, 0)",
      gridLineColor: "rgba(255, 255, 255, 0.04)",
      chartOnly: false,
      noTimeScale: false,
    })
  );

  const iframeSrc = `https://s.tradingview.com/embed-widget/mini-symbol-overview/?locale=en#${widgetConfig}`;

  return (
    <div className="rounded-xl p-3.5 bg-[#090d16] border border-[rgba(245,197,66,0.35)] hover:border-[rgba(245,197,66,0.5)] transition-all flex flex-col justify-between shadow-xl flex-1 h-full min-h-[290px]">
      {/* Header đồng bộ viền vàng với các mục khác */}
      <div className="flex items-center justify-between pb-2 border-b border-[rgba(245,197,66,0.2)] shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#61e294] animate-pulse" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-white m-0">
            Live Gold Price (XAUUSD)
          </h3>
        </div>

        {/* Nút chọn Timeframe */}
        <div className="flex items-center gap-0.5 bg-[#111622] p-0.5 rounded-lg border border-white/10">
          {(["1D", "1M", "1Y", "ALL"] as DateRange[]).map((r) => (
            <button
              key={r}
              onClick={() => setDateRange(r)}
              className={`text-[0.65rem] px-2 py-0.5 rounded font-mono transition-colors cursor-pointer ${
                dateRange === r
                  ? "bg-[rgba(245,197,66,0.2)] text-[#f5c542] font-bold border border-[rgba(245,197,66,0.35)]"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* TradingView Live Chart Canvas - Pure React Iframe tránh xung đột Extension */}
      <div className="relative w-full flex-1 min-h-[225px] mt-2 bg-[#05070d] rounded-lg overflow-hidden border border-[rgba(245,197,66,0.15)]">
        <iframe
          key={dateRange}
          src={iframeSrc}
          className="absolute inset-0 w-full h-full border-0"
          title="TradingView Live XAUUSD Mini Overview"
          loading="lazy"
        />
      </div>
    </div>
  );
}

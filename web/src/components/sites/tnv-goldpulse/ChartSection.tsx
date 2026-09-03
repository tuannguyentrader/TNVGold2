"use client";

import { TrendingUp } from "lucide-react";
import { useLanguage } from "@/lib/language-context";

export function ChartSection() {
  const { t } = useLanguage();

  return (
    <section id="qx-pulsepro" className="my-4">
      <div className="qx-card p-3.5 border-[rgba(207,167,68,0.25)]">
        {/* Header */}
        <div className="flex items-center justify-between gap-3 flex-wrap pb-2.5 border-b border-white/5">
          <div className="flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4 text-[#61e294]" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-white m-0">
              {t.flowTitle}
            </h3>
          </div>
        </div>

        {/* TradingView Live Chart */}
        <div className="relative w-full h-[400px] my-2 bg-[#06080e] rounded-xl border border-white/5 overflow-hidden">
          <iframe
            src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_widget&symbol=OANDA%3AXAUUSD&interval=15&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=%5B%5D&theme=dark&style=1&timezone=Etc%2FUTC&studies_overrides=%7B%7D&overrides=%7B%7D&enabled_features=%5B%5D&disabled_features=%5B%5D&locale=en&utm_source=localhost"
            className="w-full h-full border-0"
            title="TradingView Live XAUUSD Chart"
            loading="lazy"
          />
        </div>

        {/* Footer Notes */}
        <div className="flex items-center justify-between text-[0.68rem] text-gray-500 mt-2 flex-wrap">
          <span>{t.flowFooter}</span>
        </div>
      </div>
    </section>
  );
}

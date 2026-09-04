"use client";

import { LivePulseProvider } from "@/lib/live-pulse-context";
import { ActionBanner } from "./ActionBanner";
import { LiveMetricsGrid } from "./LiveMetricsGrid";
import { AnalysisSummary } from "./AnalysisSummary";
import { LiveGoldPriceChart } from "./LiveGoldPriceChart";
import { SponsorCard } from "./SponsorCard";
import { ChartSection } from "./ChartSection";
import { TechnicalGrid } from "./TechnicalGrid";
import { HistoryTable } from "./HistoryTable";
import { SiteFooter } from "./SiteFooter";
import { DisclaimerBanner } from "./DisclaimerBanner";
import { ProUpgradeBar } from "./ProUpgradeBar";

export function TNVGoldPulseApp() {
  return (
    <LivePulseProvider>
      <main className="max-w-[1260px] mx-auto px-3 sm:px-4 py-3 pb-20 text-white font-sans">
        <DisclaimerBanner />

        {/* Header dùng SiteHeader global từ layout.tsx (Logo + Nav + Lang + Bell) */}

        <ProUpgradeBar />

        {/* Action / Ticker Banner */}
        <ActionBanner />

        {/* Main Dashboard Top Section */}
        <div className="grid grid-cols-1 lg:grid-cols-[1.22fr_1fr] gap-3.5 mb-4 items-stretch">
          {/* Left Golden Border Box: 6 Metrics + AI Analysis Panel */}
          <div className="rounded-2xl border border-[rgba(245,197,66,0.35)] bg-[#070b13] p-3.5 shadow-2xl h-full flex flex-col justify-between">
            <div className="grid grid-cols-1 md:grid-cols-[1.32fr_1fr] gap-2.5 h-full items-stretch">
              {/* 6 Metric Cards */}
              <div className="w-full h-full">
                <LiveMetricsGrid />
              </div>

              {/* AI Analysis Panel */}
              <div className="w-full h-full">
                <AnalysisSummary />
              </div>
            </div>
          </div>

          {/* Right Expanded Box: News + Live Gold Price Chart */}
          <div className="flex flex-col gap-3 h-full justify-between">
            <SponsorCard />
            <LiveGoldPriceChart />
          </div>
        </div>

        {/* 4. Technical Indicators Grid */}
        <TechnicalGrid />

        {/* 5. Gold Session Flow Chart */}
        <ChartSection />

        {/* 6. Ring Buffer Snapshot History Table */}
        <HistoryTable />

        {/* 7. Regulatory Footer */}
        <SiteFooter />

        {/* SubscribeBar + LanguageProvider đã ở layout.tsx (global) */}
      </main>
    </LivePulseProvider>
  );
}

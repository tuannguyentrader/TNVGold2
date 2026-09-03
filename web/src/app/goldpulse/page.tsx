import { TNVGoldPulseApp } from "@/components/sites/tnv-goldpulse";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "TNV Gold Pulse — Real-Time Algorithmic Market Analytics",
  description:
    "TNV provides real-time algorithmic market analytics, multi-timeframe bias conviction, Gold Session Flow visualization, and institutional order flow metrics for XAUUSD traders.",
};

export default function GoldPulseRoute() {
  return <TNVGoldPulseApp />;
}

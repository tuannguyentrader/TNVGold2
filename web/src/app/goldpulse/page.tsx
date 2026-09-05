import { TNVGoldPulseApp } from "@/components/sites/tnv-goldpulse";
import { getLatestPulse, getPulseHistory } from "@/lib/pulse-store";
import type { Metadata } from "next";

// Revalidate mỗi 30 giây — Next.js sẽ fetch lại từ Redis trên server
export const revalidate = 30;

export const metadata: Metadata = {
  title: "TNV Gold Pulse — Real-Time Algorithmic Market Analytics",
  description:
    "TNV provides real-time algorithmic market analytics, multi-timeframe bias conviction, Gold Session Flow visualization, and institutional order flow metrics for XAUUSD traders.",
};

export default async function GoldPulseRoute() {
  // Fetch data TRÊN SERVER (trước khi gửi HTML về client)
  // → User nhận được HTML có data sẵn, không phải đợi client fetch
  const pulse = await getLatestPulse();
  const history = await getPulseHistory(10);

  return <TNVGoldPulseApp initialPulse={pulse} initialHistory={history} />;
}

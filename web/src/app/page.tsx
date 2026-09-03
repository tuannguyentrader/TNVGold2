import type { Metadata } from "next";
import LandingClient from "@/components/landing/LandingClient";

export const metadata: Metadata = {
  title: "TNV Gold — Phân tích Vàng XAUUSD Real-Time bằng AI",
  description:
    "Dashboard phân tích vàng XAUUSD real-time với bias, score, multi-timeframe, session flow, AI analysis tiếng Việt. Bot Telegram Pro tự động gửi tín hiệu.",
  alternates: {
    canonical: "/",
  },
};

export default function HomePage() {
  return <LandingClient />;
}

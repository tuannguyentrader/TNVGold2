import { NextResponse } from "next/server";
import { getLatestPulse, getPulseHistory } from "@/lib/pulse-store";

export const dynamic = "force-dynamic";

/**
 * GET /api/pulse
 * Trả về pulse snapshot hiện tại + history 60 phút gần nhất.
 *
 * Data flow:
 *  - Telegram bot (Python) ghi pulse lên Upstash Redis mỗi 5 phút (key: tnv:current_pulse)
 *  - Web đọc từ Redis qua pulse-store.ts
 *  - LivePulseProvider poll endpoint này mỗi 10s
 *
 * (POST method đã xoá — EA cũ không còn dùng, bot ghi trực tiếp vào Redis)
 */
export async function GET() {
  const latest = await getLatestPulse();
  const history = await getPulseHistory();

  return NextResponse.json({
    success: true,
    data: latest,
    history,
    serverTime: new Date().toISOString(),
  });
}

import { NextResponse } from "next/server";
import { getLatestPulse, getPulseHistory } from "@/lib/pulse-store";

export const dynamic = "force-dynamic";

/**
 * GET /api/pulse
 * Trả về pulse snapshot hiện tại + history tín hiệu gần nhất.
 *
 * History đầy đủ (tối đa 500 tín hiệu) được SSR 1 lần ở /goldpulse.
 * Endpoint này được client poll mỗi 10s — chỉ trả 25 bản gần nhất để
 * payload nhẹ (~15KB), đủ để merge tín hiệu mới vào bảng client.
 *
 * Data flow:
 *  - Telegram bot (Python) ghi pulse + history lên Upstash Redis (mỗi 5 phút)
 *  - Web đọc từ Redis qua pulse-store.ts
 *  - LivePulseProvider poll endpoint này mỗi 10s
 */
export async function GET() {
  const latest = await getLatestPulse();
  const history = await getPulseHistory(25);

  return NextResponse.json({
    success: true,
    data: latest,
    history,
    serverTime: new Date().toISOString(),
  });
}

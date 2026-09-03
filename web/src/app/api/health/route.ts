// Health check — cho UptimeRobot / cron-job.org kiểm tra Web còn sống
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({
    status: "ok",
    service: "tnvgold-web",
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  });
}

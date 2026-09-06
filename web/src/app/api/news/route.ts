import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

/**
 * Fetch ForexFactory calendar từ mirror JSON feed.
 * URL: https://nfs.faireconomy.media/ff_calendar_thisweek.json
 * Đây là mirror của ForexFactory, trả về JSON array trực tiếp (không cần rss2json).
 * Cache 1h để giảm tải server mirror.
 */
const FF_JSON_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json";
const CACHE_TTL_SECONDS = 3600; // 1 giờ

interface FFEvent {
  title: string;
  country: string;
  date: string;
  impact: "High" | "Medium" | "Low" | "Holiday";
  forecast: string;
  previous: string;
}

const IMPACT_COLORS: Record<string, string> = {
  High: "🔴",
  Medium: "🟡",
  Low: "🟢",
  Holiday: "⚪",
};

export async function GET() {
  try {
    const res = await fetch(FF_JSON_URL, {
      next: { revalidate: CACHE_TTL_SECONDS },
    });

    if (!res.ok) {
      return NextResponse.json({ success: false, items: [] }, { status: 502 });
    }

    const events: FFEvent[] = await res.json();
    if (!Array.isArray(events) || events.length === 0) {
      return NextResponse.json({ success: false, items: [] }, { status: 200 });
    }

    // Lấy 5 events gần nhất (theo date)
    const sorted = [...events]
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
      .slice(0, 5);

    const items = sorted.map((e) => {
      const d = new Date(e.date);
      const dateStr = d.toLocaleDateString("vi-VN", {
        day: "2-digit",
        month: "2-digit",
      });
      const timeStr = d.toLocaleTimeString("en-GB", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      });
      const impactIcon = IMPACT_COLORS[e.impact] || "⚪";
      const title = `${impactIcon} ${e.country} • ${e.title}`;

      return {
        title,
        source: "ForexFactory",
        time: `${dateStr} ${timeStr}`,
        url: `https://www.forexfactory.com/calendar`,
        impact: e.impact,
      };
    });

    return NextResponse.json({ success: true, items });
  } catch {
    return NextResponse.json({ success: false, items: [] }, { status: 500 });
  }
}

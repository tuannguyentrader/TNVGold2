// Cron — fetch tin tức từ ForexFactory mỗi 30 phút
import { NextResponse } from "next/server";
import { addNews, clearOldNews } from "@/lib/news-store";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

const FF_RSS = "https://www.forexfactory.com/ffcal_week_this.xml";
const RSS2JSON_API = "https://api.rss2json.com/v1/api.json";

export async function GET(request: Request) {
  // Auth — Vercel Cron header hoặc Bearer
  const expected = process.env.TNV_SECRET_KEY;
  const authHeader = request.headers.get("authorization");
  const cronHeader = request.headers.get("x-vercel-cron");

  if (!expected) {
    return NextResponse.json(
      { success: false, error: "Server auth not configured" },
      { status: 500 }
    );
  }
  if (!cronHeader && authHeader !== `Bearer ${expected}`) {
    return NextResponse.json({ success: false, error: "Unauthorized" }, { status: 401 });
  }

  try {
    // Fetch từ rss2json (proxy ForexFactory)
    const url = `${RSS2JSON_API}?rss_url=${encodeURIComponent(FF_RSS)}&count=20`;
    const res = await fetch(url, { next: { revalidate: 0 } });
    if (!res.ok) {
      return NextResponse.json(
        { success: false, error: `Upstream returned ${res.status}` },
        { status: 502 }
      );
    }
    const data = await res.json();
    if (!data.items || !Array.isArray(data.items)) {
      return NextResponse.json(
        { success: false, error: "Invalid upstream response" },
        { status: 502 }
      );
    }

    let added = 0;
    for (const item of data.items.slice(0, 20)) {
      // Strip HTML tags from title
      const cleanTitle = (item.title || "").replace(/<[^>]*>/g, "").trim();
      if (!cleanTitle) continue;

      const result = await addNews({
        title: cleanTitle,
        time: item.pubDate || new Date().toISOString(),
        url: item.link || "",
        source: "ForexFactory",
      });
      if (result) added++;
    }

    // Cleanup old news (>7 days)
    await clearOldNews(7 * 24 * 60 * 60 * 1000);

    return NextResponse.json({
      success: true,
      message: `News fetched and stored`,
      added,
      total: data.items.length,
    });
  } catch (err) {
    return NextResponse.json(
      { success: false, error: "Failed to fetch news", detail: String(err) },
      { status: 500 }
    );
  }
}

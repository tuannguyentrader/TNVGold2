// Cron — fetch tin tức từ ForexFactory mỗi 30 phút
// Dùng URL giống Telegram bot: https://nfs.faireconomy.media/ff_calendar_thisweek.xml
// Fallback: rss2json proxy nếu XML trực tiếp fail
import { NextResponse } from "next/server";
import { addNews, clearOldNews } from "@/lib/news-store";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

const FF_XML = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml";
const FF_RSS_OLD = "https://www.forexfactory.com/ffcal_week_this.xml";
const RSS2JSON_API = "https://api.rss2json.com/v1/api.json";

interface NewsItem {
  title: string;
  time: string;
  url?: string;
  source: string;
  impact?: string;
  currency?: string;
}

// Parse XML từ faireconomy.media — format: <weeklyevents>...</weeklyevents>
// Mỗi event: <event><title>...</title><country>USD</country><time>...</time>...
function parseXmlEvents(xml: string): NewsItem[] {
  const items: NewsItem[] = [];
  // Match tất cả <event>...</event>
  const eventRegex = /<event>([\s\S]*?)<\/event>/g;
  let match: RegExpExecArray | null;
  while ((match = eventRegex.exec(xml)) !== null) {
    const block = match[1];
    const titleMatch = block.match(/<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?<\/title>/);
    const countryMatch = block.match(/<country>(.*?)<\/country>/);
    const timeMatch = block.match(/<time>(.*?)<\/time>/);
    const impactMatch = block.match(/<impact>(.*?)<\/impact>/);
    const urlMatch = block.match(/<url>(.*?)<\/url>/);

    if (!titleMatch) continue;
    const title = (titleMatch[1] || "").trim();
    if (!title) continue;

    items.push({
      title,
      time: timeMatch ? new Date(timeMatch[1]).toISOString() : new Date().toISOString(),
      url: urlMatch ? urlMatch[1] : "",
      source: "ForexFactory",
      currency: countryMatch ? countryMatch[1] : "",
      impact: impactMatch ? impactMatch[1] : "",
    });
  }
  return items;
}

async function fetchViaXml(): Promise<NewsItem[] | null> {
  try {
    const res = await fetch(FF_XML, {
      next: { revalidate: 0 },
      headers: { "User-Agent": "TNVGold-Web/1.0" },
    });
    if (!res.ok) return null;
    const xml = await res.text();
    const items = parseXmlEvents(xml);
    return items.length > 0 ? items : null;
  } catch {
    return null;
  }
}

async function fetchViaRss2Json(): Promise<NewsItem[]> {
  const url = `${RSS2JSON_API}?rss_url=${encodeURIComponent(FF_RSS_OLD)}&count=20`;
  const res = await fetch(url, { next: { revalidate: 0 } });
  if (!res.ok) throw new Error(`rss2json returned ${res.status}`);
  const data = await res.json();
  if (!data.items || !Array.isArray(data.items)) return [];
  return data.items.map((item: any) => ({
    title: (item.title || "").replace(/<[^>]*>/g, "").trim(),
    time: item.pubDate || new Date().toISOString(),
    url: item.link || "",
    source: "ForexFactory",
  }));
}

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
    // Thử XML trực tiếp trước (giống bot)
    let items = await fetchViaXml();
    let source = "xml";

    // Fallback: rss2json
    if (!items || items.length === 0) {
      items = await fetchViaRss2Json();
      source = "rss2json";
    }

    if (!items || items.length === 0) {
      return NextResponse.json(
        { success: false, error: "No events from any source" },
        { status: 502 }
      );
    }

    let added = 0;
    for (const item of items.slice(0, 20)) {
      if (!item.title) continue;
      const result = await addNews({
        title: item.title,
        time: item.time,
        url: item.url || "",
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
      total: items.length,
      source,
    });
  } catch (err) {
    return NextResponse.json(
      { success: false, error: "Failed to fetch news", detail: String(err) },
      { status: 500 }
    );
  }
}

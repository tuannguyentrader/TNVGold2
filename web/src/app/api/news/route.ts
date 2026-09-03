import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    // Fetch ForexFactory calendar by proxying through rss2json to bypass CORS
    const res = await fetch(
      "https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Fwww.forexfactory.com%2Fffcal_week_this.xml&count=10",
      { next: { revalidate: 300 } }
    );

    if (!res.ok) {
      return NextResponse.json({ success: false, items: [] }, { status: 502 });
    }

    const json = await res.json();
    const rawItems = (json.items || []).slice(0, 5);

    const items = rawItems.map((item: any) => ({
      title: item.title?.replace(/<[^>]*>/g, "") || "No title",
      source: "ForexFactory",
      time: item.pubDate || "",
      url: item.link || "#",
    }));

    return NextResponse.json({ success: true, items });
  } catch {
    return NextResponse.json({ success: false, items: [] }, { status: 500 });
  }
}

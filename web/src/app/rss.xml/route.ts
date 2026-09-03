// RSS feed cho blog + news
import { listPosts } from "@/lib/blog-store";
import { listNews } from "@/lib/news-store";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://tnvgold.vercel.app";

function escapeXml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export const dynamic = "force-dynamic";

export async function GET() {
  const posts = await listPosts({ limit: 20 });
  const news = await listNews({ limit: 10 });

  const items: string[] = [];

  // Blog posts
  for (const p of posts) {
    const link = `${SITE_URL}/blog/${p.slug}`;
    items.push(`
    <item>
      <title>${escapeXml(p.title.vi)}</title>
      <link>${link}</link>
      <guid>${link}</guid>
      <pubDate>${new Date(p.publishedAt).toUTCString()}</pubDate>
      <description>${escapeXml(p.excerpt.vi)}</description>
      <author>${escapeXml(p.author)}</author>
      <category>${escapeXml(p.type)}</category>
    </item>`);
  }

  // News
  for (const n of news) {
    const link = `${SITE_URL}/tin-tuc/${n.id}`;
    items.push(`
    <item>
      <title>${escapeXml(n.title)}</title>
      <link>${link}</link>
      <guid>${link}</guid>
      <pubDate>${new Date(n.time).toUTCString()}</pubDate>
      <description>${escapeXml(n.title)} - ${n.currency} - ${n.impact} impact</description>
      <category>news</category>
    </item>`);
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>TNV Gold — Blog &amp; Tin tức</title>
    <link>${SITE_URL}</link>
    <description>Phân tích vàng XAUUSD real-time, tin tức kinh tế USD</description>
    <language>vi-VN</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    ${items.join("\n")}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: {
      "Content-Type": "application/rss+xml; charset=utf-8",
    },
  });
}

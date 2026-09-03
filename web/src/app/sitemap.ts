import type { MetadataRoute } from "next";
import { listPosts } from "@/lib/blog-store";
import { listNews } from "@/lib/news-store";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://tnvgold.vercel.app";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();

  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    { url: SITE_URL, lastModified: now, changeFrequency: "daily", priority: 1.0 },
    { url: `${SITE_URL}/goldpulse`, lastModified: now, changeFrequency: "hourly", priority: 0.9 },
    { url: `${SITE_URL}/blog`, lastModified: now, changeFrequency: "hourly", priority: 0.8 },
    { url: `${SITE_URL}/tin-tuc`, lastModified: now, changeFrequency: "hourly", priority: 0.8 },
  ];

  // Blog posts (dynamic)
  let blogPages: MetadataRoute.Sitemap = [];
  try {
    const posts = await listPosts({ limit: 200 });
    blogPages = posts.map((p) => ({
      url: `${SITE_URL}/blog/${p.slug}`,
      lastModified: new Date(p.publishedAt),
      changeFrequency: "weekly" as const,
      priority: 0.7,
    }));
  } catch {
    /* empty */
  }

  // News (dynamic)
  let newsPages: MetadataRoute.Sitemap = [];
  try {
    const news = await listNews({ limit: 100 });
    newsPages = news.map((n) => ({
      url: `${SITE_URL}/tin-tuc/${n.id}`,
      lastModified: new Date(n.fetchedAt),
      changeFrequency: "daily" as const,
      priority: 0.6,
    }));
  } catch {
    /* empty */
  }

  return [...staticPages, ...blogPages, ...newsPages];
}

// News store — lưu tin tức kinh tế USD
import { Redis } from "@upstash/redis";

const redisUrl =
  process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
const redisToken =
  process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;

const redis = redisUrl && redisToken
  ? new Redis({ url: redisUrl, token: redisToken })
  : null;

const KV_KEY_NEWS_INDEX = "tnv:news:index";
const KV_KEY_NEWS = (id: string) => `tnv:news:item:${id}`;
const NEWS_TTL = 7 * 24 * 60 * 60; // 7 ngày

export interface NewsItem {
  id: string;            // hash của title
  title: string;
  time: string;          // ISO time
  url: string;
  source: string;
  impact: "high" | "medium" | "low";
  currency: string;      // USD, EUR...
  forecast?: string;
  previous?: string;
  fetchedAt: number;     // Unix ms
}

const inMemory: Map<string, NewsItem> = new Map();

function detectImpact(title: string): "high" | "medium" | "low" {
  const t = title.toLowerCase();
  if (t.includes("high") || t.match(/nfp|cpi|fomc|interest rate|gdp|non-farm|payrolls/)) {
    return "high";
  }
  if (t.includes("medium")) return "medium";
  return "low";
}

function detectCurrency(title: string): string {
  const t = title.toLowerCase();
  if (t.includes("usd") || t.includes("dollar") || t.includes("fed")) return "USD";
  if (t.includes("eur")) return "EUR";
  if (t.includes("gbp")) return "GBP";
  if (t.includes("jpy")) return "JPY";
  if (t.includes("aud")) return "AUD";
  return "OTHER";
}

function makeId(title: string, time: string): string {
  return Buffer.from(`${title}|${time}`).toString("base64").slice(0, 20).replace(/[+/=]/g, "");
}

export async function listNews(options?: { limit?: number; currency?: string }): Promise<NewsItem[]> {
  const limit = options?.limit ?? 30;

  let items: NewsItem[];
  if (redis) {
    try {
      const ids = (await redis.get<string[]>(KV_KEY_NEWS_INDEX)) || [];
      if (ids.length === 0) {
        items = Array.from(inMemory.values());
      } else {
        const keys = ids.slice(0, 100).map((i) => KV_KEY_NEWS(i));
        const found = await redis.mget<(NewsItem | null)[]>(...keys);
        items = found.filter((n): n is NewsItem => n !== null);
      }
    } catch {
      items = Array.from(inMemory.values());
    }
  } else {
    items = Array.from(inMemory.values());
  }

  if (options?.currency) {
    items = items.filter((n) => n.currency === options.currency);
  }

  // Sort by time desc (newest first)
  items.sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());
  return items.slice(0, limit);
}

export async function addNews(input: { title: string; time: string; url: string; source?: string }): Promise<NewsItem | null> {
  if (!input.title || !input.time) return null;

  const id = makeId(input.title, input.time);
  const item: NewsItem = {
    id,
    title: input.title,
    time: input.time,
    url: input.url || "",
    source: input.source || "ForexFactory",
    impact: detectImpact(input.title),
    currency: detectCurrency(input.title),
    fetchedAt: Date.now(),
  };

  if (redis) {
    try {
      await redis.set(KV_KEY_NEWS(id), item, { ex: NEWS_TTL });
      const index = (await redis.get<string[]>(KV_KEY_NEWS_INDEX)) || [];
      if (!index.includes(id)) {
        index.unshift(id);
        await redis.set(KV_KEY_NEWS_INDEX, index.slice(0, 200), { ex: NEWS_TTL });
      }
      return item;
    } catch {
      inMemory.set(id, item);
      return item;
    }
  }
  inMemory.set(id, item);
  return item;
}

export async function clearOldNews(maxAgeMs: number = 7 * 24 * 60 * 60 * 1000): Promise<void> {
  const cutoff = Date.now() - maxAgeMs;
  const items = await listNews({ limit: 200 });
  for (const item of items) {
    if (item.fetchedAt < cutoff) {
      if (redis) {
        try {
          await redis.del(KV_KEY_NEWS(item.id));
        } catch {
          /* ignore */
        }
      }
      inMemory.delete(item.id);
    }
  }
  // Rebuild index
  if (redis) {
    try {
      const remaining = (await listNews({ limit: 200 })).map((i) => i.id);
      await redis.set(KV_KEY_NEWS_INDEX, remaining, { ex: NEWS_TTL });
    } catch {
      /* ignore */
    }
  }
}

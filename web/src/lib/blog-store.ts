// Blog store — lưu trữ bài viết vào Upstash Redis
import { Redis } from "@upstash/redis";

const redisUrl =
  process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
const redisToken =
  process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;

const redis = redisUrl && redisToken
  ? new Redis({ url: redisUrl, token: redisToken })
  : null;

const KV_KEY_INDEX = "tnv:blog:index";          // danh sách slug (mảng)
const KV_KEY_POST = (slug: string) => `tnv:blog:post:${slug}`;
const HISTORY_TTL = 90 * 24 * 60 * 60;          // 90 ngày

export interface BlogPost {
  slug: string;
  title: { vi: string; en: string };
  excerpt: { vi: string; en: string };
  contentMd: { vi: string; en: string };
  tags: string[];
  type: "analysis" | "news" | "tutorial";
  author: string;
  publishedAt: number;     // Unix ms
  lang: "vi" | "en";       // primary language
  relatedSnapshot?: {
    symbol: string;
    price: number;
    bias: "LONG" | "SHORT" | "NEUTRAL";
    score: number;
  };
}

const inMemory: Map<string, BlogPost> = new Map();

// Seed 2 bài mẫu nếu store rỗng (chỉ lần đầu)
function seedIfEmpty() {
  if (inMemory.size > 0) return;
  const now = Date.now();
  inMemory.set("welcome", {
    slug: "welcome",
    title: { vi: "Chào mừng đến với TNV Gold", en: "Welcome to TNV Gold" },
    excerpt: {
      vi: "Giới thiệu về TNV Gold Pulse và cách sử dụng dashboard phân tích vàng XAUUSD real-time.",
      en: "Introduction to TNV Gold Pulse and how to use the real-time XAUUSD analysis dashboard.",
    },
    contentMd: {
      vi: `## Chào mừng đến với TNV Gold

**TNV Gold Pulse** là dashboard phân tích vàng **XAUUSD** real-time bằng AI.

### Tính năng chính

- **Bias Real-Time** — Long/Short/Neutral cập nhật mỗi 10 giây
- **Multi-Timeframe** — M5, M15, M30, H1 đồng thời
- **Quality Score 0-10** — chấm điểm chất lượng tín hiệu
- **AI Analysis** — giải thích tín hiệu bằng tiếng Việt

### Cách sử dụng

1. Mở [Dashboard](/goldpulse)
2. Theo dõi bias hiện tại
3. Đọc phân tích AI
4. Quyết định vào lệnh

⚠️ *Đây là công cụ hỗ trợ, không phải lời khuyên đầu tư.*`,
      en: `## Welcome to TNV Gold

**TNV Gold Pulse** is a real-time AI-powered dashboard for **XAUUSD** gold analysis.

### Key Features

- **Real-Time Bias** — Long/Short/Neutral updated every 10 seconds
- **Multi-Timeframe** — M5, M15, M30, H1 simultaneously
- **Quality Score 0-10** — signal quality scoring
- **AI Analysis** — plain-language signal explanations

### How to use

1. Open [Dashboard](/goldpulse)
2. Follow the current bias
3. Read the AI analysis
4. Make your trading decision

⚠️ *This is a tool, not investment advice.*`,
    },
    tags: ["intro", "guide"],
    type: "tutorial",
    author: "TNV",
    publishedAt: now,
    lang: "vi",
  });
  inMemory.set("xau-analysis-2026-09", {
    slug: "xau-analysis-2026-09",
    title: { vi: "Phân tích XAUUSD tháng 9/2026", en: "XAUUSD Analysis September 2026" },
    excerpt: {
      vi: "Tổng quan thị trường vàng tháng 9/2026: xu hướng tăng, các mốc quan trọng cần theo dõi.",
      en: "Gold market overview September 2026: bullish trend, key levels to watch.",
    },
    contentMd: {
      vi: `## Phân tích XAUUSD tháng 9/2026

### Bối cảnh thị trường

Vàng đang trong xu hướng **tăng mạnh** trong tháng 9/2026, với nhiều yếu tố hỗ trợ:

- Fed bắt đầu chu kỳ giảm lãi suất
- Căng thẳng địa chính trị gia tăng
- Nhu cầu trú ẩn an toàn tăng cao

### Các mốc quan trọng

- **Kháng cự:** 3,200 / 3,250 USD
- **Hỗ trợ:** 3,050 / 2,980 USD

### Tín hiệu kỹ thuật

| Timeframe | Bias | Score |
|-----------|------|-------|
| M5 | LONG | 7 |
| M15 | LONG | 8 |
| H1 | LONG | 6 |

### Khuyến nghị

Ưu tiên canh **LONG** ở các vùng hỗ trợ, SL dưới 2,950.

⚠️ *Quản lý vốn chặt chẽ, không all-in.*`,
      en: `## XAUUSD Analysis September 2026

### Market Context

Gold is in a **strong uptrend** in September 2026, with multiple supporting factors:

- Fed starting rate cut cycle
- Rising geopolitical tensions
- Increased safe-haven demand

### Key Levels

- **Resistance:** 3,200 / 3,250 USD
- **Support:** 3,050 / 2,980 USD

### Technical Signals

| Timeframe | Bias | Score |
|-----------|------|-------|
| M5 | LONG | 7 |
| M15 | LONG | 8 |
| H1 | LONG | 6 |

### Recommendation

Prioritize **LONG** entries at support zones, SL below 2,950.

⚠️ *Manage risk carefully, never all-in.*`,
    },
    tags: ["analysis", "monthly"],
    type: "analysis",
    author: "TNV AI",
    publishedAt: now - 86400000,
    lang: "vi",
  });
}

export async function listPosts(options?: { limit?: number; type?: string }): Promise<BlogPost[]> {
  seedIfEmpty();
  const limit = options?.limit ?? 50;

  let posts: BlogPost[];
  if (redis) {
    try {
      const slugs = (await redis.get<string[]>(KV_KEY_INDEX)) || [];
      if (slugs.length === 0) {
        // Fallback: load from in-memory seeds
        posts = Array.from(inMemory.values());
      } else {
        const keys = slugs.map((s) => KV_KEY_POST(s));
        const found = await redis.mget<(BlogPost | null)[]>(...keys);
        posts = found.filter((p): p is BlogPost => p !== null);
      }
    } catch {
      posts = Array.from(inMemory.values());
    }
  } else {
    posts = Array.from(inMemory.values());
  }

  // Filter by type
  if (options?.type) {
    posts = posts.filter((p) => p.type === options.type);
  }

  // Sort newest first
  posts.sort((a, b) => b.publishedAt - a.publishedAt);

  return posts.slice(0, limit);
}

export async function getPost(slug: string): Promise<BlogPost | null> {
  seedIfEmpty();

  if (redis) {
    try {
      const post = await redis.get<BlogPost>(KV_KEY_POST(slug));
      if (post) return post;
    } catch {
      // fall through to in-memory
    }
  }
  return inMemory.get(slug) || null;
}

export async function createPost(post: BlogPost): Promise<void> {
  if (redis) {
    try {
      await redis.set(KV_KEY_POST(post.slug), post, { ex: HISTORY_TTL });
      const index = (await redis.get<string[]>(KV_KEY_INDEX)) || [];
      if (!index.includes(post.slug)) {
        index.unshift(post.slug);
        await redis.set(KV_KEY_INDEX, index.slice(0, 200), { ex: HISTORY_TTL });
      }
      return;
    } catch {
      // fall through
    }
  }
  inMemory.set(post.slug, post);
}

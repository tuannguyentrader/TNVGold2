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

// KHÔNG còn bài mẫu hardcode.
// Trước đây store tự "seed" 2 bài demo (welcome + phân tích 9/2026) khi index
// rỗng. Chúng chứa DỮ LIỆU GIẢ (kháng cự 3.200 USD trong khi vàng đang ~4.400,
// nhận định thị trường bịa) → không được phép xuất hiện trên blog công khai.
// Blog chỉ hiển thị bài THẬT từ Redis (bài tự động + bài admin đăng); chưa có
// bài nào thì trang hiện trạng thái trống trung thực.

export async function listPosts(options?: { limit?: number; type?: string }): Promise<BlogPost[]> {
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

/**
 * Timestamp (ms) của bài pulse tự động GẦN NHẤT, hoặc 0 nếu chưa có.
 * Rẻ hơn listPosts: chỉ đọc index (mảng slug đã unshift mới-nhất-trước)
 * và fetch tối đa 5 key gần đầu.
 */
export async function getLatestPulsePostAt(): Promise<number> {
  if (!redis) return 0;
  try {
    const slugs = (await redis.get<string[]>(KV_KEY_INDEX)) || [];
    const pulseSlugs = slugs.filter((s) => s.startsWith("xau-pulse-")).slice(0, 5);
    if (pulseSlugs.length === 0) return 0;
    const keys = pulseSlugs.map((s) => KV_KEY_POST(s));
    const found = await redis.mget<(BlogPost | null)[]>(...keys);
    const times = found
      .filter((p): p is BlogPost => !!p && typeof p.publishedAt === "number")
      .map((p) => p.publishedAt);
    return times.length ? Math.max(...times) : 0;
  } catch {
    return 0;
  }
}

export async function getPost(slug: string): Promise<BlogPost | null> {

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

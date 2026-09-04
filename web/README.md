# 🏆 TNV Gold — Marketing Web + Auto-Publish

Trang web marketing/landing + blog tự động cho TNV Gold. Tự động đăng bài phân tích XAUUSD hàng giờ, tổng hợp tin tức kinh tế USD, SEO đầy đủ (sitemap, RSS, JSON-LD, OG).

> **Dự án liên quan:** [TNVGold Telegram Bot](../TNVGold%20Telegram/) — bot Python gửi tín hiệu tự động, quản lý user Free/Pro.

---

## ⚡ Tính năng

- **Landing page** đầy đủ 7 sections (Hero, Features, Pricing, FAQ, CTA, Footer) với i18n VI/EN
- **Blog tự động** — Cron mỗi giờ tạo bài phân tích XAUUSD từ pulse snapshot
- **Tin tức kinh tế** — Cron 30 phút fetch từ ForexFactory, tự lọc USD High Impact
- **SEO đầy đủ**: sitemap.xml động, robots.txt, Open Graph image, JSON-LD Article, RSS feed
- **Dashboard `/goldpulse`** — real-time pulse từ Upstash Redis (Telegram bot ghi mỗi 5 phút)

---

## 🚀 Tech Stack

- **Framework**: Next.js 16 (App Router, React 19, TypeScript)
- **Styling**: Tailwind CSS v4 + Custom Dark Theme (gold #f5c542, dark #05060a)
- **Data**: Upstash Redis (serverless REST)
- **AI rendering**: react-markdown 10.x
- **OG Image**: Edge runtime `next/og`
- **Deployment**: Vercel Cloud Serverless
- **Cron**: Vercel Cron (Hobby) hoặc cron-job.org (free, recommended)

---

## 🛠️ Local Development

```bash
# Install dependencies
pnpm install

# Start local dev server
pnpm run dev

# Type check only
pnpm run typecheck

# Full validation (lint + typecheck + build)
pnpm run check
```

Mở [http://localhost:3000](http://localhost:3000).

---

## 🌐 Routes

| Route | Mô tả |
|---|---|
| `/` | Landing page (Hero, Features, Pricing, FAQ, Footer) |
| `/goldpulse` | Dashboard real-time pulse |
| `/blog` | Danh sách bài viết phân tích |
| `/blog/[slug]` | Chi tiết bài viết (markdown render) |
| `/tin-tuc` | Tin tức kinh tế USD |
| `/tin-tuc/[id]` | Chi tiết tin tức |
| `/sitemap.xml` | Sitemap (động) |
| `/rss.xml` | RSS feed (blog + news) |
| `/robots.txt` | Robots |

---

## 📡 API Endpoints

| Endpoint | Method | Mục đích | Auth |
|---|---|---|---|
| `/api/health` | GET | Health check | — |
| `/api/pulse` | GET | Lấy pulse hiện tại (từ Redis) | — |
| `/api/news` | GET | ForexFactory proxy (rss2json) | — |
| `/api/news/store` | GET | News từ Redis store | — |
| `/api/posts` | GET | List blog posts | — |
| `/api/posts` | POST | Tạo post (admin/cron) | Bearer |
| `/api/posts/[slug]` | GET | Detail post | — |
| `/api/og` | GET | OG image 1200x630 | — |
| `/api/cron/blog-generate` | GET | Auto blog (mỗi giờ) | Cron / Bearer |
| `/api/cron/news-fetch` | GET | Auto news (mỗi 30 min) | Cron / Bearer |

---

## 🔐 Environment Variables (Vercel)

```bash
# Redis (Upstash)
KV_REST_API_URL=https://xxx.upstash.io
KV_REST_API_TOKEN=xxx

# Auth (dùng cho POST + cron)
TNV_SECRET_KEY=your-random-secret-key

# Site URL (cho canonical, OG, sitemap)
NEXT_PUBLIC_SITE_URL=https://tnvgold.vercel.app
```

---

## 🚀 Triển khai lên Vercel

### 1. Kết nối repo
- Vào https://vercel.com/new
- Import `tuannguyentrader/TNVGold`
- Framework: Next.js (tự nhận)
- Build: `pnpm run build`

### 2. Cấu hình env vars
Trong Vercel Dashboard → Project → Settings → Environment Variables, thêm:
- `KV_REST_API_URL`
- `KV_REST_API_TOKEN`
- `TNV_SECRET_KEY`
- `NEXT_PUBLIC_SITE_URL`

### 3. Cron Jobs
**Vercel Hobby plan** giới hạn cron (max 2 jobs, mỗi job tối thiểu 1 lần/ngày).

Khuyến nghị: dùng **cron-job.org** (miễn phí) cho cron chi tiết:
- Blog: `https://tnvgold.vercel.app/api/cron/blog-generate` — mỗi giờ
- News: `https://tnvgold.vercel.app/api/cron/news-fetch` — mỗi 30 phút

Chi tiết xem [docs/operations/CRON_SETUP.md](docs/operations/CRON_SETUP.md).

### 4. Uptime monitor
- Đăng ký https://uptimerobot.com
- Monitor `https://tnvgold.vercel.app/api/health`, interval 5 phút

### 5. SEO submit
- Vào https://search.google.com/search-console
- Verify domain, submit `sitemap.xml`

---

## 📂 Cấu trúc dự án

```
src/
├── app/
│   ├── api/
│   │   ├── health/route.ts
│   │   ├── news/{route.ts, store/route.ts}
│   │   ├── pulse/{route.ts, clear/route.ts}
│   │   ├── posts/{route.ts, [slug]/route.ts}
│   │   ├── cron/{blog-generate, news-fetch}/route.ts
│   │   └── og/route.tsx
│   ├── blog/{page.tsx, [slug]/page.tsx, *-client.tsx}
│   ├── tin-tuc/{page.tsx, [id]/page.tsx, *-client.tsx}
│   ├── rss.xml/route.ts
│   ├── sitemap.ts
│   ├── robots.ts
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── landing/         # 9 file component
│   └── sites/...        # Dashboard
├── lib/
│   ├── blog-store.ts
│   ├── blog-helpers.ts
│   ├── news-store.ts
│   ├── pulse-store.ts
│   ├── language-context.tsx
│   ├── live-pulse-context.tsx
│   └── ...
└── types/market.ts
```

---

## 📡 Data Source

Dashboard `/goldpulse` lấy data từ **Upstash Redis**, được ghi bởi **Telegram bot Python** (chạy trên VPS, scheduler 5 phút/lần). Bot đọc candles từ MT5 local, phân tích bằng `analyze_tnv()`, ghi lên key `tnv:current_pulse` (TTL 60s).

Cấu hình bot:
- Copy `telegram-bot/redis_writer.py` + `telegram-bot/scheduler.py` (đã sửa) lên VPS
- Set env: `KV_REST_API_URL`, `KV_REST_API_TOKEN` (cùng với Vercel)
- Bot tự ghi pulse mỗi 5 phút → Web tự hiển thị

Xem chi tiết tại: `telegram-bot/SETUP_VPS.md`

---

## 📄 License

Proprietary © 2026 TNV Gold. All rights reserved.

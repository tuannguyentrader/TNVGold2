# 🚀 Setup Cron + SEO — Hướng dẫn Vận hành

> Sau khi deploy lên Vercel, làm theo các bước dưới đây để tự động hóa cron và submit SEO.

---

## 1. Cron Jobs (chạy tự động)

### Vercel Cron (tự động từ `vercel.json`)

Vercel tự đọc `vercel.json` ở root repo. Không cần config gì thêm.

**Hạn chế Hobby plan:**
- Tối đa 2 cron jobs
- Mỗi job chạy **1 lần/ngày tối thiểu** (không phải hourly)

Nếu cần chạy hourly → cần Vercel Pro ($20/tháng) HOẶC dùng cron-job.org.

### Cron-job.org (MIỄN PHÍ, khuyến nghị)

Vào https://cron-job.org → đăng ký tài khoản → tạo 2 jobs:

#### Job 1: Auto blog (mỗi giờ)
- **URL:** `https://tnvgold.vercel.app/api/cron/blog-generate`
- **Schedule:** `0 * * * *` (mỗi giờ, phút 0)
- **Headers:** Không cần (Vercel tự nhận diện từ User-Agent)
- **Method:** GET

#### Job 2: Auto news (mỗi 30 phút)
- **URL:** `https://tnvgold.vercel.app/api/cron/news-fetch`
- **Schedule:** `*/30 * * * *` (phút 0 và 30)
- **Method:** GET

#### Test thủ công
```bash
curl https://tnvgold.vercel.app/api/cron/blog-generate
curl https://tnvgold.vercel.app/api/cron/news-fetch
```

Sau khi chạy:
- Vào `/blog` → sẽ thấy bài mới "XAUUSD Pulse — YYYY-MM-DD HH"
- Vào `/tin-tuc` → sẽ thấy tin USD mới

---

## 2. Google Search Console

### Bước 1: Verify domain

1. Vào https://search.google.com/search-console
2. Click **Add Property** → chọn **URL prefix**
3. Nhập `https://tnvgold.vercel.app`
4. Verify bằng **HTML tag** (Vercel hỗ trợ):
   - Copy meta tag
   - Vào Vercel Dashboard → Project → Settings → Environment Variables
   - Thêm `NEXT_PUBLIC_GOOGLE_VERIFY` = meta content
   - Hoặc edit `src/app/layout.tsx` thêm:
     ```tsx
     verification: { google: "your-verify-code" }
     ```

### Bước 2: Submit sitemap

1. Vào Search Console → Sitemaps
2. Nhập `sitemap.xml` → Submit
3. Đợi 1-3 ngày Google crawl

### Bước 3: Request indexing cho từng URL quan trọng

- `/` (landing)
- `/blog/welcome`
- `/blog/xau-analysis-2026-09`

---

## 3. Uptime Monitoring

### UptimeRobot (miễn phí)

1. Vào https://uptimerobot.com → đăng ký
2. Add New Monitor:
   - **Type:** HTTP(s)
   - **URL:** `https://tnvgold.vercel.app/api/health`
   - **Interval:** 5 minutes
3. Add Alert Contacts (email)

Khi web down → email cảnh báo ngay.

---

## 4. Google Analytics (optional)

Thêm vào `src/app/layout.tsx`:
```tsx
{/* Google Analytics */}
<Script
  src={`https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GA_ID}`}
  strategy="afterInteractive"
/>
<Script id="ga-init" strategy="afterInteractive">
  {`window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', '${process.env.NEXT_PUBLIC_GA_ID}');`}
</Script>
```

Vercel env: `NEXT_PUBLIC_GA_ID` = `G-XXXXXXXXXX`

---

## 5. Backup dữ liệu (optional)

Upstash Redis có sẵn **Daily Backup** trong dashboard. Bật:
1. Vào https://console.upstash.com → chọn Redis database
2. Settings → Daily Backup → Enable

Backup giữ 7 ngày, có thể restore.

---

## 6. Checklist triển khai

- [ ] Vercel deploy thành công
- [ ] Env vars đầy đủ: `KV_REST_API_URL`, `KV_REST_API_TOKEN`, `TNV_SECRET_KEY`, `NEXT_PUBLIC_SITE_URL`
- [ ] Test 5 trang: `/`, `/goldpulse`, `/blog`, `/tin-tuc`, `/api/health`
- [ ] Cấu hình cron-job.org (nếu Hobby plan)
- [ ] Submit sitemap.xml lên Google Search Console
- [ ] Setup UptimeRobot monitor `/api/health`
- [ ] (Optional) Google Analytics
- [ ] (Optional) Telegram bot test thử `/blog-generate` để verify cron

---

## 7. Endpoints tổng hợp

| Endpoint | Method | Mục đích | Auth |
|---|---|---|---|
| `/api/health` | GET | Health check | — |
| `/api/pulse` | GET | Lấy pulse hiện tại | — |
| `/api/pulse` | POST | Ghi pulse (từ EA) | Bearer |
| `/api/pulse/clear` | POST | Xoá pulse | Bearer |
| `/api/news` | GET | ForexFactory proxy | — |
| `/api/news/store` | GET | News từ store | — |
| `/api/posts` | GET | List blog posts | — |
| `/api/posts` | POST | Tạo post (admin/cron) | Bearer |
| `/api/posts/[slug]` | GET | Detail post | — |
| `/api/og` | GET | OG image 1200x630 | — |
| `/api/cron/blog-generate` | GET | Auto blog (mỗi giờ) | Cron header / Bearer |
| `/api/cron/news-fetch` | GET | Auto news (mỗi 30 min) | Cron header / Bearer |
| `/sitemap.xml` | GET | Sitemap | — |
| `/robots.txt` | GET | Robots | — |
| `/rss.xml` | GET | RSS feed | — |

# T1 — Phân tích kỹ thuật web Next.js TNVGold (web-analyzer)

Phạm vi: toàn bộ `src/` của dự án `/Users/apple/Documents/dsh/TNVGold`.
Kiểm chứng: `tsc --noEmit` → **PASS** (strict). `eslint src` → **FAIL** (5 errors, 3 warnings).

---

## 1. Kiến trúc hiện tại

**Entry / Layout**
- `src/app/layout.tsx` — RootLayout, metadata + viewport, nạp Google Fonts bằng `<link>`, inject script chặn lỗi extension.
- `src/app/page.tsx` và `src/app/goldpulse/page.tsx` — **cùng render** `TNVGoldPulseApp` tại 2 URL riêng biệt.

**App client (bộ khung)**
- `src/components/sites/tnv-goldpulse/TNVGoldPulseApp.tsx` — wrapper `"use client"`:
  `LanguageProvider > LivePulseProvider > main` chứa 14 section–component:
  DisclaimerBanner, HeroHeader, ProUpgradeBar, ActionBanner, LiveMetricsGrid (6 MetricCard), AnalysisSummary, SponsorCard, LiveGoldPriceChart, TechnicalGrid (6 TechCard), ChartSection, HistoryTable, SiteFooter, SubscribeBar.

**Contexts (React)**
- `src/lib/language-context.tsx` — `LanguageProvider` (`vi`/`en`), bảng `translations` lớn (>200 key), persist `tnv_lang` vào `localStorage` trong `useEffect`.
- `src/lib/live-pulse-context.tsx` — `LivePulseProvider` poll `GET /api/pulse` mỗi 10s (`cache:"no-store"`), giữ `pulse`, `history`, `isLiveConnected`, `lastUpdated`. Chỉ cập nhật khi `data.price > 0`.

**Lib / Store**
- `src/lib/pulse-store.ts` — client Upstash Redis (env `KV_REST_API_URL|UPSTASH_REDIS_REST_URL` + token). `getLatestPulse/getPulseHistory/updatePulse`. Mode chờ: fallback `localCache` trong bộ nhớ (mất dữ liệu khi serverless sleep). Khóa `tnv:current_pulse`, `tnv:pulse_history` (cap 15).
- `src/lib/tnv-engine.ts` — engine "chấm điểm chất lượng" (Wilder vol, HTF, quality score 0–10). **KHÔNG được import ở đâu**.
- `src/lib/tnv-turtle-engine.ts` — chỉ `export * from "./tnv-engine"` (re-export thừa).
- `src/lib/utils.ts` — `cn()` (chỉ dùng bởi `ui/button.tsx`, vốn không dùng).

**API routes**
- `GET /api/pulse` (`force-dynamic`) — trả `{success,data,history,serverTime}`.
- `POST /api/pulse` — nhận payload từ EA/MT5, merge với snapshot hiện tại, ghi Redis. Auth là **tuỳ chọn**.
- `POST /api/pulse/clear` — xoá 2 khoá Redis.
- `GET /api/news` — proxy ForexFactory qua `rss2json`, trả 5 mục.

**Data-flow (MT5 → UI)**
```
EA MT5 (docs/TNV_WebBridge_EA.mq5) --POST /api/pulse--> Upstash Redis
                       ^ auth tuỳ chọn + payload merge
UI: LivePulseProvider --GET /api/pulse (poll 10s)--> context --> 14 component
```

**Styling / i18n / types**
- Tailwind v4 + `globals.css` (651 dòng) gồm toàn bộ hệ class `qx-*` legacy (design system cũ) song song với Tailwind inline trong component.
- i18n qua context `vi`/`en`.
- `src/types/market.ts` — định nghĩa `MarketBias = "BULLISH"|"BEARISH"|"NEUTRAL"`, `MetricCardData`, `HistoryRecord`, `ChartDataPoint`… **KHÔNG được import**; enum bias **khác** với `LONG|SHORT|NEUTRAL` của `pulse-store`.

---

## 2. Điểm mạnh

- Tách bạch rõ: context (state) / store (persistence) / page composition, không monolith.
- `strict: true`, `tsc --noEmit` pass, dùng `??`/type an toàn ở nhiều chỗ, có default snapshot trung tính.
- Bilingual xuyên suốt qua context; gần như không hardcode text hiển thị (trừ vài label inline như "PULSE", "ENTRY", "Status").
- Upstash Redis qua REST (phù hợp serverless), tương thích cả Vercel KV.
- Có chạm tới a11y: flip bằng bàn phím (Enter/Space), ARIA `progressbar`/`meter`, focus-visible.
- Components tách nhỏ, mỗi metric/modal là 1 file riêng.

---

## 3. Điểm yếu (kèm file/dòng tham chiếu) — xếp theo tác động

### MỨC CAO (bảo mật / dữ liệu / tính trung thực sản phẩm)

- **C1 — Auth POST `/api/pulse` là tuỳ chọn + secret mặc định nằm trong source.**
  `src/app/api/pulse/route.ts:20-29`: `const secretKey = process.env.TNV_SECRET_KEY || "**REDACTED**"`; check `if (authHeader && authHeader !== ...)` — nếu gọi không kèm header thì **không cần auth**. Bất kỳ ai cũng có thể `POST` ghi đè giá vàng live. Secret mặc định lộ trong git.
  → **Bắt buộc** 401 nếu thiếu/sai token; bỏ giá trị fallback hardcode; dùng HMAC + rate-limit theo IP; validate payload & allowlist field.

- **C2 — Merge `||` làm mất giá trị hợp lệ bằng 0 và ghi đè cả cụm con.**
  `src/app/api/pulse/route.ts:53-81` dùng `payload.score || current.score`, `payload.volatility || current.volatility`, `payload.exit || current.exit`, `payload.entry?.high || current.entry.high`, `payload.spread || current.spread`, `payload.multiTf?.m15 || current.multiTf.m15`. Khi EA gửi `0` (hợp lệ) hoặc chỉ cập nhật một phần, giá trị bị bỏ qua/giữ lại, và `multiTf` bị thay cả object → mất trường.
  → dùng nullish `??` (bỏ qua chỉ khi `null/undefined`), merge `multiTf`/`entry` sâu từng trường, có schema runtime (zod).

- **C3 — Tính năng "trả phí"/"thông báo" là giả (chỉ state cục bộ, không backend).**
  - `NotificationModal.tsx` (toàn bộ): subscribe email, kết nối Telegram, push notification bật/tắt, smart alerts… đều chỉ `setState` + `setTimeout`, không gọi API, không persist, không gửi gì thật.
  - `ProUpgradeBar.tsx:91-94`: nút "Get TNV PRO Now" → `alert("Redirecting to secure checkout...")`.
  - `HeroHeader.tsx:58-67` "Manage" (API key/token MT5): chỉ `setKeySaved` rồi đóng, không lưu/không dùng.
  - `SiteFooter.tsx:36-79`: Terms/Privacy/Refund đều `alert()`.
  - Mâu thuẫn trải nghiệm: `ProUpgradeBar.tsx:31` hứa "1-second live stream", README hứa "zero latency"/"1s", nhưng app poll 10s và không có kênh realtime.
  → cần thống nhất: hoặc hiện thực backend thật, hoặc gỡ/gắn nhãn "coming soon" để không gây hiểu lầm; không dùng `alert()`.

- **C4 — `/api/news` phụ thuộc bên thứ ba, `any`, cấu hình mâu thuẫn.**
  `src/app/api/news/route.ts:3` `dynamic="force-dynamic"` **và** `:10` `next:{revalidate:300}` (xung đột); `:20` `map((item:any)=>...)`; không timeout/fallback; proxy `rss2json` (rate-limit free tier) → trả 502/500.
  → gọi thẳng feed với ISR đúng, type mục tin, cache mặc định + fallback last-known, bỏ `any`, thêm timeout & retry.

### MỨC TRUNG BÌNH (bảo trì / hiệu năng / nhất quán)

- **C5 — `npm run lint` / `npm run check` FAIL.** `eslint src`: 5 errors + 3 warnings:
  - `react-hooks/set-state-in-effect` ×3: `src/lib/live-pulse-context.tsx:67`, `src/lib/language-context.tsx:364`, `src/components/sites/tnv-goldpulse/HeroHeader.tsx:28`.
  - `@typescript-eslint/no-explicit-any` ×2: `src/app/api/news/route.ts:20`, `src/components/sites/tnv-goldpulse/SponsorCard.tsx:39`.
  - `no-unused-vars` ×2: `src/components/sites/tnv-goldpulse/AnalysisSummary.tsx:44,48` (`dirAdj`, `alignment`).
  - `@next/next/no-page-custom-font`: `src/app/layout.tsx:36`.
  → `npm run check` (lint && typecheck && build) không thể xanh.

- **C6 — Poll 10s re-render toàn cây; không dedup/không chống race/không trạng thái lỗi.**
  `src/lib/live-pulse-context.tsx` mỗi `setPulse/setHistory` thay object mới → mọi consumer re-render; `fetchLivePulse` set state cả khi dữ liệu không đổi; không bảo vệ phản hồi đến trễ ghi đè bản mới (race); `isLiveConnected` **không bao giờ** chuyển `false` khi API fail → badge "LIVE" luôn sáng; không UI loading/error.
  → dùng SWR/React Query (polling + dedup + stale-if-error), so sánh bằng để tránh render thừa, biến `isLiveConnected=false` khi lỗi, thêm indicator offline.

- **C7 — Nhiều mã chết / thừa / không nhất quán.**
  - `src/components/*.tsx` — 21 file re-export 1 dòng trỏ về `sites/tnv-goldpulse/`, **không được import ở đâu** (chỉ `app/page.tsx`, `app/goldpulse/page.tsx` import từ `sites/tnv-goldpulse`) → shim thừa.
  - `src/components/ui/button.tsx` + `src/lib/utils.ts` — không dùng.
  - `src/types/market.ts` — không dùng, và enum bias (`BULLISH/BEARISH`) **lệch** với `LONG/SHORT` của `pulse-store` (`src/lib/pulse-store.ts:16-37`) → nguy cơ drift.
  - `src/lib/tnv-engine.ts` + `tnv-turtle-engine.ts` (re-export) — orphan; **điểm chất lượng `score` đến thẳng từ MT5**, engine không được gọi (server/client). Nếu không dùng → xoá.
  → dọn shim, reconcile type enum, quyết định dùng hay bỏ engine.

- **C8 — Trùng nội dung 2 URL + SEO/i18n thiếu.**
  `src/app/page.tsx` và `src/app/goldpulse/page.tsx` cùng metadata, không canonical/redirect → duplicate SEO. `layout.tsx:32` `<html lang="en">` hardcode dù giao diện song ngữ (a11y/SEO lệch khi chọn vi). Thiếu `sitemap.xml`, `robots.txt`, OG/twitter meta, JSON-LD.
  → 1 canonical route + redirect, `lang` động theo context (hoặc 2 thẻ html), bổ sung metadata SEO.

- **C9 — CSS legacy phình to.**
  `src/app/globals.css` (651 dòng) chứa cả design system `qx-*` cũ (`.qx-card`, `.qx-range-*`, `.qx-flip-*`…) không còn dùng (component đã viết lại bằng Tailwind inline — chỉ còn `ConfidenceBar.tsx` dùng `.qx-bar-*`, `RsiRangeBar.tsx` dùng `.qx-range-*`). → bundle CSS lớn, khó bảo trì.
  → purge class không dùng, chỉ giữ `.qx-bar-*`/`.qx-range-*` cần thiết (hoặc thay bằng Tailwind), nạp font bằng `next/font` (sửa warning C5).

- **C10 — `next.config.ts` trống, không hardening.**
  `src/next.config.ts` không có `headers` (CSP / X-Frame-Options / Referrer-Policy / Permissions-Policy), không `images.remotePatterns`, không `output:"standalone"`; các iframe TradingView (`s.tradingview.com`) trong `ChartSection.tsx:24` & `LiveGoldPriceChart.tsx:31` load không kiểm soát.
  → thêm security headers, sandbox/allowlist iframe, cấu hình images, cân nhắc standalone.

### MỨC THẤP (đúng đắn / UX nhỏ)

- **C11 — Thang điểm không nhất quán.** `score` trong `pulse-store.ts` là 0–10 (docstring `"score (0-10)"`), nhưng UI nhân 10 (`score*10`) hiển thị và threshold màu dùng `score>=8` (LiveMetricsGrid.tsx:91, HistoryTable.tsx:109) trong khi gauge dùng `*10`. Translation `scoreStatus:"8 / 10"`. → chọn 1 thang và chuẩn hoá cả hiển thị lẫn ngưỡng.
- **C12 — Đếm lịch sử không đồng bộ.** `pulse-store.ts:140` lưu 15; `getPulseHistory()` trả max 10 (`:116`); UI header `HistoryTable` hiển thị count theo `filtered.length`; trước đó text "Last 7 snapshots" (`language-context.tsx:219,328`). → thống nhất 1 con số.
- **C13 — Session logic.** `HeroHeader.tsx:8-15` `getActiveSession()` phân nhánh UTC có chồng lấn (`utcHour>=22 || <7 → Tokyo`; `>=17 && <22 → NY`; `>=8 && <13 → London`; `>=13 && <17 → London & NY Overlap`; còn lại → London Pre-market) → thứ tự/ngưỡng hơi lộn xộn.
- **C14 — `ChartSection.tsx` chưa hiện thực "Session Flow".** Đủ nhãn `tabSession/tabTradingView`, `ctrlPulse/ctrlPrice/ctrlSessions/ctrlEma` trong translation nhưng component chỉ render iframe TradingView, không có tab hay visualisation luồng phiên → tính năng README quảng cáo chưa có.

---

## 4. Đề xuất cải thiện (tác động → hành động)

**Ưu tiên 1 (tác động cao):**
- Bảo mật POST `/api/pulse` (bắt buộc auth, bỏ secret mặc định, HMAC + rate-limit) — C1.
- Sửa merge `||` → `??` + schema runtime cho payload — C2.
- Gỡ/mark "coming soon" các tính năng giả & thay `alert()` — C3; nếu giữ cam kết 1s live thì hiện thực realtime (SSE/WebSocket) hoặc hạ cam kết.
- Sửa `/api/news` (typed, ISR, fallback, bỏ `any`) — C4.

**Ưu tiên 2 (tác động trung bình):**
- For fixed `npm run lint`/`check` xanh (5 errors) — C5.
- Nâng cấp polling → SWR/React Query; dedup, chống race, isLiveConnected=false khi lỗi — C6.
- Dọn mã chết: shim `components/*.tsx`, `ui/button`, `utils`, `types/market.ts`, `tnv-engine` — C7.
- Canonical route `/goldpulse`, `lang` động, thêm sitemap/robots/OG — C8.
- Purge CSS legacy `qx-*`, dùng `next/font` — C9.
- Security headers + cấu hình next.config — C10.

**Ưu tiên 3 (tác động thấp):**
- Chuẩn hoá thang điểm 0–10/0–100 (C11), thống nhất số lịch sử (C12), rà session logic (C13), bổ sung Session Flow thật hoặc gỡ nhãn (C14).

---

## 5. Ghi chú triển khai
- Verification run: `tsc --noEmit` PASS; `eslint src` FAIL (5 errors / 3 warnings) là bằng chứng cho C5.
- Không có `.env*` file trong repo; `.gitignore` chặn `.env*.local`; secret mặc định nằm trong code (C1).
- Không build sản xuất trong phạm vi phân tích; đề xuất chạy `npm run check` sau khi sửa nhóm C5.

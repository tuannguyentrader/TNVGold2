# TNVGold — Báo cáo Cải thiện Toàn diện (Tổng hợp T1 Web + T2 MT5 + T3 UX)

> **Nguồn:** 3 phân tích độc lập (web-analyzer T1, mt5-analyzer T2, ux-reviewer T3) + kiểm chứng `tsc --noEmit` PASS / `eslint src` FAIL.
> **Trạng thái:** CHỈ PHÂN TÍCH — chưa thực thi. Mọi thay đổi chờ **người dùng xác nhận** theo đúng team goal.
> Các mã điểm yếu giữ nguyên ký hiệu gốc (Web `W-*`, MT5 `B/C/D-*`, UX `P*`) để truy vết dễ dàng.

---

## Mục lục
1. [Tóm tắt điều hành](#1-tóm-tắt-điều-hành)
2. [Bức tranh tổng thể & điểm mạnh](#2-bức-tranh-tổng-thể--điểm-mạnh)
3. [Nhóm WEB (Next.js)](#3-nhóm-web-nextjs)
4. [Nhóm MT5 (EA/Indicator)](#4-nhóm-mt5-eaindicator)
5. [Nhóm UX](#5-nhóm-ux)
6. [Vấn đề xuyên nhóm (cross-cutting)](#6-vấn-đề-xuyên-nhóm)
7. [Lộ trình triển khai đề xuất — việc nên làm trước](#7-lộ-trình-triển-khai-đề-xuất--việc-nên-làm-trước)
8. [Phụ lục: bản đồ file](#8-phụ-lục-bản-đồ-file)

---

## 1. Tóm tắt điều hành

Dự án **TNVGold** là dashboard vàng (XAUUSD) theo thời gian thực: EA/Indicator MT5 → webhook `POST /api/pulse` → Upstash Redis → Next.js poll 10s → UI. Về mặt **cơ chế** pipeline hoạt động, nhưng có **3 vấn đề chiến lược** khiến sản phẩm chưa đáp ứng cam kết:

1. **Dữ liệu chỉ báo chiến lược KHÔNG THẬT (MT5).** ADX=32.4 / VWAP=+6.20 là **hằng số cứng** (B1); EMA chạy **ngược chiều** → emaGap≈0 (C1-MT5); ATR không phải Wilder (C3-MT5); RSI kiểu Cutler (C2-MT5); "Quality Score/Pulse" chỉ 4/8 cố định (C4-MT5); nhãn HTF "Pass/Not Against" chỉ dựa trên có bias hay không (C5-MT5). ⇒ Các con số/trạng thái trend, volume flow, đánh giá tín hiệu hiển thị trên dashboard hiện **mang tính trang trí / sai lệch**.
2. **Bảo mật & bền vững dữ liệu (Web + MT5).** Endpoint `POST /api/pulse` **thực chất mở** (bỏ qua check khi thiếu header) và có secret mặc định trong source (W-C1 = B2). EA và web dùng **token mặc định khác nhau** → EA thường bị 401. Chỉ **một key Redis duy nhất** → nhiều symbol ghi đè (C6-MT5), history ghi trùng (B4).
3. **Nhiều tính năng quảng cáo là "giả"/chưa có.** Notification/đăng ký/pro-tokens/alert đều chỉ `setState` + `alert()` (W-C3); cam kết "1-second live stream"/"zero latency" trong khi app poll 10s và EA chỉ gửi mỗi khi đóng nến M5 (~5 phút) (D2-MT5); "Session Flow" tab không tồn tại (W-C14); "phân tích tự động" là template client-side (D7-MT5).

Điểm mạnh nên giữ: tách bạch context/store/composition, strict TS, default snapshot trung tính, Upstash REST serverless-friendly, a11y cơ bản (flip bằng bàn phím, ARIA progressbar/meter), layout tuần tự rõ ràng, responsive có breakpoint, i18n xuyên suốt (nhưng chưa đủ).

---

## 2. Bức tranh tổng thể & điểm mạnh

**Kiến trúc hiện tại**
```
[MT5 Indicator "10s TNV V2" (.ex5 — KHÔNG có source trong repo)]
      │ iCustom + CopyBuffer(buffer 0,1,3,6,7)
      ▼
[TNV_WebBridge_EA.mq5]  tự tính bias/score/RSI/ATR/EMA/Multi-TF/HTF
      │ WebRequest POST → https://tnvgold.vercel.app/api/pulse  (auth tuỳ chọn)
      ▼
[Next.js POST /api/pulse]  JSON.parse → merge (xử lý 0 sai) → updatePulse()
      ▼
[Upstash Redis: tnv:current_pulse + tnv:pulse_history] (1 key duy nhất, cap 15)
      ▼
[GET /api/pulse (force-dynamic)] → LivePulseProvider poll 10s → context
      ▼
[UI 14 section: HeroHeader, ActionBanner, LiveMetricsGrid(6 MetricCard),
 AnalysisSummary, TechnicalGrid(6 TechCard), ChartSection, HistoryTable, ...]
```

**Điểm mạnh (giữ nguyên)**
- Tách `context` (state) / `store` (persistence) / `page` (composition), không monolith; component nhỏ, dễ sửa.
- `strict: true` + `tsc --noEmit` PASS; default snapshot trung tính, defensive.
- Upstash Redis qua REST (serverless-friendly), tương thích Vercel KV.
- A11y nền tảng: flip-card bàn phím, `role=progressbar`/`meter`, focus/aria.
- Layout tuần tự rõ (header→risk→signal→metrics→technical→chart→history→footer→sticky bar), responsive, semantic màu long/short + icon.
- i18n `vi`/`en` xuyên context (chưa đủ, xem P1).

---

## 3. Nhóm WEB (Next.js)

### 3.1 Điểm yếu (kèm ref)

**🔴 Cao**
- **W-C1 — Auth `POST /api/pulse` tuỳ chọn + secret mặc định trong source.** `src/app/api/pulse/route.ts:20-29`: `secretKey = env.TNV_SECRET_KEY || "**REDACTED**"`; `if (authHeader && authHeader !== ...)` → **không gửi header = không cần auth**, ai cũng ghi đè dữ liệu live; secret lộ trong git. *(Đồng nhất với B2-MT5.)*
- **W-C2 — Merge `||` mất giá trị hợp lệ = 0 / ghi đè cả cụm con.** `route.ts:53-81`: `payload.score || current.score`, `.volatility`, `.exit`, `.entry?.high`, `.spread`, `multiTf?.m15`… → EA gửi `0` (hợp lệ) bị bỏ; `multiTf` bị thay cả object.
- **W-C3 — Tính năng trả phí/thông báo "giả".** `NotificationModal.tsx` (subscribe email/Telegram/push/smart-alert: chỉ `setState`+`setTimeout`, không backend); `ProUpgradeBar.tsx:91-94` nút "Get TNV PRO" → `alert("Redirecting...")`; `HeroHeader.tsx:58-67` "Manage/token" chỉ `setKeySaved` rồi đóng; `SiteFooter.tsx:36-79` Terms/Privacy/Refund → `alert()`. *(Chồng với U-P5, D7-MT5.)*
- **W-C4 — `/api/news` phụ thuộc thứ ba + `any` + cấu hình mâu thuẫn.** `src/app/api/news/route.ts:3` `force-dynamic` **và** `:10` `next.revalidate=300` (xung đột); `:20` `item:any`; không timeout/fallback; proxy `rss2json` (free-tier rate-limit) → 502/500.

**🟠 Trung bình**
- **W-C5 — `npm run check` KHÔNG xanh (eslint FAIL).** 5 errors + 3 warnings: `react-hooks/set-state-in-effect` ×3 (`lib/live-pulse-context.tsx:67`, `lib/language-context.tsx:364`, `sites/tnv-goldpulse/HeroHeader.tsx:28`); `no-explicit-any` ×2 (`api/news/route.ts:20`, `SponsorCard.tsx:39`); `no-unused-vars` ×2 (`AnalysisSummary.tsx:44,48`); `no-page-custom-font` (`layout.tsx:36`).
- **W-C6 — Poll 10s re-render toàn cây; không dedup/không chống race/không trạng thái lỗi.** `live-pulse-context.tsx`: mỗi `setPulse/setHistory` thay object mới → mọi consumer render; không so sánh dữ liệu không đổi; không bảo vệ phản hồi đến trễ; `isLiveConnected` **không bao giờ** `false` khi API fail → badge LIVE luôn sáng. *(Chồng U-P3.)*
- **W-C7 — Nhiều mã chết / không nhất quán.** 21 shim `src/components/*.tsx` (re-export 1 dòng về `sites/tnv-goldpulse/`) **không được import**; `components/ui/button.tsx` + `lib/utils.ts` không dùng; `types/market.ts` không dùng và enum bias `BULLISH/BEARISH` **lệch** `LONG/SHORT` của `pulse-store.ts:16-37`; `lib/tnv-engine.ts` + `tnv-turtle-engine.ts` (re-export) orphan — **điểm score đến thẳng từ MT5, engine không được gọi**.
- **W-C8 — Trùng nội dung 2 URL + SEO/i18n.** `app/page.tsx` & `app/goldpulse/page.tsx` cùng metadata, không canonical/redirect; `layout.tsx:32` `<html lang="en">` hardcode; thiếu sitemap/robots/OG/JSON-LD. *(Chồng U-P1.)*
- **W-C9 — CSS legacy phình.** `globals.css` (651 dòng) chứa design system `qx-*` cũ không còn dùng (chỉ `ConfidenceBar` dùng `.qx-bar-*`, `RsiRangeBar` dùng `.qx-range-*`).
- **W-C10 — `next.config.ts` trống, không hardening.** Không security headers (CSP/X-Frame/Referrer/Permissions), không `images.remotePatterns`, không `output:"standalone"`; iframe TradingView (`s.tradingview.com`) load không kiểm soát (`ChartSection.tsx:24`, `LiveGoldPriceChart.tsx:31`).

**🟡 Thấp**
- **W-C11 — Thang điểm không nhất quán.** `score` 0–10 (docstring `pulse-store.ts`) nhưng UI nhân 10 (`score*10`) và ngưỡng màu `score>=8` (`LiveMetricsGrid.tsx:91`, `HistoryTable.tsx:109`) trong khi gauge dùng `*10`.
- **W-C12 — Đếm lịch sử lệch.** Redis lưu 15, `getPulseHistory` trả tối đa 10, text "Last 7 snapshots" (`language-context.tsx:219,328`).
- **W-C13 — Session logic chồng lấn.** `HeroHeader.tsx:8-15` `getActiveSession()` phân nhánh UTC có ngưỡng trùng/khó hiểu.
- **W-C14 — "Session Flow" chưa hiện thực.** Đủ template `tabSession/tabTradingView`, `ctrlPulse/ctrlPrice/ctrlSessions/ctrlEma` nhưng `ChartSection.tsx` chỉ render iframe TradingView, không tab/visualisation.

### 3.2 Đề xuất (Web)
| Mã | Đề xuất | Mô tả / lý do | Tác động | Ưu tiên | Khó khăn |
|---|---|---|---|---|---|
| W-C1 | Bắt buộc auth `POST /api/pulse` | 401 khi thiếu/sai token; bỏ secret mặc định; HMAC + rate-limit theo IP | Bảo mật | Cao | Thấp |
| W-C2 | Đổi `\|\|`→`??` + schema runtime (zod) | Giữ giá trị `0` hợp lệ, merge sâu `multiTf`/`entry`, validate kiểu | Đúng dữ liệu | Cao | Trung bình |
| W-C3 | Dọn/hiện thực tính năng "trả phí" | Hoặc build backend thật, hoặc gắn nhãn "coming soon"; thay `alert()` bằng modal/toast | Trung thực sản phẩm | Cao | Trung bình |
| W-C4 | Sửa `/api/news` | Gọi thẳng feed, typed, ISR đúng, cache mặc định + fallback, bỏ `any`, thêm timeout/retry | Ổn định | Cao | Thấp |
| W-C5 | Fix lint | Sửa 5 lỗi + 3 warning để `npm run check` xanh | CI | Trung bình | Thấp |
| W-C6 | SWR/React Query polling | Dedup, chống race, `isLiveConnected=false` khi lỗi, UI loading/error | Hiệu năng/UX | Trung bình | Trung bình |
| W-C7 | Dọn mã chết | Xoá 21 shim, `ui/button`, `utils`, `types/market.ts`, quyết định dùng/bỏ `tnv-engine`; thống nhất enum bias | Bảo trì | Trung bình | Thấp |
| W-C8 | Canonical + i18n SEO | 1 route canonical `/goldpulse`, `lang` động, thêm sitemap/robots/OG | SEO/a11y | Trung bình | Thấp |
| W-C9 | Purge CSS legacy | Xoá class `qx-*` không dùng, nạp font `next/font` | Bundle | Trung bình | Thấp |
| W-C10 | Hardening next.config | Security headers, sandbox/allowlist iframe, cấu hình images | Bảo mật | Trung bình | Thấp |
| W-C11/12/13 | Chuẩn hoá | Thống nhất thang 0–10/0–100, số lịch sử, session logic | Đúng đắn/UX | Thấp | Thấp |
| W-C14 | Session Flow thật | Triển khai tab + visualisation hoặc gỡ nhãn | Sản phẩm | Thấp | Cao |

---

## 4. Nhóm MT5 (EA/Indicator)

### 4.1 Điểm yếu (kèm ref — `docs/TNV_WebBridge_EA.mq5`)

**🔴 Blocker**
- **B1 — ADX & VWAP là hằng số cứng.** `:188` `"adx":32.4,"vwap":6.20` → badge "Strong Trend"/"Above VWAP/Bullish Flow" **luôn giả**.
- **B2 — Mismatch token + endpoint mở.** EA `InpSecretToken="**REDACTED**"` (`:14`); web mặc định `"**REDACTED**"` (`route.ts:21`) → EA bị 401 nếu không set env; **đồng thời** `route.ts:24` bỏ check khi thiếu header → unauthenticated write. *(Trùng W-C1.)*
- **B3 — Missing source indicator.** EA phụ thuộc `iCustom(...,"10s TNV V2")` nhưng **không có `.mq5`/tài liệu buffer** trong repo → không audit/tái lập, dễ vỡ.
- **B4 — Không idempotency/dedup.** `pulse-store.ts:138-142` `history.unshift()` không chống trùng; `g_last_candle` (`:42-44`) chỉ dedup theo nến M5, không áp dụng giữa nhiều EA/chart.

**🟠 Cao**
- **C1-MT5 — EMA chạy NGƯỢC CHIỀU.** `:133-139` seed tại nến mới `[0]`, đệ quy mới→cũ → `ema9≈ema21≈price`, `emaGap≈0` vô nghĩa.
- **C2-MT5 — RSI kiểu Cutler, không Wilder.** `:117-125` tổng gains/losses tuyệt đối, chỉ dựa Close → lệch `iRSI`.
- **C3-MT5 — "ATR" là TR trung bình cộng, không Wilder.** `:113,128` → khác `iATR`/`computeWilderVolatility`.
- **C4-MT5 — Quality Score chỉ 4/8 cố định.** `:84-96` không dùng `tnv-engine.calculateQualityScore`; `m15s/m30s/h1s` = 8/7/9 cứng.
- **C5-MT5 — Nhãn HTF sai.** `:177-178` "Pass/Not Against" chỉ dựa trên có bias hay không, không đánh giá hướng HTF.
- **C6-MT5 — Multi-symbol ghi đè.** Một key `tnv:current_pulse` duy nhất → last-writer wins, history trộn symbol.
- **C7-MT5 — README sai tên file.** `README.md:48` ghi `TNV_WebBridge.mq5`, thực tế `TNV_WebBridge_EA.mq5`.

**🟡 Trung bình**
- **D1** — Buffer offset cứng (`:61-63,92-93`); **D2** — chỉ cập nhật khi đóng nến M5 (~5 phút trễ, frontend 10s); **D3** — `exit10` chỉ là support/level thấp không phải profit target; **D4** — thời gian không chuẩn hoá timezone; **D5** — không retry, lỗi chỉ `PrintFormat` (terminal), `WebRequest` đồng bộ trong `OnTick`; **D6** — `spread_val` default tĩnh 1.2; **D7** — EA không gửi `analysisText` (phân tích là template client-side).

### 4.2 Đề xuất (MT5)
| Mã | Đề xuất | Lý do | Tác động | Ưu tiên | Khó khăn |
|---|---|---|---|---|---|
| B1 | Tính ADX thật (`iADX`) + VWAP thật (tích luỹ vol×price/vol) | Bỏ 2 hằng số giả, badge trend/volume có nghĩa | Chính xác dữ liệu | Cao | Trung bình |
| B2 | Một nguồn token; bắt buộc kiểm tra header | EA không bị 401; endpoint không mở | Bảo mật | Cao | Thấp |
| B4 | Dedup/idempotency (key theo symbol+time; EA dùng GlobalVariable) | Hết ghi trùng, hết trộn symbol | Bền dữ liệu | Cao | Trung bình |
| B3/C7 | Bổ sung source indicator / ghi rõ buffer; sửa README | Audit được, người dùng cài đặt đúng | Bảo trì | Cao | Trung bình |
| C1-MT5 | Viết lại EMA xuôi (quá khứ→hiện tại), test với `iMA` | emaGap thật | Chính xác | Cao | Trung bình |
| C2/C3-MT5 | RSI Wilder + ATR Wilder (khớp `iRSI`/`iATR`) | Đúng chỉ báo chuẩn | Chính xác | Cao | Trung bình |
| C4-MT5 | EA tính score theo `calculateQualityScore` | Score 0–10 có nghĩa | Chính xác | Cao | Trung bình |
| C5-MT5 | Dùng `isHTFNotAgainst`/so hướng HTF thật | HTF không gây hiểu lầm | Chính xác | Trung bình | Trung bình |
| C6-MT5 | Key Redis theo symbol | Multi-symbol không ghi đè | Bền dữ liệu | Cao | Thấp |
| D2 | Gửi khi bias/score thay đổi, hoặc hiện rõ độ trễ | "Real-time" đúng nghĩa | UX | Trung bình | Trung bình |
| D3 | Phân biệt exitHigh (target) vs exitLow (stop) | Nhãn đúng | Đúng đắn | Trung bình | Thấp |
| D4 | Chuẩn hoá thời gian UTC; frontend hiển thị theo client | Hết lệch múi giờ | Đúng đắn | Trung bình | Thấp |
| D5 | Retry/backoff, log rõ, hiện trạng kết nối trên UI | Thấy được lỗi | Vận hành | Trung bình | Trung bình |
| D7 | EA gửi `analysisText` hoặc bỏ nhãn "phân tích tự động" | Trung thực | Sản phẩm | Trung bình | Thấp |

---

## 5. Nhóm UX

### 5.1 Điểm yếu (ref — `sites/tnv-goldpulse/`)
- **U-P1 (H) — i18n EN/VI chưa đủ.** `NotificationModal`, `ProUpgradeBar`, `SponsorCard` **hardcode tiếng Anh**, không `useLanguage()`; nhiều key dịch có sẵn nhưng không dùng → tiếng Anh lọt vào VI: 'PULSE'/'ENTRY'/'EXIT'/'High:'/'Low:'/'Status:' (LiveMetricsGrid), 'PULSE'/'snapshots'/'Prev'/'Next' (HistoryTable), 'Bullish/Bearish Flow'/'Tight:' (TechnicalGrid); các key `signalBadge/shareSignal/copied/historyCount/tabSession/tabTradingView/legend*/ctrl*/hoverInspect/flowSynced` không được nối. `<html lang="en">` (layout) và widget TradingView `locale='en'` (LiveGoldPriceChart, ChartSection) luôn tiếng Anh; session name (London/NY/Tokyo) luôn tiếng Anh.
- **U-P2 (H) — Accessibility baseline.** Modal thiếu `role=dialog`/`aria-modal`/focus-trap/focus-return (tab vào background); `InfoTip` chỉ hover, không focus/`aria-describedby`; flip-card thiếu `role=button`/`aria-pressed`/focus ring; chữ ~10px (`0.6-0.7rem`) + `gray-400/500` tương phản thấp dưới WCAG AA; nhiều chỉ báo truyền đạt **chỉ bằng màu** (PULSE, VWAP).
- **U-P3 (M) — Live status & trust.** `isLiveConnected`/`lastUpdated` có trong context nhưng **không được tiêu thụ**; không loading/empty/error; trạng thái 0/neutral đầu không phân biệt được với live-neutral.
- **U-P4 (M) — Flip-card interaction.** Tự flip-back sau 10s (MetricCard, SponsorCard) ngắt việc đọc; không có affordance mũi tên; grid `grid-cols-2` fixed + nowrap tràn trên mobile hẹp.
- **U-P5 (M/L) — Khác.** `alert()` cho Terms/Privacy/Refund, permission-denied, 'Redirecting to secure checkout' (không thực sự redirect); Session Flow tab chết; shim `src/components/*.tsx` + class `.qx-*` chết. *(Chồng W-C3, W-C14, W-C7, W-C9.)*

### 5.2 Đề xuất (UX)
| Mã | Đề xuất | Lý do | Tác động | Ưu tiên | Khó khăn |
|---|---|---|---|---|---|
| P1 | Hoàn thiện EN/VI parity | Localize 3 modal + nối key thừa + `lang`/widget locale theo ngôn ngữ (không đổi thiết kế) | Trải nghiệm | Cao | Thấp |
| P2 | Accessibility baseline | Modal shared (dialog/aria-modal/focus-trap/focus-return); InfoTip keyboard+touch; flip-card `role=button`/`aria-pressed`/focus + cue không-màu; tăng font/contrast | Tiếp cận | Cao | Trung bình |
| P3 | Live status & trust | Hiện `isLiveConnected`/`lastUpdated` (chấm kết nối + 'cập nhật Xs trước'), trạng thái loading/empty/error, latency | Tin cậy | Trung bình | Trung bình |
| P4 | Flip-card interaction | Bỏ/opt-in auto flip-back (pause khi hover/focus), thêm affordance, cho 1 cột dưới ~480px, wrap dải giá | UX mobile | Trung bình | Thấp |
| P5 | Stretch | Thay `alert()` bằng modal/toast in-app; PRO CTA navigate thật; làm hoặc gỡ Session Flow tabs; xoá dead code | Sản phẩm | Thấp | Trung bình |

---

## 6. Vấn đề xuyên nhóm (cross-cutting)

Các điểm yếu này **xuất hiện từ ≥2 nhóm** và nên xử lý như một cụm thống nhất:

1. **Xác thực & kiểm soát ghi (W-C1 + MT5-B2).** Một quyết định (bắt buộc token, một nguồn secret, dedup) giải quyết cả "endpoint mở" và "EA bị 401".
2. **Trung thực dữ liệu / tính năng giả (W-C3 + MT5-B1/C4/C5/D7 + U-P5).** Nhóm "đừng hiển thị con số/tính năng không có thật": ADX/VWAP/score/HTF giả, alert() giả, "1s live"/"Session Flow" chưa có.
3. **i18n hoàn chỉnh (W-C8 + U-P1).** `<html lang>`, widget locale, ngôn ngữ trong 3 modal, key thừa — cùng một lần chạm với ngôn ngữ.
4. **Dead code & CSS legacy (W-C7 + W-C9 + U-P5).** Dọn shim `src/components/*.tsx`, class `qx-*`, `ui/button`/`utils`, `types/market.ts`, `tnv-engine`.
5. **Real-time thật (W-C6 + MT5-D2).** Bỏ poll 10s "giả realtime" hoặc hiện rõ độ trễ; nếu cam kết 1s thì cần kênh realtime (SSE/WebSocket).

---

## 7. Lộ trình triển khai đề xuất — việc nên làm trước

> Theo thứ tự "trước tiên". Mỗi mục = 1 sprint/commit nhỏ, độc lập, ít phá vỡ. **Chờ người dùng xác nhận từng bước.**

**GIAI ĐOẠN 0 — An toàn & trung thực (làm ngay, chặn rủi ro):**
- ✅ Bắt buộc auth `POST /api/pulse` (401 khi thiếu/sai token); đặt `TNV_SECRET_KEY` trên Vercel = token EA; **bỏ secret mặc định** trong source. *(W-C1, B2)*
- ✅ Đổi merge `||`→`??` + schema runtime (zod) để không mất giá trị `0`; merge sâu `multiTf`/`entry`. *(W-C2)*
- ✅ Bỏ 2 hằng số giả ADX=32.4/VWAP=6.20 → tính thật (`iADX`, VWAP tích luỹ); sửa EMA ngược chiều; ATR/Rsi Wilder. *(B1, C1/C2/C3-MT5)*
- ✅ Dedup/idempotency + key Redis theo symbol (`tnv:current_pulse:{symbol}`). *(B4, C6-MT5)*
- ✅ Gỡ/gắn nhãn "coming soon" cho các tính năng "giả"(notification/pro/1s live); thay `alert()` bằng modal/toast in-app. *(W-C3, U-P5)*

**GIAI ĐOẠN 1 — Đúng chuẩn chỉ báo & đồng bộ nguồn:**
- ✅ Score theo `calculateQualityScore` thật; nhãn HTF theo hướng HTF thật (`isHTFNotAgainst`). *(C4/C5-MT5)*
- ✅ Bổ sung source indicator "10s TNV V2" hoặc tài liệu buffer; sửa README tên file `TNV_WebBridge_EA.mq5`. *(B3, C7-MT5)*
- ✅ Giới hạn phạm vi dữ liệu: phân biệt exitHigh/exitLow, chuẩn hoá timezone UTC, retry/backoff + hiển thị trạng thái kết nối, EA gửi `analysisText` hoặc bỏ nhãn "tự động". *(D3/D4/D5/D7-MT5)*

**GIAI ĐOẠN 2 — Trải nghiệm song ngữ & tiếp cận (tác động thị giác cao, rủi ro thấp):**
- ✅ Hoàn thiện i18n EN/VI parity (3 modal + key thừa + `lang`/widget locale). *(P1, W-C8)*
- ✅ Accessibility baseline (modal dialog/focus-trap, InfoTip keyboard/touch, flip-card role/aria, font/contrast). *(P2)*

**GIAI ĐOẠN 3 — Hiệu năng & bảo trì:**
- ✅ Fix lint 5 lỗi + 3 warning → `npm run check` xanh. *(W-C5)*
- ✅ SWR/React Query polling (dedup, chống race, `isLiveConnected=false` khi lỗi). *(W-C6, P3)*
- ✅ Dọn dead code (shim, `ui/button`, `utils`, `types/market.ts`, `tnv-engine`) + purge CSS `qx-*` + `next/font`. *(W-C7, W-C9)*
- ✅ Canonical route + `lang` động + sitemap/robots/OG; security headers + cấu hình `next.config`. *(W-C8, W-C10)*

**GIAI ĐOẠN 4 — Nâng cao (tùy chọn):**
- ✅ Session Flow tabs thật + visualisation (hoặc gỡ nhãn), thống nhất thang điểm/đếm lịch sử/session logic, realtime 1s (SSE/WebSocket) nếu thật sự cần. *(W-C11/12/13/14, P4, D2)*

**Ghi chú:** Ưu tiên trên đặt **an toàn + trung thực dữ liệu** trước (GĐ0) vì hiện sản phẩm hiển thị dữ liệu chiến lược sai và có endpoint mở; sau đó mới đến trải nghiệm và bảo trì. Mọi thay đổi **giữ nguyên** thiết kế dark/gold hiện tại.

---

## 8. Phụ lục: bản đồ file

**Web / Next.js**
- `src/app/layout.tsx` — metadata, `<html lang>`, font link, inject script chặn extension.
- `src/app/page.tsx`, `src/app/goldpulse/page.tsx` — cùng render `TNVGoldPulseApp` (trùng URL).
- `src/components/sites/tnv-goldpulse/TNVGoldPulseApp.tsx` — wrapper client (2 provider + 14 section).
- `src/lib/language-context.tsx` — i18n `vi`/`en` (bảng translations) + persist `localStorage`.
- `src/lib/live-pulse-context.tsx` — poll `GET /api/pulse` 10s.
- `src/lib/pulse-store.ts` — Upstash Redis (key `tnv:current_pulse`, `tnv:pulse_history`), fallback memory.
- `src/lib/tnv-engine.ts`, `tnv-turtle-engine.ts` — engine quality-score **orphan** (không dùng).
- `src/types/market.ts` — **không dùng**, enum bias lệch.
- `src/app/api/pulse/route.ts` (GET+POST), `src/app/api/pulse/clear/route.ts`, `src/app/api/news/route.ts`.
- `src/components/ui/button.tsx`, `src/lib/utils.ts` — **không dùng**.

**MT5**
- `docs/TNV_WebBridge_EA.mq5` (+ `.ex5`) — EA gửi webhook (nguồn tính toán chính).
- `docs/TNV_WebBridge_EA.ex5` — bản biên dịch.
- `README.md:43-49` — hướng dẫn cài đặt (tên file sai).

**UX**
- `src/components/sites/tnv-goldpulse/*` (HeroHeader, ActionBanner, LiveMetricsGrid, MetricCard, FlipBackContent, InfoTip, ConfidenceBar, PulseGauge, AnalysisSummary, SponsorCard, LiveGoldPriceChart, TechnicalGrid, TechCard, ChartSection, HistoryTable, SiteFooter, SubscribeBar, DisclaimerBanner, ProUpgradeBar, NotificationModal).
- `src/app/globals.css` — Tailwind v4 + class `qx-*` legacy.

---

*Báo cáo tổng hợp bởi `web-analyzer` (task T4) từ 3 phân tích T1/T2/T3. Trạng thái: chờ người dùng xác nhận trước khi thực thi.*

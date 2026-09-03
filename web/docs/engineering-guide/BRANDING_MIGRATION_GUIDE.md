# Hướng dẫn Migration: GoldPulse (QuantXi) → TNV

> **Dự án:** TNV Website Clone  
> **Kiến trúc sư:** nha-phan-tich (Phân tích & Design)  
> **Mục đích:** Tài liệu này dành cho các engineer thực hiện rebranding từ QuantXi Gold Pulse sang TNV.  
> **Lưu ý quan trọng:** Project ĐÃ có toàn bộ component đang chạy — đây là bản MODIFIED, không phải tạo mới từ đầu. Chỉ cần CẬP NHẬT branding, text, và thêm component còn thiếu.

---

## 1. Kiến trúc tổng quan

### Công nghệ
| Layer | Công nghệ | Ghi chú |
|-------|-----------|---------|
| Framework | Next.js 16 (App Router) | `page.tsx` duy nhất ở `src/app/` |
| UI Runtime | React 19 | Strict Mode |
| Styling | Tailwind CSS v4 + `globals.css` | Dùng CSS variables + utility classes |
| UI Library | shadcn/ui (@base-ui/react) | `src/components/ui/button.tsx` đã có |
| Icons | Lucide React | Có thể bổ sung SVG icons |
| Font | Poppins (Google Fonts) | Định nghĩa trong `globals.css` |

### Cấu trúc page (`src/app/page.tsx`)
Thứ tự các section từ trên xuống dưới:

```
main.qx-container (max-width: 1200px, margin: 0 auto, padding: 20px 16px)
├── DisclaimerBanner
├── HeroHeader
├── ProUpgradeBar
├── ActionBanner
├── .qx-top-row (flex row, wrap)
│   ├── .qx-live-shell (flex: 1)
│   │   └── .qx-live-layout (flex row, wrap)
│   │       ├── .qx-live-metrics → LiveMetricsGrid
│   │       └── AnalysisSummary
│   └── aside.qx-side-shell (flex: 0 0 280px)
│       ├── SponsorCard
│       └── MyFXBook placeholder div
├── ChartSection
├── HistoryTable
└── SiteFooter
```

### Danh sách component ĐÃ TỒN TẠI (17 files)

| File | "use client"? | Chức năng |
|------|---------------|-----------|
| `src/components/DisclaimerBanner.tsx` | ❌ Không | Disclaimer + link |
| `src/components/HeroHeader.tsx` | ✅ Có | Title + badge + tags |
| `src/components/ProUpgradeBar.tsx` | ✅ Có | Free plan bar + CTA |
| `src/components/ActionBanner.tsx` | ✅ Có | Dynamic action indicator |
| `src/components/LiveMetricsGrid.tsx` | ❌ Không | Grid 6 metric cards |
| `src/components/MetricCard.tsx` | ✅ Có | Reusable card (standard + flip) |
| `src/components/FlipBackContent.tsx` | ✅ Có | Back face của flip card |
| `src/components/ConfidenceBar.tsx` | ❌ Không | Progress bar component |
| `src/components/RsiRangeBar.tsx` | ❌ Không | RSI range bar + needle |
| `src/components/PulseGauge.tsx` | ❌ Không | Radial SVG gauge |
| `src/components/AnalysisSummary.tsx` | ✅ Có | AI Analysis panel |
| `src/components/SponsorCard.tsx` | ✅ Có | Broker sponsor card |
| `src/components/ChartSection.tsx` | ✅ Có | Chart + controls |
| `src/components/HistoryTable.tsx` | ❌ Không | Data table |
| `src/components/SiteFooter.tsx` | ❌ Không | Footer + links |
| `src/components/InfoTip.tsx` | ✅ Có | Tooltip helper |
| `src/components/ui/button.tsx` | ✅ Có | shadcn button primitive |

---

## 2. Brand Mapping: QuantXi → TNV

### 2.1 Text cần đổi (trực tiếp trong component)

| File | Old text (QuantXi/GoldPulse) | New text (TNV) |
|------|------------------------------|----------------|
| **`src/app/layout.tsx`** | `title: "GoldPulse – quantxi.online"` | `title: "TNV Gold Pulse – Chỉ số Vàng"` |
| **`src/app/layout.tsx`** | `description: "Live bias, confidence & readiness for XAUUSD with market context."` | `description: "Chỉ số thị trường vàng XAUUSD trực tiếp — bias, confidence, readiness"` |
| **`src/app/page.tsx`** | `export default function GoldPulsePage()` | → `TNVPage` |
| **`src/components/HeroHeader.tsx`** | `QuantXi Gold Pulse` | `TNV Gold Pulse` |
| **`src/components/HeroHeader.tsx`** | `Live bias, confidence & readiness for XAUUSD with market context.` | `Chỉ số vàng XAUUSD — bias, confidence & readiness` |
| **`src/components/SiteFooter.tsx`** | `QuantXi provides market analytics...` | `TNV cung cấp dữ liệu phân tích thị trường...` |
| **`src/components/SiteFooter.tsx`** | `© 2026 QuantXi. All rights reserved.` | `© 2026 TNV. All rights reserved.` |
| **`src/components/SiteFooter.tsx`** | `GoldPulse is a data visualisation tool...` | `TNV Gold Pulse là công cụ trực quan hóa dữ liệu...` |

### 2.2 CSS class prefix (qx- → tnv-)
**Không bắt buộc** nhưng nên làm để tránh conflict nếu có nhiều page. Nếu làm thì rename toàn bộ `qx-` → `tnv-` trong:
- `globals.css` (~40+ class definitions)
- Tất cả component `.tsx` (~20 files)
- Có thể giữ nguyên để tiết kiệm thời gian — hiện tại chỉ có 1 page.

**Khuyến nghị:** Giữ nguyên prefix `qx-` cho MVP, chỉ đổi sau khi TNV có thêm page khác.

### 2.3 File đã có CSS class mapping
```
.qx-card, .qx-card-label, .qx-card-main, .qx-card-footer
.qx-big-number, .qx-bias-value, .qx-ready-value, .qx-basic-value
.qx-strong, .qx-subtext
.qx-chip, .qx-chip-neutral, .qx-chip-up, .qx-chip-down, .qx-chip-outline
.qx-bar-track, .qx-bar-fill
.qx-range-bar, .qx-range-zones, .qx-zone-*, .qx-range-needle
.qx-flip, .qx-flip-front, .qx-flip-back, .qx-flip-badge, .qx-flip-rows, .qx-flip-row, .qx-flip-tf, .qx-flip-val
.qx-info-tip
.qx-hero, .qx-hero-left, .qx-hero-sub, .qx-hero-tags
.qx-pill, .qx-pill-soft, .qx-tier-*, .qx-pill-session
.qx-row
.qx-pulse-gauge-wrap
.qx-container
.qx-top-row, .qx-live-shell, .qx-live-layout, .qx-live-metrics, .qx-side-shell
.qx-btn-primary, .qx-btn-outline
.qx-history-table, .qx-history, .qx-history-header
```

---

## 3. Design Tokens (giữ nguyên, chỉ đổi tên brand)

### 3.1 Colors (từ `globals.css` :root/.dark)

| Token | Giá trị | Usage |
|-------|---------|-------|
| `--background` | `#05060a` | Nền chính |
| `--foreground` | `#fdfdfd` | Text chính |
| `--card` | `#0b0f16` → `#111622` | Gradient nền card |
| `--primary` (gold) | `#f5c542` | Gold primary |
| `--primary-foreground` | `#05060a` | Text trên gold bg |
| `--gold-dark` | `#cfa744` | Gold gradient |
| `--secondary` | `#111622` | Secondary surface |
| `--secondary-foreground` | `rgba(244,244,244,0.78)` | Label text |
| `--muted` | `#111622` | Muted surface |
| `--muted-foreground` | `rgba(220,220,220,0.78)` | Muted text |
| `--accent` | `rgba(207,167,68,0.3)` | Gold accent bg |
| `--accent-foreground` | `#f5c542` | Gold accent text |
| `--destructive` | `#ff8383` | Red/bearish |
| `--chart-1` | `#f5c542` | Gold chart line |
| `--chart-2` | `#61e294` | Green chart line |
| `--chart-3` | `#ff8383` | Red chart line |
| `--chart-4` | `#00d4ff` | Cyan chart line |
| `--chart-5` | `#cfa744` | Dark gold |
| `--border` | `rgba(255,255,255,0.06)` | Subtle border |
| `--ring` | `rgba(207,167,68,0.5)` | Focus ring gold |
| `--radius` | `0.625rem` | Base radius |

### 3.2 Background gradient (body)
```css
body {
  background-image: radial-gradient(
    circle at top left,
    rgba(207, 167, 68, 0.08),
    transparent 60%
  ), #05060a;
}
```

### 3.3 Sizing & Spacing
| Item | Giá trị |
|------|---------|
| Max container width | 1200px |
| Card border-radius | 16px |
| Button/pill radius | 999px |
| Chip radius | 999px |
| Card padding | 12px 14px 14px |
| Card shadow | `0 12px 32px rgba(0,0,0,0.55)` |
| Card hover shadow | `+ inset 0 0 30px rgba(207,167,68,0.06)` |
| Gutter (gap) | 10px–14px (components), 20px (sections) |

### 3.4 Font
- **Family:** `"Poppins", system-ui, -apple-system, "Segoe UI", sans-serif`
- **Scale:**
  - H1: 1.6rem / 700 / -0.02em letter-spacing
  - H2: 1.15rem / 600
  - H3: 1.05rem / 600
  - Card label: 0.72rem / uppercase / 0.11em spacing
  - Big number: 1.4rem / 600
  - Bias value: 1.3rem / 600 (gold)
  - Readiness: 1.15rem / 600 (gold)
  - Basic value: 1rem / 500
  - Subtext: 0.78rem / green tint
  - Footer: 0.78rem

---

## 4. Các section cần tạo MỚI: TechnicalGrid

Hiện tại **chưa có** component `TechnicalGrid`. Các indicator kỹ thuật sau cần được implement:

| Card | Dữ liệu |
|------|---------|
| **ADX** | Giá trị + Trend label (Strong/Weak) |
| **EMA** | Fast/Slow crossover hint |
| **VWAP** | Price vs VWAP (above/below) |
| **ATR** | Giá trị ATR + % of price |
| **Spread** | Bid/Ask spread |
| **Risk Score** | Composite risk level |

**Vị trí bố trí:** Dưới LiveMetricsGrid, trên ChartSection — hoặc bên trong sidebar area.

```tsx
<div className="qx-tech-row" style={{ marginBottom: 20 }}>
  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 10 }}>
    {/* ADX card */}
    {/* EMA card */}
    {/* VWAP card */}
    {/* ATR card */}
    {/* Spread card */}
    {/* Risk card */}
  </div>
</div>
```

Mỗi card dùng lại `MetricCard` (standard variant, không flip) với label, value, và footer mô tả ngắn.

---

## 5. Kỹ thuật quan trọng

### 5.1 "use client" directive
Component có `onClick`, `onMouseEnter`, `useState`, hoặc browser event handlers **phải** có `"use client"` ở đầu file.

**Hiện trạng:**
- ✅ Đã có: HeroHeader, ProUpgradeBar, ActionBanner, MetricCard, FlipBackContent, InfoTip, AnalysisSummary, SponsorCard, ChartSection, ui/button
- ❌ **THIẾU** (cần thêm): `LiveMetricsGrid.tsx` (import các component client — nếu không có event trực tiếp thì vẫn có thể là server component, nhưng để an toàn nên thêm `"use client"` nếu có bất kỳ dynamic behavior nào)

### 5.2 Thứ tự import trong `page.tsx`
Các import đã theo đúng thứ tự render. Nếu thêm `TechnicalGrid`, import và chèn sau `SponsorCard` / trước `ChartSection`.

```tsx
import { TechnicalGrid } from "@/components/TechnicalGrid";
// ... trong JSX:
<SponsorCard />
<TechnicalGrid />  {/* <-- thêm ở đây */}
<ChartSection />
```

### 5.3 Không dùng inline styles khi đã có CSS class
Trong code hiện tại có MỘT SỐ inline styles (đặc biệt ở `ChartSection.tsx`, `SiteFooter.tsx`) — nên migrate dần vào `globals.css` hoặc CSS module, nhưng **không bắt buộc trong giai đoạn rebranding** nếu trang đã chạy.

### 5.4 Build & Dev
```bash
npm run dev      # Dev server
npm run build    # Production build (kiểm tra lỗi TypeScript)
npm run check    # Lint + typecheck + build
```

### 5.5 Xử lý multilingual
Nếu TNV muốn hiển thị tiếng Việt:
- Đổi `lang="en"` → `lang="vi"` trong `layout.tsx`
- Đổi text trong component như mapping ở mục 2.1
- Có thể giữ song ngữ (English UI + Vietnamese description)

### 5.6 SEO metadata
Trong `layout.tsx`:
```tsx
export const metadata: Metadata = {
  title: "TNV Gold Pulse – Chỉ số Vàng",
  description: "Chỉ số thị trường vàng XAUUSD trực tiếp — bias, confidence, readiness",
  // Thêm Open Graph
  openGraph: {
    title: "TNV Gold Pulse",
    description: "...",
  },
};
```

---

## 6. Tóm tắt công việc cho Engineer

### Priority 1 — Branding text (dễ, nhanh)
- [ ] `layout.tsx`: title + description
- [ ] `page.tsx`: function name
- [ ] `HeroHeader.tsx`: "QuantXi Gold Pulse" → "TNV Gold Pulse"
- [ ] `SiteFooter.tsx`: all "QuantXi" → "TNV"

### Priority 2 — TechnicalGrid (component mới)
- [ ] Tạo `src/components/TechnicalGrid.tsx`
- [ ] 6 card: ADX, EMA, VWAP, ATR, Spread, Risk Score
- [ ] Thêm vào `page.tsx` sau SponsorCard

### Priority 3 — Polish & consistency
- [ ] Thêm `"use client"` cho các component còn thiếu
- [ ] Đảm bảo layout responsive (mobile: single column)
- [ ] Kiểm tra build `npm run build` không lỗi

### Optional — Deep rebrand
- [ ] (Không khuyến nghị) Rename `qx-` → `tnv-` classes
- [ ] Thêm Google Analytics / tracking code
- [ ] Thêm Open Graph images

---

## 7. Tài liệu tham khảo

| File | Nội dung |
|------|----------|
| `src/app/globals.css` | Theme variables + component styles (591 dòng) |
| `src/app/page.tsx` | Page composition (59 dòng) |
| `src/app/layout.tsx` | Root layout + metadata (22 dòng) |
| `docs/research/DESIGN_TOKENS.md` | Design tokens từ captain |
| `docs/research/COMPONENT_INVENTORY.md` | Component inventory |
| `docs/engineering-guide/BRANDING_MIGRATION_GUIDE.md` | **← This file** |

---

*Tài liệu được tạo bởi nha-phan-tich (Phân
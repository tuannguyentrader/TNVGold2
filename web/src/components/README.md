# TNV Components — Tổng quan & Hướng dẫn Cấu trúc Thư mục

> **Vị trí lưu trữ chính thức:** `src/components/sites/tnv-goldpulse/`  
> Để tránh nhầm lẫn với các dự án clone website trong tương lai, tất cả component của TNV Gold Pulse đã được cô lập hoàn toàn vào thư mục riêng: `src/components/sites/tnv-goldpulse/`.  
> Các file tại `src/components/*.tsx` đóng vai trò re-export alias tương thích ngược.

---

## 📁 Cấu trúc Thư mục Cô lập

```
src/
├── app/
│   ├── page.tsx                       # Route chính (render TNVGoldPulseApp)
│   ├── goldpulse/page.tsx             # Route riêng /goldpulse
│   ├── globals.css                    # Design tokens & styles
│   └── layout.tsx                     # Root layout & Google Fonts
└── components/
    ├── sites/
    │   └── tnv-goldpulse/             # 🌟 Thư mục riêng biệt cho dự án TNV Gold Pulse
    │       ├── index.ts               # Barrel export tất cả component
    │       ├── TNVGoldPulseApp.tsx    # Master Page Layout component
    │       ├── HeroHeader.tsx         # Header, branding, license modal, alerts
    │       ├── ActionBanner.tsx       # Ticker trạng thái Neutral/Long/Short
    │       ├── ProUpgradeBar.tsx      # Bar nâng cấp PRO + Modal
    │       ├── DisclaimerBanner.tsx   # Cảnh báo rủi ro (Risk notice)
    │       ├── LiveMetricsGrid.tsx    # Lưới 6 thẻ chỉ số đo lường
    │       ├── MetricCard.tsx         # Component thẻ chỉ số + Flip interaction
    │       ├── FlipBackContent.tsx    # Nội dung mặt sau Multi-Timeframe
    │       ├── PulseGauge.tsx         # Đồng hồ Radial Pulse đo xung lực
    │       ├── ConfidenceBar.tsx      # Thanh tiến trình độ tin cậy
    │       ├── RsiRangeBar.tsx        # Thanh dải đo RSI (14)
    │       ├── InfoTip.tsx            # Tooltip giải thích chỉ số
    │       ├── AnalysisSummary.tsx    # Bảng phân tích AI + PulseGauge
    │       ├── SponsorCard.tsx        # Thẻ tin tức thị trường & Đối tác Exness
    │       ├── LiveGoldPriceChart.tsx # Biểu đồ giá vàng trực tiếp chuẩn TradingView
    │       ├── TechnicalGrid.tsx      # Lưới 6 chỉ báo kỹ thuật chuyên sâu
    │       ├── TechCard.tsx           # Thẻ chỉ báo kỹ thuật
    │       ├── ChartSection.tsx       # Biểu đồ Session Flow™ + TradingView Live tab
    │       ├── HistoryTable.tsx       # Bảng lịch sử Ring Buffer Snapshots
    │       ├── NotificationModal.tsx  # Modal thông báo & Telegram Bot
    │       ├── SiteFooter.tsx         # Footer pháp lý & điều khoản
    │       └── SubscribeBar.tsx       # Thanh đăng ký nhận bản tin ở cuối trang
    └── ui/                            # shadcn / base-ui primitives dùng chung
```

---

## 🧭 Thứ tự hiển thị trên trang

1. **DisclaimerBanner** — ⚠ Disclaimer + link "Full disclaimer"
2. **HeroHeader** — Tiêu đề "TNV Gold Pulse" badge BETA + London/NY + Pro Active + Manage API Key
3. **ProUpgradeBar** — Free plan bar + CTA "Upgrade to TNV PRO"
4. **ActionBanner** — Dynamic action indicator (Neutral/WAIT/LONG/SHORT) + share button
5. **Main Dashboard Top Grid**:
   - **Left Gold Box**:
     - `LiveMetricsGrid` (6 cards: Bias, Confidence, Readiness, Trend Strength, Volatility, RSI 14 - hỗ trợ Flip sang Multi-TF)
     - `AnalysisSummary` (AI Analysis panel + PulseGauge radial)
   - **Right Box**:
     - `SponsorCard` (News radar tab & Exness sponsor tab)
     - `LiveGoldPriceChart` (Biểu đồ giá vàng real-time TradingView style)
6. **TechnicalGrid** — Lưới 6 chỉ báo chuyên sâu (ADX, EMA Gap, VWAP, ATR %, Spread, Risk State)
7. **ChartSection** — Biểu đồ Session Flow™ (Tokyo, London, NY) + Tab TradingView Widget
8. **HistoryTable** — Data table lịch sử 15 phút từ Ring Buffer
9. **SiteFooter** — Tuyên bố miễn trừ trách nhiệm & Bản quyền TNV 2026
10. **SubscribeBar** — Thanh ghim dưới cùng đăng ký nhận bản tin miễn phí

---

## 🎨 Design Tokens

| Token | Value |
|-------|-------|
| BG chính | `#05060a` |
| Card gradient | `#0b0f16` → `#111622` |
| Gold primary | `#f5c542` |
| Gold dark | `#cfa744` |
| Green (bullish) | `#61e294` |
| Red (bearish) | `#ff8383` |
| Cyan (Tokyo / info) | `#00d4ff` |
| Font | Poppins |
| Card radius | 14px / 16px |
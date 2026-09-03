# GoldPulse Clone — Component Inventory

## 1. DisclaimerBanner
- **Path**: `src/components/DisclaimerBanner.tsx`
- **Structure**: Warning icon ⚠ + text paragraph + link
- **States**: Always visible, static
- **Styling**: Subtle border, gold link color `#f5c542`

## 2. HeroHeader
- **Path**: `src/components/HeroHeader.tsx`
- **Structure**: 
  - Left: h1 "QuantXi Gold Pulse" + tier badge (FREE/PRO) + subtitle + tag pills (Updated, Latency, Next refresh, Session)
  - Right: API key section (collapsible)
- **States**: Tier badge changes class `qx-tier-free` / `qx-tier-pro`

## 3. ProUpgradeBar
- **Path**: `src/components/ProUpgradeBar.tsx`
- **Structure**: Text span + CTA link button
- **Styling**: Green-tinted background, gold button

## 4. ActionBanner
- **Path**: `src/components/ActionBanner.tsx`
- **Structure**: Icon + text + share button
- **Dynamic classes**: `qx-action-blocked`, `qx-action-long`, `qx-action-short`, `qx-action-wait`

## 5. MetricCard (core reusable)
- **Path**: `src/components/MetricCard.tsx`
- **Variants**:
  - Standard card (label + value + footer)
  - Flip card (front/back)
- **Props**: label, value, footer, tooltip text, flipContent (optional), trend, children
- **Children**: Can embed ConfidenceBar, RsiRangeBar, etc.

## 6. FlipCard
- **Path**: `src/components/FlipCard.tsx`
- **Structure**: Two `.qx-card` divs (front + back), toggled by `.qx-flipped` class
- **Back content**: Multi-TF rows (15m, 1h, 4h)

## 7. ConfidenceBar
- **Path**: `src/components/ConfidenceBar.tsx`
- **Structure**: Bar track div + fill div (gradient gold)
- **Props**: value (0-100%)

## 8. RsiRangeBar
- **Path**: `src/components/RsiRangeBar.tsx`
- **Structure**: Three colored zones (green/neutral/red) + needle
- **Props**: value (0-100)

## 9. PulseGauge
- **Path**: `src/components/PulseGauge.tsx`
- **Structure**: SVG circles (track + fill) + center text (number + label)
- **Props**: value (0-100), band label

## 10. AnalysisSummary
- **Path**: `src/components/AnalysisSummary.tsx`
- **Structure**: Header (kicker + time), body text, gauge
- **Styling**: Gold border, dark gradient bg

## 11. SponsorCard
- **Path**: `src/components/SponsorCard.tsx`
- **Structure**: Pill badge + heading + link

## 12. ChartSection (GoldSessionFlow)
- **Path**: `src/components/ChartSection.tsx`
- **Structure**: 
  - Chart header (title + session legend)
  - Controls bar (checkboxes + TF buttons + range select + buttons)
  - Canvas area
  - Footer notes

## 13. HistoryTable
- **Path**: `src/components/HistoryTable.tsx`
- **Structure**: Table with header + tbody (dynamically filled)
- **Columns**: Time, Price, Pulse, Bias, Conf, Ready, ADX, Vol

## 14. SiteFooter
- **Path**: `src/components/SiteFooter.tsx`
- **Structure**: Disclaimer text + copyright + links

## 15. GaugeNeedle (utility)
- **Path**: `src/components/GaugeNeedle.tsx`
- **Props**: position (percentage or angle)

## 16. InfoTip
- **Path**: `src/components/InfoTip.tsx`
- **Props**: text (tooltip content)
- **Behavior**: Hover to show tooltip

## 17. SponsorRow
- **Path**: `src/components/SponsorRow.tsx`
- **Structure**: Sponsor card + MyFXBook iframe (optional)

## 18. Page (GoldPulsePage)
- **Path**: `src/app/page.tsx`
- **Structure**: Composes all sections in order

---

## Data Flow

Props-based static UI for emulation phase. Live data connections (API) would be phase 2.

The page component holds all state as static placeholder values (—, —%, etc.) matching the loading state of the original site.
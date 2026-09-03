# GoldPulse Clone — Design Tokens & Architecture

## Target Site
- **URL**: https://quantxi.online/goldpulse/
- **Tech Stack (Original)**: WordPress (Astra theme) + SureCart + Custom JS/CSS
- **Purpose**: Live XAUUSD trading dashboard — bias, confidence, readiness, trend strength, volatility, RSI, and chart

---

## Color Palette

### Background & Surface
| Token | Hex | Usage |
|-------|-----|-------|
| `--bg-page` | `#05060a` | Main page background |
| `--bg-card` | `#0b0f16` → `#111622` | Card gradient base |
| `--bg-elevated` | `#151a25` | Tooltip / modal surface |
| `--bg-hover` | `rgba(207,167,68,0.06)` | Card hover overlay |
| `--bg-pro-bar` | `rgba(97,226,148,0.1)` | Pro upgrade bar bg |

### Brand / Accent
| Token | Hex | Usage |
|-------|-----|-------|
| `--gold-primary` | `#f5c542` | Primary gold accent |
| `--gold-dark` | `#cfa744` | Darker gold (gradients) |
| `--gold-subtle` | `rgba(245,197,66,0.12)` | Subtle gold bg |
| `--gold-border` | `rgba(207,167,68,0.5)` | Gold borders |

### Semantic
| Token | Hex | Usage |
|-------|-----|-------|
| `--green` | `#61e294` | Bullish / up |
| `--green-bg` | `rgba(97,226,148,0.18)` | Up chip bg |
| `--red` | `#ff8383` | Bearish / down |
| `--red-bg` | `rgba(255,96,96,0.16)` | Down chip bg |
| `--warning` | `#f5c542` | Neutral/warning |
| `--cyan` | `#00d4ff` | Info/zone color |

### Text
| Token | Hex | Usage |
|-------|-----|-------|
| `--text-primary` | `#fdfdfd` | Primary text |
| `--text-secondary` | `rgba(244,244,244,0.78)` | Card labels |
| `--text-muted` | `rgba(220,220,220,0.78)` | Footer/subtle |
| `--text-subtle` | `rgba(230,230,230,0.8)` | Very subtle |

---

## Typography

- **Font Family**: `Poppins`, system-ui, -apple-system, sans-serif
- **Base Size**: 16px
- **Scale**:
  - `h1`: 1.5rem–2rem, 700 weight
  - `h2`: 1.25rem–1.5rem, 600 weight
  - `h3`: 1rem–1.15rem, 600 weight
  - Card labels: `0.72rem`, uppercase, letter-spacing 0.11em
  - Card values: `1.15rem–1.4rem`, 600 weight
  - Chips/tags: `0.75rem–0.78rem`
  - Footer text: `0.78rem`

---

## Border Radius
- Cards: `16px`
- Buttons/pills: `999px`
- Chips: `999px`
- Inputs: `6px–8px`
- Tooltip: `10px`

---

## Spacing Scale
| Token | Value |
|-------|-------|
| `--space-xs` | 4px |
| `--space-sm` | 6px |
| `--space-md` | 8px |
| `--space-lg` | 12px |
| `--space-xl` | 14px–16px |
| `--space-2xl` | 20px–22px |

---

## Shadows
- Card: `0 12px 32px rgba(0,0,0,0.55)`
- Card hover: `0 12px 32px rgba(0,0,0,0.55), inset 0 0 30px rgba(207,167,68,0.06)`
- Tooltip: `0 12px 36px rgba(0,0,0,0.85)`
- Pro button: `0 12px 40px rgba(0,0,0,0.7)`

---

## Layout Structure (Desktop)

```
[Page Container - max-width 1200px]
├── Disclaimer Banner
├── Hero Header
│   ├── Left: Title + subtitle + tags
│   └── Right: API key section (hidden by default)
├── Pro Upgrade Bar
├── Action Banner
├── Top Row
│   ├── Live Metrics Grid (cards)
│   │   ├── Bias (flip card)
│   │   ├── Confidence (flip card)
│   │   ├── Readiness
│   │   ├── Trend Strength / ADX (flip card)
│   │   ├── Volatility
│   │   └── RSI (flip card)
│   └── Right Panel
│       ├── AI Analysis Summary
│       └── Pulse Gauge (radial)
├── Sponsor / MyFXBook Section
├── Chart Section (Gold Session Flow)
│   ├── Controls bar
│   ├── Legend
│   └── Canvas
├── History Table
└── Footer (disclaimer + links)
```

---

## Responsive Behavior
- **Desktop (>1024px)**: Side-by-side metrics grid (2 columns) + summary panel
- **Tablet (768–1024px)**: Metrics grid adjusts, summary panel below
- **Mobile (<768px)**: Single column, stacked layout

---

## Component Inventory

### 1. DisclaimerBanner
- Warning icon + text + link

### 2. HeroHeader
- Title with tier badge, subtitle, tag pills

### 3. ProUpgradeBar
- Text + CTA button (gold gradient)

### 4. ActionBanner
- Dynamic status indicator with icon + text + share button

### 5. MetricCard (reusable)
- Info tooltip (i icon)
- Card label
- Main value
- Optional footer
- Flip card variant (front/back with multi-TF data)

### 6. ConfidenceBar
- Track + fill bar (gold gradient)

### 7. RsiRangeBar
- Colored zone segments + needle indicator

### 8. PulseGauge (radial SVG)
- SVG circle track + fill, center text

### 9. AnalysisSummary
- AI Analysis header + text + timestamp

### 10. SponsorCard
- Broker sponsor card with pill + CTA

### 11. ChartSection (Gold Session Flow)
- Controls, TF buttons, canvas, legend

### 12. HistoryTable
- Table with time/price/pulse/bias/conf/ready/ADX/vol columns

### 13. SiteFooter
- Disclaimer text + copyright + links
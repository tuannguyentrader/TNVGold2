# Dashboard Specification

## Overview
- Target route: `/`
- Implementation: `src/app/page.tsx` and existing `src/components/` dashboard components
- Interaction model: mixed static, click-driven, and hover-driven

## Structure
- Main max width 1260px with 12px mobile / 16px small-screen gutters.
- Vertical order: disclaimer, hero, upgrade bar, action ticker, top dashboard, technical grid, session chart, history table, footer, fixed subscribe bar.
- Desktop top dashboard is `1.22fr 1fr`; inner metrics/analysis panel uses a metrics-heavy column plus analysis column. Mobile stacks all columns.

## Exact extracted tokens
- Page background: `#05060a` with dark radial accents.
- Card surfaces: `#0b0f16` to `#111622` gradients.
- Gold: `#f5c542`; dark gold: `#cfa744`.
- Positive: `#61e294`; negative: `#ff8383`; cyan: `#00d4ff`.
- Body font from local implementation: Poppins, system fallback; live page also renders Roboto for WordPress-managed regions.
- Card radius: 14px; dashboard panel radius: 16px; compact controls use 8px to 12px.
- Base body size: 14px; card labels approximately 0.72rem, uppercase, 0.11em tracking.

## Live content snapshot
- Brand: `GoldPulse`, BETA, TNV rebrand in local clone.
- Bias: `Neutral`; confidence: `13%`; readiness: `Medium` (`3 / 5`); trend strength: `Flat`; ADX: `14.0`; RSI: `63.3`.
- Live price reference: `$4617.89`, daily change `-6.47 (-0.14%)`.
- Live page source title: `GoldPulse – quantxi.online`.

## Assets
- No content images are required by the local dashboard; charts and gauges are SVG/CSS. Live favicon sources were `https://api.quantxi.online/img/favicon-48.png`, `favicon-192.png`, and `apple-touch-icon.png`.

## Responsive
- 1440px: multi-column dashboard and full header controls.
- 768px: wrapped controls and reduced columns.
- 390px: single-column content, hidden center header status, fixed subscribe bar remains.

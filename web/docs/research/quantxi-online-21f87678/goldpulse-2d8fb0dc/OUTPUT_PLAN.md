# TNV GoldPulse Clone Output Plan & Isolation Architecture

- **Source URL:** `https://quantxi.online/goldpulse/`
- **Destination Routes:**
  - `/` (Root route -> [src/app/page.tsx](file:///Users/apple/ai-website-cloner/src/app/page.tsx))
  - `/goldpulse` (Isolated pathname route -> [src/app/goldpulse/page.tsx](file:///Users/apple/ai-website-cloner/src/app/goldpulse/page.tsx))
- **Branding:** TNV Gold Pulse
- **Site Key:** `tnv-goldpulse` (alias `quantxi-online-21f87678`)
- **Page Key:** `goldpulse-2d8fb0dc`
- **Artifact Root:** [docs/research/quantxi-online-21f87678/goldpulse-2d8fb0dc/](file:///Users/apple/ai-website-cloner/docs/research/quantxi-online-21f87678/goldpulse-2d8fb0dc/)
- **Screenshot Root:** [docs/design-references/quantxi-online-21f87678/goldpulse-2d8fb0dc/](file:///Users/apple/ai-website-cloner/docs/design-references/quantxi-online-21f87678/goldpulse-2d8fb0dc/)
- **Component Root:** [src/components/sites/tnv-goldpulse/](file:///Users/apple/ai-website-cloner/src/components/sites/tnv-goldpulse/)
  - `src/components/*.tsx` provides backward-compatible re-export wrappers to prevent breaking legacy imports.

## Directory Isolation Benefits
1. Complete isolation prevents file collisions when cloning new websites in the future.
2. Every component has its own dedicated namespace with TypeScript strict types and `"use client"` directives.
3. Master application layout component `TNVGoldPulseApp` can be mounted in any Next.js route effortlessly.

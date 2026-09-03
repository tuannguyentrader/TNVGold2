# 🏆 TNVGold — Monorepo

Monorepo cho 2 dự án TNVGold:

- **`telegram-bot/`** — Bot Telegram Python (XAUUSD analysis, Free/Pro tier, signals, news)
- **`web/`** — Next.js 16 marketing web + auto-publish blog + SEO

## Cấu trúc

```
TNVGold/
├── telegram-bot/          # Python — đã deploy trên VPS Windows
│   ├── bot.py
│   ├── storage.py
│   ├── analyzer.py
│   └── ... (15 modules)
│
├── web/                   # Next.js 16 — đã deploy trên Vercel
│   ├── src/
│   │   ├── app/           # 16 routes (landing, goldpulse, blog, tin-tuc, ...)
│   │   ├── components/    # landing/ + sites/
│   │   └── lib/           # blog-store, news-store, pulse-store, ...
│   ├── vercel.json        # Cron config
│   └── package.json
│
└── README.md              # File này
```

## Deploy

### Telegram bot (VPS Windows)
- File: `telegram-bot/` → copy sang `C:\Users\Administrator\Desktop\TNVGold Telegram\`
- Chạy: `python bot.py`
- Docs: `telegram-bot/SETUP_VPS.md`

### Web (Vercel)
- Root directory: `web/`
- Build: `pnpm run build` (auto-detect)
- Vercel project: `tnvgold` (URL: `https://tnvgold.vercel.app`)
- Env: `KV_REST_API_URL`, `KV_REST_API_TOKEN`, `TNV_SECRET_KEY`, `NEXT_PUBLIC_SITE_URL`

## Liên kết

- 🌐 Web: https://tnvgold.vercel.app
- 🤖 Bot: @TNVGold_bot
- 📞 Admin: @TuanNguyenTrader
- 📂 Repo cũ: https://github.com/tuannguyentrader/TNVGold

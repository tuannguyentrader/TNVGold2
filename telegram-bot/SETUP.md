# 📲 TNVGold Telegram Bot — Hướng dẫn setup

Bot phân tích XAUUSD (vàng), đọc nến từ MT5 hoặc Gold-API, hỗ trợ **8 AI**: DeepSeek, Gemini, ChatGPT, Claude, Grok, OpenRouter, KiraAI, Ollama.  
**API key lưu trong SQLite** — quản lý qua lệnh `/keys` trên Telegram, không cần file `.env`.

---

## 1. Chuẩn bị (1 lần duy nhất)

### A. Telegram Bot Token (30 giây, miễn phí)
1. Mở Telegram, tìm `@BotFather`
2. Gõ `/newbot` → đặt tên + username (vd: `TNVGold_Bot`)
3. BotFather trả về **token** dạng `123456:ABC-...`

Lưu token vào 1 trong 2 cách:
- **Cách 1 (khuyên dùng)**: Tạo file `telegram_token.txt` bên cạnh `main.py`, dán token vào
- **Cách 2**: Set biến môi trường `export TELEGRAM_BOT_TOKEN="..."`

### B. API Key AI (ít nhất 1)
Chỉ cần **1 key** là bot chạy được. Thêm nhiều key để linh hoạt đổi AI.

| AI | Lấy key ở đâu | Lệnh thêm |
|---|---|---|
| **DeepSeek** (rẻ nhất) | platform.deepseek.com → API Keys | `/keys set deepseek sk-...` |
| **Gemini** (nhanh, rẻ) | aistudio.google.com → API Key | `/keys set gemini AIza...` |
| **ChatGPT** (mạnh) | platform.openai.com → API Keys | `/keys set openai sk-...` |
| **Claude** (chất lượng nhất) | console.anthropic.com → API Keys | `/keys set claude sk-ant-...` |
| **Grok** (xAI) | x.ai/api | `/keys set grok xai-...` |
| **OpenRouter** (1 key mọi model) | openrouter.ai → API Keys | `/keys set openrouter sk-or-...` |
| **KiraAI** (VN, rẻ) | kiraai.vn | `/keys set kiraai ...` |
| **Ollama** (local) | — (không cần key, tự cài Ollama) | — |

---

## 2. Cài đặt

```bash
cd "TNVGold Telegram"
pip install -r requirements.txt
```

## 3. Chạy

```bash
python3 main.py
```

Lần đầu chạy, bot sẽ yêu cầu **Telegram token** nếu chưa có. Dán token vào file `telegram_token.txt` rồi chạy lại.

## 4. Dùng trên Telegram

Mở chat với bot, gõ `/start` để xem hướng dẫn.

### Lệnh chính

| Lệnh | Chức năng |
|---|---|
| `/xau` `/xau m5` | Báo cáo tổng M5 (xu hướng + TNV + khuyến nghị) |
| `/xau m15` `/xau m30` `/xau h1` `/xau h4` `/xau d1` | Báo cáo tổng theo khung |
| `/candle` `/candle m5` | Phân tích nến M5 → dự đoán nến tiếp |
| `/candle m15` `/candle h1` | Phân tích nến theo khung |
| `/news` | Lịch kinh tế XAUUSD hôm nay (Forex Factory) |
| `/tnvgold` `/tnv` | Tín hiệu TNV (SYSTEM 1) — Score, Entry/SL/TP, HTF filter |
| `/indicators` | Bảng chỉ báo (RSI, MACD, ATR, SMA, EMA, BB, Fib) |
| `/price` | Giá XAU hiện tại |
| `/alert 3000` | Đặt cảnh báo giá khi chạm $3000 |
| `/alerts` | Danh sách alert |
| `/delalert 3` | Xóa alert #3 |
| `/lang` | Chuyển ngôn ngữ vi/en |
| `/keys` | Xem trạng thái API key |
| `/model` | Xem AI đang dùng |

### Quản lý AI

| Lệnh | Chức năng |
|---|---|
| `/keys` | Xem trạng thái các API key đã lưu |
| `/keys set deepseek sk-...` | Thêm key cho DeepSeek |
| `/keys remove openai` | Xóa key ChatGPT |
| `/model` | Xem AI đang dùng |
| `/model claude` | Chuyển sang Claude |
| `/model deepseek` | Chuyển sang DeepSeek |

### Thứ tự ưu tiên tự động

Nếu chưa `/model` chọn AI cụ thể, bot tự chọn AI đầu tiên có key theo thứ tự:

```
DeepSeek → Gemini → ChatGPT → Claude → Grok → OpenRouter → KiraAI → Ollama
```

Ví dụ: bạn có key Gemini + DeepSeek → bot dùng **DeepSeek** (đứng trước).

---

## 5. Lấy Chat ID (để nhận báo cáo tự động)

1. Gửi bất kỳ tin nhắn cho bot
2. Mở: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Tìm `"chat":{"id": <SỐ>` — đó là chat id của bạn
4. Set vào biến môi trường: `export XAU_CHAT_IDS="<số>"` (có thể nhiều, cách dấu phẩy)

---

## 6. Chạy 24/7

- **VPS**: `sudo cp tnvgold-telegram.service /etc/systemd/system/` → `sudo systemctl enable --now tnvgold-telegram`
- **Mac**: chạy trong terminal + `tmux` hoặc dùng `launchd`

---

## 🔐 Lưu ý bảo mật

- API key lưu trong SQLite (`data/xau_bot.db`) — không phải file text
- Bot chỉ chấp nhận lệnh từ `ALLOWED_CHAT_IDS` (whitelist)
- Không dùng file `.env` — key được quản lý qua Telegram
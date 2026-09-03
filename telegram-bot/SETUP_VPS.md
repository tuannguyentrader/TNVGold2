# 🚀 Deploy TNVGold Telegram Bot lên VPS Windows Server

Hướng dẫn này dành cho **VPS Windows Server có cài MT5 chạy 24/24** — bot sẽ đọc nến trực tiếp từ MT5 (chế độ `local`), chính xác nhất.

---

## 📁 Các file cần copy lên VPS

Copy **toàn bộ thư mục `TNVGold Telegram`** lên VPS (vd: `C:\TNVGold`), gồm:

```
TNVGold Telegram/
├── bot.py                 ← Telegram bot (lệnh /xau /tnvgold /candle /alert /keys...)
├── tnv_engine.py          ← TNV Indicator (breakout + quality score)
├── candle_analysis.py     ← Phân tích từng nến → dự đoán xu hướng
├── indicators.py          ← RSI, MACD, ATR, SMA, EMA, BB, Fib
├── collector.py           ← Poll giá (fallback Gold-API)
├── mt5_connector.py       ← Đọc nến trực tiếp từ MT5
├── alert_engine.py        ← Cảnh báo giá
├── scheduler.py           ← Báo cáo định kỳ
├── analyzer.py            ← Gọi AI (8 provider)
├── config.py              ← Cấu hình
├── storage.py             ← SQLite (lưu key + nến)
├── main.py                ← Khởi động
├── requirements.txt
├── SETUP.md
└── data/                  ← tự tạo (xau_bot.db)
```

> ⚠️ **Không cần copy** file `.service` (dành cho Linux systemd) và `tnvgold.env.example` (tham khảo).

---

## 1. Cài Python trên VPS

1. Vào https://python.org/downloads/ → tải **Python 3.11+** (Windows installer)
2. Khi cài, **TÍCH CHỌN "Add Python to PATH"** (rất quan trọng)
3. Kiểm tra: mở `cmd` → `python --version`

## 2. Copy code bot lên VPS

- Copy thư mục `TNVGold Telegram` → `C:\TNVGold`

## 3. Cài dependencies

Mở `cmd` trong thư mục bot:

```cmd
cd C:\TNVGold
pip install -r requirements.txt
pip install MetaTrader5
```

> `MetaTrader5` — thư viện đọc nến trực tiếp từ MT5 đang chạy (chỉ chạy trên Windows có MT5 — đúng case của bạn).

## 4. Cấu hình

### A. Telegram token (bắt buộc)
Tạo file `telegram_token.txt` trong `C:\TNVGold`, dán token bot vào:
```
123456:ABC-...
```
(hoặc set biến môi trường `TELEGRAM_BOT_TOKEN`)

### B. Chọn chế độ MT5 (quan trọng!)
Tạo file `tnvgold.env` (hoặc set biến môi trường) với:
```
MT5_MODE=local
```

> `local` = bot đọc nến M5/M15/M30/H1 trực tiếp từ MT5 trên VPS — **chính xác nhất**.

### C. API key AI (qua Telegram, không cần sửa file)
Bot lưu key trong SQLite. Sau khi chạy, mở Telegram gõ:
```
/keys set deepseek sk-xxx      → thêm key DeepSeek
/keys                           → xem trạng thái
/model deepseek                 → chọn AI dùng
```

Hỗ trợ 8 AI: `deepseek`, `gemini`, `openai`, `claude`, `grok`, `openrouter`, `kiraai`, `ollama`.

## 5. Chạy thử

```cmd
cd C:\TNVGold
python main.py
```

Mở Telegram, gõ `/start` → `/xau` để test.

## 6. Chạy 24/7 bằng Task Scheduler (kể cả khi đóng cửa sổ)

1. Mở **Task Scheduler** (tìm trong Start menu)
2. **Create Task**:
   - **General**: đặt tên `TNVGoldBot`, chọn "Run whether user is logged on or not"
   - **Triggers**: New → "At startup"
   - **Actions**: New → Start a program:
     - Program: `C:\Python3xx\python.exe` (đường dẫn Python — xem bằng `where python`)
     - Arguments: `main.py`
     - Start in: `C:\TNVGold`
   - **Settings**: tick "Restart if fails" (mặc định)
3. **OK** — bot chạy tự động mỗi khi VPS khởi động

---

## 📱 Các lệnh bot trên Telegram

| Lệnh | Chức năng |
|---|---|
| `/start` | Hướng dẫn |
| `/xau` `/xau m5` | Báo cáo tổng M5 (xu hướng + TNV + khuyến nghị) |
| `/xau m15` `/xau h1` `/xau h4` | Báo cáo tổng theo khung |
| `/candle` `/candle m5` | Phân tích nến M5 → dự đoán nến tiếp |
| `/candle m15` `/candle h1` | Phân tích nến theo khung |
| `/news` | Lịch kinh tế XAUUSD hôm nay (Forex Factory) |
| `/tnvgold` `/tnv` | Tín hiệu TNV (SYSTEM 1) — Score, Entry/SL/TP, HTF filter |
| `/indicators` | Bảng chỉ báo (RSI, MACD, ATR, SMA, EMA, BB, Fib) |
| `/price` | Giá hiện tại |
| `/alert 3000` | Đặt cảnh báo giá |
| `/alerts` `/delalert <id>` | Xem / xóa alert |
| `/keys` | Xem/xử lý API key |
| `/keys set <ai> <key>` | Thêm key |
| `/keys remove <ai>` | Xóa key |
| `/model` | Xem AI đang dùng |
| `/model <ai>` | Đổi AI |
| `/lang` | Đổi ngôn ngữ (vi/en) |

---

## 🧠 Thứ tự ưu tiên AI tự chọn

Khi chưa `/model`, bot tự chọn AI đầu tiên có key theo thứ tự:

```
DeepSeek → Gemini → ChatGPT → Claude → Grok → OpenRouter → KiraAI → Ollama
```

---

## ⚠️ Lưu ý quan trọng

1. **MT5 phải chạy** khi bot khởi động để đọc nến local. Nếu MT5 chưa mở → bot tự fallback Gold-API.
2. **Không tự tin tuyệt đối** — bot phân tích tham khảo, tự chịu trách nhiệm khi giao dịch thật.
3. **API key nằm trong SQLite** (`data/xau_bot.db`) — không phải file text, quản lý qua `/keys`.
4. **Bảo mật**: chỉ cho `ALLOWED_CHAT_IDS` dùng bot, firewall chỉ mở port cần thiết.
# TNV Gold — MT5 Data Flow & EA/Indicator Analysis

> Phân tích luồng dữ liệu MT5 lên web, cấu trúc EA WebBridge và độ chính xác
> của các chỉ báo (RSI / ATR / ADX / VWAP / EMA / Multi-TF / HTF).
> Người phân tích: `mt5-analyzer` (team tnv-audit-improve). Trạng thái: CHỈ PHÂN TÍCH — chưa thực thi.

---

## 1. Tổng quan pipeline

```
[MT5 Indicator "10s TNV V2" (.ex5 — KHÔNG có source trong repo)]
        │  iCustom + CopyBuffer (buffer 0,1,3,6,7)
        ▼
[TNV_WebBridge_EA.mq5  — docs/TNV_WebBridge_EA.mq5]
        │  tự tính bias / score / RSI / ATR / EMA / Multi-TF / HTF
        │  WebRequest POST → https://tnvgold.vercel.app/api/pulse
        ▼
[Next.js /api/pulse POST — src/app/api/pulse/route.ts]
        │  check auth (Bearer) → JSON.parse → merge → updatePulse()
        ▼
[pulse-store.ts — Upstash Redis: tnv:current_pulse + tnv:pulse_history]
        ▼
[GET /api/pulse → live-pulse-context.tsx poll 10s]
        ▼
[UI: LiveMetricsGrid / TechnicalGrid / AnalysisSummary ...]
```

**Điểm mấu chốt:** Indicator "10s TNV V2" (nguồn tính toán chính) **không có trong repo**.
EA tự tính lại toàn bộ giá trị từ MqlRates/CopyClose, nên mọi thứ RSI/ATR/EMA/ADX/VWAP
trên web đến từ EA, không phải từ indicator gốc.

---

## 2. Các lỗi / vấn đề PHÁT HIỆN (xếp theo mức nghiêm trọng)

### 🔴 BLOCKER / NGHIÊM TRỌNG

#### B1. ADX và VWAP là HẰNG SỐ CỨNG (hardcode) — dữ liệu giả
`docs/TNV_WebBridge_EA.mq5:188`
```mql5
"indicators":{"rsi":%.1f,"atr":%.2f,"emaGap":%.2f,"adx":32.4,"vwap":6.20,"spread":%.2f}
```
- `adx` luôn = **32.4**, `vwap` luôn = **+6.20** bất kể thị trường.
- UI `TechnicalGrid` hiển thị badge **"Strong Trend"** (ADX>25) và **"Above VWAP / Bullish Flow"**
  dựa trên 2 giá trị này → **luôn luôn sai / mang tính trang trí**.
- Hệ quả: các chỉ báo "trend strength" và "volume flow" trên dashboard là FAKE.

#### B2. Mismatch token xác thực → mặc định EA luôn bị 401 (và endpoint lại mở)
- EA: `InpSecretToken = "**REDACTED**"` (`.mq5:14`), gửi `Authorization: Bearer **REDACTED**`.
- Web: `process.env.TNV_SECRET_KEY || "**REDACTED**"` (`route.ts:21`).
- Nếu không set env `TNV_SECRET_KEY`, mặc định `**REDACTED**` ≠ `**REDACTED**`
  → **MỌI POST từ EA bị 401**, pulse không bao giờ cập nhật. README không nói set env này.
- **Đồng thời** tại `route.ts:24`: `if (authHeader && authHeader !== ...)`. Nếu không có header
  `Authorization` thì **bỏ qua kiểm tra** → endpoint thực chất là **mở (unauthenticated write)**.
  Người khác có thể POST dữ liệu giả mà không cần token.
- Kết luận: đường xác thực "đúng" bị vỡ (EA bị từ chối), còn kẻ tấn công chỉ cần **bỏ header** là qua.

#### B3. Source indicator "10s TNV V2" không có trong repo
- EA phụ thuộc `iCustom(_Symbol, PERIOD_CURRENT, "10s TNV V2")` nhưng không có `.mq5`/tài liệu
  mô tả buffer nào là gì. Chỉ có EA. → Không thể audit công thức gốc, không tái lập được, dễ vỡ nếu
  chỉnh indicator (đổi số buffer).

#### B4. Ghi history trùng lặp / không idempotency (dedup nhiều chart)
- `pulse-store.ts:138-142`: mỗi POST đều `history.unshift(snapshot)` — không kiểm tra trùng `time`.
- Nếu nhiều chart cùng symbol M5 (hoặc EA restart), mỗi lần đóng nến M5 sẽ ghi **nhiều bản ghi trùng** vào history.
- `g_last_candle` (`.mq5:42-44`) chỉ dedup theo thời điểm nến M5, **không** áp dụng giữa nhiều EA/nhiều chart.

### 🟠 CAO

#### C1. Công thức EMA chạy SAI CHIỀU (backward replacement)
`.mq5:133-139`
```mql5
ema9 = ema9_arr[0];  // [0] = nến mới nhất (series)
for(i = 1; i < 30; i++) ema9 = (ema9_arr[i] - ema9)*m9 + ema9;
```
- `ArraySetAsSeries(ema9_arr, true)` → index 0 = hiện tại. Vòng lặp chạy **từ mới → cũ**,
  seed tại giá hiện tại và cộng dồn ngược thời gian.
- EMA chuẩn là phép đệ quy **hướng thuận (quá khứ → hiện tại)**. Chạy ngược cho kết quả luôn
  bám sát giá hiện tại → `ema9 ≈ ema21 ≈ price` → `emaGap ≈ 0`. Tín hiệu EMA gap gần như vô nghĩa.
- Cần seed từ chỉ báo cũ nhất (index 29) rồi chạy xuôi về index 0 (hiện tại).

#### C2. RSI không chuẩn Wilder / dùng kiểu Cutler + chỉ dựa vào Close
`.mq5:117-125`: dùng tổng gains/losses tuyệt đối (Cutler's RSI), không smooth Wilder, và
chỉ dựa trên `CopyClose`, mặc `losses==0 → 100`. Sẽ lệch so với `iRSI` chuẩn của MT5.
Đáng chú ý: `tnv-engine.ts` không có RSI; RI chỉ nằm bên EA.

#### C3. "ATR" thực chất là TR trung bình cộng giản đơn, không phải ATR Wilder
`.mq5:113` `volatility = tr_sum / 20.0` (trung bình cộng TR) rồi `.mq5:128` `atr_val = volatility`.
- Web hiển thị nhãn **ATR** nhưng giá trị là trung bình cộng TR 20 nến, **không** dùng Wilder smoothing
  (khác `iATR` và khác `computeWilderVolatility` trong `tnv-engine.ts:51`). → sai lệch giá trị ATR.

#### C4. Score (Quality Score) từ EA không khớp engine TNV
- EA `.mq5:84-96` chỉ gán `score = 4` (NEUTRAL) hoặc `8` (LONG/SHORT) + override 8 khi có mũi tên.
- Trong khi `tnv-engine.ts:calculateQualityScore` (score 0–10, điều kiện bắt buộc body ratio ≥0.5,
  close trong 1/3, bonus range/HTF/N) **không** được EA sử dụng.
- Kết quả: "Quality Score / Pulse" hiển thị trên web = 4 hoặc 8 cố định → **không phản ánh chất lượng tín hiệu**.
- `m15s/m30s/h1s` = 8/7/9 cố định (`.mq5:158,166,174`) cũng là số trang trí.

#### C5. "HTF" nhãn sai: không phải filter HTF thật
`.mq5:177-178`: `if(bias=="NEUTRAL") htfLabel="Pass"; else htfLabel="Not Against";`
- Nhãn "Pass" / "Not Against" chỉ dựa trên việc có bias hay không, **không** đánh giá hướng HTF.
  `tnv-engine.ts:isHTFNotAgainst` có logic thật nhưng EA không dùng → badge HTF gây hiểu lầm.

#### C6. Multi-symbol ghi đè lẫn nhau (store một key duy nhất)
- `pulse-store.ts` chỉ có `KV_KEY_PULSE = "tnv:current_pulse"` (một snapshot, không key theo symbol).
- Nếu EA gắn trên nhiều symbol (XAUUSD, ...), mỗi symbol ghi đè `current_pulse` → **last-writer wins**,
  history trộn symbol khác nhau. Không có key/namespace theo symbol.

#### C7. Tên file trong README sai → người dùng không tìm được EA
`README.md:48` ghi `Attach docs/TNV_WebBridge.mq5`, nhưng file thực là `docs/TNV_WebBridge_EA.mq5`.
→ Người dùng làm theo hướng dẫn sẽ không tìm thấy file.

### 🟡 TRUNG BÌNH

#### D1. Kiểm tra số lượng buffer và offset nhạy cảm
- `.mq5:61-63` copy 3 thanh nhưng chỉ dùng `[1]`; `:92-93` copy 5 dùng `[1]` — phụ thuộc vào cách
  indicator nạp buffer (nếu đổi offset/đếm sẽ vỡ). Nên dùng hằng số đặt tên + kiểm tra `copied` đầy đủ.

#### D2. Dữ liệu chỉ cập nhật mỗi khi đóng nến M5 (độ trễ lên tới ~5 phút)
- `.mq5:42-44` gate `if(iTime_M5 == g_last_candle) return;` → mỗi nến M5 đóng mới gửi 1 lần,
  trong khi frontend poll 10s. "Price / Bias / Score" trên web **đứng yên** giữa các nến → không "real-time".
- Cân nhắc gửi theo tick hoặc gửi khi bias/score thay đổi; hoặc chấp nhận & hiển thị rõ độ trễ.

#### D3. `exit10` chỉ là support/level thấp (không phải profit target)
- Với M5/M15/M30/H1, `exit10` = 10-nến thấp nhất — bản chất là **hỗ trợ/stop**, không phải mục tiêu lời.
  Nhãn "Exit" gây hiểu lầm về hướng khi bias = LONG (lẽ ra nên dùng exit high).

#### D4. Thời gian: không chuẩn hóa timezone
- EA gửi `TimeToString(TimeCurrent())` = giờ terminal. Web lưu nguyên chuỗi này; `serverTime` của
  GET là ISO UTC. Frontend không normalize → người xem khác múi giờ thấy giờ/giá trị lệch.

#### D5. Không retry / không báo lỗi ra UI, chỉ `PrintFormat` (terminal log)
- `.mq5:207` chỉ in log khi HTTP ≠ 200/201; khi `WebRequest` trả -1 (URL chưa allow-list, chỉ mạng…)
  người dùng web không hề biết. Không có cơ chế retry/backoff; gọi `WebRequest` đồng bộ trong `OnTick`
  có thể block terminal nếu server chậm.

#### D6. `spread_val` default tĩnh 1.2 (đô la)
- `.mq5:143` `if(spread_val <= 0) spread_val = 1.2;` — giá trị mặc định cứng, có thể không đúng
  với spread XAUUSD thực tế.

#### D7. `analysisText` không do EA gửi
- JSON trong EA `.mq5:180-195` **không** có `analysisText` → web luôn dùng `current.analysisText`
  (text seed/template trong `language-context.tsx`) hoặc sinh client-side (`AnalysisSummary.tsx::genAnalysis`).
  → "phân tích tự động" thực chất là template, không phải dữ liệu MT5.

---

## 3. Đề xuất cải thiện (ưu tiên)

### Khắc phục ngay (blocker)
1. **B1 — Tính ADX thật** bằng `iADX`/`CopyBuffer` hoặc tự tính DI+/DI−/DX; **tính VWAP thật**
   (vol×price tích lũy / vol tích lũy trong ngày/phiên). Bỏ 2 hằng số 32.4 / 6.20.
2. **B2 — Một nguồn token duy nhất**: đặt `TNV_SECRET_KEY` trong Vercel = giá trị `InpSecretToken`;
   và **bắt buộc** kiểm tra header (không cho "bỏ qua khi thiếu header") → đổi `if (authHeader && ...)`
   thành `if (authHeader !== Bearer ${secretKey}) return 401;`. Trả về 401 khi thiếu/khớp sai.
3. **B4 — Dedup/idempotency**: thêm `id`/key theo `(symbol,time)` để không ghi trùng history
   (server-side `Set`/so sánh entry đầu history); EA dùng `GlobalVariable` (hoặc `datetime` timestamp
   + `symbol`) để không gửi trùng giữa nhiều chart cùng symbol.
4. **B3/C7 —** bổ sung source indicator hoặc ghi rõ số buffer vào tài liệu; sửa README về
   `TNV_WebBridge_EA.mq5`.

### Cải thiện chỉ báo & độ chính xác
5. **C1** — Viết lại EMA chạy **quá khứ → hiện tại** (seed index 29, đệ quy xuôi về 0). Thêm test
   đối chiếu với `iMA` (EMA9/EMA21).
6. **C2** — Dùng RSI Wilder chuẩn (smooth avg gain/loss) khớp `iRSI(...,14)`; tối ưu: tính trên M5.
7. **C3** — `atr_val` dùng Wilder smoothing (khớp `iATR(...,14)` và `computeWilderVolatility`).
8. **C4** — EA tính Quality Score theo đúng `calculateQualityScore` (body ratio, close 1/3,
   bonus range/HTF/N) để score 0–10 có nghĩa; bỏ score cứng 4/8.
9. **C5** — Dùng `isHTFNotAgainst` / so hướng nến HTF thật để đặt `htf` thay vì chỉ "Not Against".
10. **C6** — Key Redis theo symbol: `tnv:current_pulse:{symbol}`, `tnv:pulse_history:{symbol}`.

### Trải nghiệm / vận hành
11. **D2** — Hoặc gửi theo sự thay đổi bias/score giữa các tick, hoặc thêm dấu "last updated" rõ ràng.
12. **D3** — Đổi nhãn/ý nghĩa "exit": phân biệt `exitHigh` (mục tiêu khi LONG) vs `exitLow` (stop).
13. **D4** — Chuẩn hóa thời gian về UTC (ISO) khi lưu; frontend `toLocaleTimeString` theo client.
14. **D5** — Thêm retry/backoff, log lỗi rõ ràng (kể cả -1), hiển thị trạng thái kết nối trên UI.
15. **D7** — Hoặc EA gửi `analysisText`, hoặc bỏ nhãn "phân tích tự động" để không gây hiểu lầm.

---

## 4. Kết luận
- Pipeline MT5 → Web có đủ các mắt xích (EA → API → Redis → UI) và **hoạt động về mặt cơ chế**,
  nhưng **độ chính xác dữ liệu chiến lược thấp**: ADX/VWAP là hằng số, EMA ngược chiều, ATR không Wilder,
  score chỉ 4/8, HTF là nhãn giả.
- **Điều kiện tiên quyết để "thật":** (a) xác thực token nhất quán + bắt buộc, (b) dedup/khóa theo symbol,
  (c) tính lại ADX/VWAP thật, (d) sửa EMA/ATR/RSI/score cho khớp engine TNV.
- Không thực thi thay đổi nào — **chờ người dùng xác nhận** trước khi code (đúng quy trình team).

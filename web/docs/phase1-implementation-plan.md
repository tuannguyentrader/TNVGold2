# Kế hoạch triển khai Giai đoạn 1 (GĐ1) — TNVGold

> Nguồn: `docs/improvement-plan-t4.md` (mục 4 MT5, mục 7 lộ trình GĐ1) + `docs/analysis/MT5_DATAFLOW_AND_EA_ANALYSIS.md` + `docs/TNV_WebBridge_EA.mq5`.
> Người lập: `web-analyzer` (task T11). Trạng thái: **KẾ HOẠCH** — chưa thực thi; chờ người dùng xác nhận trước khi code.
> Quy ước: mỗi mục có mã gốc (C4/C5/B3/D3/D4/D5/C7) kèm file:line để truy vết.

---

## 0. Tóm tắt GĐ1

Mục tiêu GĐ1: đưa **dữ liệu chiến lược trở nên đúng và đáng tin** sau khi đã hoàn tất GĐ0 (an toàn + trung thực phía web). GĐ1 gồm **7 mục**, được nhóm thành **3 nhóm** theo nơi triển khai (MT5 thuần / Web thuần / xuyên nhóm), sắp theo lộ trình sprint/commit nhỏ, độc lập, chạy được.

Về bản chất, GĐ1 là **chuyển trọng tâm từ "hiển thị con số trang trí" sang "số liệu có cơ sở"**: điểm chất lượng tín hiệu thật (score 0–10), nhãn HTF theo hướng thật, phân biệt mục tiêu giá (exitHigh) với dừng lỗ (exitLow), thời gian chuẩn UTC, cơ chế retry/backoff + trạng thái kết nối hiển thị, và tài liệu nguồn indicator để có thể audit & tái lập.

---

## 1. Danh mục đầy đủ 7 mục (mô tả + lý do)

| # | Mã | Mục | Mô tả | Lý do | Nhóm |
|---|---|---|---|---|---|
| 1 | C4-MT5 | **Score theo `calculateQualityScore` thật** | EA tính score 0–10 theo đúng thuật toán quality (body ratio ≥0.5, close trong 1/3, bonus range/HTF/N) thay vì score cứng 4/8; bỏ `m15s/m30s/h1s` = 8/7/9 cứng | "Quality Score/Pulse" hiện chỉ là số trang trí, không phản ánh chất lượng tín hiệu | MT5 |
| 2 | C5-MT5 | **HTF theo hướng thật** | `htf` dựa trên hướng HTF thật (so high/low liên tiếp — logic `isHTFNotAgainst`), thay cho nhãn "Pass"/"Not Against" chỉ dựa trên có bias hay không | Badge HTF gây hiểu lầm, không phải filter thật | MT5 |
| 3 | B3-MT5 | **Bổ sung source indicator / tài liệu buffer** | Bổ sung source `.mq5` của "10s TNV V2" hoặc tài liệu hoá buffer (0,1,3,6,7) và ý nghĩa từng buffer; EA kiểm tra `copied` đầy đủ | Không audit được công thức gốc; dễ vỡ nếu chỉnh indicator/đổi buffer | MT5 |
| 4 | D3-MT5 | **Phân biệt exitHigh / exitLow** | Thêm `exitHigh` (mục tiêu lời) và `exitLow` (dừng lỗ/hỗ trợ), dùng đúng theo chiều bias; sửa nhãn hiển thị | `exit10` hiện chỉ là support/stop, nhãn "Exit" gây hiểu lầm về hướng | MT5 + Web |
| 5 | D4-MT5 | **Chuẩn hoá timezone UTC** | EA gửi thời gian theo UTC/ISO; web lưu UTC; frontend hiển thị theo múi giờ người xem | Người xem khác múi giờ thấy thời gian/giá trị lệch | MT5 + Web |
| 6 | D5-MT5 | **Retry/backoff + hiển thị trạng thái kết nối** | EA retry/backoff khi lỗi (`-1`, 429, network), log rõ kể cả lỗi allow-list; web hiển thị trạng thái kết nối (surface `isLiveConnected`/`lastUpdated`) | Người dùng web không biết khi WebRequest fail; EA block nếu server chậm | MT5 + Web |
| 7 | C7-MT5 | **Sửa README tên file** | `README.md:48` đổi từ `docs/TNV_WebBridge.mq5` → `docs/TNV_WebBridge_EA.mq5` | Người dùng làm theo hướng dẫn không tìm thấy file | Web/doc |

---

## 2. Phân nhóm triển khai (Web / MT5 / Xuyên nhóm)

**A. MT5 thuần (indicator/EA) — `docs/TNV_WebBridge_EA.mq5`:**
- (1) Score thật (C4) — logic tính score 0–10 trong EA (port `calculateQualityScore` từ `src/lib/tnv-engine.ts` sang MQL5).
- (2) HTF thật (C5) — tính hướng HTF theo high/low + set `htf` đúng.
- (3) Source indicator + tài liệu buffer (B3) — thêm source `.mq5` hoặc doc buffer + guard `copied`.

**B. Web thuần — `README.md`:**
- (7) Sửa tên file (C7).

**C. Xuyên nhóm (MT5 gửi + Web nhận/hiển thị):**
- (4) exitHigh/exitLow (D3): EA thêm trường; `src/types`/`src/lib/pulse-store.ts` schema; UI (LiveMetricsGrid/TechnicalGrid/HistoryTable/AnalysisSummary) hiển thị.
- (5) Timezone UTC (D4): EA gửi ISO/UTC; web `formatTime`/hiển thị theo client; lưu UTC.
- (6) Kết nối & retry (D5): EA retry/backoff; web surface `isLiveConnected`/`lastUpdated` (context đã có sẵn từ T9) + thành phần status.

**Lưu ý:** các thay đổi schema (exitHigh/exitLow, time) vừa chạm MT5 vừa chạm web → nên làm **một commit cho cả 2 phía** để giữ consistency (không để MT5 gửi trường lạ mà web chưa hiểu hoặc ngược lại).

---

## 3. Ưu tiên theo tác động + khó khăn

| Ưu tiên | Mục | Tác động | Khó khăn | Lý do ưu tiên |
|---|---|---|---|---|
| **Cao** | (3) B3 — source/tài liệu buffer | Cao (audit/tái lập) | Thấp–Trung (chỉ doc/guard) | Nền tảng để (1)/(2) chính xác; không có buffer mapping thì HTF/score khó kiểm chứng |
| **Cao** | (2) C5 — HTF thật | Cao (đúng nghĩa filter) | Trung (cần HTF candles + logic) | Nhãn HTF hiện gây hiểu lầm; là thành phần bên trong (1) |
| **Cao** | (1) C4 — Score thật | Cao (Pulse/score có nghĩa) | Trung–Cao (port thuật toán + test) | Lõi "chất lượng tín hiệu"; phụ thuộc (2)+(3) |
| **Trung** | (4) D3 — exitHigh/exitLow | Trung (đúng đắn hiển thị) | Trung (schema 2 phía) | Nhãn/target rõ ràng; schema change |
| **Trung** | (5) D4 — timezone UTC | Trung (đúng đắn) | Thấp–Trung | Dễ làm; cải thiện đáng kể trải nghiệm đọc |
| **Trung** | (6) D5 — retry + status | Trung (đáng tin/vận hành) | Trung (EA + web) | Biết được trạng thái kết nối; tránh block |
| **Thấp** | (7) C7 — README | Thấp (không code) | Rất thấp (1 dòng) | Sửa nhanh, làm sớm để hướng dẫn đúng |

**Gạch đầu dòng việc NÊN LÀM TRƯỚC (theo tác động/phụ thuộc):**
- ✅ Sửa `README.md` tên file (7) — 1 phút, không rủi ro, làm ngay.
- ✅ Tài liệu hoá buffer indicator "10s TNV V2" + guard `copied` (3) — trước mọi tính toán HTF/score để có dữ liệu kiểm chứng.
- ✅ HTF thật (2) — trước (1) vì score dùng HTF.
- ✅ Score thật (1) — sau (2)+(3).
- ✅ exitHigh/exitLow (4), timezone UTC (5), retry/backoff + trạng thái kết nối (6) — độc lập, làm sau cụm chỉ báo, mỗi mục 1 commit nhỏ.

---

## 4. Lộ trình sprint/commit nhỏ (mỗi commit chạy được, độc lập)

**Sprint 0 — Chuẩn bị & nền tảng (ready, cheap):**
1. **Commit G1-1 [Web/doc]** — Sửa `README.md:48` → `docs/TNV_WebBridge_EA.mq5`. *(C7)*

**Sprint 1 — Nền tảng dữ liệu chỉ báo (MT5) — [GĐ1 chính]:**
2. **Commit G1-2 [MT5/doc]** — Bổ sung `docs/indicator-tnv-v2-buffers.md` (hoặc source `.mq5`) mô tả buffer 0/1/3/6/7; EA thêm guard kiểm tra `CopyBuffer` đủ số phần tử & sửa offset bằng hằng số đặt tên. *(B3/D1)*
3. **Commit G1-3 [MT5]** — Tính hướng HTF thật (high/low liên tiếp trên M15/M30/H1) và set `htf` đúng (bỏ nhãn "Pass/Not Against" chỉ dựa trên bias). *(C5)*
4. **Commit G1-4 [MT5]** — Port `calculateQualityScore` → MQL5; tính score 0–10 thật (bodyRatio, close trong 1/3, bonus range/HTF/N) dùng volatility + HTF thật; bỏ score cứng 4/8 và `m15s/m30s/h1s` cứng. *(C4)*

**Sprint 2 — Đúng đắn dữ liệu & kết nối (MT5 + Web):**
5. **Commit G1-5 [MT5+Web]** — exitHigh/exitLow: EA gửi `exitHigh`+`exitLow`; `src/lib/pulse-store.ts`/`src/types` thêm trường (tương thích cũ bằng `??`/default); UI (LiveMetricsGrid "EXIT", TechnicalGrid, HistoryTable, AnalysisSummary) hiển thị target/stop đúng theo bias. *(D3)*
6. **Commit G1-6 [MT5+Web]** — Timezone UTC: EA gửi ISO/UTC; `pulse-store` lưu UTC; web `formatTime`/table/gauge hiển thị theo client; tránh mix `TimeToString` terminal + `serverTime` ISO. *(D4)*
7. **Commit G1-7 [MT5+Web]** — Retry/backoff trong EA (kể cả lỗi `-1`/429, log rõ, không block `OnTick` quá lâu) + web surface `isLiveConnected`/`lastUpdated` (thành phần status: chấm kết nối + "cập nhật Xs trước" + trạng thái offline). *(D5 + UX P3)*

**Sprint 3 (tùy chọn) — Hoàn thiện hiển thị:**
8. **Commit G1-8 [Web]** — Nếu còn, đồng bộ hiển thị (chấm kết nối, exit label, dấu thời gian client-local) cho đúng với schema đã đổi; chạy `npm run typecheck` + `npm run lint` (2 file web đã sửa).

---

## 5. Phụ thuộc giữa các mục (mục nào phải xong trước)

```
(7) README ──────────────────────────────────────────┐  (độc lập, làm sớm)
                                                     ▼
(3) Source indicator / doc buffer ──► (2) HTF thật ──► (1) Score thật
        │   ▲                              ▲                │
        │   └──── (3) cần xong trước (2) ───┘                │
        │                                                   │
        └───────────────────────────────────────────────────┘
                                                 (1) dùng kết quả HTF của (2)

(4) exitHigh/exitLow ──► (6) hiển thị exit mới phụ thuộc schema (4)
(5) timezone UTC  ── độc lập ──┐
(6) retry/backoff + status ────┘ (6-web) có thể dùng `isLiveConnected` đã có từ T9
```

- **(1) score thật phụ thuộc (2) HTF thật** (vì `calculateQualityScore` nhận `htfCandles`/`isHTFNotAgainst`). → (2) trước (1).
- **(2) HTF thật phụ thuộc (3) buffer mapping đúng** (vì đọc HTF candles qua `iCustom`). → (3) trước (2).
- **(4) exitHigh/exitLow & (5) timezone & (6) kết nối độc lập với (1)(2)(3)** → có thể song song sau cụm chỉ báo, nhưng (6-web) schema hiển thị exit chỉ có ý nghĩa sau (4).
- **(7) README độc lập** — làm trước để hướng dẫn đúng.
- **Web phải cùng commit với MT5 cho (4)(5)(6)** để giữ schema nhất quán 2 phía.

---

## 6. Cách kiểm thử / verify từng mục

| Mục | Cách kiểm thử / verify | Công cụ |
|---|---|---|
| (1) Score thật | So sánh score EA với giá trị mong đợi trên các nến mẫu (body ≥50%, close 1/3, range/HTF); assert khoảng 0–10; đối chiếu lại trên UI (Pulse/Gauge/HistoryTable) khớp EA | MetaEditor + Strategy Tester; kiểm thử TS port (nếu giữ engine) |
| (2) HTF thật | Kiểm tra htf = "Bullish"/"Bearish"/"Neutral" theo hướng high/low HTF; so với `isHTFNotAgainst`; ghi log nến để đối chiếu tự động | MetaEditor log; test đơn vị logic (port) |
| (3) Buffer/doc | `CopyBuffer` đủ số phần tử; offset đặt hằng số; doc mô tả đúng buffer 0/1/3/6/7; thử với indicator thật | Compile EA (MetaEditor) + kiểm tra log không có "buffer insufficient" |
| (4) exitHigh/exitLow | Với bias LONG: exitHigh > exitLow; web hiển thị "Mục tiêu"/"Dừng lỗ" đúng; với SHORT ngược lại | API POST mẫu + GET → kiểm tra schema; UI snapshot |
| (5) Timezone UTC | EA gửi ISO/UTC; Redis lưu UTC; web `formatTime` hiển thị theo múi giờ client; so khớp giữa các múi giờ khác nhau | So sánh chuỗi thời gian; test client format |
| (6) Retry + kết nối | Giả lập mạng fail/`-1`/429 → retry có backoff, log rõ; không treo OnTick; web hiện "offline"/"cập nhật Xs" qua `isLiveConnected`/`lastUpdated` | Giả lập WebRequest lỗi (terminal), kiểm tra UI status |
| (7) README | File `docs/TNV_WebBridge_EA.mq5` tồn tại; đường dẫn trong README khớp | `ls docs/TNV_WebBridge_EA.mq5` |

**Verify chung khi chạm web:** `npm run typecheck` (bắt buộc PASS), `npm run lint` (2 file web đã sửa phải sạch; toàn project còn 5 lỗi/3 warning **tồn tại từ trước** ở file ngoài phạm vi — vấn đề C5 ghi nhận riêng). **Khi chạm MT5:** compile EA bằng MetaEditor/Strategy Tester; không có test harness tự động — cần kiểm thử thủ công có checklist.

---

## 7. Rủi ro & lưu ý

- **(1)(2) đổi logic EA → ảnh hưởng trực tiếp dữ liệu hiển thị.** Cần kiểm thử trên dữ liệu thật trước khi deploy để không đẩy số liệu "sai kiểu mới" lên production.
- **Source indicator "10s TNV V2" chưa có trong repo.** Nếu không có source, buộc lòng chỉ tài liệu hoá buffer (3) — chấp nhận giới hạn audit; nếu có, bổ sung source để (1)(2) chính xác.
- **Schema (4)(5) đổi 2 phía** → phải deploy web + EA cùng lúc để tránh web không hiểu trường mới hoặc EA gửi trường lạ.
- **Mức ưu tiên GĐ1 trong báo cáo t4** đặt đúng chuẩn chỉ báo (1)(2) làm lõi; các mục (4)(5)(6)(7) hoàn thiện độ đáng tin/trải nghiệm sau đó.
- Mọi commit **chờ người dùng xác nhận** trước khi thực thi (team goal).

---

## Phụ lục: tham chiếu file
- `docs/TNV_WebBridge_EA.mq5` — EA gửi webhook (sửa score/HTF/exit/time/retry).
- `src/lib/tnv-engine.ts` — thuật toán `calculateQualityScore`/`computeWilderVolatility`/`isHTFNotAgainst` (nguồn port sang MQL5).
- `src/lib/pulse-store.ts` — schema `PulseSnapshot` (thêm exitHigh/exitLow; chuẩn hoá time).
- `src/components/sites/tnv-goldpulse/LiveMetricsGrid.tsx`, `TechnicalGrid.tsx`, `HistoryTable.tsx`, `AnalysisSummary.tsx` — hiển thị exit/time/status.
- `src/lib/live-pulse-context.tsx` — `isLiveConnected`/`lastUpdated` (sẵn sàng để surface, từ T9).
- `README.md:48` — sửa tên file.
- `docs/improvement-plan-t4.md` (§4 MT5, §7 GĐ1) — nguồn kế hoạch.

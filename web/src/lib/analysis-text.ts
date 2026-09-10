// Sinh câu phân tích AI (khối TNV ANALYSIS trên dashboard) từ dữ liệu pulse.
//
// Tách khỏi component để TEST ĐƯỢC bằng dữ liệu thật — trước đây nằm trong
// AnalysisSummary.tsx (React) nên không kiểm chứng được, dẫn tới lỗi số liệu
// tồn tại âm thầm.
//
// ⚠️ LỖI ĐÃ SỬA (báo cáo 10/09/2026):
// Câu cũ: "Gold is displaying strong bullish momentum as Pulse reaches 100 and
// the price sits +0.05% above the $4423.31 level..."
//   - $4423.31 là TP. Với lệnh LONG, TP LUÔN nằm TRÊN giá (giá 4417.63 < TP
//     4423.31) → câu nói giá "ở trên TP" là SAI NGƯỢC sự thật.
//   - Mốc so sánh đúng là ENTRY — mức giá bứt phá mà lệnh đã đi qua
//     ($4415.63, giá đang cao hơn $2.00 = +0.05%).
//   - "Pulse reaches 100" lấy giá trị kim đồng hồ (score × 10) đưa vào câu
//     chữ → lệch với thang 0-10 của tín hiệu Telegram ("score 10"). Nay dùng
//     score/10 cho mọi câu chữ; kim đồng hồ vẫn vẽ theo thang 0-100.
//   - Khoảng cách chỉ ghi % nhưng gắn vào mốc TP; nay ghi cả USD + % so với
//     entry, đúng chiều (above/below theo dấu thật của giá - entry).
//   - Nhánh SHORT còn dùng string surgery hỏng (replace "+"/"-") làm mất dấu.

import type { PulseSnapshot } from "./pulse-store";

export type AnalysisLang = "vi" | "en";

export function buildAnalysisText(
  pulse: PulseSnapshot,
  language: AnalysisLang
): string {
  // Ưu tiên analysisText do bot gửi kèm (nếu có)
  if (pulse.analysisText?.[language]) return pulse.analysisText[language]!;

  const score = pulse.score;
  const price = pulse.price;

  // Mốc so sánh = giá entry (breakout); thiếu thì lấy giá hiện tại
  const entryRef = pulse.entry.price ?? price;
  const diff = price - entryRef;
  const absDiff = Math.abs(diff);
  const gainVal = pulse.entry.gain ?? 0;
  const gainText = `${gainVal >= 0 ? "+" : ""}${gainVal.toFixed(2)}%`;
  // Mục tiêu / dừng lỗ; fallback theo N khi chưa có lệnh
  const tpRef = pulse.tp ?? price + pulse.volatility * 2;
  const slRef = pulse.sl ?? price - pulse.volatility * 1.5;
  const sideEn = diff >= 0 ? "above" : "below";
  const sideVi = diff >= 0 ? "cao hơn" : "thấp hơn";

  // ── NEUTRAL: chưa có lệnh, chỉ so với biên N ──
  if (pulse.bias === "NEUTRAL") {
    if (language === "vi") {
      return `Vàng đang giao dịch đi ngang với chỉ số Pulse ${score}/10, giá ổn định quanh $${price.toFixed(2)}. Cấu trúc đa khung thời gian chưa có sự đồng thuận rõ ràng. Theo dõi: phá vỡ trên $${(price + pulse.volatility).toFixed(2)} để xác nhận đà tăng, hoặc thủng $${(price - pulse.volatility).toFixed(2)} để kích hoạt xu hướng giảm.`;
    }
    return `Gold is trading sideways with Pulse score ${score}/10, price holding around $${price.toFixed(2)}. Multi-timeframe structure is not providing clear directional alignment. Watch for: a breakout above $${(price + pulse.volatility).toFixed(2)} to confirm upside momentum, or a breakdown below $${(price - pulse.volatility).toFixed(2)} to trigger bearish bias.`;
  }

  const direction =
    pulse.bias === "LONG"
      ? language === "vi"
        ? "tăng"
        : "bullish"
      : language === "vi"
        ? "giảm"
        : "bearish";

  // ── SHORT ──
  if (pulse.bias === "SHORT") {
    if (language === "vi") {
      return `Vàng đang duy trì đà ${direction} mạnh mẽ với chỉ số Pulse ${score}/10. Giá $${price.toFixed(2)} đang ${sideVi} mức phá vỡ $${entryRef.toFixed(2)} là $${absDiff.toFixed(2)} (${gainText}). Cấu trúc đa khung thời gian đồng thuận. Theo dõi: đà giảm tiếp diễn hướng tới mục tiêu $${tpRef.toFixed(2)}, hoặc nhịp hồi kiểm tra lại ngưỡng kháng cự $${slRef.toFixed(2)} trước khi hình thành nhịp giảm mới.`;
    }
    return `Gold is displaying strong ${direction} momentum with Pulse score ${score}/10. Price $${price.toFixed(2)} sits $${absDiff.toFixed(2)} (${gainText}) ${sideEn} the $${entryRef.toFixed(2)} breakdown level, with higher-timeframe structure providing clean directional alignment. Watch for: continuation toward the $${tpRef.toFixed(2)} target, or a pullback toward the $${slRef.toFixed(2)} resistance to test supply before the next leg lower.`;
  }

  // ── LONG (mặc định) ──
  if (language === "vi") {
    return `Vàng đang duy trì đà ${direction} mạnh mẽ với chỉ số Pulse ${score}/10. Giá $${price.toFixed(2)} đang ${sideVi} mức bứt phá $${entryRef.toFixed(2)} là $${absDiff.toFixed(2)} (${gainText}). Cấu trúc đa khung thời gian đồng thuận. Theo dõi: đà tăng tiếp diễn hướng tới mục tiêu $${tpRef.toFixed(2)}, hoặc nhịp điều chỉnh kiểm tra lại ngưỡng hỗ trợ $${slRef.toFixed(2)} trước khi hình thành nhịp tăng mới.`;
  }
  return `Gold is displaying strong ${direction} momentum with Pulse score ${score}/10. Price $${price.toFixed(2)} sits $${absDiff.toFixed(2)} (${gainText}) ${sideEn} the $${entryRef.toFixed(2)} breakout level, with higher-timeframe structure providing clean directional alignment. Watch for: continuation toward the $${tpRef.toFixed(2)} target, or a pullback toward the $${slRef.toFixed(2)} support to test demand before the next leg higher.`;
}

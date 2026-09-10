// Helper: lấy pulse hiện tại từ pulse-store
import { getLatestPulse as getLatest } from "./pulse-store";

export async function getLatestPulse() {
  try {
    const p = await getLatest();
    if (!p) return null;
    return {
      symbol: p.symbol,
      price: p.price,
      bias: p.bias,
      score: p.score,
      volatility: p.volatility,
      multiTf: p.multiTf,
      // Vùng giao dịch — để bài blog tự động có khối Entry/SL/TP khi đang có
      // lệnh (bias LONG/SHORT). Trước đây bị cắt nên bài chỉ có giá + bias.
      entry: p.entry,
      sl: p.sl,
      tp: p.tp,
    };
  } catch {
    return null;
  }
}

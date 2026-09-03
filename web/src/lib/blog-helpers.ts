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
    };
  } catch {
    return null;
  }
}

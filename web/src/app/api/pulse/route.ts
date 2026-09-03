import { NextResponse } from "next/server";
import {
  getLatestPulse,
  getPulseHistory,
  updatePulse,
  type PulseSnapshot,
  type MultiTfData,
  type TechnicalIndicators,
} from "@/lib/pulse-store";

export const dynamic = "force-dynamic";

export async function GET() {
  const latest = await getLatestPulse();
  const history = await getPulseHistory();

  return NextResponse.json({
    success: true,
    data: latest,
    history,
    serverTime: new Date().toISOString(),
  });
}

// Merge sâu một cụm MultiTfData: ưu tiên giá trị mới, nhưng giữ giá trị hợp lệ (kể cả 0).
function mergeMultiTf(
  payloadItem: Partial<MultiTfData> | undefined,
  base: MultiTfData
): MultiTfData {
  return {
    bias: payloadItem?.bias ?? base.bias,
    score: payloadItem?.score ?? base.score,
    high: payloadItem?.high ?? base.high,
    low: payloadItem?.low ?? base.low,
    exit: payloadItem?.exit ?? base.exit,
    htf: payloadItem?.htf ?? base.htf,
    volatility: payloadItem?.volatility ?? base.volatility,
  };
}

function mergeIndicators(
  payloadItem: Partial<TechnicalIndicators> | undefined,
  base: TechnicalIndicators
): TechnicalIndicators {
  return {
    rsi: payloadItem?.rsi ?? base.rsi,
    atr: payloadItem?.atr ?? base.atr,
    emaGap: payloadItem?.emaGap ?? base.emaGap,
    adx: payloadItem?.adx ?? base.adx,
    vwap: payloadItem?.vwap ?? base.vwap,
    spread: payloadItem?.spread ?? base.spread,
  };
}

// Đảm bảo nhất quán bias/score: khi bias là NEUTRAL thì không mang ý nghĩa tín hiệu,
// nên score (top-level và từng khung) được đưa về 0 để tránh hiển thị mâu thuẫn
// "NEUTRAL + score cao" trên toàn bộ dashboard.
function normalizeNeutralScore(snapshot: PulseSnapshot): PulseSnapshot {
  const normalizeMultiTfItem = (item: MultiTfData): MultiTfData =>
    item.bias === "NEUTRAL" ? { ...item, score: 0 } : item;

  return {
    ...snapshot,
    score: snapshot.bias === "NEUTRAL" ? 0 : snapshot.score,
    multiTf: {
      m15: normalizeMultiTfItem(snapshot.multiTf.m15),
      m30: normalizeMultiTfItem(snapshot.multiTf.m30),
      h1: normalizeMultiTfItem(snapshot.multiTf.h1),
    },
  };
}

export async function POST(request: Request) {
  try {
    const secretKey = process.env.TNV_SECRET_KEY;

    // Fail closed: nếu chưa cấu hình secret thì từ chối, không có giá trị mặc định trong source.
    if (!secretKey) {
      return NextResponse.json(
        { success: false, error: "Server authentication not configured" },
        { status: 500 }
      );
    }

    // Bắt buộc xác thực: thiếu hoặc sai Authorization bearer token đều trả 401.
    const authHeader = request.headers.get("authorization");
    if (authHeader !== `Bearer ${secretKey}`) {
      return NextResponse.json(
        { success: false, error: "Unauthorized access token" },
        { status: 401 }
      );
    }

    // Safely parse JSON even if MT5 sends trailing null bytes or whitespace
    const rawText = await request.text();
    const cleanText = rawText.replace(/\0/g, "").trim();

    if (!cleanText) {
      return NextResponse.json(
        { success: false, error: "Empty request body" },
        { status: 400 }
      );
    }

    const payload = JSON.parse(cleanText) as Partial<PulseSnapshot>;

    if (!payload || typeof payload.price !== "number") {
      return NextResponse.json(
        { success: false, error: "Invalid payload format. 'price' number is required." },
        { status: 400 }
      );
    }

    // Merge với current state dùng nullish coalescing (??) để giữ giá trị 0 hợp lệ,
    // và merge sâu đối với entry/multiTf/indicators.
    const current = await getLatestPulse();
    const mergedEntryHigh = payload.entry?.high ?? current.entry.high;
    const mergedSnapshot: PulseSnapshot = {
      symbol: payload.symbol ?? current.symbol,
      time: payload.time ?? new Date().toLocaleTimeString("en-GB", { hour12: false }),
      price: payload.price,
      bias: payload.bias ?? current.bias,
      score: payload.score ?? current.score,
      volatility: payload.volatility ?? current.volatility,
      entry: {
        high: mergedEntryHigh,
        low: payload.entry?.low ?? current.entry.low,
        gain:
          payload.entry?.gain ??
          Number((payload.price - mergedEntryHigh).toFixed(2)),
      },
      exit: payload.exit ?? current.exit,
      exitSignal: payload.exitSignal ?? current.exitSignal ?? false,
      signalAge: payload.signalAge ?? current.signalAge ?? 0,
      htf: payload.htf ?? current.htf,
      multiTf: {
        m15: mergeMultiTf(payload.multiTf?.m15, current.multiTf.m15),
        m30: mergeMultiTf(payload.multiTf?.m30, current.multiTf.m30),
        h1: mergeMultiTf(payload.multiTf?.h1, current.multiTf.h1),
      },
      indicators: mergeIndicators(payload.indicators, current.indicators),
      analysisText: payload.analysisText ?? current.analysisText,
    };

    // Chỉ giữ snapshot nhất quán (NEUTRAL → score 0) trước khi lưu/trả về.
    const normalizedSnapshot = normalizeNeutralScore(mergedSnapshot);

    await updatePulse(normalizedSnapshot);

    return NextResponse.json({
      success: true,
      message: "TNV Gold pulse updated successfully",
      data: normalizedSnapshot,
    });
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : "Internal Server Error";
    return NextResponse.json(
      { success: false, error: errorMsg },
      { status: 500 }
    );
  }
}

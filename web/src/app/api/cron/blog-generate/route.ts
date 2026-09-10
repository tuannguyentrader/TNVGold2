// Cron endpoint — tạo bài blog tự động từ pulse hiện tại
// Được cron-job.org gọi mỗi giờ, nhưng code TỰ GIỚI HẠN còn ~6 bài/ngày
// (xem MIN_HOURS_BETWEEN_POSTS) để tránh spam thin/duplicate content làm
// tụt SEO cả site.

import { NextResponse } from "next/server";
import { createPost, getLatestPulsePostAt } from "@/lib/blog-store";
import { getLatestPulse } from "@/lib/blog-helpers";

export const dynamic = "force-dynamic";
export const maxDuration = 60; // giây

// Số giờ tối thiểu giữa 2 bài pulse tự động
const MIN_HOURS_BETWEEN_POSTS = 4;

export async function GET(request: Request) {
  // Auth — CHỈ chấp nhận Bearer TNV_SECRET_KEY.
  // (Đã bỏ nhánh x-vercel-cron: header đó client nào cũng gửi được → auth bypass)
  const expected = process.env.TNV_SECRET_KEY;
  const authHeader = request.headers.get("authorization");

  if (!expected) {
    return NextResponse.json(
      { success: false, error: "Server auth not configured" },
      { status: 500 }
    );
  }
  if (authHeader !== `Bearer ${expected}`) {
    return NextResponse.json(
      { success: false, error: "Unauthorized" },
      { status: 401 }
    );
  }

  try {
    const pulse = await getLatestPulse();

    // Gate: không có pulse tươi (Redis hết TTL) thì KHÔNG đăng bài — tránh
    // tự đăng bài rác "Giá $0.00, NEUTRAL" lên blog công khai (TTL 90 ngày).
    if (!pulse || pulse.price <= 0) {
      return NextResponse.json({
        success: true,
        skipped: "no-fresh-pulse",
        message: "Pulse trống hoặc hết hạn — bỏ qua lần này, đợi bot ghi lại",
      });
    }

    // Nhịp tối thiểu 4 giờ giữa 2 bài pulse — cron gọi mỗi giờ nhưng lần
    // thừa tự bỏ qua (HTTP 200, không fail alert). Chống 24 bài/ngày trùng
    // nội dung làm tụt SEO.
    const MIN_MS = MIN_HOURS_BETWEEN_POSTS * 60 * 60 * 1000;
    const lastPostAt = await getLatestPulsePostAt();
    if (lastPostAt && Date.now() - lastPostAt < MIN_MS) {
      const minsLeft = Math.ceil((MIN_MS - (Date.now() - lastPostAt)) / 60000);
      return NextResponse.json({
        success: true,
        skipped: "throttled",
        message: `Bài trước mới ${Math.round((Date.now() - lastPostAt) / 60000)} phút — còn ${minsLeft} phút nữa mới đăng tiếp`,
      });
    }

    const now = new Date();
    const slug = `xau-pulse-${now.toISOString().slice(0, 13).replace(/[-:T]/g, "")}`; // YYYYMMDDHH

    const biasVi = pulse?.bias === "LONG" ? "TĂNG" : pulse?.bias === "SHORT" ? "GIẢM" : "TRUNG TÍNH";
    const biasEn = pulse?.bias || "NEUTRAL";

    // ── Nhãn phiên + mốc giờ VN ──────────────────────────────────────────
    // Tiêu đề cũ chỉ có mốc thời gian ("XAUUSD Pulse — 20:34:21 8/9/2026") →
    // các bài gần như trùng nhau = thin content. Thêm PHIÊN giao dịch + bias
    // + giá để mỗi bài có tiêu đề riêng, có nghĩa, mô tả đúng nội dung.
    const vn = new Date(now.getTime() + 7 * 3600 * 1000); // dịch sang giờ VN (UTC+7)
    const vnHour = vn.getUTCHours();
    const timeLabel = `${String(vnHour).padStart(2, "0")}:${String(vn.getUTCMinutes()).padStart(2, "0")} ${String(vn.getUTCDate()).padStart(2, "0")}/${String(vn.getUTCMonth() + 1).padStart(2, "0")}`;

    // Phiên theo giờ VN: Á 07-15, Âu 15-20, Mỹ 20-03, còn lại ngoài phiên
    const sessionVi =
      vnHour >= 7 && vnHour < 15 ? "phiên Á"
      : vnHour >= 15 && vnHour < 20 ? "phiên Âu"
      : vnHour >= 20 || vnHour < 3 ? "phiên Mỹ"
      : "ngoài phiên";
    const sessionEn =
      vnHour >= 7 && vnHour < 15 ? "Asian"
      : vnHour >= 15 && vnHour < 20 ? "London"
      : vnHour >= 20 || vnHour < 3 ? "New York"
      : "off-session";

    const priceStr = pulse?.price ? `$${pulse.price.toFixed(2)}` : "—";
    const titleVi = `XAUUSD ${sessionVi} ${timeLabel}: bias ${biasVi}, giá ${priceStr}`;
    const titleEn = `XAUUSD ${sessionEn} session ${timeLabel}: ${biasEn} bias at ${priceStr}`;

    // Khối vùng giao dịch — chỉ khi đang có lệnh (bias LONG/SHORT kèm entry/SL/TP)
    const entryP = pulse?.entry?.price ?? null;
    const slP = pulse?.sl ?? null;
    const tpP = pulse?.tp ?? null;
    const hasTrade = !!(pulse && pulse.bias !== "NEUTRAL" && entryP && slP && tpP);
    const tradeVi = hasTrade
      ? `\n### Vùng giao dịch\n\n- **Entry:** $${entryP?.toFixed(2)}\n- **Stop Loss (1.5N):** $${slP?.toFixed(2)}\n- **Take Profit (2.0N):** $${tpP?.toFixed(2)}\n`
      : "";
    const tradeEn = hasTrade
      ? `\n### Trade levels\n\n- **Entry:** $${entryP?.toFixed(2)}\n- **Stop Loss (1.5N):** $${slP?.toFixed(2)}\n- **Take Profit (2.0N):** $${tpP?.toFixed(2)}\n`
      : "";

    const post = {
      slug,
      title: {
        vi: titleVi,
        en: titleEn,
      },
      excerpt: {
        vi: `${sessionVi} ${timeLabel}: XAUUSD ${priceStr}, bias ${biasVi}, score ${pulse?.score ?? "—"}/10.`,
        en: `${sessionEn} session ${timeLabel}: XAUUSD ${priceStr}, ${biasEn} bias, score ${pulse?.score ?? "—"}/10.`,
      },
      contentMd: {
        vi: `## ${titleVi}

### Tổng quan

- **Giá hiện tại:** $${pulse?.price?.toFixed(2) || "—"}
- **Bias:** ${biasVi}
- **Score:** ${pulse?.score ?? "—"}/10
- **Volatility:** ${pulse?.volatility?.toFixed(2) || "—"}
${tradeVi}

### Multi-Timeframe

| TF | Bias | Score |
|----|------|-------|
| M15 | ${pulse?.multiTf?.m15?.bias || "—"} | ${pulse?.multiTf?.m15?.score ?? "—"} |
| M30 | ${pulse?.multiTf?.m30?.bias || "—"} | ${pulse?.multiTf?.m30?.score ?? "—"} |
| H1 | ${pulse?.multiTf?.h1?.bias || "—"} | ${pulse?.multiTf?.h1?.score ?? "—"} |

> ⚠️ *Bài tự động từ TNV Gold AI. Quản lý vốn chặt chẽ.*`,
        en: `## ${titleEn}

### Overview

- **Current price:** $${pulse?.price?.toFixed(2) || "—"}
- **Bias:** ${biasEn}
- **Score:** ${pulse?.score ?? "—"}/10
- **Volatility:** ${pulse?.volatility?.toFixed(2) || "—"}
${tradeEn}

### Multi-Timeframe

| TF | Bias | Score |
|----|------|-------|
| M15 | ${pulse?.multiTf?.m15?.bias || "—"} | ${pulse?.multiTf?.m15?.score ?? "—"} |
| M30 | ${pulse?.multiTf?.m30?.bias || "—"} | ${pulse?.multiTf?.m30?.score ?? "—"} |
| H1 | ${pulse?.multiTf?.h1?.bias || "—"} | ${pulse?.multiTf?.h1?.score ?? "—"} |

> ⚠️ *Auto-generated by TNV Gold AI. Manage risk carefully.*`,
      },
      tags: ["pulse", "hourly"],
      type: "analysis" as const,
      author: "TNV AI",
      publishedAt: now.getTime(),
      lang: "vi" as const,
      relatedSnapshot: pulse
        ? {
            symbol: pulse.symbol || "XAUUSD",
            price: pulse.price,
            bias: pulse.bias,
            score: pulse.score,
          }
        : undefined,
    };

    await createPost(post);

    return NextResponse.json({
      success: true,
      message: "Post created",
      slug: post.slug,
      title: post.title.vi,
    });
  } catch (err) {
    console.error("[blog-generate] error:", err);
    return NextResponse.json(
      { success: false, error: "Failed to create post" },
      { status: 500 }
    );
  }
}

// OG Image generator — tạo ảnh 1200x630 cho blog/news
import { ImageResponse } from "next/og";

export const runtime = "edge";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://tnvgold.vercel.app";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const title = searchParams.get("title") || "TNV Gold — Phân tích Vàng XAUUSD";
  const subtitle = searchParams.get("subtitle") || "Real-time AI-powered gold analytics";
  const type = (searchParams.get("type") || "default") as "default" | "blog" | "news";

  const accentColor = type === "blog" ? "#f5c542" : type === "news" ? "#ff8383" : "#f5c542";

  return new ImageResponse(
    (
      <div
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
          padding: "60px",
          background: "linear-gradient(135deg, #05060a 0%, #0b0f16 100%)",
          fontFamily: "sans-serif",
        }}
      >
        {/* Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div
            style={{
              width: "60px",
              height: "60px",
              borderRadius: "12px",
              background: `linear-gradient(135deg, ${accentColor} 0%, #cfa744 100%)`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "36px",
              fontWeight: "bold",
              color: "#05060a",
            }}
          >
            ⚡
          </div>
          <div style={{ fontSize: "32px", fontWeight: "bold", color: "#fdfdfd" }}>
            <span style={{ color: accentColor }}>TNV</span> Gold
          </div>
        </div>

        {/* Title */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            marginTop: "auto",
          }}
        >
          <div
            style={{
              fontSize: "64px",
              fontWeight: "bold",
              color: "#fdfdfd",
              lineHeight: 1.2,
              maxWidth: "1000px",
              display: "flex",
            }}
          >
            {title.slice(0, 90)}
          </div>
          {subtitle && (
            <div
              style={{
                fontSize: "28px",
                color: "#9ca3af",
                marginTop: "24px",
                display: "flex",
              }}
            >
              {subtitle.slice(0, 100)}
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: "40px",
            fontSize: "24px",
            color: "#6b7280",
          }}
        >
          <div style={{ display: "flex" }}>{SITE_URL.replace("https://", "")}</div>
          {type !== "default" && (
            <div
              style={{
                display: "flex",
                padding: "8px 20px",
                background: `${accentColor}20`,
                border: `1px solid ${accentColor}50`,
                borderRadius: "999px",
                color: accentColor,
                fontSize: "20px",
                fontWeight: "600",
                textTransform: "uppercase",
              }}
            >
              {type === "blog" ? "Blog" : "News"}
            </div>
          )}
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    }
  );
}

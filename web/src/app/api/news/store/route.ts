import { NextResponse } from "next/server";
import { listNews } from "@/lib/news-store";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const limit = parseInt(searchParams.get("limit") || "30");
  const currency = searchParams.get("currency") || undefined;

  try {
    const news = await listNews({ limit, currency });
    return NextResponse.json({ success: true, data: news, count: news.length });
  } catch (err) {
    return NextResponse.json(
      { success: false, error: "Failed to list news", detail: String(err) },
      { status: 500 }
    );
  }
}

import { NextResponse } from "next/server";
import { Redis } from "@upstash/redis";

const redisUrl =
  process.env.KV_REST_API_URL ||
  process.env.UPSTASH_REDIS_REST_URL;
const redisToken =
  process.env.KV_REST_API_TOKEN ||
  process.env.UPSTASH_REDIS_REST_TOKEN;

const redis = redisUrl && redisToken
  ? new Redis({ url: redisUrl, token: redisToken })
  : null;

export async function POST(request: Request) {
  // Auth check - Bearer TNV_SECRET_KEY (giống /api/pulse POST)
  const expected = process.env.TNV_SECRET_KEY;
  if (!expected) {
    return NextResponse.json(
      { success: false, error: "Server authentication not configured" },
      { status: 500 }
    );
  }
  const authHeader = request.headers.get("authorization") || "";
  if (authHeader !== `Bearer ${expected}`) {
    return NextResponse.json(
      { success: false, error: "Unauthorized access token" },
      { status: 401 }
    );
  }

  if (!redis) {
    return NextResponse.json({ success: false, error: "No Redis configured" });
  }

  try {
    await redis.del("tnv:current_pulse");
    await redis.del("tnv:pulse_history");
    return NextResponse.json({ success: true, message: "All pulse data cleared from Redis" });
  } catch (err) {
    return NextResponse.json(
      { success: false, error: "Failed to clear Redis", detail: String(err) },
      { status: 500 }
    );
  }
}

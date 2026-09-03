import { NextResponse } from "next/server";
import { getPost } from "@/lib/blog-store";

export const dynamic = "force-dynamic";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ slug: string }> }
) {
  const { slug } = await params;

  try {
    const post = await getPost(slug);
    if (!post) {
      return NextResponse.json(
        { success: false, error: "Post not found" },
        { status: 404 }
      );
    }
    return NextResponse.json({ success: true, data: post });
  } catch (err) {
    return NextResponse.json(
      { success: false, error: "Failed to get post", detail: String(err) },
      { status: 500 }
    );
  }
}

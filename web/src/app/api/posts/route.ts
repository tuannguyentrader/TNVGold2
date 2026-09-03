import { NextResponse } from "next/server";
import { listPosts, createPost, type BlogPost } from "@/lib/blog-store";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const limit = parseInt(searchParams.get("limit") || "50");
  const type = searchParams.get("type") || undefined;

  try {
    const posts = await listPosts({ limit, type });
    return NextResponse.json({ success: true, data: posts, count: posts.length });
  } catch (err) {
    return NextResponse.json(
      { success: false, error: "Failed to list posts", detail: String(err) },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  // Auth — Bearer TNV_SECRET_KEY (cùng pattern với /api/pulse)
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
      { success: false, error: "Unauthorized" },
      { status: 401 }
    );
  }

  try {
    const body = (await request.json()) as BlogPost;
    // Validate
    if (!body.slug || !body.title?.vi || !body.contentMd?.vi) {
      return NextResponse.json(
        { success: false, error: "Missing required fields: slug, title.vi, contentMd.vi" },
        { status: 400 }
      );
    }

    const post: BlogPost = {
      slug: body.slug,
      title: body.title,
      excerpt: body.excerpt || { vi: "", en: "" },
      contentMd: body.contentMd,
      tags: body.tags || [],
      type: body.type || "analysis",
      author: body.author || "TNV",
      publishedAt: body.publishedAt || Date.now(),
      lang: body.lang || "vi",
      relatedSnapshot: body.relatedSnapshot,
    };

    await createPost(post);
    return NextResponse.json({ success: true, data: { slug: post.slug } });
  } catch (err) {
    return NextResponse.json(
      { success: false, error: "Failed to create post", detail: String(err) },
      { status: 500 }
    );
  }
}

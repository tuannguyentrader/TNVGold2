"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowRight, Calendar, Tag } from "lucide-react";
import { useLanguage } from "@/lib/language-context";

interface Post {
  slug: string;
  title: { vi: string; en: string };
  excerpt: { vi: string; en: string };
  tags: string[];
  type: string;
  author: string;
  publishedAt: number;
  lang: "vi" | "en";
}

export function BlogListClient() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const { language } = useLanguage();
  const lang = (language as "vi" | "en") || "vi";

  useEffect(() => {
    fetch("/api/posts")
      .then((r) => r.json())
      .then((d) => {
        if (d.success) setPosts(d.data);
      })
      .catch(() => setPosts([]))
      .finally(() => setLoading(false));
  }, []);

  const ui = {
    vi: {
      title: "Blog & Phân tích",
      subtitle: "Bài viết mới nhất về vàng XAUUSD, cập nhật hàng giờ.",
      empty: "Chưa có bài viết nào.",
      loading: "Đang tải...",
      readMore: "Đọc tiếp",
      by: "bởi",
      type: {
        analysis: "Phân tích",
        news: "Tin tức",
        tutorial: "Hướng dẫn",
      },
    },
    en: {
      title: "Blog & Analysis",
      subtitle: "Latest posts about XAUUSD gold, updated hourly.",
      empty: "No posts yet.",
      loading: "Loading...",
      readMore: "Read more",
      by: "by",
      type: {
        analysis: "Analysis",
        news: "News",
        tutorial: "Tutorial",
      },
    },
  }[lang];

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-gray-400">{ui.loading}</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-6 py-12">
      <div className="max-w-5xl mx-auto">
        <header className="mb-12">
          <Link href="/" className="text-sm text-[#f5c542] hover:underline mb-4 inline-block">
            ← TNV Gold
          </Link>
          <h1 className="text-3xl md:text-4xl font-bold mb-3">{ui.title}</h1>
          <p className="text-gray-400">{ui.subtitle}</p>
        </header>

        {posts.length === 0 ? (
          <p className="text-gray-500 text-center py-12">{ui.empty}</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {posts.map((p) => {
              const date = new Date(p.publishedAt);
              const typeLabel = ui.type[p.type as keyof typeof ui.type] || p.type;
              return (
                <Link
                  key={p.slug}
                  href={`/blog/${p.slug}`}
                  className="block p-6 rounded-xl bg-[#0b0f16] border border-white/5 hover:border-[#f5c542]/30 transition group"
                >
                  <div className="flex items-center gap-3 text-xs text-gray-500 mb-3">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {date.toLocaleDateString(lang === "vi" ? "vi-VN" : "en-US", {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-[#f5c542]/10 text-[#f5c542]">
                      {typeLabel}
                    </span>
                  </div>
                  <h2 className="text-xl font-semibold mb-2 group-hover:text-[#f5c542] transition">
                    {p.title[lang]}
                  </h2>
                  <p className="text-sm text-gray-400 mb-4 line-clamp-2">
                    {p.excerpt[lang]}
                  </p>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">
                      {ui.by} {p.author}
                    </span>
                    <span className="text-[#f5c542] flex items-center gap-1 group-hover:gap-2 transition-all">
                      {ui.readMore}
                      <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}

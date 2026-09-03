"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Calendar, Tag, ArrowLeft } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { useLanguage } from "@/lib/language-context";

interface Post {
  slug: string;
  title: { vi: string; en: string };
  excerpt: { vi: string; en: string };
  contentMd: { vi: string; en: string };
  tags: string[];
  type: string;
  author: string;
  publishedAt: number;
}

export function BlogDetailClient({ slug }: { slug: string }) {
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  const { language } = useLanguage();
  const lang = (language as "vi" | "en") || "vi";

  useEffect(() => {
    fetch(`/api/posts/${slug}`)
      .then((r) => r.json())
      .then((d) => {
        if (d.success) setPost(d.data);
      })
      .catch(() => setPost(null))
      .finally(() => setLoading(false));
  }, [slug]);

  const ui = {
    vi: { loading: "Đang tải...", notFound: "Không tìm thấy bài viết.", back: "← Quay lại Blog", by: "bởi" },
    en: { loading: "Loading...", notFound: "Post not found.", back: "← Back to Blog", by: "by" },
  }[lang];

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-gray-400">{ui.loading}</p>
      </main>
    );
  }

  if (!post) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 mb-4">{ui.notFound}</p>
          <Link href="/blog" className="text-[#f5c542] hover:underline">
            {ui.back}
          </Link>
        </div>
      </main>
    );
  }

  const date = new Date(post.publishedAt);

  return (
    <main className="min-h-screen px-6 py-12">
      <article className="max-w-3xl mx-auto">
        <Link
          href="/blog"
          className="text-sm text-[#f5c542] hover:underline mb-6 inline-flex items-center gap-1"
        >
          <ArrowLeft className="w-3 h-3" />
          {ui.back}
        </Link>

        <header className="mb-8 pb-8 border-b border-white/5">
          <div className="flex items-center gap-3 text-xs text-gray-500 mb-4">
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {date.toLocaleDateString(lang === "vi" ? "vi-VN" : "en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </span>
            <span className="text-gray-500">·</span>
            <span>
              {ui.by} <strong className="text-gray-300">{post.author}</strong>
            </span>
          </div>

          <h1 className="text-3xl md:text-4xl font-bold mb-3 leading-tight">
            {post.title[lang]}
          </h1>
          {post.excerpt[lang] && (
            <p className="text-lg text-gray-400">{post.excerpt[lang]}</p>
          )}

          {post.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-4">
              {post.tags.map((t) => (
                <span
                  key={t}
                  className="text-xs px-2 py-1 rounded bg-white/5 text-gray-400 flex items-center gap-1"
                >
                  <Tag className="w-3 h-3" />
                  {t}
                </span>
              ))}
            </div>
          )}
        </header>

        <div className="prose prose-invert prose-headings:text-white prose-p:text-gray-300 prose-strong:text-white prose-a:text-[#f5c542] prose-a:no-underline hover:prose-a:underline prose-table:my-6 prose-th:text-left prose-th:text-gray-200 prose-td:text-gray-300 prose-code:text-[#f5c542] prose-code:bg-[#f5c542]/10 prose-code:px-1 prose-code:rounded max-w-none">
          <ReactMarkdown>{post.contentMd[lang] || post.contentMd.vi}</ReactMarkdown>
        </div>

        <footer className="mt-12 pt-6 border-t border-white/5 text-sm text-gray-500">
          <Link href="/blog" className="text-[#f5c542] hover:underline">
            {ui.back}
          </Link>
        </footer>
      </article>
    </main>
  );
}

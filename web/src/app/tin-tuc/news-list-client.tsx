"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Calendar, ExternalLink, Filter } from "lucide-react";
import { useLanguage } from "@/lib/language-context";

interface NewsItem {
  id: string;
  title: string;
  time: string;
  url: string;
  source: string;
  impact: "high" | "medium" | "low";
  currency: string;
}

export function NewsListClient() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "USD" | "high">("all");
  const { language } = useLanguage();
  const lang = (language as "vi" | "en") || "vi";

  useEffect(() => {
    fetch("/api/news/store")
      .then((r) => r.json())
      .then((d) => {
        if (d.success) setNews(d.data);
      })
      .catch(() => setNews([]))
      .finally(() => setLoading(false));
  }, []);

  const ui = {
    vi: {
      title: "Tin tức thị trường",
      subtitle: "Lịch kinh tế USD, tin quan trọng ảnh hưởng vàng XAUUSD",
      empty: "Chưa có tin tức nào.",
      loading: "Đang tải...",
      all: "Tất cả",
      usd: "USD",
      high: "High Impact",
      impact: { high: "Quan trọng", medium: "Trung bình", low: "Thấp" },
    },
    en: {
      title: "Market News",
      subtitle: "USD economic calendar, key events affecting XAUUSD gold",
      empty: "No news yet.",
      loading: "Loading...",
      all: "All",
      usd: "USD",
      high: "High Impact",
      impact: { high: "High", medium: "Medium", low: "Low" },
    },
  }[lang];

  const filtered = news.filter((n) => {
    if (filter === "all") return true;
    if (filter === "USD") return n.currency === "USD";
    if (filter === "high") return n.impact === "high";
    return true;
  });

  const impactColor = (impact: string) => {
    if (impact === "high") return "bg-red-500/20 text-red-400 border-red-500/30";
    if (impact === "medium") return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
    return "bg-gray-500/20 text-gray-400 border-gray-500/30";
  };

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
        <header className="mb-8">
          <Link href="/" className="text-sm text-[#f5c542] hover:underline mb-4 inline-block">
            ← TNV Gold
          </Link>
          <h1 className="text-3xl md:text-4xl font-bold mb-3">{ui.title}</h1>
          <p className="text-gray-400 mb-4">{ui.subtitle}</p>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setFilter("all")}
              className={`px-3 py-1.5 text-sm rounded-md border transition ${
                filter === "all"
                  ? "border-[#f5c542] bg-[#f5c542]/10 text-[#f5c542]"
                  : "border-white/10 text-gray-400 hover:border-white/20"
              }`}
            >
              {ui.all}
            </button>
            <button
              onClick={() => setFilter("USD")}
              className={`px-3 py-1.5 text-sm rounded-md border transition ${
                filter === "USD"
                  ? "border-[#f5c542] bg-[#f5c542]/10 text-[#f5c542]"
                  : "border-white/10 text-gray-400 hover:border-white/20"
              }`}
            >
              {ui.usd}
            </button>
            <button
              onClick={() => setFilter("high")}
              className={`px-3 py-1.5 text-sm rounded-md border transition ${
                filter === "high"
                  ? "border-[#f5c542] bg-[#f5c542]/10 text-[#f5c542]"
                  : "border-white/10 text-gray-400 hover:border-white/20"
              }`}
            >
              {ui.high}
            </button>
          </div>
        </header>

        {filtered.length === 0 ? (
          <p className="text-gray-500 text-center py-12">{ui.empty}</p>
        ) : (
          <div className="space-y-3">
            {filtered.map((n) => {
              const date = new Date(n.time);
              return (
                <Link
                  key={n.id}
                  href={`/tin-tuc/${n.id}`}
                  className="block p-4 rounded-xl bg-[#0b0f16] border border-white/5 hover:border-[#f5c542]/30 transition"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500 mb-2">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {date.toLocaleString(lang === "vi" ? "vi-VN" : "en-US", {
                            year: "numeric",
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                        <span className="px-2 py-0.5 rounded border text-[10px] font-semibold uppercase">
                          {n.currency}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded border text-[10px] font-semibold uppercase ${impactColor(n.impact)}`}
                        >
                          {ui.impact[n.impact]}
                        </span>
                      </div>
                      <h3 className="text-base font-semibold mb-1">{n.title}</h3>
                      <p className="text-xs text-gray-500">Nguồn: {n.source}</p>
                    </div>
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

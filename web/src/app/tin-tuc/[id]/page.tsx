import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Calendar, ExternalLink } from "lucide-react";
import { listNews } from "@/lib/news-store";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const all = await listNews({ limit: 200 });
  const item = all.find((n) => n.id === id);
  if (!item) return { title: "Tin không tồn tại" };

  return {
    title: item.title,
    description: `Tin kinh tế ${item.currency} - Impact: ${item.impact}. ${item.title}`,
    openGraph: {
      title: item.title,
      description: `${item.currency} - ${item.impact} impact - ${item.source}`,
      type: "article",
      publishedTime: new Date(item.time).toISOString(),
    },
    alternates: {
      canonical: `/tin-tuc/${id}`,
    },
  };
}

export default async function NewsDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const all = await listNews({ limit: 200 });
  const item = all.find((n) => n.id === id);

  if (!item) notFound();

  const date = new Date(item.time);
  const impactColor =
    item.impact === "high"
      ? "text-red-400 border-red-500/30 bg-red-500/10"
      : item.impact === "medium"
      ? "text-yellow-400 border-yellow-500/30 bg-yellow-500/10"
      : "text-gray-400 border-gray-500/30 bg-gray-500/10";

  return (
    <main className="min-h-screen px-6 py-12">
      <article className="max-w-3xl mx-auto">
        <Link
          href="/tin-tuc"
          className="text-sm text-[#f5c542] hover:underline mb-6 inline-flex items-center gap-1"
        >
          <ArrowLeft className="w-3 h-3" />
          Quay lại Tin tức
        </Link>

        <header className="mb-8 pb-8 border-b border-white/5">
          <div className="flex flex-wrap items-center gap-2 text-xs mb-4">
            <span className="flex items-center gap-1 text-gray-500">
              <Calendar className="w-3 h-3" />
              {date.toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" })}
            </span>
            <span className="px-2 py-0.5 rounded border border-white/10 text-[10px] font-semibold uppercase">
              {item.currency}
            </span>
            <span
              className={`px-2 py-0.5 rounded border text-[10px] font-semibold uppercase ${impactColor}`}
            >
              {item.impact} impact
            </span>
          </div>

          <h1 className="text-2xl md:text-3xl font-bold leading-tight mb-4">
            {item.title}
          </h1>

          <p className="text-sm text-gray-500">Nguồn: {item.source}</p>
        </header>

        <div className="prose prose-invert max-w-none">
          <p className="text-gray-300">
            Sự kiện kinh tế <strong>{item.currency}</strong> mức độ{" "}
            <strong className={item.impact === "high" ? "text-red-400" : ""}>{item.impact}</strong>{" "}
            diễn ra vào <strong>{date.toLocaleString("vi-VN")}</strong>.
          </p>
          <p className="text-gray-400">
            Sự kiện này có thể ảnh hưởng đến giá vàng XAUUSD. Theo dõi dashboard{" "}
            <Link href="/goldpulse" className="text-[#f5c542] hover:underline">Gold Pulse</Link>{" "}
            để cập nhật real-time.
          </p>

          {item.url && (
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-lg border border-[#f5c542]/50 text-[#f5c542] hover:bg-[#f5c542]/10 transition"
            >
              <ExternalLink className="w-4 h-4" />
              Xem chi tiết tại {item.source}
            </a>
          )}
        </div>

        <footer className="mt-12 pt-6 border-t border-white/5 text-sm text-gray-500">
          <Link href="/tin-tuc" className="text-[#f5c542] hover:underline">
            ← Quay lại danh sách
          </Link>
        </footer>
      </article>
    </main>
  );
}

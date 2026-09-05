"use client";

import { useState, useMemo } from "react";
import { History, TrendingUp, TrendingDown, Clock, Filter, ChevronLeft, ChevronRight } from "lucide-react";
import { useLanguage } from "@/lib/language-context";
import { useLivePulse } from "@/lib/live-pulse-context";

const PAGE_SIZE = 10;

export function HistoryTable() {
  const { language, t } = useLanguage();
  const { history } = useLivePulse();
  const [filterBias, setFilterBias] = useState<string>("ALL");
  const [page, setPage] = useState(0);

  const filtered = useMemo(() => {
    if (filterBias === "ALL") return history;
    return history.filter((r) => r.bias === filterBias);
  }, [history, filterBias]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages - 1);
  const paged = filtered.slice(safePage * PAGE_SIZE, (safePage + 1) * PAGE_SIZE);

  const formatTime = (time: string) => {
    if (!time || time === "—") return time;
    const now = new Date();
    const dateStr = now.toLocaleDateString("en-GB", { day: "2-digit", month: "2-digit" });
    return `${dateStr} ${time}`;
  };

  return (
    <section className="qx-history my-5" aria-label={t.historyTitle}>
      <div className="flex items-center justify-between gap-3 mb-2.5 flex-wrap">
        <div>
          <h2 className="text-sm font-bold text-white flex items-center gap-1.5 m-0">
            <History className="w-4 h-4 text-[#f5c542]" />
            {t.historyTitle}
          </h2>
          <p className="text-[0.74rem] text-gray-400 mt-0.5">
            {t.historySub}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 bg-[#111622] p-0.5 rounded-lg border border-white/5">
            <Filter className="w-3 h-3 text-gray-400 ml-1.5" />
            {(["ALL", "LONG", "SHORT", "NEUTRAL"] as const).map((opt) => (
              <button
                key={opt}
                onClick={() => { setFilterBias(opt); setPage(0); }}
                className={`text-[0.65rem] px-2 py-0.5 rounded font-medium transition-all cursor-pointer ${
                  filterBias === opt
                    ? "bg-[rgba(245,197,66,0.2)] text-[#f5c542] font-bold"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                {opt === "ALL" ? "ALL" : opt}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1.5 text-[0.7rem] text-[#f5c542] font-mono">
            <Clock className="w-3 h-3" />
            <span>{filtered.length} snapshots</span>
          </div>
        </div>
      </div>

      {paged.length > 0 ? (
      <div className="overflow-x-auto rounded-xl border border-white/10 bg-[#0b0f16] shadow-xl">
        <table className="w-full text-left border-collapse font-sans">
          <thead>
            <tr className="border-b border-white/10 bg-white/[0.03] text-gray-400 font-semibold uppercase tracking-wider text-[0.68rem]">
              <th className="py-2.5 px-3.5">{t.colTime}</th>
              <th className="py-2.5 px-3.5">{t.colPrice}</th>
              <th className="py-2.5 px-3.5">{t.colSignal}</th>
              <th className="py-2.5 px-3.5">PULSE</th>
              <th className="py-2.5 px-3.5">{t.colVolatility}</th>
              <th className="py-2.5 px-3.5">{t.colHigh}</th>
              <th className="py-2.5 px-3.5">{t.colLow}</th>
              <th className="py-2.5 px-3.5">{t.colHTF}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 font-mono text-[0.74rem]">
            {paged.map((row, idx) => (
              <tr key={idx} className="hover:bg-white/[0.04] transition-colors">
                <td className="py-2.5 px-3.5 text-gray-300 font-medium whitespace-nowrap">
                  {formatTime(row.time)}
                </td>
                <td className="py-2.5 px-3.5 text-white font-bold">
                  ${row.price.toFixed(2)}
                </td>
                <td className="py-2.5 px-3.5">
                  {row.bias === "LONG" && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[0.68rem] font-bold bg-[rgba(97,226,148,0.15)] text-[#61e294] border border-[rgba(97,226,148,0.3)]">
                      <TrendingUp className="w-3 h-3" /> LONG
                    </span>
                  )}
                  {row.bias === "SHORT" && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[0.68rem] font-bold bg-[rgba(255,96,96,0.15)] text-[#ff8383] border border-[rgba(255,96,96,0.3)]">
                      <TrendingDown className="w-3 h-3" /> SHORT
                    </span>
                  )}
                  {row.bias === "NEUTRAL" && (
                    <span className="inline-flex items-center gap-1 text-[0.68rem] font-medium text-gray-400">
                      NEUTRAL
                    </span>
                  )}
                </td>
                <td className="py-2.5 px-3.5">
                  <span className={`font-bold ${row.score >= 8 ? "text-[#61e294]" : row.score >= 5 ? "text-[#f5c542]" : "text-gray-400"}`}>
                    {row.score * 10}
                  </span>
                </td>
                <td className="py-2.5 px-3.5 text-gray-300">${row.volatility.toFixed(2)}</td>
                <td className="py-2.5 px-3.5 text-white">${row.entry.price != null ? row.entry.price.toFixed(2) : "—"}</td>
                <td className="py-2.5 px-3.5 text-[#ff8383]">{row.sl != null ? row.sl.toFixed(2) : "—"}</td>
                <td className="py-2.5 px-3.5 text-[#61e294]">{row.htf}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      ) : (
        <div className="rounded-xl border border-white/10 bg-[#0b0f16] shadow-xl px-6 py-10 flex flex-col items-center justify-center text-center">
          <div className="w-12 h-12 rounded-full bg-[rgba(245,197,66,0.1)] border border-[rgba(245,197,66,0.25)] flex items-center justify-center mb-3">
            <History className="w-6 h-6 text-[#f5c542]" />
          </div>
          <h3 className="text-sm font-semibold text-white mb-1">
            {language === "vi" ? "Chưa có dữ liệu lịch sử" : "No history yet"}
          </h3>
          <p className="text-[0.74rem] text-gray-400 max-w-sm">
            {language === "vi"
              ? "Hệ thống sẽ tự động ghi lại mỗi 5 phút khi bot gửi pulse. Vui lòng đợi hoặc kiểm tra kết nối bot."
              : "The system will auto-record every 5 minutes when the bot sends a pulse. Please wait or check the bot connection."}
          </p>
        </div>
      )}

      {/* Phân trang */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 mt-3 text-[0.72rem] text-gray-400">
          <button
            onClick={() => setPage(Math.max(0, safePage - 1))}
            disabled={safePage === 0}
            className="flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
          >
            <ChevronLeft className="w-3.5 h-3.5" /> Prev
          </button>
          <span className="font-mono text-gray-300">
            {safePage + 1} / {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages - 1, safePage + 1))}
            disabled={safePage >= totalPages - 1}
            className="flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
          >
            Next <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </section>
  );
}
"use client";

import { useState, useMemo } from "react";
import { History, TrendingUp, TrendingDown, Clock, Filter, ChevronLeft, ChevronRight, CalendarDays } from "lucide-react";
import { useLanguage } from "@/lib/language-context";
import { useLivePulse } from "@/lib/live-pulse-context";

const PAGE_SIZE = 10;

// Khoảng thời gian lọc (theo ngày — tính lùi từ bây giờ)
const PERIODS = [
  { key: "7d", days: 7 },
  { key: "30d", days: 30 },
  { key: "90d", days: 90 },
] as const;

export function HistoryTable() {
  const { language, t } = useLanguage();
  const { history } = useLivePulse();
  const [filterBias, setFilterBias] = useState<string>("ALL");
  const [period, setPeriod] = useState<string>("30d"); // mặc định: 30 ngày
  const [page, setPage] = useState(0);

  // Lọc kết hợp: hướng + khoảng thời gian
  const filtered = useMemo(() => {
    const days = PERIODS.find((p) => p.key === period)?.days ?? 30;
    const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
    return history.filter((r) => {
      if (filterBias !== "ALL" && r.bias !== filterBias) return false;
      const ts = new Date(r.time).getTime();
      if (!isNaN(ts) && ts > 0 && ts < cutoff) return false; // snapshot cũ chỉ có HH:MM:SS → NaN → không lọc
      return true;
    });
  }, [history, filterBias, period]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages - 1);
  const paged = filtered.slice(safePage * PAGE_SIZE, (safePage + 1) * PAGE_SIZE);

  const periodLabels: Record<string, { vi: string; en: string }> = {
    "7d": { vi: "7 ngày", en: "7 days" },
    "30d": { vi: "30 ngày", en: "30 days" },
    "90d": { vi: "90 ngày", en: "90 days" },
  };

  const formatTime = (time: string) => {
    if (!time || time === "—") return time;
    // Bot ghi ISO timestamp (UTC+7) — parse per-row, hiện giờ VN dd/MM HH:mm
    const d = new Date(time);
    if (!isNaN(d.getTime())) {
      return d.toLocaleString("vi-VN", {
        timeZone: "Asia/Ho_Chi_Minh",
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    }
    // Fallback snapshot cũ chỉ có HH:MM:SS — hiển thị nguyên bản
    return time;
  };

  // Nhãn cột theo ngôn ngữ (fallback text thẳng nếu key chưa có)
  const colEntry = language === "vi" ? "Entry" : "Entry";
  const colSL = "SL";
  const colTP = "TP";

  return (
    <section className="qx-history my-5" aria-label={t.historyTitle}>
      <div className="flex items-center justify-between gap-3 mb-2.5 flex-wrap">
        <div>
          <h2 className="text-sm font-bold text-white flex items-center gap-1.5 m-0">
            <History className="w-4 h-4 text-[#f5c542]" />
            {t.historyTitle}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          {/* Lọc khoảng thời gian: 7 / 30 / 90 ngày (mặc định 30) */}
          <div className="flex items-center gap-1 bg-[#111622] p-0.5 rounded-lg border border-white/5">
            <CalendarDays className="w-3 h-3 text-gray-400 ml-1.5" />
            {PERIODS.map((p) => (
              <button
                key={p.key}
                onClick={() => { setPeriod(p.key); setPage(0); }}
                className={`text-[0.65rem] px-2 py-0.5 rounded font-medium transition-all cursor-pointer ${
                  period === p.key
                    ? "bg-[rgba(245,197,66,0.2)] text-[#f5c542] font-bold"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                {language === "vi" ? periodLabels[p.key].vi : periodLabels[p.key].en}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1 bg-[#111622] p-0.5 rounded-lg border border-white/5">
            <Filter className="w-3 h-3 text-gray-400 ml-1.5" />
            {(["ALL", "LONG", "SHORT"] as const).map((opt) => (
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
            <span>{filtered.length} {language === "vi" ? "tín hiệu" : "signals"}</span>
          </div>
        </div>
      </div>

      {paged.length > 0 ? (
      <div className="overflow-x-auto rounded-xl border border-white/10 bg-[#0b0f16] shadow-xl">
        <table className="w-full text-left border-collapse font-sans">
          <thead>
            <tr className="border-b border-white/10 bg-white/[0.03] text-gray-400 font-semibold uppercase tracking-wider text-[0.68rem]">
              <th className="py-2.5 px-2.5">#</th>
              <th className="py-2.5 px-3.5">{t.colTime}</th>
              <th className="py-2.5 px-3.5">{t.colSignal}</th>
              <th className="py-2.5 px-3.5">PULSE</th>
              <th className="py-2.5 px-3.5">N</th>
              <th className="py-2.5 px-3.5">{colEntry}</th>
              <th className="py-2.5 px-3.5">{colSL}</th>
              <th className="py-2.5 px-3.5">{colTP}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 font-mono text-[0.74rem]">
            {paged.map((row, idx) => (
              <tr key={`${row.time}-${idx}`} className="hover:bg-white/[0.04] transition-colors">
                {/* Số thứ tự toàn cục: trang 0 bắt đầu từ 1, trang sau cộng dồn.
                    #1 = tín hiệu MỚI NHẤT (bot ghi vào đầu mảng). */}
                <td className="py-2.5 px-2.5 text-gray-500 text-[0.68rem]">
                  {filtered.length - (safePage * PAGE_SIZE + idx)}
                </td>
                <td className="py-2.5 px-3.5 text-gray-300 font-medium whitespace-nowrap">
                  {formatTime(row.time)}
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
                  <span className={`font-bold ${row.score >= 0.8 ? "text-[#61e294]" : row.score >= 0.5 ? "text-[#f5c542]" : "text-gray-400"}`}>
                    {row.score > 0 && row.score <= 1 ? (row.score * 10).toFixed(1) : row.score.toFixed(1)}
                  </span>
                </td>
                <td className="py-2.5 px-3.5 text-gray-300">{(row.volatility ?? 0).toFixed(2)}</td>
                <td className="py-2.5 px-3.5 text-white">
                  {row.entry?.price != null ? `$${row.entry.price.toFixed(2)}` : "—"}
                </td>
                <td className="py-2.5 px-3.5 text-[#ff8383]">{row.sl != null ? row.sl.toFixed(2) : "—"}</td>
                <td className="py-2.5 px-3.5 text-[#61e294]">{row.tp != null ? row.tp.toFixed(2) : "—"}</td>
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
          {history.length === 0 ? (
            // Chưa có data nào trong Redis — bot chưa ghi tín hiệu nào
            <>
              <h3 className="text-sm font-semibold text-white mb-1">
                {language === "vi" ? "Chưa có tín hiệu nào" : "No signals yet"}
              </h3>
              <p className="text-[0.74rem] text-gray-400 max-w-sm">
                {language === "vi"
                  ? "Bảng ghi lại mỗi khi hệ thống đổi hướng LONG/SHORT. Khi thị trường NEUTRAL không có lệnh — đợi tín hiệu đầu tiên."
                  : "The table records every LONG/SHORT direction change. No trades while the market is NEUTRAL — waiting for the first signal."}
              </p>
            </>
          ) : (
            // Có data nhưng filter thời gian/hướng không khớp bản nào
            <>
              <h3 className="text-sm font-semibold text-white mb-1">
                {language === "vi" ? "Không có tín hiệu trong khoảng này" : "No signals in this range"}
              </h3>
              <p className="text-[0.74rem] text-gray-400 max-w-sm">
                {language === "vi"
                  ? "Thử chọn khoảng thời gian dài hơn (90 ngày) hoặc đổi filter ALL."
                  : "Try a longer range (90 days) or switch the filter to ALL."}
              </p>
            </>
          )}
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

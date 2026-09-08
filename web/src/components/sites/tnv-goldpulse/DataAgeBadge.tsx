"use client";

import { useEffect, useState } from "react";
import { Clock, Radio } from "lucide-react";
import { useLanguage } from "@/lib/language-context";
import { useLivePulse } from "@/lib/live-pulse-context";

/**
 * DataAgeBadge — hiển thị TUỔI THẬT của dữ liệu (Age = now − Date(pulse.time)),
 * tự cập nhật mỗi 30 giây bằng setInterval bên trong component.
 *
 * Quy tắc màu / trạng thái:
 *   < 6 phút   → tươi        (xanh #61e294)  "Live" / "Vừa cập nhật"
 *   6–15 phút  → vàng nhạt   (#f5c542)       "Cập nhật X phút trước" / "Updated X min ago"
 *   > 15 phút  → cũ          (đỏ #ff8383)    "Cũ X phút" / "Stale · X min"
 *
 * LƯU Ý (bug cũ đã tránh): pulse.time bản cũ có thể là "HH:MM:SS" hoặc "—"
 * → Date.parse trả NaN (hoặc một số engine tự gán ngày hôm nay).
 * Khi đó tuổi KHÔNG xác định được → hiển thị trung tính "—",
 * KHÔNG tự suy ra ngày hôm nay. lastUpdated của context là giờ client fetch,
 * KHÔNG phải tuổi dữ liệu — cố ý không dùng.
 */

// Chỉ chấp nhận timestamp có phần NGÀY đầy đủ (ISO, vd "2026-09-08T15:23:05+07:00").
// Chống engine JS parse "HH:MM:SS" thành today → tuổi luôn ~0 (bug cũ).
const FULL_DATE_TIME_RE = /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}/;

const FRESH_MS = 6 * 60 * 1000;   // < 6 phút: tươi
const WARN_MS = 15 * 60 * 1000;   // 6–15 phút: vàng, > 15 phút: đỏ
const TICK_MS = 30 * 1000;        // cập nhật lại tuổi mỗi 30 giây

function parsePulseTime(time: string | undefined | null): number | null {
  if (!time || !FULL_DATE_TIME_RE.test(time) ) return null;
  const ms = Date.parse(time);
  return Number.isFinite(ms) ? ms : null;
}

/**
 * Tuổi dữ liệu (phút) dùng chung cho mọi badge/metric — tính từ pulse.time thật,
 * tự tick mỗi 30 giây. Trả về null khi không xác định được
 * (SSR trước mount, pulse rỗng, hoặc time kiểu cũ "HH:MM:SS" / "—").
 */
export function usePulseAgeMinutes(): number | null {
  const { pulse } = useLivePulse();
  const [now, setNow] = useState<number | null>(null);

  useEffect(() => {
    setNow(Date.now());
    const interval = setInterval(() => setNow(Date.now()), TICK_MS);
    return () => clearInterval(interval);
  }, []);

  const snapshotMs = parsePulseTime(pulse?.time);
  const ageMs =
    snapshotMs != null && now != null ? Math.max(0, now - snapshotMs) : null;
  return ageMs != null ? Math.floor(ageMs / 60000) : null;
}

export function DataAgeBadge() {
  const { language } = useLanguage();
  const { pulse, isLiveConnected } = useLivePulse();

  const [now, setNow] = useState<number | null>(null);

  useEffect(() => {
    setNow(Date.now());
    const interval = setInterval(() => setNow(Date.now()), TICK_MS);
    return () => clearInterval(interval);
  }, []);

  // Tuổi dữ liệu thật = now − Date(pulse.time). Trước mount (SSR) chưa có `now`
  // → chưa xác định được → trung tính, tránh hydration mismatch.
  const snapshotMs = parsePulseTime(pulse?.time);
  const ageMs = snapshotMs != null && now != null ? Math.max(0, now - snapshotMs) : null;
  const ageMin = ageMs != null ? Math.floor(ageMs / 60000) : null;

  // Không có dữ liệu thật hoặc không parse được thời gian → trung tính "—"
  const unknown = !pulse || pulse.price <= 0 || ageMin == null;
  const fresh = ageMin != null && ageMin < 6;
  const stale = ageMin != null && ageMin >= 15;

  const label = unknown
    ? "—"
    : language === "vi"
    ? fresh
      ? "Vừa cập nhật"
      : stale
      ? `Cũ ${ageMin} phút`
      : `Cập nhật ${ageMin} phút trước`
    : fresh
    ? "Live"
    : stale
    ? `Stale · ${ageMin} min`
    : `Updated ${ageMin} min ago`;

  // Màu trạng thái: tươi → xanh, vàng nhạt, đỏ. Unknown → trung tính xám.
  const tone = unknown
    ? {
        wrap: "bg-white/5 text-gray-400 border-white/10",
        dot: "bg-gray-500",
      }
    : fresh
    ? {
        wrap: "bg-[rgba(97,226,148,0.12)] text-[#61e294] border-[rgba(97,226,148,0.25)]",
        dot: "bg-[#61e294] animate-pulse",
      }
    : stale
    ? {
        wrap: "bg-[rgba(255,131,131,0.12)] text-[#ff8383] border-[rgba(255,131,131,0.25)]",
        dot: "bg-[#ff8383]",
      }
    : {
        wrap: "bg-[rgba(245,197,66,0.12)] text-[#f5c542] border-[rgba(245,197,66,0.25)]",
        dot: "bg-[#f5c542]",
      };

  const titleVi = unknown
    ? "Không xác định được tuổi dữ liệu"
    : fresh
    ? "Dữ liệu mới (dưới 6 phút)"
    : stale
    ? "Dữ liệu cũ (trên 15 phút)"
    : "Dữ liệu trong 6–15 phút gần nhất";
  const titleEn = unknown
    ? "Data age unknown"
    : fresh
    ? "Fresh data (under 6 minutes)"
    : stale
    ? "Stale data (over 15 minutes)"
    : "Data from the last 6–15 minutes";

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[0.66rem] font-semibold border whitespace-nowrap ${tone.wrap}`}
      title={language === "vi" ? titleVi : titleEn}
    >
      {unknown ? (
        <Clock className="w-3 h-3" />
      ) : (
        <Radio className={`w-3 h-3 ${fresh && isLiveConnected ? "animate-pulse" : ""}`} />
      )}
      <span className="uppercase tracking-wider">{label}</span>
    </div>
  );
}

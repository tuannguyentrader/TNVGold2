"use client";

import { useEffect, useRef, useState } from "react";

interface InfoTipProps {
  text: string;
}

/**
 * InfoTip — tooltip cho metric card, hoạt động trên cả desktop (hover) lẫn mobile (tap).
 * - Desktop: giữ nguyên hover show/hide (onMouseEnter/onMouseLeave), click cũng toggle được.
 * - Mobile/touch: tap icon để mở/đóng; tap ra ngoài (click-outside) hoặc bấm Escape thì đóng.
 * - Icon luôn hiển thị trên mọi kích thước màn hình.
 * - Panel giới hạn max-w để không tràn màn hình nhỏ (right-0 + max-w min(300px, 78vw)).
 */
export function InfoTip({ text }: InfoTipProps) {
  const [isOpen, setIsOpen] = useState(false);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const rootRef = useRef<HTMLDivElement | null>(null);

  const show = () => {
    if (hideTimer.current) clearTimeout(hideTimer.current);
    setIsOpen(true);
  };

  const hide = () => {
    hideTimer.current = setTimeout(() => setIsOpen(false), 200);
  };

  // Click-outside: chạm ra ngoài → đóng ngay (mobile + desktop đều áp dụng).
  useEffect(() => {
    if (!isOpen) return;
    const onPointerDownOutside = (e: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDownOutside);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDownOutside);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [isOpen]);

  useEffect(() => {
    return () => {
      if (hideTimer.current) clearTimeout(hideTimer.current);
    };
  }, []);

  return (
    <div
      ref={rootRef}
      className="absolute top-2 right-2 z-40"
      onMouseEnter={show}
      onMouseLeave={hide}
      onClick={(e) => {
        e.stopPropagation();
        setIsOpen((v) => !v);
      }}
    >
      <button
        type="button"
        aria-label="Info"
        aria-expanded={isOpen}
        className="w-4 h-4 rounded-full border border-[rgba(245,197,66,0.35)] bg-black/40 hover:bg-[rgba(245,197,66,0.15)] hover:border-[#f5c542] text-[#f5c542] text-[0.62rem] font-serif font-bold italic flex items-center justify-center transition-all cursor-pointer shadow-sm"
      >
        i
      </button>

      {isOpen && (
        <div
          className="absolute right-0 top-full mt-1.5 w-max min-w-[220px] max-w-[min(300px,78vw)] p-2.5 rounded-xl border border-[rgba(245,197,66,0.4)] bg-[#111622] text-[#fdfdfd] shadow-2xl text-[0.72rem] leading-relaxed z-50 select-text break-words"
          onMouseEnter={show}
          onMouseLeave={hide}
          onClick={(e) => e.stopPropagation()}
        >
          {text}
        </div>
      )}
    </div>
  );
}

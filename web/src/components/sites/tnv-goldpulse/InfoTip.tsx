"use client";

import { useRef, useState } from "react";

interface InfoTipProps {
  text: string;
}

export function InfoTip({ text }: InfoTipProps) {
  const [isOpen, setIsOpen] = useState(false);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const show = () => {
    if (hideTimer.current) clearTimeout(hideTimer.current);
    setIsOpen(true);
  };

  const hide = () => {
    hideTimer.current = setTimeout(() => setIsOpen(false), 200);
  };

  return (
    <div
      className="absolute top-2 right-2 z-40"
      onMouseEnter={show}
      onMouseLeave={hide}
      onClick={(e) => e.stopPropagation()}
    >
      <button
        type="button"
        className="w-4 h-4 rounded-full border border-[rgba(245,197,66,0.35)] bg-black/40 hover:bg-[rgba(245,197,66,0.15)] hover:border-[#f5c542] text-[#f5c542] text-[0.62rem] font-serif font-bold italic flex items-center justify-center transition-all cursor-pointer shadow-sm"
      >
        i
      </button>

      {isOpen && (
        <div
          className="absolute right-0 top-full mt-1.5 min-w-[220px] max-w-[300px] p-2.5 rounded-xl border border-[rgba(245,197,66,0.4)] bg-[#111622] text-[#fdfdfd] shadow-2xl text-[0.72rem] leading-relaxed z-50 select-text break-words"
          onMouseEnter={show}
          onMouseLeave={hide}
        >
          {text}
        </div>
      )}
    </div>
  );
}
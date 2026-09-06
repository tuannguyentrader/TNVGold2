"use client";

import { useState, useEffect } from "react";

interface BrokerSlide {
  brand: string;
  title: string;
  desc: string;
  url: string;
}

const SLIDES: BrokerSlide[] = [
  {
    brand: "Exness",
    title: "Trade Gold with Raw Institutional Spreads",
    desc: "Ultra-fast execution synchronized with TNV Indicator breakout alerts.",
    url: "https://one.exnessonelink.com/a/aml5fdpb?source=app",
  },
  {
    brand: "IC Markets",
    title: "Raw ECN Spreads from 0.0 pips",
    desc: "Deep liquidity and lightning execution for serious XAUUSD traders.",
    url: "https://one.exnessonelink.com/a/aml5fdpb?source=app",
  },
  {
    brand: "Pepperstone",
    title: "Award-Winning Razor Pricing",
    desc: "Tight spreads and reliable uptime for algorithmic gold strategies.",
    url: "https://one.exnessonelink.com/a/aml5fdpb?source=app",
  },
];

const AUTO_ROTATE_MS = 10_000;

export function SponsorCard() {
  const [active, setActive] = useState(0);

  // Auto-rotate every 10s
  useEffect(() => {
    const timer = setInterval(() => {
      setActive((i) => (i + 1) % SLIDES.length);
    }, AUTO_ROTATE_MS);
    return () => clearInterval(timer);
  }, []);

  // Click vào card → next broker (giống click dot)
  const handleCardClick = () => {
    setActive((i) => (i + 1) % SLIDES.length);
  };

  const slide = SLIDES[active];

  return (
    <div
      onClick={handleCardClick}
      className="rounded-xl p-3.5 bg-[#090d16] border border-[rgba(245,197,66,0.35)] flex flex-col justify-between shadow-xl min-h-[148px] cursor-pointer select-none"
    >
      {/* Slide content (fade transition) */}
      <div key={active} className="animate-in fade-in duration-500">
        <div className="mb-1.5">
          <span className="inline-block px-2 py-0.5 rounded-full bg-[rgba(245,197,66,0.12)] text-[#f5c542] border border-[rgba(245,197,66,0.25)] text-[0.65rem] font-bold">
            {slide.brand}
          </span>
        </div>
        <h3 className="text-xs font-bold text-white mb-0.5">
          {slide.title}
        </h3>
        <p className="text-[0.72rem] text-gray-400 mb-2">
          {slide.desc}
        </p>
        <a
          href={slide.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="inline-block px-4 py-1 rounded-full border border-[#f5c542] text-[#f5c542] text-xs font-semibold hover:bg-[#f5c542] hover:text-[#05060a] transition-all cursor-pointer"
        >
          Open Account
        </a>
      </div>

      {/* Dots — click để chuyển nhanh + hiển thị vị trí */}
      <div className="flex items-center justify-center gap-1.5 mt-2.5">
        {SLIDES.map((_, i) => (
          <button
            key={i}
            onClick={(e) => {
              e.stopPropagation();
              setActive(i);
            }}
            aria-label={`Slide ${i + 1}`}
            className={`w-1.5 h-1.5 rounded-full transition-all cursor-pointer ${
              i === active ? "bg-[#f5c542]" : "bg-gray-600 hover:bg-gray-400"
            }`}
          />
        ))}
      </div>
    </div>
  );
}

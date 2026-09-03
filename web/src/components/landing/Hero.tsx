"use client";

import Link from "next/link";
import { i18n, type Lang, ADMIN_TELEGRAM } from "./i18n";

export function Hero({ lang }: { lang: Lang }) {
  const t = i18n[lang];
  return (
    <section className="flex items-center justify-center px-6 py-20 md:py-28">
      <div className="max-w-4xl text-center">
        <span className="inline-block px-3 py-1 mb-6 text-xs font-medium tracking-wider uppercase rounded-full bg-[#f5c542]/10 text-[#f5c542] border border-[#f5c542]/30">
          {t.badge}
        </span>
        <h1 className="text-4xl md:text-6xl font-bold mb-6">
          <span className="text-[#f5c542]">{t.heroTitle1}</span>{" "}
          <span>{t.heroTitle2}</span>
        </h1>
        <p className="text-lg md:text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
          {t.heroDesc}
        </p>
        <div className="flex flex-wrap gap-4 justify-center">
          <Link
            href="/goldpulse"
            className="px-6 py-3 rounded-lg bg-[#f5c542] text-[#05060a] font-semibold hover:bg-[#cfa744] transition"
          >
            {t.ctaDashboard}
          </Link>
          <a
            href={ADMIN_TELEGRAM}
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 rounded-lg border border-[#f5c542]/50 text-[#f5c542] hover:bg-[#f5c542]/10 transition"
          >
            {t.ctaContact}
          </a>
        </div>
      </div>
    </section>
  );
}

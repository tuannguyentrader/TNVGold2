"use client";

import { i18n, type Lang, ADMIN_TELEGRAM } from "./i18n";

export function BottomCTA({ lang }: { lang: Lang }) {
  const t = i18n[lang];
  return (
    <section className="px-6 py-20 border-t border-white/5">
      <div className="max-w-3xl mx-auto text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">{t.ctaTitle}</h2>
        <p className="text-lg text-gray-400 mb-8">{t.ctaDesc}</p>
        <a
          href={ADMIN_TELEGRAM}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block px-8 py-4 rounded-lg bg-[#f5c542] text-[#05060a] font-semibold hover:bg-[#cfa744] transition"
        >
          {t.ctaButton}
        </a>
      </div>
    </section>
  );
}

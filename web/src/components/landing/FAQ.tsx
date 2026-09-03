"use client";

import { ChevronDown } from "lucide-react";
import { i18n, type Lang } from "./i18n";

export function FAQ({
  lang,
  openFaq,
  setOpenFaq,
}: {
  lang: Lang;
  openFaq: number | null;
  setOpenFaq: (n: number | null) => void;
}) {
  const t = i18n[lang];
  return (
    <section className="px-6 py-20 border-t border-white/5">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-3">{t.faqTitle}</h2>
        </div>
        <div className="space-y-3">
          {t.faq.map((item, i) => {
            const isOpen = openFaq === i;
            return (
              <div
                key={i}
                className="rounded-xl bg-[#0b0f16] border border-white/5 overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaq(isOpen ? null : i)}
                  className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-white/[0.02] transition"
                  aria-expanded={isOpen}
                >
                  <span className="font-medium pr-4">{item.q}</span>
                  <ChevronDown
                    className={`w-5 h-5 text-[#f5c542] flex-shrink-0 transition-transform ${
                      isOpen ? "rotate-180" : ""
                    }`}
                  />
                </button>
                {isOpen && (
                  <div className="px-6 pb-4 text-sm text-gray-400 leading-relaxed border-t border-white/5 pt-3">
                    {item.a}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

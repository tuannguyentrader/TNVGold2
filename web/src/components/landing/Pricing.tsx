"use client";

import { Check, Sparkles } from "lucide-react";
import { i18n, type Lang, ADMIN_TELEGRAM, BOT_TELEGRAM } from "./i18n";

export function Pricing({ lang }: { lang: Lang }) {
  const t = i18n[lang];
  return (
    <section className="px-6 py-20 border-t border-white/5">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-3">{t.pricingTitle}</h2>
          <p className="text-gray-400 max-w-2xl mx-auto">{t.pricingSubtitle}</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Free */}
          <div className="p-8 rounded-xl bg-[#0b0f16] border border-white/5">
            <h3 className="text-2xl font-bold mb-2">{t.pricingFree.name}</h3>
            <div className="mb-6">
              <span className="text-4xl font-bold">{t.pricingFree.price}</span>
              <span className="text-gray-400 text-sm ml-1">{t.pricingFree.period}</span>
            </div>
            <ul className="space-y-3 mb-8">
              {t.pricingFree.features.map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                  <Check className="w-4 h-4 text-[#f5c542] mt-0.5 flex-shrink-0" />
                  <span>{f}</span>
                </li>
              ))}
            </ul>
            <a
              href={BOT_TELEGRAM}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full text-center px-6 py-3 rounded-lg border border-white/10 hover:border-[#f5c542]/50 hover:bg-[#f5c542]/5 transition"
            >
              {t.pricingFree.cta}
            </a>
          </div>

          {/* Pro */}
          <div className="relative p-8 rounded-xl bg-gradient-to-br from-[#f5c542]/[0.08] to-transparent border border-[#f5c542]/30">
            <div className="absolute -top-3 right-6 px-3 py-1 text-xs font-semibold rounded-full bg-[#f5c542] text-[#05060a] flex items-center gap-1">
              <Sparkles className="w-3 h-3" />
              {t.pricingPro.badge}
            </div>
            <h3 className="text-2xl font-bold mb-2 text-[#f5c542]">{t.pricingPro.name}</h3>
            <div className="mb-6">
              <span className="text-4xl font-bold">{t.pricingPro.price}</span>
              <span className="text-gray-400 text-sm ml-1">{t.pricingPro.period}</span>
            </div>
            <ul className="space-y-3 mb-8">
              {t.pricingPro.features.map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-200">
                  <Check className="w-4 h-4 text-[#f5c542] mt-0.5 flex-shrink-0" />
                  <span>{f}</span>
                </li>
              ))}
            </ul>
            <a
              href={ADMIN_TELEGRAM}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full text-center px-6 py-3 rounded-lg bg-[#f5c542] text-[#05060a] font-semibold hover:bg-[#cfa744] transition"
            >
              {t.pricingPro.cta}
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

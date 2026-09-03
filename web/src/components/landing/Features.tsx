"use client";

import {
  Activity,
  BarChart3,
  Bot,
  Globe,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { i18n, type Lang } from "./i18n";

const featureIcons = [Activity, TrendingUp, BarChart3, Globe, Sparkles, Bot];

export function Features({ lang }: { lang: Lang }) {
  const t = i18n[lang];
  return (
    <section className="px-6 py-20 border-t border-white/5">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-3">{t.featuresTitle}</h2>
          <p className="text-gray-400 max-w-2xl mx-auto">{t.featuresSubtitle}</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {t.features.map((f, i) => {
            const Icon = featureIcons[i] || BarChart3;
            return (
              <div
                key={i}
                className="p-6 rounded-xl bg-[#0b0f16] border border-white/5 hover:border-[#f5c542]/30 transition"
              >
                <div className="w-10 h-10 rounded-lg bg-[#f5c542]/10 flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-[#f5c542]" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-gray-400 leading-relaxed">{f.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

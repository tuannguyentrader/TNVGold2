"use client";

import Link from "next/link";
import { Zap } from "lucide-react";
import { i18n, type Lang } from "./i18n";

export function Header({ lang, setLang }: { lang: Lang; setLang: (l: Lang) => void }) {
  const t = i18n[lang];
  return (
    <header className="px-6 py-4 flex justify-between items-center border-b border-white/5 sticky top-0 bg-[#05060a]/80 backdrop-blur z-50">
      <Link href="/" className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#f5c542] to-[#cfa744] flex items-center justify-center">
          <Zap className="w-5 h-5 text-[#05060a]" />
        </div>
        <span className="font-semibold">
          <span className="text-[#f5c542]">TNV</span> Gold
        </span>
      </Link>
      <button
        onClick={() => setLang(lang === "vi" ? "en" : "vi")}
        className="px-3 py-1.5 text-sm font-medium rounded-md border border-white/10 hover:border-[#f5c542]/50 hover:bg-[#f5c542]/5 transition"
      >
        {t.languageToggle}
      </button>
    </header>
  );
}

"use client";

import Link from "next/link";
import { Send } from "lucide-react";
import { i18n, type Lang, ADMIN_TELEGRAM, BOT_TELEGRAM } from "./i18n";

export function Footer({ lang }: { lang: Lang }) {
  const t = i18n[lang];
  return (
    <footer className="border-t border-white/5 px-6 py-12">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#f5c542] to-[#cfa744] flex items-center justify-center">
                <Send className="w-4 h-4 text-[#05060a]" />
              </div>
              <span className="font-semibold">
                <span className="text-[#f5c542]">TNV</span> Gold
              </span>
            </Link>
            <p className="text-xs text-gray-500 max-w-xs">{t.footerDisclaimer}</p>
          </div>

          {/* Product */}
          <div>
            <h4 className="text-sm font-semibold mb-3 text-gray-200">{t.footerProduct}</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <Link href="/goldpulse" className="hover:text-[#f5c542] transition">
                  {t.footerDashboard}
                </Link>
              </li>
              <li>
                <Link href="/blog" className="hover:text-[#f5c542] transition">
                  {t.footerBlog}
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="text-sm font-semibold mb-3 text-gray-200">{t.footerResources}</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <a href="#faq" className="hover:text-[#f5c542] transition">
                  {t.footerFaq}
                </a>
              </li>
            </ul>
          </div>

          {/* Connect */}
          <div>
            <h4 className="text-sm font-semibold mb-3 text-gray-200">{t.footerConnect}</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <a
                  href={ADMIN_TELEGRAM}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-[#f5c542] transition"
                >
                  {t.footerContact}
                </a>
              </li>
              <li>
                <a
                  href={BOT_TELEGRAM}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-[#f5c542] transition"
                >
                  @TNVGold_bot
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-6 border-t border-white/5 text-center text-xs text-gray-500">
          {t.footerRights}
        </div>
      </div>
    </footer>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { Zap, Newspaper, BookOpen, LayoutDashboard, Bell, Check, ChevronDown } from "lucide-react";
import { i18n, type Lang } from "./i18n";

export function Header({ lang, setLang }: { lang: Lang; setLang: (l: Lang) => void }) {
  const t = i18n[lang];
  const pathname = usePathname();

  // Language dropdown state
  const [showLangMenu, setShowLangMenu] = useState(false);
  const langMenuRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (langMenuRef.current && !langMenuRef.current.contains(e.target as Node)) {
        setShowLangMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Close on ESC
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setShowLangMenu(false);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const navItems = [
    { href: "/goldpulse", label: t.navDashboard, icon: LayoutDashboard },
    { href: "/blog", label: t.navBlog, icon: BookOpen },
    { href: "/tin-tuc", label: t.navNews, icon: Newspaper },
  ];

  const isActive = (href: string) => pathname === href || pathname?.startsWith(href + "/");

  return (
    <header className="px-6 py-4 flex justify-between items-center border-b border-white/5 sticky top-0 bg-[#05060a]/80 backdrop-blur z-50">
      <div className="flex items-center gap-8">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#f5c542] to-[#cfa744] flex items-center justify-center">
            <Zap className="w-5 h-5 text-[#05060a]" />
          </div>
          <span className="font-semibold">
            <span className="text-[#f5c542]">TNV</span> Gold
          </span>
        </Link>

        {/* Nav menu — chỉ hiện trên md+ */}
        <nav className="hidden md:flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={[
                  "flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition",
                  active
                    ? "bg-[#f5c542]/10 text-[#f5c542]"
                    : "text-gray-400 hover:text-white hover:bg-white/5",
                ].join(" ")}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="flex items-center gap-2">
        {/* Bell — mở Subscribe Free */}
        <button
          onClick={() => {
            // Dispatch event — SubscribeBar ở layout.tsx sẽ nghe và mở modal ngay
            window.dispatchEvent(new CustomEvent("tnv:open-subscribe"));
          }}
          className="p-1.5 rounded-md border border-white/10 bg-white/5 hover:bg-white/10 text-[#f5c542] hover:border-[#f5c542]/40 transition-all cursor-pointer"
          title={lang === "vi" ? "Đăng ký / Thông báo" : "Subscribe / Notifications"}
          aria-label="Subscribe"
        >
          <Bell className="w-4 h-4" />
        </button>

        {/* Language dropdown — đồng bộ với SiteHeader */}
        <div className="relative" ref={langMenuRef}>
          <button
            onClick={() => setShowLangMenu(!showLangMenu)}
            className="flex items-center gap-1 px-2 py-1 rounded-md border border-white/10 bg-[#0e131f] hover:border-white/20 text-[0.7rem] font-semibold text-gray-200 transition-all cursor-pointer"
            title="Select Language"
            aria-expanded={showLangMenu}
          >
            <span>{lang === "en" ? "🇬🇧" : "🇻🇳"}</span>
            <span className="uppercase">{lang}</span>
            <ChevronDown className="w-3 h-3 text-gray-400" />
          </button>

          {showLangMenu && (
            <div className="absolute right-0 top-full mt-1.5 z-50 min-w-[130px] rounded-xl border border-white/10 bg-[#0b0f16] p-1 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
              <button
                onClick={() => {
                  setLang("en");
                  setShowLangMenu(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                  lang === "en"
                    ? "bg-[rgba(245,197,66,0.15)] text-[#f5c542] font-bold"
                    : "text-gray-300 hover:bg-white/5 hover:text-white"
                }`}
              >
                <span className="flex items-center gap-2">
                  <span>🇬🇧</span> English
                </span>
                {lang === "en" && <Check className="w-3 h-3 text-[#f5c542]" />}
              </button>

              <button
                onClick={() => {
                  setLang("vi");
                  setShowLangMenu(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                  lang === "vi"
                    ? "bg-[rgba(245,197,66,0.15)] text-[#f5c542] font-bold"
                    : "text-gray-300 hover:bg-white/5 hover:text-white"
                }`}
              >
                <span className="flex items-center gap-2">
                  <span>🇻🇳</span> Tiếng Việt
                </span>
                {lang === "vi" && <Check className="w-3 h-3 text-[#f5c542]" />}
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

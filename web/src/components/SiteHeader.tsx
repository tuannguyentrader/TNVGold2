"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { Zap, LayoutDashboard, BookOpen, Newspaper, Bell, Check, ChevronDown } from "lucide-react";
import { useLanguage } from "@/lib/language-context";

/**
 * SiteHeader — header global cho MỌI trang (trừ landing).
 * - Logo "TNV Gold" → về trang chủ
 * - Nav menu: Dashboard / Blog / Tin tức
 * - Language dropdown
 * - Bell notification
 * - Ẩn trên landing (landing có Header riêng với i18n)
 */
export function SiteHeader() {
  const pathname = usePathname() || "/";
  const { language, setLanguage } = useLanguage();
  const lang = (language as "vi" | "en") || "vi";

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

  // Ẩn trên landing
  if (pathname === "/") return null;

  const navItems = [
    {
      href: "/goldpulse",
      labelVi: "Dashboard",
      labelEn: "Dashboard",
      icon: LayoutDashboard,
    },
    {
      href: "/blog",
      labelVi: "Blog",
      labelEn: "Blog",
      icon: BookOpen,
    },
    {
      href: "/tin-tuc",
      labelVi: lang === "vi" ? "Tin tức" : "News",
      labelEn: "News",
      icon: Newspaper,
    },
  ];

  const isActive = (href: string) => pathname === href || pathname.startsWith(href + "/");

  return (
    <header className="px-4 sm:px-6 py-3 flex justify-between items-center border-b border-white/5 sticky top-0 bg-[#05060a]/85 backdrop-blur z-50">
      <div className="flex items-center gap-4 md:gap-8 min-w-0">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2 group shrink-0"
          aria-label={lang === "vi" ? "Về trang chủ TNV Gold" : "Back to TNV Gold home"}
        >
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#f5c542] to-[#cfa744] flex items-center justify-center">
            <Zap className="w-5 h-5 text-[#05060a]" />
          </div>
          <span className="font-semibold hidden sm:inline">
            <span className="text-[#f5c542]">TNV</span>{" "}
            <span className="text-white group-hover:text-[#f5c542] transition">Gold</span>
          </span>
        </Link>

        {/* Nav menu — desktop */}
        <nav className="hidden md:flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            const label = lang === "vi" ? item.labelVi : item.labelEn;
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
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Right: Language + Bell (đồng bộ với landing) */}
      <div className="flex items-center gap-2">
        {/* Language Dropdown */}
        <div className="relative" ref={langMenuRef}>
          <button
            onClick={() => setShowLangMenu(!showLangMenu)}
            className="flex items-center gap-1 px-2 py-1 rounded-md border border-white/10 bg-[#0e131f] hover:border-white/20 text-[0.7rem] font-semibold text-gray-200 transition-all cursor-pointer"
            title="Select Language"
            aria-expanded={showLangMenu}
          >
            <span>{language === "en" ? "🇬🇧" : "🇻🇳"}</span>
            <span className="uppercase">{language}</span>
            <ChevronDown className="w-3 h-3 text-gray-400" />
          </button>

          {showLangMenu && (
            <div className="absolute right-0 top-full mt-1.5 z-50 min-w-[130px] rounded-xl border border-white/10 bg-[#0b0f16] p-1 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
              <button
                onClick={() => {
                  setLanguage("en");
                  setShowLangMenu(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                  language === "en"
                    ? "bg-[rgba(245,197,66,0.15)] text-[#f5c542] font-bold"
                    : "text-gray-300 hover:bg-white/5 hover:text-white"
                }`}
              >
                <span className="flex items-center gap-2">
                  <span>🇬🇧</span> English
                </span>
                {language === "en" && <Check className="w-3 h-3 text-[#f5c542]" />}
              </button>

              <button
                onClick={() => {
                  setLanguage("vi");
                  setShowLangMenu(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                  language === "vi"
                    ? "bg-[rgba(245,197,66,0.15)] text-[#f5c542] font-bold"
                    : "text-gray-300 hover:bg-white/5 hover:text-white"
                }`}
              >
                <span className="flex items-center gap-2">
                  <span>🇻🇳</span> Tiếng Việt
                </span>
                {language === "vi" && <Check className="w-3 h-3 text-[#f5c542]" />}
              </button>
            </div>
          )}
        </div>

        {/* Bell — mở Subscribe modal */}
        <button
          className="p-1.5 rounded-md border border-white/10 bg-white/5 hover:bg-white/10 text-[#f5c542] hover:border-[#f5c542]/40 transition-all cursor-pointer"
          title={lang === "vi" ? "Đăng ký / Thông báo" : "Subscribe / Notifications"}
          aria-label="Subscribe"
          onClick={() => {
            window.dispatchEvent(new CustomEvent("tnv:open-subscribe"));
          }}
        >
          <Bell className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}

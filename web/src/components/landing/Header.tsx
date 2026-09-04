"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Zap, Newspaper, BookOpen, LayoutDashboard } from "lucide-react";
import { i18n, type Lang } from "./i18n";

export function Header({ lang, setLang }: { lang: Lang; setLang: (l: Lang) => void }) {
  const t = i18n[lang];
  const pathname = usePathname();

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

      <button
        onClick={() => setLang(lang === "vi" ? "en" : "vi")}
        className="px-3 py-1.5 text-sm font-medium rounded-md border border-white/10 hover:border-[#f5c542]/50 hover:bg-[#f5c542]/5 transition"
      >
        {t.languageToggle}
      </button>
    </header>
  );
}

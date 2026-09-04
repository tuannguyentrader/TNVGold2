"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Zap, LayoutDashboard, BookOpen, Newspaper, ArrowLeft } from "lucide-react";
import { useLanguage } from "@/lib/language-context";

/**
 * SiteHeader — header global cho MỌI trang (landing, blog, news, goldpulse).
 * - Click logo "TNV Gold" → về trang chủ
 * - Nav: Dashboard / Blog / Tin tức (highlight active)
 * - Ẩn trên landing page (vì landing đã có Header riêng với CTA)
 */
export function SiteHeader() {
  const pathname = usePathname() || "/";
  const { language } = useLanguage();
  const lang = (language as "vi" | "en") || "vi";

  // Ẩn trên landing + goldpulse — cả 2 đều có Header riêng
  if (pathname === "/" || pathname.startsWith("/goldpulse")) return null;

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
      labelVi: "Tin tức",
      labelEn: "News",
      icon: Newspaper,
    },
  ];

  const isActive = (href: string) => pathname === href || pathname.startsWith(href + "/");

  return (
    <header className="px-6 py-3 flex justify-between items-center border-b border-white/5 sticky top-0 bg-[#05060a]/85 backdrop-blur z-50">
      <div className="flex items-center gap-4 md:gap-8">
        {/* Logo — click về trang chủ */}
        <Link
          href="/"
          className="flex items-center gap-2 group"
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

        {/* Back to home — chỉ hiện trên mobile / trang detail */}
        {pathname !== "/" && pathname !== "/blog" && pathname !== "/tin-tuc" && pathname !== "/goldpulse" && (
          <Link
            href="/"
            className="md:hidden text-xs text-gray-400 hover:text-[#f5c542] inline-flex items-center gap-1"
          >
            <ArrowLeft className="w-3 h-3" />
            {lang === "vi" ? "Trang chủ" : "Home"}
          </Link>
        )}

        {/* Nav menu */}
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

      {/* Right side: link về home trên mobile */}
      <div className="flex items-center gap-2">
        <Link
          href="/"
          className="md:hidden text-xs text-[#f5c542] hover:underline"
        >
          {lang === "vi" ? "Trang chủ" : "Home"}
        </Link>
        {/* Desktop: link về home nhỏ */}
        <Link
          href="/"
          className="hidden md:inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium text-gray-400 hover:text-[#f5c542] hover:bg-[#f5c542]/5 transition"
        >
          <ArrowLeft className="w-3 h-3" />
          {lang === "vi" ? "Trang chủ" : "Home"}
        </Link>
      </div>
    </header>
  );
}

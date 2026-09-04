"use client";

import { useState, useEffect } from "react";
import { Header } from "./Header";
import { Hero } from "./Hero";
import { Features } from "./Features";
import { Pricing } from "./Pricing";
import { FAQ } from "./FAQ";
import { BottomCTA } from "./BottomCTA";
import { Footer } from "./Footer";
import { type Lang } from "./i18n";

export default function LandingClient() {
  const [lang, setLang] = useState<Lang>("vi");
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  // Load ngôn ngữ từ localStorage — dùng chung key 'tnv_lang' với useLanguage()
  useEffect(() => {
    const saved = localStorage.getItem("tnv_lang");
    if (saved === "vi" || saved === "en") setLang(saved);

    // Nghe event từ tab khác + từ useLanguage (cùng trang)
    const onLangChange = (e: Event) => {
      const detail = (e as CustomEvent<{ lang: Lang }>).detail;
      if (detail?.lang === "vi" || detail?.lang === "en") {
        setLang(detail.lang);
      }
    };
    const onStorage = (e: StorageEvent) => {
      if (e.key === "tnv_lang" && (e.newValue === "vi" || e.newValue === "en")) {
        setLang(e.newValue);
      }
    };
    window.addEventListener("tnv:lang-change", onLangChange);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener("tnv:lang-change", onLangChange);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  // Lưu + dispatch event khi đổi ngôn ngữ
  useEffect(() => {
    if (typeof document !== "undefined") document.documentElement.lang = lang;
    localStorage.setItem("tnv_lang", lang);
    // Xoá key cũ để dọn dẹp
    localStorage.removeItem("tnv_landing_lang");
    // Báo cho các component khác trong cùng trang biết
    window.dispatchEvent(new CustomEvent("tnv:lang-change", { detail: { lang } }));
  }, [lang]);

  return (
    <main className="min-h-screen flex flex-col">
      <Header lang={lang} setLang={setLang} />
      <Hero lang={lang} />
      <Features lang={lang} />
      <Pricing lang={lang} />
      <div id="faq">
        <FAQ lang={lang} openFaq={openFaq} setOpenFaq={setOpenFaq} />
      </div>
      <BottomCTA lang={lang} />
      <Footer lang={lang} />
    </main>
  );
}

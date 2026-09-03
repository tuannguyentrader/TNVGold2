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

  useEffect(() => {
    const saved = localStorage.getItem("tnv_landing_lang");
    if (saved === "vi" || saved === "en") setLang(saved);
  }, []);

  useEffect(() => {
    if (typeof document !== "undefined") document.documentElement.lang = lang;
    localStorage.setItem("tnv_landing_lang", lang);
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

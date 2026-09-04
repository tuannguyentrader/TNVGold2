"use client";

import { useState } from "react";
import { Header } from "./Header";
import { Hero } from "./Hero";
import { Features } from "./Features";
import { Pricing } from "./Pricing";
import { FAQ } from "./FAQ";
import { BottomCTA } from "./BottomCTA";
import { Footer } from "./Footer";
import { type Lang } from "./i18n";
import { useLanguage } from "@/lib/language-context";

export default function LandingClient() {
  const { language, setLanguage } = useLanguage();
  const lang = (language as Lang) || "vi";
  const setLang = (l: Lang) => setLanguage(l);
  const [openFaq, setOpenFaq] = useState<number | null>(null);

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

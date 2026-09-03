"use client";

import { useState, useEffect, useRef } from "react";
import { Bell, Key, Check, ChevronDown } from "lucide-react";
import { NotificationModal } from "./NotificationModal";
import { useLanguage } from "@/lib/language-context";

function getActiveSession(): string {
  const utcHour = new Date().getUTCHours();
  if (utcHour >= 8 && utcHour < 13) return "London";
  if (utcHour >= 13 && utcHour < 17) return "London & NY Overlap";
  if (utcHour >= 17 && utcHour < 22) return "New York";
  if (utcHour >= 22 || utcHour < 7) return "Tokyo";
  return "London Pre-market";
}

export function HeroHeader() {
  const { language, setLanguage, t } = useLanguage();
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [keySaved, setKeySaved] = useState(false);
  const [showNotificationModal, setShowNotificationModal] = useState(false);
  const [showLangMenu, setShowLangMenu] = useState(false);
  const [session, setSession] = useState<string>("London Session");
  const langMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSession(getActiveSession());
    const interval = setInterval(() => {
      setSession(getActiveSession());
    }, 60000);
    return () => clearInterval(interval);
  }, []);

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

  // Handle ESC key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setShowKeyModal(false);
        setShowLangMenu(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleSaveKey = (e: React.FormEvent) => {
    e.preventDefault();
    if (apiKey.trim()) {
      setKeySaved(true);
      setTimeout(() => {
        setShowKeyModal(false);
        setKeySaved(false);
      }, 1200);
    }
  };

  return (
    <>
      <header className="flex items-center justify-between gap-3 py-3 mb-3 text-sm flex-wrap">
        {/* Left: Brand -> TNV Gold */}
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-2">
            <svg
              viewBox="0 0 24 24"
              className="w-6 h-6 text-[#f5c542]"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              <circle cx="12" cy="4" r="1.5" fill="#f5c542" />
              <circle cx="18" cy="8" r="1.5" fill="#f5c542" />
              <circle cx="6" cy="16" r="1.5" fill="#f5c542" />
            </svg>
            <h1 className="text-xl font-bold tracking-tight text-white m-0 flex items-center gap-1.5">
              <span className="text-[#f5c542]">TNV</span>
              <span>Gold</span>
            </h1>
          </div>

          <span className="px-2 py-0.5 rounded-md text-[0.68rem] font-bold tracking-wider uppercase bg-[#18392b] text-[#61e294] border border-[#61e294]/30">
            {t.brandTag}
          </span>
        </div>

        {/* Center: Tên phiên hiện tại • 10s refresh */}
        <div className="hidden md:flex items-center gap-2 text-xs text-gray-300 font-medium">
          <span className="text-[#f5c542] font-semibold">{session}</span>
          <span className="text-gray-600">&bull;</span>
          <span className="text-gray-400 font-mono text-[0.7rem]">10s refresh</span>
        </div>

        {/* Right: Language Dropdown Menu + Manage + Bell */}
        <div className="flex items-center gap-2">
          {/* Language Dropdown Menu */}
          <div className="relative" ref={langMenuRef}>
            <button
              onClick={() => setShowLangMenu(!showLangMenu)}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-white/10 bg-[#0e131f] hover:border-white/20 text-xs font-semibold text-gray-200 transition-all cursor-pointer"
              title="Select Language"
              aria-expanded={showLangMenu}
            >
              <span>{language === "en" ? "🇬🇧" : "🇻🇳"}</span>
              <span className="text-[0.7rem] uppercase">{language}</span>
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

          <button
            onClick={() => setShowKeyModal(true)}
            className="px-3 py-1 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-xs font-semibold text-gray-200 transition-all cursor-pointer"
          >
            {t.manageBtn}
          </button>

          <button
            onClick={() => setShowNotificationModal(true)}
            className="p-1.5 rounded-full border border-white/10 bg-white/5 hover:bg-white/10 text-[#f5c542] hover:border-[#f5c542]/40 transition-all cursor-pointer"
            title="Notification Center"
            aria-label="Notification Center"
          >
            <Bell className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Notifications Modal */}
      <NotificationModal
        isOpen={showNotificationModal}
        onClose={() => setShowNotificationModal(false)}
      />

      {/* API Key Modal */}
      {showKeyModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200"
          onClick={() => setShowKeyModal(false)}
        >
          <div
            className="relative w-full max-w-md rounded-2xl border border-[rgba(207,167,68,0.4)] bg-[#0b0f16] p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2 mb-3">
              <Key className="w-4 h-4 text-[#f5c542]" />
              <h3 className="text-base font-bold text-white m-0">{t.configTitle}</h3>
              <span className="text-[0.6rem] px-2 py-0.5 rounded-full bg-[rgba(245,197,66,0.12)] text-[#f5c542] border border-[rgba(245,197,66,0.3)] font-semibold uppercase tracking-wider whitespace-nowrap">
                Coming soon
              </span>
            </div>
            <p className="text-xs text-gray-400 mb-2">
              {t.configDesc}
            </p>
            <div className="mb-4 rounded-lg border border-[rgba(245,197,66,0.25)] bg-[rgba(245,197,66,0.06)] px-3 py-2 text-[0.7rem] text-gray-300">
              <span className="font-semibold text-[#f5c542]">
                {language === "vi" ? "Xem trước:" : "Preview:"}
              </span>{" "}
              {language === "vi"
                ? "Đồng bộ MT5 trực tiếp sẽ sớm ra mắt. Xác thực token chưa hoạt động."
                : "live MT5 streaming sync is coming soon. Token validation is not active yet."}
            </div>
            <form onSubmit={handleSaveKey} className="space-y-4">
              <div>
                <input
                  type="text"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="tnv_xxxxxxxxxxxxxxxx"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-white/10 bg-[#111622] text-sm text-white font-mono placeholder:text-gray-600 focus:outline-none focus:border-[#f5c542]"
                  autoFocus
                />
              </div>
              <div className="flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setShowKeyModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-gray-400 hover:text-white cursor-pointer"
                >
                  {t.cancel}
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-[#f5c542] text-[#05060a] hover:opacity-90 transition-opacity flex items-center gap-1.5 cursor-pointer shadow-md"
                >
                  {keySaved ? (
                    <>
                      <Check className="w-3.5 h-3.5" /> {t.saved}
                    </>
                  ) : (
                    t.saveKey
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

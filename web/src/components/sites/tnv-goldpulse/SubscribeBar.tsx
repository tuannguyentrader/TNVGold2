"use client";

import { useState, useEffect } from "react";
import { AlertTriangle, X } from "lucide-react";
import { NotificationModal } from "./NotificationModal";
import { useLanguage } from "@/lib/language-context";

/**
 * SubscribeBar — thanh sticky bottom (global trên mọi trang).
 * Style + nội dung lấy từ DisclaimerBanner cũ.
 * Click "Subscribe Free" → mở modal.
 */
export function SubscribeBar() {
  const { t, language } = useLanguage();
  const [dismissed, setDismissed] = useState(false);
  const [showModal, setShowModal] = useState(false);

  // Nghe event từ Bell icon ở SiteHeader / Header landing
  useEffect(() => {
    const handler = () => {
      setDismissed(false);
      setShowModal(true);
    };
    window.addEventListener("tnv:open-subscribe", handler);
    return () => window.removeEventListener("tnv:open-subscribe", handler);
  }, []);

  if (dismissed) return null;

  return (
    <>
      <div
        className="fixed bottom-0 left-0 right-0 z-40 flex items-center justify-between gap-3 px-3.5 py-2 border-t border-[rgba(245,197,66,0.2)] bg-[rgba(245,197,66,0.04)] backdrop-blur-md text-[0.76rem] text-[rgba(230,230,230,0.85)] shadow-2xl animate-in slide-in-from-bottom duration-300"
      >
        <div className="flex items-center gap-2 max-w-[1220px] mx-auto w-full">
          <AlertTriangle className="w-3.5 h-3.5 text-[#f5c542] shrink-0" />
          <span className="leading-relaxed">
            <strong className="text-[#f5c542] font-semibold">
              {language === "vi" ? "Lưu ý rủi ro:" : "Risk Notice:"}
            </strong>{" "}
            {t.subBarText}
          </span>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={() => setShowModal(true)}
            className="px-3 py-1 rounded-lg bg-[#f5c542] text-[#05060a] font-bold text-[0.7rem] hover:bg-[#cfa744] transition-all cursor-pointer shadow-md"
          >
            {t.subBarBtn}
          </button>
          <button
            onClick={() => setDismissed(true)}
            className="text-[rgba(255,255,255,0.4)] hover:text-white transition-colors p-1 cursor-pointer"
            title="Close bar"
            aria-label="Close bar"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <NotificationModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
      />
    </>
  );
}

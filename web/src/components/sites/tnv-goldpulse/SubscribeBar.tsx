"use client";

import { useState, useEffect } from "react";
import { X } from "lucide-react";
import { NotificationModal } from "./NotificationModal";
import { useLanguage } from "@/lib/language-context";

export function SubscribeBar() {
  const { t } = useLanguage();
  const [dismissed, setDismissed] = useState(false);
  const [showModal, setShowModal] = useState(false);

  // Nghe event từ Bell icon ở SiteHeader / Header landing
  useEffect(() => {
    const handler = () => {
      setDismissed(false); // hiện lại bar nếu user đã đóng
      setShowModal(true);
    };
    window.addEventListener("tnv:open-subscribe", handler);
    return () => window.removeEventListener("tnv:open-subscribe", handler);
  }, []);

  if (dismissed) return null;

  return (
    <>
      <div className="fixed bottom-0 left-0 right-0 z-40 bg-[#080d16]/95 backdrop-blur-md border-t border-white/10 px-4 py-2.5 shadow-2xl animate-in slide-in-from-bottom duration-300">
        <div className="max-w-[1220px] mx-auto flex items-center justify-between gap-4">
          {/* Left Text */}
          <div className="flex items-center gap-2 text-xs sm:text-sm text-gray-200">
            <span className="text-base">&#9993;</span>
            <span>
              {t.subBarText}
            </span>
          </div>

          {/* Right Action */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-1.5 rounded-lg bg-[#61e294] text-[#05060a] font-bold text-xs hover:bg-[#52d385] transition-all cursor-pointer shadow-md"
            >
              {t.subBarBtn}
            </button>
            <button
              onClick={() => setDismissed(true)}
              className="text-gray-400 hover:text-white transition-colors p-1 cursor-pointer"
              title="Close bar"
              aria-label="Close bar"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <NotificationModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
      />
    </>
  );
}

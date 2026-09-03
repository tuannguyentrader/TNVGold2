"use client";

import { useState } from "react";
import { Shield, X } from "lucide-react";
import { useLanguage } from "@/lib/language-context";

type LegalDoc = "terms" | "privacy" | "refund";

export function SiteFooter() {
  const { language, t } = useLanguage();
  const [activeDoc, setActiveDoc] = useState<LegalDoc | null>(null);

  const docMeta: Record<LegalDoc, { title: string; body: string }> = {
    terms: {
      title: language === "vi" ? "Điều khoản Dịch vụ TNV" : "TNV Terms of Service",
      body:
        language === "vi"
          ? "TNV Gold phục vụ mục đích phân tích & giáo dục. Người dùng tự quản lý rủi ro vốn; mọi quyết định giao dịch đều do người dùng tự chịu trách nhiệm."
          : "TNV Gold is for analysis & educational purposes only. Users manage their own capital risk; all trading decisions are made solely by the user.",
    },
    privacy: {
      title: language === "vi" ? "Chính sách Bảo mật TNV" : "TNV Privacy Policy",
      body:
        language === "vi"
          ? "TNV tuyệt đối không chia sẻ thông tin cá nhân hoặc API key của người dùng cho bên thứ ba."
          : "No user API keys or personal data are shared with third parties.",
    },
    refund: {
      title: language === "vi" ? "Chính sách Hoàn tiền TNV" : "TNV Refund Policy",
      body:
        language === "vi"
          ? "TNV cam kết hỗ trợ tối đa cho các gói tài khoản PRO. Chính sách hoàn tiền sẽ được công bố chi tiết khi cập nhật."
          : "Satisfaction guarantee on PRO subscriptions. Detailed refund terms will be published at launch.",
    },
  };

  return (
    <>
      <footer
        id="footer"
        className="mt-10 pt-6 border-t border-white/10 text-[0.74rem] text-gray-400 leading-relaxed font-sans"
      >
        <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-white/[0.02] border border-white/5 mb-5">
          <Shield className="w-4 h-4 text-[#f5c542] shrink-0 mt-0.5" />
          <div className="space-y-1 text-[0.72rem] text-gray-400">
            <p className="text-gray-300 font-semibold m-0">
              {language === "vi" ? "Công bố Pháp lý & Quản lý Rủi ro" : "Regulatory & Risk Disclosure"}
            </p>
            <p className="m-0">
              {t.footerDesc}{" "}
              {language === "vi"
                ? "Chúng tôi không cung cấp dịch vụ tư vấn tài chính, ủy thác hay quản lý tài khoản. Mọi quyết định giao dịch đều do người dùng tự chịu trách nhiệm."
                : "We do not provide financial advice, personalized trading signals, managed accounts, or direct trade execution. All trading decisions are made solely by the user."}
            </p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pb-5 text-[0.72rem] text-gray-500">
          <div>
            {t.footerRights}
          </div>

          <div className="flex items-center gap-3 font-medium">
            <button
              type="button"
              onClick={() => setActiveDoc("terms")}
              className="text-[#f5c542] hover:underline cursor-pointer"
            >
              {language === "vi" ? "Điều khoản" : "Terms"}
            </button>
            <span>&bull;</span>
            <button
              type="button"
              onClick={() => setActiveDoc("privacy")}
              className="text-[#f5c542] hover:underline cursor-pointer"
            >
              {language === "vi" ? "Bảo mật" : "Privacy"}
            </button>
            <span>&bull;</span>
            <button
              type="button"
              onClick={() => setActiveDoc("refund")}
              className="text-[#f5c542] hover:underline cursor-pointer"
            >
              {language === "vi" ? "Chính sách Hoàn tiền" : "Refund Policy"}
            </button>
          </div>
        </div>
      </footer>

      {/* In-app legal modal (replaces native alert) */}
      {activeDoc && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="legal-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200"
          onClick={() => setActiveDoc(null)}
        >
          <div
            className="relative w-full max-w-md rounded-2xl border border-[rgba(207,167,68,0.4)] bg-[#0b0f16] p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 id="legal-modal-title" className="text-base font-bold text-white m-0">
                {docMeta[activeDoc].title}
              </h3>
              <button
                type="button"
                onClick={() => setActiveDoc(null)}
                className="text-gray-400 hover:text-white transition-colors p-1 cursor-pointer"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-[0.78rem] text-gray-300 leading-relaxed m-0">
              {docMeta[activeDoc].body}
            </p>
            <div className="flex items-center justify-end mt-5">
              <button
                type="button"
                onClick={() => setActiveDoc(null)}
                className="px-5 py-2 rounded-xl text-xs font-bold bg-[#f5c542] text-[#05060a] hover:opacity-90 transition-opacity cursor-pointer shadow-md"
              >
                {language === "vi" ? "Đóng" : "Close"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

"use client";

import { useState, useEffect } from "react";
import { Sparkles, ArrowRight, ShieldCheck, CheckCircle2, X } from "lucide-react";

export function ProUpgradeBar() {
  const [showProModal, setShowProModal] = useState(false);
  const [proToast, setProToast] = useState(false);

  // Auto-dismiss the "coming soon" toast after 3 seconds
  useEffect(() => {
    if (proToast) {
      const t = setTimeout(() => setProToast(false), 3000);
      return () => clearTimeout(t);
    }
  }, [proToast]);

  const handleGetPro = () => {
    // No real checkout backend yet — show a clear "coming soon" status instead of a fake alert
    setProToast(true);
  };

  // Handle ESC key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && showProModal) {
        setShowProModal(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [showProModal]);

  return (
    <>
      <div
        id="qx-pro-bar"
        className="flex items-center justify-between gap-3 px-3.5 py-2.5 mb-4 rounded-xl bg-gradient-to-r from-[rgba(97,226,148,0.12)] via-[rgba(97,226,148,0.06)] to-[rgba(245,197,66,0.08)] border border-[rgba(97,226,148,0.3)] text-[0.8rem] text-[#e8f5e9] flex-wrap shadow-sm"
      >
        <div className="flex items-center gap-2">
          <div className="p-1 rounded-md bg-[rgba(97,226,148,0.2)] text-[#61e294]">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <span>
            <strong className="text-white font-semibold">TNV Free:</strong> Standard 15-min refresh. Upgrade to <span className="text-[#f5c542] font-semibold">TNV PRO</span> for 1-second live stream &amp; Telegram alerts.
          </span>
        </div>

        <button
          onClick={() => setShowProModal(true)}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[0.72rem] font-bold bg-gradient-to-r from-[#cfa744] via-[#f5c542] to-[#f5d061] text-[#05060a] hover:shadow-[0_0_16px_rgba(245,197,66,0.4)] transition-all transform hover:-translate-y-0.5 cursor-pointer whitespace-nowrap"
        >
          Upgrade to TNV PRO
          <ArrowRight className="w-3 h-3" />
        </button>
      </div>

      {/* Pro Modal */}
      {showProModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200"
          onClick={() => setShowProModal(false)}
        >
          <div
            className="relative w-full max-w-md rounded-2xl border border-[rgba(207,167,68,0.5)] bg-[#0b0f16] p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setShowProModal(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors p-1 cursor-pointer"
              aria-label="Close modal"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="text-center mb-5">
              <span className="inline-block px-2.5 py-0.5 rounded-full text-[0.65rem] font-bold tracking-wider uppercase bg-[rgba(245,197,66,0.12)] text-[#f5c542] border border-[rgba(245,197,66,0.3)] mb-1.5">
                TNV PRO MEMBERSHIP
              </span>
              <h2 className="text-lg font-bold text-white m-0">Unlock Institutional Grade Market Flow</h2>
              <p className="text-[0.74rem] text-gray-400 mt-0.5">Real-time algorithmic edge for serious gold traders</p>
            </div>

            <div className="space-y-2 mb-5">
              {[
                "1-Second Real-Time Live Streaming Data",
                "Automated Telegram & Discord High-Probability Alerts",
                "Complete Multi-Timeframe Ring Buffer History",
                "Exclusive Session Flow Orderbook & Liquidity Zones",
                "Direct API Webhook & Pine Script Integration",
              ].map((feat, idx) => (
                <div key={idx} className="flex items-center gap-2 text-[0.74rem] text-gray-200">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#61e294] shrink-0" />
                  <span>{feat}</span>
                </div>
              ))}
            </div>

            <div className="p-3.5 rounded-xl bg-[#111622] border border-[rgba(255,255,255,0.08)] flex items-center justify-between mb-5">
              <div>
                <div className="text-[0.68rem] text-gray-400">Monthly Pass</div>
                <div className="text-base font-bold text-white">$49 <span className="text-[0.68rem] text-gray-400 font-normal">/ month</span></div>
              </div>
              <div className="flex flex-col items-end gap-1.5">
                <button
                  onClick={handleGetPro}
                  className="px-4 py-2 rounded-xl font-bold text-xs bg-gradient-to-r from-[#cfa744] to-[#f5c542] text-[#05060a] hover:opacity-90 transition-opacity shadow-lg cursor-pointer"
                >
                  Get TNV PRO Now
                </button>
                <span className="text-[0.62rem] font-semibold uppercase tracking-wider text-[#f5c542]/80">
                  Coming soon
                </span>
              </div>
            </div>

            <div className="flex items-center justify-center gap-1.5 text-[0.68rem] text-gray-500">
              <ShieldCheck className="w-3.5 h-3.5 text-gray-400" />
              <span>30-Day Money Back Guarantee &bull; Cancel Anytime</span>
            </div>
          </div>
        </div>
      )}

      {/* In-app "coming soon" toast (replaces native alert) */}
      {proToast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[60] px-4 py-2.5 rounded-xl border border-[rgba(245,197,66,0.4)] bg-[#111622] text-[0.78rem] text-gray-200 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
          <span className="font-semibold text-[#f5c542]">TNV PRO</span> — Checkout is coming soon. Our team is finalizing secure billing.
        </div>
      )}
    </>
  );
}

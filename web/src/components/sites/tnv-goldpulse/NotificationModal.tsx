"use client";

import { useState, useEffect } from "react";
import { X, Bell, ChevronDown, ChevronUp, Check, Send } from "lucide-react";

interface NotificationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function NotificationModal({ isOpen, onClose }: NotificationModalProps) {
  const [email, setEmail] = useState("");
  const [sessionTime, setSessionTime] = useState("london");
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [pushEnabled, setPushEnabled] = useState(false);
  const [pushPermissionMsg, setPushPermissionMsg] = useState<string | null>(null);

  // Accordion states
  const [smartAlertsOpen, setSmartAlertsOpen] = useState(false);
  const [economicEventsOpen, setEconomicEventsOpen] = useState(false);
  const [pushNotificationsOpen, setPushNotificationsOpen] = useState(true);
  const [advancedOpen, setAdvancedOpen] = useState(true);

  // Advanced toggles
  const [pauseAll, setPauseAll] = useState(false);
  const [sendToEmail, setSendToEmail] = useState(true);
  const [quietHours, setQuietHours] = useState(true);
  const [testSent, setTestSent] = useState(false);

  // Telegram state
  const [telegramChatId, setTelegramChatId] = useState("");
  const [telegramSaved, setTelegramSaved] = useState(false);

  // Handle ESC key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      setIsSubscribed(true);
      setTimeout(() => setIsSubscribed(false), 3000);
    }
  };

  const handleEnablePush = async () => {
    if (typeof window !== "undefined" && "Notification" in window) {
      try {
        const permission = await Notification.requestPermission();
        if (permission === "granted") {
          setPushEnabled(true);
          setPushPermissionMsg(null);
        } else {
          setPushPermissionMsg("Notification permission was not granted in your browser settings. Enable it in your browser to receive push alerts.");
        }
      } catch {
        setPushEnabled(true);
        setPushPermissionMsg(null);
      }
    } else {
      setPushEnabled(true);
      setPushPermissionMsg(null);
    }
  };

  const handleSendTestAlert = () => {
    setTestSent(true);
    setTimeout(() => setTestSent(false), 3000);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-[480px] my-8 rounded-2xl border border-[rgba(255,255,255,0.1)] bg-[#0c1017] p-6 shadow-2xl text-gray-200 font-sans"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/5">
          <h2 className="text-lg font-bold text-white flex items-center gap-2 m-0">
            <Bell className="w-5 h-5 text-[#f5c542]" />
            Notifications &amp; Alerts
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors p-1 cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-3.5 max-h-[75vh] overflow-y-auto pr-1">
          {/* 1. Daily Gold Pulse (Email Newsletter) */}
          <div className="rounded-xl border border-[rgba(255,255,255,0.08)] bg-[#121824] p-4">
            <div className="flex items-center justify-between gap-2 mb-1">
              <h3 className="text-sm font-bold text-white m-0">Daily TNV Gold Pulse</h3>
              <span className="text-[0.6rem] px-2 py-0.5 rounded-full bg-[rgba(245,197,66,0.12)] text-[#f5c542] border border-[rgba(245,197,66,0.3)] font-semibold uppercase tracking-wider whitespace-nowrap">
                Coming soon
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-1 mb-3">
              One email each weekday morning with bias, pulse, key pivot levels, and high-impact gold events.
            </p>

            <form onSubmit={handleSubscribe} className="space-y-2.5">
              <input
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg bg-white/5 border border-white/10 focus:border-[#f5c542] focus:outline-none text-xs text-white placeholder-gray-500 transition-colors"
                required
              />

              <div className="relative">
                <select
                  value={sessionTime}
                  onChange={(e) => setSessionTime(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-lg bg-white/5 border border-white/10 focus:border-[#f5c542] focus:outline-none text-xs text-white appearance-none cursor-pointer pr-8"
                >
                  <option value="london" className="bg-[#121824] text-white">London open (08:00 UTC / 15:00 GMT+7)</option>
                  <option value="ny" className="bg-[#121824] text-white">New York open (13:30 UTC / 20:30 GMT+7)</option>
                  <option value="tokyo" className="bg-[#121824] text-white">Tokyo open (00:00 UTC / 07:00 GMT+7)</option>
                </select>
                <ChevronDown className="w-4 h-4 text-gray-400 absolute right-3 top-3 pointer-events-none" />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 rounded-lg text-xs font-bold bg-[#48bb78] hover:bg-[#38a169] text-[#05060a] transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-md"
              >
                {isSubscribed ? (
                  <>
                    <Check className="w-4 h-4" />
                    Subscribed Successfully!
                  </>
                ) : (
                  "Subscribe - Free"
                )}
              </button>
            </form>
          </div>

          {/* 2. Telegram VIP Alert Bot */}
          <div className="rounded-xl border border-[rgba(0,136,204,0.3)] bg-[rgba(0,136,204,0.06)] p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-[#0088cc] flex items-center gap-1.5 uppercase tracking-wider">
                <Send className="w-3.5 h-3.5" />
                Telegram Real-Time Bot
              </span>
              <span className="text-[0.65rem] px-2 py-0.5 rounded-full bg-[#0088cc]/20 text-[#0088cc] font-semibold">
                COMING SOON
              </span>
            </div>
            <p className="text-xs text-gray-300 mb-3">
              Receive instant XAUUSD high-conviction signals directly to your Telegram.
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Your Telegram @username or Chat ID"
                value={telegramChatId}
                onChange={(e) => setTelegramChatId(e.target.value)}
                className="flex-1 px-3 py-2 rounded-lg bg-black/40 border border-white/10 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#0088cc]"
              />
              <button
                onClick={() => {
                  if (telegramChatId) {
                    setTelegramSaved(true);
                    setTimeout(() => setTelegramSaved(false), 3000);
                  }
                }}
                className="px-4 py-2 rounded-lg bg-[#0088cc] hover:bg-[#0077b5] text-white text-xs font-bold transition-colors shrink-0 cursor-pointer"
              >
                {telegramSaved ? "Connected!" : "Connect"}
              </button>
            </div>
          </div>

          {/* 3. Smart Alerts Accordion */}
          <div className="rounded-xl border border-white/5 bg-[#121824] overflow-hidden">
            <button
              onClick={() => setSmartAlertsOpen(!smartAlertsOpen)}
              className="w-full flex items-center justify-between p-3.5 text-xs font-bold text-gray-300 hover:text-white transition-colors cursor-pointer"
            >
              <span>Smart Alerts (Pulse &gt; 80, Breakouts)</span>
              {smartAlertsOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
            </button>
            {smartAlertsOpen && (
              <div className="p-3.5 pt-0 text-xs text-gray-400 space-y-2 border-t border-white/5">
                <label className="flex items-center gap-2 cursor-pointer text-gray-300">
                  <input type="checkbox" defaultChecked className="accent-[#f5c542]" />
                  <span>Alert on Extreme Pulse Spike (&gt; 85)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-gray-300">
                  <input type="checkbox" defaultChecked className="accent-[#f5c542]" />
                  <span>Session Opening Breakout Confirmation</span>
                </label>
              </div>
            )}
          </div>

          {/* 4. Economic Events Accordion */}
          <div className="rounded-xl border border-white/5 bg-[#121824] overflow-hidden">
            <button
              onClick={() => setEconomicEventsOpen(!economicEventsOpen)}
              className="w-full flex items-center justify-between p-3.5 text-xs font-bold text-gray-300 hover:text-white transition-colors cursor-pointer"
            >
              <span>Economic Events (CPI, FOMC, NFP)</span>
              {economicEventsOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
            </button>
            {economicEventsOpen && (
              <div className="p-3.5 pt-0 text-xs text-gray-400 space-y-2 border-t border-white/5">
                <label className="flex items-center gap-2 cursor-pointer text-gray-300">
                  <input type="checkbox" defaultChecked className="accent-[#f5c542]" />
                  <span>High-Impact Tier-1 USD Macro Data 15m Warning</span>
                </label>
              </div>
            )}
          </div>

          {/* 5. Push notifications Accordion */}
          <div className="rounded-xl border border-white/5 bg-[#121824] overflow-hidden">
            <button
              onClick={() => setPushNotificationsOpen(!pushNotificationsOpen)}
              className="w-full flex items-center justify-between p-3.5 text-xs font-bold text-gray-300 hover:text-white transition-colors cursor-pointer"
            >
              <span>Push notifications</span>
              {pushNotificationsOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
            </button>

            {pushNotificationsOpen && (
              <div className="p-3.5 pt-0 space-y-2">
                <button
                  onClick={handleEnablePush}
                  className={`w-full py-2.5 rounded-lg text-xs font-bold flex items-center justify-center gap-2 cursor-pointer transition-all ${
                    pushEnabled
                      ? "bg-[rgba(97,226,148,0.2)] text-[#61e294] border border-[#61e294]/40"
                      : "bg-[#f5c542] hover:bg-[#e5b532] text-[#05060a]"
                  }`}
                >
                  <Bell className="w-4 h-4" />
                  {pushEnabled ? "Browser Push Notifications Active ✓" : "Enable browser notifications"}
                </button>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[0.62rem] font-semibold uppercase tracking-wider text-[#f5c542]/80">
                    Coming soon
                  </span>
                  {pushPermissionMsg && (
                    <span className="text-[0.68rem] text-[#ff8383] leading-snug text-right">
                      {pushPermissionMsg}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* 6. Advanced Accordion */}
          <div className="rounded-xl border border-white/5 bg-[#121824] overflow-hidden">
            <button
              onClick={() => setAdvancedOpen(!advancedOpen)}
              className="w-full flex items-center justify-between p-3.5 text-xs font-bold text-gray-300 hover:text-white transition-colors cursor-pointer"
            >
              <span>Advanced</span>
              {advancedOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
            </button>

            {advancedOpen && (
              <div className="p-3.5 pt-0 space-y-4 border-t border-white/5">
                {/* Pause all alerts toggle */}
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-xs font-semibold text-gray-200">Pause all alerts</div>
                    <div className="text-[0.7rem] text-gray-500">Silences everything without losing settings</div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setPauseAll(!pauseAll)}
                    className={`w-10 h-5 flex items-center rounded-full p-1 cursor-pointer transition-colors ${
                      pauseAll ? "bg-[#f5c542]" : "bg-gray-700"
                    }`}
                  >
                    <div
                      className={`bg-white w-3.5 h-3.5 rounded-full shadow-md transform transition-transform ${
                        pauseAll ? "translate-x-5" : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>

                {/* Send alerts to email toggle */}
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-xs font-semibold text-gray-200">Send alerts to email</div>
                    <div className="text-[0.7rem] text-gray-500">Uses the email configured above</div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSendToEmail(!sendToEmail)}
                    className={`w-10 h-5 flex items-center rounded-full p-1 cursor-pointer transition-colors ${
                      sendToEmail ? "bg-[#f5c542]" : "bg-gray-700"
                    }`}
                  >
                    <div
                      className={`bg-white w-3.5 h-3.5 rounded-full shadow-md transform transition-transform ${
                        sendToEmail ? "translate-x-5" : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>

                {/* Quiet hours checkbox */}
                <div className="flex items-start gap-2.5">
                  <input
                    type="checkbox"
                    id="quietHours"
                    checked={quietHours}
                    onChange={(e) => setQuietHours(e.target.checked)}
                    className="mt-0.5 accent-[#f5c542] rounded cursor-pointer"
                  />
                  <label htmlFor="quietHours" className="cursor-pointer">
                    <div className="text-xs font-semibold text-gray-200">Quiet hours</div>
                    <div className="text-[0.7rem] text-gray-500">22:00-06:00 UTC, Tier-1 events still fire</div>
                  </label>
                </div>

                {/* Status Box */}
                <div className="p-3 rounded-lg bg-black/40 border border-white/5 text-[0.72rem] text-gray-400 flex items-center justify-between">
                  <span>Registered as: <strong className="text-gray-200">{email || "no email saved"}</strong></span>
                  <div className="flex gap-1.5">
                    <span className="px-2 py-0.5 rounded bg-white/5 text-[0.65rem] border border-white/5">
                      Push: {pushEnabled ? "on" : "off"}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-white/5 text-[0.65rem] border border-white/5">
                      Email: {sendToEmail ? "on" : "off"}
                    </span>
                  </div>
                </div>

                {/* Test Alert Button */}
                <button
                  type="button"
                  onClick={handleSendTestAlert}
                  className="w-full py-2.5 rounded-lg text-xs font-semibold border border-white/10 bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white transition-all cursor-pointer"
                >
                  {testSent ? "✓ Test Alert Dispatched to Device" : "Send me a test alert"}
                </button>
                <span className="text-[0.62rem] font-semibold uppercase tracking-wider text-[#f5c542]/80 text-center w-full block -mt-1">
                  Coming soon
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

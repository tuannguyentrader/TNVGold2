"use client";

import React, { createContext, useContext, useState, useEffect, type ReactNode } from "react";

export type Language = "vi" | "en";

export interface Translations {
  // Header
  brandTitle: string;
  brandTag: string;
  engineCenter: string;
  multiTfSync: string;
  refreshRate: string;
  manageBtn: string;
  configTitle: string;
  configDesc: string;
  saveKey: string;
  saved: string;
  cancel: string;

  // Action Banner
  signalBadge: string;
  actionText: string;
  shareSignal: string;
  copied: string;

  // 6 Metric Cards
  biasLabel: string;
  biasTooltip: string;
  biasFooter: string;
  biasValue: string;

  scoreLabel: string;
  scoreTooltip: string;
  scoreStatus: string;

  volatilityLabel: string;
  volatilityTooltip: string;
  volatilityStatus: string;

  entryLabel: string;
  entryTooltip: string;
  highLabel: string;
  lowLabel: string;
  breakoutStatus: string;

  exitLabel: string;
  exitTooltip: string;
  trailingLabel: string;

  htfLabel: string;
  htfTooltip: string;
  htfValue: string;
  htfBonus: string;
  htfFooter: string;

  // Analysis Summary
  analysisTitle: string;
  liveSignalBadge: string;
  analysisText: string;
  viewTechnical: string;

  // 6 Technical Indicator Cards (RSI, ATR, EMA Gap, ADX, VWAP, Spread)
  techTitle: string;
  rsiLabel: string;
  rsiNote: string;
  rsiTooltip: string;

  atrLabel: string;
  atrNote: string;
  atrTooltip: string;

  emaGapLabel: string;
  emaGapNote: string;
  emaGapTooltip: string;

  adxLabel: string;
  adxNote: string;
  adxTooltip: string;

  vwapLabel: string;
  vwapNote: string;
  vwapTooltip: string;

  spreadLabel: string;
  spreadNote: string;
  spreadTooltip: string;

  // Gold Flow Analysis Chart
  flowTitle: string;
  tabSession: string;
  tabTradingView: string;
  legendTokyo: string;
  legendLondon: string;
  legendNY: string;
  ctrlPulse: string;
  ctrlPrice: string;
  ctrlSessions: string;
  ctrlEma: string;
  hoverInspect: string;
  flowFooter: string;
  flowSynced: string;

  // History Table
  historyTitle: string;
  historySub: string;
  historyCount: string;
  colTime: string;
  colPrice: string;
  colSignal: string;
  colScore: string;
  colVolatility: string;
  colHigh: string;
  colLow: string;
  colHTF: string;

  // Subscribe Bar & Footer
  subBarText: string;
  subBarBtn: string;
  disclaimerText: string;
  footerRights: string;
  footerDesc: string;
}

const translations: Record<Language, Translations> = {
  en: {
    brandTitle: "Gold",
    brandTag: "XAUUSD • LIVE",
    engineCenter: "TNV Gold",
    multiTfSync: "Multi-TF Sync",
    refreshRate: "10s refresh",
    manageBtn: "Manage",
    configTitle: "TNV Indicator Configuration",
    configDesc: "Connect your MT5 account or enter your TNV license token to stream real-time price alerts directly.",
    saveKey: "Save & Sync MT5",
    saved: "Saved!",
    cancel: "Cancel",

    signalBadge: "TNV SIGNAL",
    actionText: "XAUUSD LONG • Entry: $2,896.40 • Now: $2,898.50 (+$2.10) • Stop: $2,891.20",
    shareSignal: "Share Signal Alert",
    copied: "Copied!",

    biasLabel: "BIAS",
    biasTooltip: "TNV System Trend & Breakout State. Click to flip for M15, M30, H1.",
    biasFooter: "Flipped 2 bars ago",
    biasValue: "LONG",

    scoreLabel: "QUALITY SCORE",
    scoreTooltip: "Candle quality score (0-10). Threshold >= 5. Click to flip for M15, M30, H1.",
    scoreStatus: "8 / 10",

    volatilityLabel: "VOLATILITY",
    volatilityTooltip: "Market volatility index. Click to flip for M15, M30, H1.",
    volatilityStatus: "Normal",

    entryLabel: "ENTRY",
    entryTooltip: "High and Low trigger levels. Click to flip for M15, M30, H1.",
    highLabel: "High",
    lowLabel: "Low",
    breakoutStatus: "+$2.10",

    exitLabel: "EXIT",
    exitTooltip: "Exit level. Click to flip for M15, M30, H1.",
    trailingLabel: "Exit Low",

    htfLabel: "HTF FILTER",
    htfTooltip: "Higher timeframe trend filter. Click to flip for M15, M30, H1.",
    htfValue: "Not Against",
    htfBonus: "Pass",
    htfFooter: "H1/M30 Structure Confirmed",

    analysisTitle: "TNV ANALYSIS",
    liveSignalBadge: "LIVE SIGNAL",
    analysisText: "Gold is displaying strong bullish momentum as Pulse reaches 80 and the price sits $2.10 above the $2,896.40 level, with higher-timeframe structure providing clean directional alignment without overhead resistance. Watch for: continuation above $2,898.50 toward upper expansion targets, or a pullback toward the $2,891.20 support to test demand before the next leg higher.",
    viewTechnical: "View technical indicators ‹",

    techTitle: "TNV Technical Indicators",
    rsiLabel: "RSI (14)",
    rsiNote: "Bullish Zone",
    rsiTooltip: "Relative Strength Index 14-period. Above 50 indicates buyer control.",

    atrLabel: "ATR (14)",
    atrNote: "0.44% of Price",
    atrTooltip: "Average True Range over the last 14 periods measuring price volatility.",

    emaGapLabel: "EMA GAP (9/21)",
    emaGapNote: "Bullish Expansion",
    emaGapTooltip: "Divergence spread between EMA 9 and EMA 21 measuring trend acceleration.",

    adxLabel: "ADX (14)",
    adxNote: "Strong Trend",
    adxTooltip: "Trend strength indicator. ADX > 25 confirms a strong trending market.",

    vwapLabel: "VWAP",
    vwapNote: "Above VWAP",
    vwapTooltip: "Price position relative to Volume Weighted Average Price.",

    spreadLabel: "SPREAD",
    spreadNote: "Tight Spread ($0.12)",
    spreadTooltip: "Current live Bid/Ask spread from the liquidity provider.",

    flowTitle: "Gold Flow Analysis",
    tabSession: "Session Flow",
    tabTradingView: "TradingView Live",
    legendTokyo: "Tokyo",
    legendLondon: "London",
    legendNY: "New York",
    ctrlPulse: "Pulse Vector",
    ctrlPrice: "XAUUSD Price",
    ctrlSessions: "Sessions",
    ctrlEma: "EMA 9/21",
    hoverInspect: "Hover chart to inspect",
    flowFooter: "TNV Session Flow & Real-Time XAUUSD Feed.",
    flowSynced: "Synced with Global Fixings",

    historyTitle: "TNV Indicator Signal History",
    historySub: "Periodic snapshot recording breakout signals, quality score, and HTF filters.",
    historyCount: "Last 7 snapshots",
    colTime: "Time",
    colPrice: "Close Price",
    colSignal: "Signal",
    colScore: "Score",
    colVolatility: "Volatility",
    colHigh: "High",
    colLow: "Low",
    colHTF: "HTF Filter",

    subBarText: "Get tomorrow's market pulse in your inbox at London open",
    subBarBtn: "Subscribe Free",
    disclaimerText: "TNV Gold is a quantitative market analytics tool and does not constitute financial advice.",
    footerRights: "© 2026 TNV. All rights reserved.",
    footerDesc: "TNV delivers high-precision real-time gold market analytics.",
  },
  vi: {
    brandTitle: "Gold",
    brandTag: "XAUUSD • TRỰC TIẾP",
    engineCenter: "TNV Gold",
    multiTfSync: "Đồng bộ Đa khung",
    refreshRate: "Làm mới 10s",
    manageBtn: "Cấu hình",
    configTitle: "Cấu hình Chỉ báo TNV",
    configDesc: "Kết nối tài khoản MT5 hoặc nhập mã bản quyền TNV để đồng bộ cảnh báo giá trực tiếp.",
    saveKey: "Lưu & Đồng bộ MT5",
    saved: "Đã lưu!",
    cancel: "Hủy",

    signalBadge: "TNV SIGNAL",
    actionText: "XAUUSD LONG • Giá vào: $2,896.40 • Hiện tại: $2,898.50 (+$2.10) • Dừng lỗ: $2,891.20",
    shareSignal: "Chia sẻ tín hiệu",
    copied: "Đã sao chép!",

    biasLabel: "BIAS",
    biasTooltip: "Trạng thái xu hướng của Hệ thống TNV. Nhấn để lật xem M15, M30, H1.",
    biasFooter: "Đã đổi chiều 2 nến trước",
    biasValue: "LONG",

    scoreLabel: "QUALITY SCORE",
    scoreTooltip: "Điểm chất lượng nến tín hiệu (0-10). Ngưỡng >= 5. Nhấn để lật xem M15, M30, H1.",
    scoreStatus: "8 / 10",

    volatilityLabel: "VOLATILITY",
    volatilityTooltip: "Chỉ số độ biến động thị trường. Nhấn để lật xem M15, M30, H1.",
    volatilityStatus: "Bình thường",

    entryLabel: "ENTRY",
    entryTooltip: "Mức giá đỉnh và đáy kích hoạt vào lệnh. Nhấn để lật xem M15, M30, H1.",
    highLabel: "High",
    lowLabel: "Low",
    breakoutStatus: "+$2.10",

    exitLabel: "EXIT",
    exitTooltip: "Mức giá thoát lệnh. Nhấn để lật xem M15, M30, H1.",
    trailingLabel: "Exit Low",

    htfLabel: "HTF FILTER",
    htfTooltip: "Bộ lọc xu hướng đa khung thời gian. Nhấn để lật xem M15, M30, H1.",
    htfValue: "Đồng thuận",
    htfBonus: "Đạt",
    htfFooter: "Cấu trúc H1/M30 xác nhận",

    analysisTitle: "TNV ANALYSIS",
    liveSignalBadge: "TÍN HIỆU LIVE",
    analysisText: "Vàng đang duy trì đà tăng mạnh mẽ với điểm xung lực Pulse đạt 80, giá bứt phá vượt $2.10 trên mức $2,896.40 cùng cấu trúc đa khung thời gian đồng thuận mà không gặp cản trở. Theo dõi: đà tăng tiếp diễn vượt $2,898.50 hướng tới các mục tiêu mở rộng, hoặc nhịp điều chỉnh kiểm tra lại ngưỡng hỗ trợ $2,891.20 trước khi hình thành nhịp tăng mới.",
    viewTechnical: "Xem bảng chỉ số kỹ thuật ‹",

    techTitle: "Chỉ số Kỹ thuật TNV",
    rsiLabel: "RSI (14)",
    rsiNote: "Vùng Tăng giá",
    rsiTooltip: "Chỉ số sức mạnh tương quan 14 nến. Trên 50 thể hiện phe Mua kiểm soát.",

    atrLabel: "ATR (14)",
    atrNote: "0.44% Giá trị",
    atrTooltip: "Biên độ dao động thực tế trung bình 14 nến gần nhất.",

    emaGapLabel: "EMA GAP (9/21)",
    emaGapNote: "Mở rộng Tăng",
    emaGapTooltip: "Khoảng cách phân kỳ giữa EMA 9 và EMA 21 đo lường gia tốc xu hướng.",

    adxLabel: "ADX (14)",
    adxNote: "Xu hướng Mạnh",
    adxTooltip: "Độ mạnh xu hướng. ADX > 25 xác nhận thị trường có xu hướng rõ rệt.",

    vwapLabel: "VWAP",
    vwapNote: "Trên mức VWAP",
    vwapTooltip: "Vị thế giá so với Đường giá trung bình theo khối lượng trong ngày.",

    spreadLabel: "SPREAD",
    spreadNote: "Spread Thấp ($0.12)",
    spreadTooltip: "Độ chênh lệch giá Bid và Ask thực tế tại sàn giao dịch.",

    flowTitle: "Phân tích Luồng Phiên Vàng",
    tabSession: "Luồng Phiên",
    tabTradingView: "TradingView Trực tiếp",
    legendTokyo: "Tokyo",
    legendLondon: "London",
    legendNY: "New York",
    ctrlPulse: "Vector Xung lực",
    ctrlPrice: "Giá Vàng XAUUSD",
    ctrlSessions: "Khung Phiên",
    ctrlEma: "EMA 9/21",
    hoverInspect: "Rê chuột vào biểu đồ để xem",
    flowFooter: "Luồng phiên TNV & Dữ liệu XAUUSD thời gian thực.",
    flowSynced: "Đồng bộ chuẩn Quốc tế",

    historyTitle: "Lịch sử Tín hiệu TNV Indicator",
    historySub: "Snapshot định kỳ ghi nhận tín hiệu Breakout, điểm chất lượng Score và bộ lọc HTF.",
    historyCount: "7 snapshot gần nhất",
    colTime: "Thời gian",
    colPrice: "Giá nến",
    colSignal: "Tín hiệu",
    colScore: "Score",
    colVolatility: "Volatility",
    colHigh: "High",
    colLow: "Low",
    colHTF: "Bộ lọc HTF",

    subBarText: "Nhận thông báo xung lực thị trường vào đầu phiên London",
    subBarBtn: "Đăng ký Miễn phí",
    disclaimerText: "TNV Gold là công cụ phân tích dữ liệu định lượng, không phải lời khuyên đầu tư tài chính.",
    footerRights: "© 2026 TNV. Bản quyền thuộc về TNV.",
    footerDesc: "TNV cung cấp hệ thống phân tích thị trường vàng thời gian thực với độ chính xác cao.",
  },
};

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: Translations;
}

const LanguageContext = createContext<LanguageContextType>({
  language: "en",
  setLanguage: () => {},
  t: translations.en,
});

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>("en");

  useEffect(() => {
    const saved = localStorage.getItem("tnv_lang") as Language;
    if (saved === "vi" || saved === "en") {
      setLanguage(saved);
    }
  }, []);

  const handleSetLanguage = (lang: Language) => {
    setLanguage(lang);
    if (typeof window !== "undefined") {
      localStorage.setItem("tnv_lang", lang);
    }
  };

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage: handleSetLanguage,
        t: translations[language],
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}

import type { Metadata, Viewport } from "next";
import "./globals.css";
import { SiteHeader } from "@/components/SiteHeader";
import { LanguageProvider } from "@/lib/language-context";
import { SubscribeBar } from "@/components/sites/tnv-goldpulse/SubscribeBar";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://tnvgold.vercel.app";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "TNV Gold — Phân tích Vàng XAUUSD Real-Time bằng AI",
    template: "%s | TNV Gold",
  },
  description:
    "TNV cung cấp phân tích thuật toán real-time cho vàng XAUUSD: bias, score, multi-timeframe (M5/M15/M30/H1), session flow Tokyo/London/NY, AI analysis bằng tiếng Việt.",
  keywords: [
    "TNV",
    "TNV Gold",
    "Gold Pulse",
    "XAUUSD",
    "phân tích vàng",
    "tín hiệu vàng",
    "Trading Analytics",
    "Market Flow",
    "Technical Indicators",
    "Session Flow",
    "tin vàng hôm nay",
  ],
  authors: [{ name: "TNV" }],
  creator: "TNV",
  publisher: "TNV",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  openGraph: {
    type: "website",
    locale: "vi_VN",
    url: SITE_URL,
    siteName: "TNV Gold",
    title: "TNV Gold — Phân tích Vàng XAUUSD Real-Time",
    description:
      "Dashboard XAUUSD real-time: bias, score, multi-timeframe, session flow, AI analysis tiếng Việt.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "TNV Gold Pulse Dashboard",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "TNV Gold — Phân tích Vàng XAUUSD Real-Time",
    description:
      "Dashboard XAUUSD real-time: bias, score, multi-timeframe, session flow.",
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: SITE_URL,
    languages: {
      "vi-VN": `${SITE_URL}/vi`,
      "en-US": `${SITE_URL}/en`,
    },
  },
  icons: {
    icon: "/favicon.ico",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#05060a",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className="dark h-full" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap"
          rel="stylesheet"
        />
        {/* Suppress unhandled third-party Chrome extension errors */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if (typeof window !== 'undefined') {
                window.addEventListener('error', function(e) {
                  if (e.filename && (e.filename.includes('chrome-extension://') || e.filename.includes('moz-extension://'))) {
                    e.stopImmediatePropagation();
                    e.preventDefault();
                    return true;
                  }
                }, true);
                window.addEventListener('unhandledrejection', function(e) {
                  if (e.reason && e.reason.stack && (e.reason.stack.includes('chrome-extension://') || e.reason.stack.includes('moz-extension://'))) {
                    e.stopImmediatePropagation();
                    e.preventDefault();
                  }
                }, true);
              }
            `,
          }}
        />
      </head>
      <body
        className="min-h-full flex flex-col antialiased bg-[#05060a] text-[#fdfdfd]"
        suppressHydrationWarning
      >
        <LanguageProvider>
          <SiteHeader />
          {children}
          <SubscribeBar />
        </LanguageProvider>
      </body>
    </html>
  );
}

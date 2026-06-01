import type { Metadata } from "next";
import "./globals.css";
import NavBar from "@/components/NavBar";
import Providers from "@/components/Providers";

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export const metadata: Metadata = {
  metadataBase: new URL("https://hyyyyyyz.github.io/embodied-arxiv/"),
  title: "embodied-arxiv",
  description:
    "每日具身智能 arXiv 论文 · Claude 阅读 · Tinder 风格浏览 (VLA · World Model · WAM · VGGT · Multi-modal)",
  icons: {
    icon: [
      { url: `${BASE}/favicon.png`, type: "image/png", sizes: "128x128" },
      { url: `${BASE}/favicon-32.png`, type: "image/png", sizes: "32x32" },
    ],
    apple: [{ url: `${BASE}/favicon.png` }],
  },
  openGraph: {
    title: "embodied-arxiv",
    description:
      "每日具身智能 arXiv 论文 · Claude 阅读 · Tinder 风格浏览",
    images: [{ url: `${BASE}/logo.png` }],
  },
};

// Runs synchronously before React hydrates so the document already has the
// correct .dark class on first paint — otherwise users in light mode would
// briefly see the dark palette flash.
const THEME_FOUC_SCRIPT = `(function(){try{var t=localStorage.getItem('embodied-arxiv/theme/v1')||'system';var d=t==='dark'||(t==='system'&&window.matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.classList.toggle('dark',d);}catch(e){}})();`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_FOUC_SCRIPT }} />
      </head>
      <body className="h-dvh flex flex-col">
        <Providers>
          <main className="flex-1 min-h-0 overflow-hidden">{children}</main>
          <NavBar />
        </Providers>
      </body>
    </html>
  );
}

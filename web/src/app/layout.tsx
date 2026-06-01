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

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh" className="dark">
      <body className="h-dvh flex flex-col">
        <Providers>
          <main className="flex-1 min-h-0 overflow-hidden">{children}</main>
          <NavBar />
        </Providers>
      </body>
    </html>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLanguage } from "@/components/LanguageContext";

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const NAV_ITEMS = [
  { href: "/", icon: "🏠", labelKey: "nav.home" },
  { href: "/papers", icon: "📝", labelKey: "nav.papers" },
  { href: "/favorites", icon: "⭐", labelKey: "nav.favorites" },
  { href: "/settings", icon: "⚙️", labelKey: "nav.settings" },
];

export default function NavBar() {
  const pathname = usePathname();
  const { t } = useLanguage();

  return (
    <nav className="flex-shrink-0 flex items-center gap-3 border-b border-[var(--border)] bg-[var(--bg-secondary)]/85 backdrop-blur-md px-3 lg:px-6 py-2 lg:py-2.5">
      {/* Logo + wordmark — wordmark hides on <640px */}
      <Link href="/" className="flex items-center gap-2 mr-auto group">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={`${BASE}/favicon.png`}
          alt=""
          width={32}
          height={32}
          className="w-7 h-7 lg:w-8 lg:h-8 rounded-full ring-1 ring-[var(--border)] group-hover:ring-[var(--accent-blue)]/50 transition"
        />
        <span className="hidden sm:inline text-sm lg:text-base font-bold tracking-tight text-[var(--text-primary)]">
          embodied-arxiv
        </span>
      </Link>

      {/* Right cluster: nav items */}
      <div className="flex items-center gap-0.5 lg:gap-1">
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-1.5 px-2.5 lg:px-3 py-1.5 lg:py-2 rounded-full text-xs lg:text-sm font-medium transition-colors ${
                isActive
                  ? "bg-[var(--accent-blue)]/15 text-[var(--accent-blue)]"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card)]"
              }`}
            >
              <span className="text-sm lg:text-base leading-none">
                {item.icon}
              </span>
              <span className="hidden md:inline">{t(item.labelKey)}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

"use client";

import { useState, useEffect } from "react";
import { useLanguage } from "@/components/LanguageContext";
import { useTheme } from "@/components/ThemeContext";
import type { ThemePref } from "@/lib/api";

const REPO_URL = "https://github.com/hyyyyyyz/embodied-arxiv";
const INDEX_PATH = "/data/index.json";

export default function AboutPage() {
  const { t, language, setLanguage } = useLanguage();
  const { theme, setTheme } = useTheme();
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
    fetch(`${base}${INDEX_PATH}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => {
        if (j?.generated_at) setLastUpdate(String(j.generated_at).slice(0, 19));
      })
      .catch(() => {});
  }, []);

  const handleClearData = () => {
    if (!confirming) {
      setConfirming(true);
      return;
    }
    try {
      const prefix = "embodied-arxiv/";
      for (let i = window.localStorage.length - 1; i >= 0; i--) {
        const k = window.localStorage.key(i);
        if (k && k.startsWith(prefix)) {
          window.localStorage.removeItem(k);
        }
      }
    } catch {}
    location.reload();
  };

  return (
    <div className="h-full overflow-y-auto px-4 lg:px-6 py-4 lg:py-6 max-w-2xl mx-auto space-y-4 lg:space-y-5">
      {/* Hero */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-5 lg:p-6">
        <h1 className="text-xl lg:text-2xl font-bold text-[var(--text-primary)] mb-2">
          {t("about.title")}
        </h1>
        <p className="text-sm lg:text-base text-[var(--text-secondary)] leading-relaxed">
          {t("about.tagline")}
        </p>
      </div>

      {/* Workflow */}
      <Section
        title={`⚙️ ${t("about.workflow")}`}
        color="var(--accent-blue)"
      >
        <p className="text-sm leading-relaxed text-[var(--text-primary)] opacity-90">
          {t("about.workflowDesc")}
        </p>
      </Section>

      {/* Coverage */}
      <Section
        title={`🎯 ${t("about.directions")}`}
        color="var(--accent-cyan)"
      >
        <p className="text-sm font-mono text-[var(--text-primary)] opacity-90">
          {t("about.directionsList")}
        </p>
      </Section>

      {/* Appearance */}
      <Section
        title={`🎨 ${t("about.appearance")}`}
        color="var(--accent-purple)"
      >
        <div className="flex gap-2">
          {(
            [
              { key: "light", label: t("about.themeLight") },
              { key: "dark", label: t("about.themeDark") },
              { key: "system", label: t("about.themeSystem") },
            ] as { key: ThemePref; label: string }[]
          ).map((opt) => (
            <LangButton
              key={opt.key}
              active={theme === opt.key}
              onClick={() => setTheme(opt.key)}
            >
              {opt.label}
            </LangButton>
          ))}
        </div>
      </Section>

      {/* Language */}
      <Section
        title={`🌐 ${t("about.language")}`}
        color="var(--accent-orange)"
      >
        <div className="flex gap-2">
          <LangButton
            active={language === "zh"}
            onClick={() => setLanguage("zh")}
          >
            {t("about.languageZh")}
          </LangButton>
          <LangButton
            active={language === "en"}
            onClick={() => setLanguage("en")}
          >
            {t("about.languageEn")}
          </LangButton>
        </div>
      </Section>

      {/* Storage / data */}
      <Section
        title={`💾 ${t("about.storage")}`}
        color="var(--accent-purple)"
      >
        <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-3">
          {t("about.storageDesc")}
        </p>
        <button
          onClick={handleClearData}
          className={`w-full py-2 border rounded-lg text-sm transition-colors ${
            confirming
              ? "border-[var(--accent-red)] bg-[var(--accent-red)]/15 text-[var(--accent-red)]"
              : "border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--accent-red)] hover:border-[var(--accent-red)]/50"
          }`}
        >
          {confirming ? t("about.confirmClear") : t("about.clearAllData")}
        </button>
      </Section>

      {/* Footer */}
      <div className="text-center text-xs text-[var(--text-secondary)] py-4 space-y-2">
        {lastUpdate && (
          <div>
            {t("about.lastUpdate")}: <span className="font-mono">{lastUpdate}</span>
          </div>
        )}
        <div>
          <a
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-[var(--accent-blue)] underline-offset-4 hover:underline"
          >
            {t("about.source")} ↗
          </a>
        </div>
      </div>

      <div className="h-4" />
    </div>
  );
}

function Section({
  title,
  color,
  children,
}: {
  title: string;
  color: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 lg:p-5">
      <h2 className="font-bold text-sm lg:text-base mb-3" style={{ color }}>
        {title}
      </h2>
      {children}
    </div>
  );
}

function LangButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-colors ${
        active
          ? "bg-[var(--accent-blue)] text-[var(--bg-primary)] border-[var(--accent-blue)]"
          : "bg-[var(--bg-primary)] text-[var(--text-secondary)] border-[var(--border)] hover:text-[var(--text-primary)]"
      }`}
    >
      {children}
    </button>
  );
}

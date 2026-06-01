"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useMemo,
} from "react";
import { type Language, translate } from "@/lib/i18n";
import { loadLanguagePref, saveLanguagePref } from "@/lib/api";

interface LanguageContextValue {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  // Default to "zh" for SSR / first paint. Hydrate from localStorage in an
  // effect so the static export doesn't mismatch the rendered HTML.
  const [language, setLanguageState] = useState<Language>("zh");

  useEffect(() => {
    const stored = loadLanguagePref();
    if (stored !== language) setLanguageState(stored);
    // Listen for cross-tab changes
    const onStorage = (e: StorageEvent) => {
      if (e.key === "embodied-arxiv/lang/v1") {
        const v = loadLanguagePref();
        setLanguageState(v);
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
    saveLanguagePref(lang);
  }, []);

  const t = useCallback(
    (key: string, params?: Record<string, string | number>) =>
      translate(language, key, params),
    [language]
  );

  const value = useMemo(
    () => ({ language, setLanguage, t }),
    [language, setLanguage, t]
  );

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

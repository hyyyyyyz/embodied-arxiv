"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useMemo,
} from "react";
import { loadThemePref, saveThemePref, LS_THEME, type ThemePref } from "@/lib/api";

interface ThemeContextValue {
  theme: ThemePref;
  resolvedTheme: "light" | "dark";
  setTheme: (theme: ThemePref) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}

function systemPrefersDark(): boolean {
  if (typeof window === "undefined") return true;
  try {
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  } catch {
    return true;
  }
}

function resolve(theme: ThemePref): "light" | "dark" {
  if (theme === "system") return systemPrefersDark() ? "dark" : "light";
  return theme;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // Default to "system" for SSR / first paint. The inline FOUC script in
  // layout.tsx already set the .dark class before hydration; we just sync
  // React state to localStorage here.
  const [theme, setThemeState] = useState<ThemePref>("system");
  const [resolvedTheme, setResolvedTheme] = useState<"light" | "dark">("dark");

  useEffect(() => {
    const stored = loadThemePref();
    setThemeState(stored);
    setResolvedTheme(resolve(stored));

    const onStorage = (e: StorageEvent) => {
      if (e.key === LS_THEME) {
        const v = loadThemePref();
        setThemeState(v);
        setResolvedTheme(resolve(v));
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  useEffect(() => {
    if (theme !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => setResolvedTheme(mq.matches ? "dark" : "light");
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [theme]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", resolvedTheme === "dark");
  }, [resolvedTheme]);

  const setTheme = useCallback((next: ThemePref) => {
    setThemeState(next);
    setResolvedTheme(resolve(next));
    saveThemePref(next);
  }, []);

  const value = useMemo(
    () => ({ theme, resolvedTheme, setTheme }),
    [theme, resolvedTheme, setTheme]
  );

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

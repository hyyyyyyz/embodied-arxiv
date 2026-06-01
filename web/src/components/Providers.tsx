"use client";

import { PapersProvider } from "@/components/PapersContext";
import { LanguageProvider } from "@/components/LanguageContext";
import { ThemeProvider } from "@/components/ThemeContext";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <PapersProvider>
          {children}
        </PapersProvider>
      </LanguageProvider>
    </ThemeProvider>
  );
}

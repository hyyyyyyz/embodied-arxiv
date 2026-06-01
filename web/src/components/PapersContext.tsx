"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  useEffect,
  useMemo,
} from "react";
import type { Paper, PapersResponse } from "@/lib/types";
import { fetchPapers as apiFetchPapers } from "@/lib/api";

interface PapersContextValue {
  papers: Paper[];
  setPapers: React.Dispatch<React.SetStateAction<Paper[]>>;
  currentIndex: number;
  setCurrentIndex: React.Dispatch<React.SetStateAction<number>>;
  /** The date *shown* (= the date of the latest data, or the selected day). */
  date: string;
  dateRange: string;
  setDateRange: (range: string) => void;
  loading: boolean;
  error: string | null;
  feedbackCount: number;
  setFeedbackCount: React.Dispatch<React.SetStateAction<number>>;
  loadPapers: (range?: string) => void;
  initialized: boolean;
}

const PapersContext = createContext<PapersContextValue | null>(null);

export function usePapersContext() {
  const ctx = useContext(PapersContext);
  if (!ctx)
    throw new Error("usePapersContext must be used within PapersProvider");
  return ctx;
}

export function PapersProvider({ children }: { children: React.ReactNode }) {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [date, setDate] = useState("");
  const [dateRange, setDateRangeState] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedbackCount, setFeedbackCount] = useState(0);
  const [initialized, setInitialized] = useState(false);

  const abortRef = useRef(false);

  const loadPapers = useCallback(
    (range?: string) => {
      setLoading(true);
      setError(null);
      abortRef.current = false;
      const effectiveRange = range ?? dateRange;
      apiFetchPapers(undefined, effectiveRange || undefined)
        .then((data: PapersResponse) => {
          if (abortRef.current) return;
          setPapers(data.papers);
          setDate(data.date);
          setCurrentIndex(0);
          setFeedbackCount(data.papers.filter((p) => p.feedback).length);
          setInitialized(true);
        })
        .catch((err: Error) => {
          if (abortRef.current) return;
          setError(err.message);
        })
        .finally(() => {
          if (!abortRef.current) setLoading(false);
        });
    },
    [dateRange]
  );

  const setDateRange = useCallback(
    (range: string) => {
      setDateRangeState(range);
      setInitialized(false);
      loadPapers(range);
    },
    [loadPapers]
  );

  useEffect(() => {
    if (!initialized && !loading) {
      loadPapers();
    }
  }, [initialized, loading, loadPapers]);

  const value = useMemo<PapersContextValue>(
    () => ({
      papers,
      setPapers,
      currentIndex,
      setCurrentIndex,
      date,
      dateRange,
      setDateRange,
      loading,
      error,
      feedbackCount,
      setFeedbackCount,
      loadPapers,
      initialized,
    }),
    [
      papers,
      currentIndex,
      date,
      dateRange,
      loading,
      error,
      feedbackCount,
      initialized,
      setDateRange,
      loadPapers,
    ]
  );

  return (
    <PapersContext.Provider value={value}>{children}</PapersContext.Provider>
  );
}

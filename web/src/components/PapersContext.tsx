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
import type { Paper, PapersResponse, SiteIndex } from "@/lib/types";
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
  selectedDate: string;
  setSelectedDate: (date: string) => void;
  availableDates: string[];
  indexLoaded: boolean;
  loading: boolean;
  error: string | null;
  feedbackCount: number;
  setFeedbackCount: React.Dispatch<React.SetStateAction<number>>;
  loadPapers: (range?: string, date?: string) => void;
  initialized: boolean;
}

const PapersContext = createContext<PapersContextValue | null>(null);

export function usePapersContext() {
  const ctx = useContext(PapersContext);
  if (!ctx)
    throw new Error("usePapersContext must be used within PapersProvider");
  return ctx;
}

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export function PapersProvider({ children }: { children: React.ReactNode }) {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [date, setDate] = useState("");
  const [dateRange, setDateRangeState] = useState("");
  const [selectedDate, setSelectedDateState] = useState("");
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [indexLoaded, setIndexLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedbackCount, setFeedbackCount] = useState(0);
  const [initialized, setInitialized] = useState(false);

  const reqIdRef = useRef(0);

  useEffect(() => {
    let cancelled = false;
    fetch(`${BASE}/data/index.json`, { cache: "no-cache" })
      .then((r) => (r.ok ? r.json() : null))
      .then((j: SiteIndex | null) => {
        if (cancelled) return;
        if (j?.dates) setAvailableDates(j.dates);
        setIndexLoaded(true);
      })
      .catch(() => {
        if (!cancelled) setIndexLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const loadPapers = useCallback(
    (range?: string, date?: string) => {
      const reqId = ++reqIdRef.current;
      setLoading(true);
      setError(null);
      const effectiveDate = (date !== undefined ? date : selectedDate) || undefined;
      const effectiveRange = effectiveDate ? undefined : (range ?? dateRange) || undefined;
      apiFetchPapers(effectiveDate, effectiveRange)
        .then((data: PapersResponse) => {
          if (reqId !== reqIdRef.current) return;
          setPapers(data.papers);
          setDate(data.date);
          setCurrentIndex(0);
          setFeedbackCount(data.papers.filter((p) => p.feedback).length);
          setInitialized(true);
        })
        .catch((err: Error) => {
          if (reqId !== reqIdRef.current) return;
          setError(err.message);
        })
        .finally(() => {
          if (reqId === reqIdRef.current) setLoading(false);
        });
    },
    [dateRange, selectedDate]
  );

  const setDateRange = useCallback(
    (range: string) => {
      setDateRangeState(range);
      setSelectedDateState("");
      setInitialized(false);
      loadPapers(range, "");
    },
    [loadPapers]
  );

  const setSelectedDate = useCallback(
    (d: string) => {
      setSelectedDateState(d);
      setDateRangeState("");
      setInitialized(false);
      loadPapers("", d);
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
      selectedDate,
      setSelectedDate,
      availableDates,
      indexLoaded,
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
      selectedDate,
      availableDates,
      indexLoaded,
      loading,
      error,
      feedbackCount,
      initialized,
      setDateRange,
      setSelectedDate,
      loadPapers,
    ]
  );

  return (
    <PapersContext.Provider value={value}>{children}</PapersContext.Provider>
  );
}

"use client";

import { useCallback } from "react";
import { usePapersContext } from "@/components/PapersContext";
import { useLanguage } from "@/components/LanguageContext";
import { submitFeedback } from "@/lib/api";
import PaperCard from "@/components/PaperCard";
import PaperListItem from "@/components/PaperListItem";
import SwipeContainer from "@/components/SwipeContainer";
import ProgressBar from "@/components/ProgressBar";

const DATE_RANGES = [
  { value: "", labelKey: "papers.today" },
  { value: "week", labelKey: "papers.thisWeek" },
  { value: "month", labelKey: "papers.thisMonth" },
];

const WEEKDAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function formatDateOption(date: string): string {
  // date is YYYY-MM-DD. Build a UTC date to keep the weekday stable across TZs.
  const [y, m, d] = date.split("-").map(Number);
  if (!y || !m || !d) return date;
  const wd = new Date(Date.UTC(y, m - 1, d)).getUTCDay();
  return `${date} · ${WEEKDAY_LABELS[wd]}`;
}

function DateRangeSelector({
  value,
  onChange,
  compact,
  t,
  selectedDate,
}: {
  value: string;
  onChange: (v: string) => void;
  compact?: boolean;
  t: (key: string, params?: Record<string, string | number>) => string;
  selectedDate: string;
}) {
  return (
    <div className="flex gap-1.5">
      {DATE_RANGES.map((r) => {
        const isActive = value === r.value && !selectedDate;
        return (
          <button
            key={r.value}
            onClick={() => onChange(r.value)}
            className={`rounded-full font-medium transition-colors ${
              isActive
                ? "bg-[var(--accent-blue)] text-[var(--bg-primary)]"
                : "bg-[var(--bg-primary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border)]"
            } ${compact ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs"}`}
          >
            {t(r.labelKey)}
          </button>
        );
      })}
    </div>
  );
}

function DatePickerSelect({
  value,
  dates,
  onChange,
  compact,
  t,
  indexLoaded,
}: {
  value: string;
  dates: string[];
  onChange: (v: string) => void;
  compact?: boolean;
  t: (key: string, params?: Record<string, string | number>) => string;
  indexLoaded: boolean;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={!indexLoaded}
      aria-label={t("papers.pickDate")}
      className={`rounded-full bg-[var(--bg-primary)] text-[var(--text-secondary)] border border-[var(--border)] font-medium hover:text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-blue)] disabled:opacity-50 disabled:cursor-not-allowed ${
        compact ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs"
      }`}
    >
      <option value="">{indexLoaded ? t("papers.allDates") : "…"}</option>
      {dates.map((d) => (
        <option key={d} value={d}>
          {formatDateOption(d)}
        </option>
      ))}
    </select>
  );
}

export default function PapersPage() {
  const {
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
  } = usePapersContext();
  const { t } = useLanguage();

  const handleFeedback = useCallback(
    async (rating: "like" | "neutral" | "dislike" | undefined) => {
      const paper = papers[currentIndex];
      if (!paper) return;

      if (rating === undefined) {
        // Clearing feedback — drop locally and persist
        setPapers((prev) =>
          prev.map((p, i) =>
            i === currentIndex ? { ...p, feedback: undefined } : p
          )
        );
        setFeedbackCount((c) => Math.max(0, c - 1));
        await submitFeedback(paper, undefined, date);
        return;
      }

      setPapers((prev) =>
        prev.map((p, i) =>
          i === currentIndex ? { ...p, feedback: rating } : p
        )
      );
      setFeedbackCount((c) => c + (paper.feedback ? 0 : 1));

      try {
        await submitFeedback(paper, rating, date);
        // Auto-advance to next card after a brief beat
        setTimeout(() => {
          if (currentIndex < papers.length - 1) {
            setCurrentIndex((i) => i + 1);
          }
        }, 500);
      } catch (err) {
        console.error("Feedback failed:", err);
        // Revert on error (extremely unlikely for localStorage)
        setPapers((prev) =>
          prev.map((p, i) =>
            i === currentIndex ? { ...p, feedback: paper.feedback } : p
          )
        );
      }
    },
    [
      papers,
      currentIndex,
      date,
      setPapers,
      setFeedbackCount,
      setCurrentIndex,
    ]
  );

  const handleSwipe = useCallback(
    (direction: "up" | "down") => {
      if (direction === "up" && currentIndex < papers.length - 1) {
        setCurrentIndex((i) => i + 1);
      } else if (direction === "down" && currentIndex > 0) {
        setCurrentIndex((i) => i - 1);
      }
    },
    [currentIndex, papers.length, setCurrentIndex]
  );

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center gap-4">
          <div className="w-10 h-10 border-2 border-[var(--accent-blue)] border-t-transparent rounded-full animate-spin" />
          <p className="text-sm lg:text-base text-[var(--text-secondary)]">
            {date
              ? t("papers.loadingDate", { date })
              : t("papers.loadingLatest")}
          </p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 px-8">
          <p className="text-[var(--accent-red)] text-sm lg:text-base text-center">
            {error}
          </p>
          <button
            onClick={() => loadPapers()}
            className="px-6 py-2.5 bg-[var(--accent-blue)] text-[var(--bg-primary)] rounded-lg text-sm lg:text-base font-bold"
          >
            {t("papers.retry")}
          </button>
        </div>
      );
    }

    if (papers.length === 0) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 px-8">
          <p className="text-5xl">📭</p>
          <p className="text-sm lg:text-base text-[var(--text-secondary)] text-center">
            {date
              ? t("papers.noResultsDate", { date })
              : t("papers.noResultsLatest")}
          </p>
        </div>
      );
    }

    return null;
  };

  const hasPapers = !loading && !error && papers.length > 0;

  return (
    <div className="h-full flex flex-col lg:flex-row">
      {/* Mobile: date-range chips + per-day picker at the top */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-secondary)] lg:hidden">
        <div className="flex items-center gap-1.5 flex-wrap">
          <DateRangeSelector
            value={dateRange}
            onChange={setDateRange}
            selectedDate={selectedDate}
            t={t}
          />
          <DatePickerSelect
            value={selectedDate}
            dates={availableDates}
            onChange={setSelectedDate}
            indexLoaded={indexLoaded}
            t={t}
          />
        </div>
      </div>

      {/* Desktop: left panel with paper list */}
      <div className="hidden lg:flex lg:flex-col lg:w-[340px] xl:w-[380px] border-r border-[var(--border)] bg-[var(--bg-secondary)] flex-shrink-0">
        <div className="flex-shrink-0 px-4 py-3 border-b border-[var(--border)]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-sm">📅</span>
              <DateRangeSelector
                value={dateRange}
                onChange={setDateRange}
                selectedDate={selectedDate}
                compact
                t={t}
              />
              <DatePickerSelect
                value={selectedDate}
                dates={availableDates}
                onChange={setSelectedDate}
                indexLoaded={indexLoaded}
                compact
                t={t}
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="bg-[var(--accent-blue)] text-[var(--bg-primary)] px-2.5 py-0.5 rounded-full text-xs font-bold">
                {papers.length} papers
              </span>
              {feedbackCount > 0 && (
                <span className="text-xs text-[var(--accent-green)]">
                  ✓{feedbackCount}
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {hasPapers &&
            papers.map((paper, index) => (
              <PaperListItem
                key={paper.arxiv_id}
                paper={paper}
                isSelected={index === currentIndex}
                onClick={() => setCurrentIndex(index)}
              />
            ))}
          {!hasPapers && (
            <div className="flex-1 flex items-center justify-center p-8">
              {renderContent()}
            </div>
          )}
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 min-w-0 flex flex-col">
        {hasPapers ? (
          <>
            <div className="lg:hidden">
              <ProgressBar
                current={currentIndex}
                total={papers.length}
                date={date}
                feedbackCount={feedbackCount}
              />
            </div>

            <div className="flex-1 min-h-0 lg:hidden">
              <SwipeContainer
                currentIndex={currentIndex}
                totalItems={papers.length}
                onSwipe={handleSwipe}
              >
                <PaperCard
                  key={papers[currentIndex].arxiv_id}
                  paper={papers[currentIndex]}
                  onFeedback={handleFeedback}
                />
              </SwipeContainer>
            </div>

            <div className="hidden lg:flex lg:flex-1 lg:min-h-0">
              <div className="flex-1 overflow-y-auto">
                <PaperCard
                  key={papers[currentIndex].arxiv_id}
                  paper={papers[currentIndex]}
                  onFeedback={handleFeedback}
                />
              </div>
            </div>
          </>
        ) : (
          renderContent()
        )}
      </div>
    </div>
  );
}

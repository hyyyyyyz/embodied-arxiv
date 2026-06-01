"use client";

import { useState } from "react";
import type { Paper } from "@/lib/types";
import { useLanguage } from "@/components/LanguageContext";
import FeedbackButtons from "./FeedbackButtons";

// Coverage directions matched to brand-palette accents.
// Falls back to the primary purple for any unknown matched_domain string.
const DOMAIN_COLORS: Record<string, string> = {
  VLA: "bg-[var(--tint-vla)] text-[var(--tint-vla-text)]",
  "World Model": "bg-[var(--tint-wm)] text-[var(--tint-wm-text)]",
  WAM: "bg-[var(--tint-wm)] text-[var(--tint-wm-text)]",
  VGGT: "bg-[var(--tint-vggt)] text-[var(--tint-vggt-text)]",
  "Multi-modal": "bg-[var(--tint-mm)] text-[var(--tint-mm-text)]",
};

interface PaperCardProps {
  paper: Paper;
  onFeedback: (rating: "like" | "neutral" | "dislike" | undefined) => void;
}

export default function PaperCard({ paper, onFeedback }: PaperCardProps) {
  const { t } = useLanguage();
  // No more lazy fetches — analysis & images are pre-baked by the build step,
  // so we can render directly off props.
  const [showAnalysis, setShowAnalysis] = useState(!!paper.highlights);
  const [lightboxImg, setLightboxImg] = useState<string | null>(null);

  const analysis = paper.highlights ?? null;
  const images = paper.images ?? [];

  const domainColor =
    DOMAIN_COLORS[paper.matched_domain] ||
    "bg-[var(--tint-vla)] text-[var(--accent-purple)]";

  const scoreColor =
    paper.scores.recommendation >= 8
      ? "bg-[var(--tint-rec-high)] text-[var(--accent-green)]"
      : paper.scores.recommendation >= 6
        ? "bg-[var(--tint-rec-mid)] text-[var(--accent-orange)]"
        : "bg-[var(--tint-rec-low)] text-[var(--accent-red)]";

  return (
    <div className="h-full flex flex-col px-4 pt-2 pb-0 lg:px-8 lg:pt-6 w-full">
      {/* Domain + categories + venue + score */}
      <div className="flex justify-between items-center mb-3 lg:mb-4 flex-shrink-0">
        <div className="flex gap-2 flex-wrap items-center">
          <span
            className={`px-3 py-1 rounded-full text-xs lg:text-sm font-bold ${domainColor}`}
          >
            {paper.matched_domain}
          </span>
          {paper.venue && (
            <span
              className="px-3 py-1 rounded-full text-xs lg:text-sm font-bold text-[var(--accent-purple)] border border-[var(--accent-purple)]/30"
              style={{ background: 'var(--venue-gradient)' }}
              title={t("paper.venue")}
            >
              {paper.venue}
            </span>
          )}
          {paper.categories.slice(0, 3).map((cat) => (
            <span
              key={cat}
              className="px-2 py-1 rounded-full text-[10px] lg:text-xs bg-[var(--bg-card)] text-[var(--text-secondary)]"
            >
              {cat}
            </span>
          ))}
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs lg:text-sm font-bold ${scoreColor}`}
        >
          {paper.scores.recommendation.toFixed(1)}
        </span>
      </div>

      {/* Title */}
      <h1 className="text-xl lg:text-2xl font-bold text-[var(--text-primary)] leading-snug mb-1 lg:mb-2 flex-shrink-0">
        {paper.title}
      </h1>

      {/* Authors + date */}
      <p className="text-xs lg:text-sm text-[var(--text-secondary)] mb-3 lg:mb-4 flex-shrink-0">
        {paper.authors.slice(0, 3).join(", ")}
        {paper.authors.length > 3 ? " et al." : ""}
        {paper.affiliations.length > 0 &&
          ` · ${paper.affiliations.slice(0, 2).join(", ")}`}
        {` · ${paper.published_date.slice(0, 10)}`}
      </p>

      {/* Content (scrollable) */}
      <div className="flex-1 overflow-y-auto space-y-3 lg:space-y-4 min-h-0 pr-1">
        {/* Image gallery */}
        {images.length > 0 && (
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1 flex-shrink-0">
            {images.slice(0, 6).map((img) => (
              <button
                key={img.filename}
                onClick={() => setLightboxImg(img.url)}
                className="flex-shrink-0 rounded-lg overflow-hidden border border-[var(--border)] hover:border-[var(--accent-blue)]/50 transition-colors bg-[var(--bg-secondary)]"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={img.url}
                  alt={img.filename}
                  className="h-28 lg:h-40 w-auto object-contain"
                  loading="lazy"
                />
              </button>
            ))}
          </div>
        )}

        {/* Chinese summary (always visible) */}
        {paper.summary && (
          <div className="bg-[var(--bg-secondary)] border-l-[3px] border-l-[var(--accent-blue)] rounded-r-lg p-3 lg:p-4">
            <div className="text-sm lg:text-base leading-relaxed text-[var(--text-primary)] opacity-90 whitespace-pre-line">
              {paper.summary}
            </div>
          </div>
        )}

        {/* Deep dive — toggle (analysis is pre-baked, so no fetch) */}
        {analysis &&
          (!showAnalysis ? (
            <button
              onClick={() => setShowAnalysis(true)}
              className="w-full py-2.5 lg:py-3 rounded-lg border border-[var(--accent-blue)]/40 bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] text-sm lg:text-base font-medium hover:bg-[var(--accent-blue)]/20 transition-colors flex items-center justify-center gap-2"
            >
              <span>🔍</span>
              {t("paper.deepDive")}
            </button>
          ) : (
            <>
              <ContentBlock
                icon="💡"
                title={t("paper.coreContribution")}
                content={analysis.contribution}
                borderColor="border-l-[var(--accent-blue)]"
                titleColor="text-[var(--accent-blue)]"
              />
              <ContentBlock
                icon="✨"
                title={t("paper.innovation")}
                content={analysis.innovation}
                borderColor="border-l-[var(--accent-purple)]"
                titleColor="text-[var(--accent-purple)]"
              />
              <ContentBlock
                icon="🔧"
                title={t("paper.methodSummary")}
                content={analysis.method}
                borderColor="border-l-[var(--accent-orange)]"
                titleColor="text-[var(--accent-orange)]"
              />
              <ContentBlock
                icon="📊"
                title={t("paper.keyResults")}
                content={analysis.results}
                borderColor="border-l-[var(--accent-green)]"
                titleColor="text-[var(--accent-green)]"
              />
            </>
          ))}

        {/* Keywords */}
        <div className="flex flex-wrap gap-1.5 lg:gap-2 pt-1 pb-2">
          {paper.matched_keywords.map((kw) => (
            <span
              key={kw}
              className="px-2 lg:px-3 py-0.5 lg:py-1 rounded-full text-[10px] lg:text-xs border border-[var(--border)] text-[var(--text-secondary)] bg-[var(--bg-card)]"
            >
              {kw}
            </span>
          ))}
        </div>
      </div>

      {/* Feedback buttons */}
      <div className="flex-shrink-0">
        <FeedbackButtons
          currentFeedback={paper.feedback}
          onFeedback={onFeedback}
          onViewPaper={() =>
            window.open(paper.arxiv_url || paper.pdf_url, "_blank")
          }
        />
      </div>

      {/* Lightbox */}
      {lightboxImg && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 lightbox-overlay"
          onClick={() => setLightboxImg(null)}
        >
          <button
            className="absolute top-4 right-4 text-white/70 hover:text-white text-3xl"
            onClick={() => setLightboxImg(null)}
          >
            &times;
          </button>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={lightboxImg}
            alt="Paper figure"
            className="max-w-[90vw] max-h-[85vh] object-contain rounded-lg"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  );
}

function ContentBlock({
  icon,
  title,
  content,
  borderColor,
  titleColor,
}: {
  icon: string;
  title: string;
  content: string;
  borderColor: string;
  titleColor: string;
}) {
  return (
    <div
      className={`bg-[var(--bg-secondary)] border-l-[3px] ${borderColor} rounded-r-lg p-3 lg:p-4`}
    >
      <div className={`text-xs lg:text-sm font-bold mb-1 lg:mb-1.5 ${titleColor}`}>
        {icon} {title}
      </div>
      <div className="text-sm lg:text-base leading-relaxed text-[var(--text-primary)] opacity-85">
        {content}
      </div>
    </div>
  );
}

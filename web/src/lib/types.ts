// All shapes consumed by the static client. Server-side-only types
// (Preferences / ResearchConfig / AppSettings) are gone — those lived in
// the runtime Anthropic + Python pipeline that we no longer have.

export interface Paper {
  arxiv_id: string;
  title: string;
  authors: string[];
  affiliations: string[];
  /** Chinese display text (pre-baked summary, may be a translation). */
  summary: string;
  /** Original English abstract. */
  original_abstract: string;
  highlights?: PaperAnalysis;
  images?: PaperImage[];
  published_date: string;
  categories: string[];
  matched_domain: string;
  matched_keywords: string[];
  scores: {
    relevance: number;
    recency: number;
    popularity: number;
    quality: number;
    recommendation: number;
  };
  pdf_url: string;
  arxiv_url: string;
  /** Conference / journal acceptance, e.g. "ICML 2026", "TPAMI". */
  venue?: string;
  /** Client-side localStorage state — not part of the static JSON. */
  feedback?: "like" | "neutral" | "dislike";
}

export interface PaperAnalysis {
  contribution: string;
  innovation: string;
  method: string;
  results: string;
}

export interface PaperImage {
  filename: string;
  url: string;
  source: string;
}

export interface PapersResponse {
  date: string;
  papers: Paper[];
  total: number;
}

/** What /public/data/index.json contains — produced by build_web_data.py. */
export interface SiteIndex {
  dates: string[];     // newest first, YYYY-MM-DD
  latest: string;      // dates[0]
  domains: string[];   // distinct matched_domain values
  generated_at: string;
}

export interface FavoriteFolder {
  id: string;
  name: string;
  paperIds: string[];
}

export interface FavoritesData {
  folders: FavoriteFolder[];
  /** Snapshot map: arxiv_id → Paper (so the favorites page can render
   *  without needing the original day's JSON to be loaded). */
  likedPapers: Record<string, Paper>;
}

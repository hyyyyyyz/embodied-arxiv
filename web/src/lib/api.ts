// Replaces the original server-backed /api/* fetchers with:
//  - static reads of /data/index.json + /data/papers/<date>.json (pre-baked
//    at build time by scripts/build_web_data.py)
//  - localStorage-backed favorites + feedback (no remote DB)
//
// Public function NAMES are kept (where still used) for minimal churn in
// callers; deprecated functions (fetchAnalysis / fetchPaperImages /
// fetchSettings / fetchPreferences / updatePreferences /
// fetchPapersWithFocus / filterPapers) have been removed — their callers
// are updated to not invoke them.
"use client";

import type {
  Paper,
  PapersResponse,
  SiteIndex,
  FavoriteFolder,
  FavoritesData,
} from "./types";

// Next.js applies basePath automatically to <Link> and <Image> but NOT to
// raw fetch(). We mirror it here for /data/* requests.
const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const LS_FAVORITES = "embodied-arxiv/favorites/v1";
const LS_FEEDBACK = "embodied-arxiv/feedback/v1";

// ──────────────────────────────────────────────────────────────
// localStorage helpers — SSR-safe (return fallback on server pass)
// ──────────────────────────────────────────────────────────────
function readLS<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const v = window.localStorage.getItem(key);
    return v ? (JSON.parse(v) as T) : fallback;
  } catch {
    return fallback;
  }
}

function writeLS(key: string, value: unknown): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* quota / private-mode */
  }
}

function loadFavorites(): FavoritesData {
  return readLS<FavoritesData>(LS_FAVORITES, { folders: [], likedPapers: {} });
}

function loadFeedbackMap(): Record<string, "like" | "neutral" | "dislike"> {
  return readLS<Record<string, "like" | "neutral" | "dislike">>(LS_FEEDBACK, {});
}

// ──────────────────────────────────────────────────────────────
// Static fetch helpers
// ──────────────────────────────────────────────────────────────
async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-cache" });
  if (!res.ok) throw new Error(`HTTP ${res.status} fetching ${path}`);
  return res.json();
}

async function loadIndex(): Promise<SiteIndex> {
  try {
    return await getJson<SiteIndex>("/data/index.json");
  } catch {
    return { dates: [], latest: "", domains: [], generated_at: "" };
  }
}

async function loadDate(date: string): Promise<PapersResponse> {
  return getJson<PapersResponse>(`/data/papers/${date}.json`);
}

// ──────────────────────────────────────────────────────────────
// Public API
// ──────────────────────────────────────────────────────────────

export async function fetchPapers(
  date?: string,
  range?: string
): Promise<PapersResponse> {
  const index = await loadIndex();
  if (!index.dates.length) {
    return { date: date || "", papers: [], total: 0 };
  }

  let dates: string[];
  if (range === "week") dates = index.dates.slice(0, 7);
  else if (range === "month") dates = index.dates.slice(0, 30);
  else if (date) dates = [date];
  else dates = [index.latest];

  const results = await Promise.allSettled(dates.map(loadDate));
  const merged: Paper[] = [];
  for (const r of results) {
    if (r.status === "fulfilled") merged.push(...r.value.papers);
  }

  // Hydrate feedback state from localStorage so card badges paint correctly
  const fb = loadFeedbackMap();
  for (const p of merged) {
    if (fb[p.arxiv_id]) p.feedback = fb[p.arxiv_id];
  }

  if (dates.length > 1) {
    merged.sort((a, b) => b.scores.recommendation - a.scores.recommendation);
  }

  return {
    date: date || dates[0] || "",
    papers: merged,
    total: merged.length,
  };
}

export async function submitFeedback(
  paper: Paper,
  rating: "like" | "neutral" | "dislike" | undefined,
  _date: string
): Promise<{ success: boolean; should_update_preferences: boolean }> {
  // Persist (or clear) the rating
  const fb = loadFeedbackMap();
  if (rating === undefined) {
    delete fb[paper.arxiv_id];
  } else {
    fb[paper.arxiv_id] = rating;
  }
  writeLS(LS_FEEDBACK, fb);

  // Sync the favorites snapshot:
  //  - `like` → snapshot this Paper so /favorites can render it later
  //  - anything else (including clearing) → drop it from favorites
  const fav = loadFavorites();
  if (rating === "like") {
    fav.likedPapers[paper.arxiv_id] = paper;
    writeLS(LS_FAVORITES, fav);
  } else if (fav.likedPapers[paper.arxiv_id]) {
    delete fav.likedPapers[paper.arxiv_id];
    for (const folder of fav.folders) {
      folder.paperIds = folder.paperIds.filter((id) => id !== paper.arxiv_id);
    }
    writeLS(LS_FAVORITES, fav);
  }

  return { success: true, should_update_preferences: false };
}

export async function fetchFavorites(): Promise<{
  papers: Paper[];
  folders: FavoriteFolder[];
}> {
  const fav = loadFavorites();
  const fb = loadFeedbackMap();
  const papers = Object.values(fav.likedPapers).map((p) => ({
    ...p,
    feedback: fb[p.arxiv_id] ?? p.feedback,
  }));
  return { papers, folders: fav.folders };
}

function generateFolderId(): string {
  return `f_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`;
}

export async function createFolder(
  name: string
): Promise<{ success: boolean; folder: FavoriteFolder }> {
  const fav = loadFavorites();
  const folder: FavoriteFolder = {
    id: generateFolderId(),
    name,
    paperIds: [],
  };
  fav.folders.push(folder);
  writeLS(LS_FAVORITES, fav);
  return { success: true, folder };
}

export async function renameFolder(
  id: string,
  name: string
): Promise<{ success: boolean }> {
  const fav = loadFavorites();
  const folder = fav.folders.find((f) => f.id === id);
  if (folder) folder.name = name;
  writeLS(LS_FAVORITES, fav);
  return { success: true };
}

export async function deleteFolder(id: string): Promise<{ success: boolean }> {
  const fav = loadFavorites();
  fav.folders = fav.folders.filter((f) => f.id !== id);
  writeLS(LS_FAVORITES, fav);
  return { success: true };
}

export async function movePaperToFolder(
  arxivId: string,
  folderId: string | null
): Promise<{ success: boolean }> {
  const fav = loadFavorites();
  for (const folder of fav.folders) {
    folder.paperIds = folder.paperIds.filter((id) => id !== arxivId);
  }
  if (folderId) {
    const target = fav.folders.find((f) => f.id === folderId);
    if (target && !target.paperIds.includes(arxivId)) {
      target.paperIds.push(arxivId);
    }
  }
  writeLS(LS_FAVORITES, fav);
  return { success: true };
}

export async function removeFavorite(
  arxivId: string
): Promise<{ success: boolean }> {
  const fav = loadFavorites();
  delete fav.likedPapers[arxivId];
  for (const folder of fav.folders) {
    folder.paperIds = folder.paperIds.filter((id) => id !== arxivId);
  }
  writeLS(LS_FAVORITES, fav);

  const fb = loadFeedbackMap();
  delete fb[arxivId];
  writeLS(LS_FEEDBACK, fb);
  return { success: true };
}

// ──────────────────────────────────────────────────────────────
// Language preference (used by LanguageContext)
// ──────────────────────────────────────────────────────────────
const LS_LANG = "embodied-arxiv/lang/v1";

export function loadLanguagePref(): "zh" | "en" {
  if (typeof window === "undefined") return "zh";
  try {
    const v = window.localStorage.getItem(LS_LANG);
    if (v === "zh" || v === "en") return v;
  } catch {}
  return "zh";
}

export function saveLanguagePref(lang: "zh" | "en"): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LS_LANG, lang);
  } catch {}
}

// ──────────────────────────────────────────────────────────────
// Theme preference (used by ThemeContext + the FOUC script in layout.tsx)
// ──────────────────────────────────────────────────────────────
export type ThemePref = "light" | "dark" | "system";
export const LS_THEME = "embodied-arxiv/theme/v1";

export function loadThemePref(): ThemePref {
  if (typeof window === "undefined") return "system";
  try {
    const v = window.localStorage.getItem(LS_THEME);
    if (v === "light" || v === "dark" || v === "system") return v;
  } catch {}
  return "system";
}

export function saveThemePref(theme: ThemePref): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LS_THEME, theme);
  } catch {}
}

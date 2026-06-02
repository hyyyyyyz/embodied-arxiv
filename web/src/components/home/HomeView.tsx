"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { Paper, PapersResponse, SiteIndex } from "@/lib/types";
import { domainColor } from "./domainTint";

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

// Stable display order for the BY DIRECTION section, matching index.json.
const DIRECTION_ORDER = [
  "VLA",
  "World Model",
  "WAM",
  "VGGT",
  "Multi-modal",
] as const;

const WEEKDAY_ZH = ["日", "一", "二", "三", "四", "五", "六"];

const REPO_URL = "https://github.com/hyyyyyyz/embodied-arxiv";

// ─────────────────────────────────────────────────────────────
// Date helpers
// ─────────────────────────────────────────────────────────────
function parseYMD(date: string): Date | null {
  const [y, m, d] = date.split("-").map(Number);
  if (!y || !m || !d) return null;
  return new Date(Date.UTC(y, m - 1, d));
}

function formatIssueDate(date: string): string {
  const d = parseYMD(date);
  if (!d) return "—————";
  const wd = WEEKDAY_ZH[d.getUTCDay()];
  return `星期${wd} · ${d.getUTCFullYear()} 年 ${
    d.getUTCMonth() + 1
  } 月 ${d.getUTCDate()} 日`;
}

function formatMMDD(date: string): string {
  return date.slice(5).replace("-", "-");
}

function formatGeneratedAt(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mi = String(d.getMinutes()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd} ${hh}:${mi}`;
}

// Map a count to 1..8 dot characters proportional to the day's volume,
// relative to the max count we've observed so far.
function dotsForCount(count: number, max: number): string {
  if (!count) return "";
  const ratio = max > 0 ? count / max : 0;
  const n = Math.max(1, Math.min(8, Math.round(ratio * 8)));
  return "·".repeat(n);
}

// ─────────────────────────────────────────────────────────────
// Skeleton primitives (theme-aware, no hardcoded grays)
// ─────────────────────────────────────────────────────────────
function SkelBar({
  className = "",
  widthPct = 100,
}: {
  className?: string;
  widthPct?: number;
}) {
  return (
    <div
      className={`rounded bg-[color:var(--bg-card)] ${className}`}
      style={{ width: `${widthPct}%` }}
    />
  );
}

function LeadSkeletonEntry({ withRule }: { withRule: boolean }) {
  return (
    <div
      className={`py-6 ${
        withRule ? "border-t border-[color:var(--border)]" : ""
      }`}
    >
      {/* chip line */}
      <SkelBar className="h-3" widthPct={28} />
      {/* title (2 lines) */}
      <div className="mt-3 space-y-2">
        <SkelBar className="h-5" widthPct={94} />
        <SkelBar className="h-5" widthPct={62} />
      </div>
      {/* description (3 lines) */}
      <div className="mt-3 space-y-1.5">
        <SkelBar className="h-3" widthPct={98} />
        <SkelBar className="h-3" widthPct={88} />
        <SkelBar className="h-3" widthPct={70} />
      </div>
      {/* foot line */}
      <div className="mt-4">
        <SkelBar className="h-2.5" widthPct={40} />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Main view
// ─────────────────────────────────────────────────────────────
type IndexState =
  | { kind: "loading" }
  | { kind: "ok"; index: SiteIndex }
  | { kind: "missing" };

type LeadState =
  | { kind: "idle" }
  | { kind: "ok"; total: number; papers: Paper[]; domainCounts: Record<string, number> }
  | { kind: "missing" };

export default function HomeView() {
  const [indexState, setIndexState] = useState<IndexState>({ kind: "loading" });
  const [leadState, setLeadState] = useState<LeadState>({ kind: "idle" });
  // dayCounts[date] = total papers that day. null = not loaded, undefined = failed.
  const [dayCounts, setDayCounts] = useState<Record<string, number | null>>({});

  // 1) Load index.json
  useEffect(() => {
    let cancelled = false;
    fetch(`${BASE}/data/index.json`, { cache: "no-cache" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((j: SiteIndex) => {
        if (cancelled) return;
        if (!j?.dates?.length) {
          setIndexState({ kind: "missing" });
          return;
        }
        setIndexState({ kind: "ok", index: j });
      })
      .catch(() => {
        if (!cancelled) setIndexState({ kind: "missing" });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // 2) Once index is known: load latest day for the LEAD column, and fan out
  //    parallel fetches for the 14-day rhythm strip.
  useEffect(() => {
    if (indexState.kind !== "ok") return;
    const { dates, latest } = indexState.index;
    let cancelled = false;

    // No seeding needed — the row UI treats `undefined` the same as `null`
    // (both render as `—`). We only fill an entry when its fetch succeeds.

    // Lead day
    fetch(`${BASE}/data/papers/${latest}.json`, { cache: "no-cache" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((j: PapersResponse) => {
        if (cancelled) return;
        const sorted = [...j.papers].sort((a, b) => {
          const ra = a.scores?.recommendation ?? 0;
          const rb = b.scores?.recommendation ?? 0;
          if (rb !== ra) return rb - ra;
          return (b.scores?.quality ?? 0) - (a.scores?.quality ?? 0);
        });
        const top5 = sorted.slice(0, 5);
        const counts: Record<string, number> = {};
        for (const p of j.papers) {
          counts[p.matched_domain] = (counts[p.matched_domain] ?? 0) + 1;
        }
        setLeadState({
          kind: "ok",
          total: j.total ?? j.papers.length,
          papers: top5,
          domainCounts: counts,
        });
        setDayCounts((prev) => ({ ...prev, [latest]: j.total ?? j.papers.length }));
      })
      .catch(() => {
        if (!cancelled) setLeadState({ kind: "missing" });
      });

    // Rhythm — 13 more dates in parallel (latest is already covered above)
    const others = dates.slice(1, 14);
    for (const d of others) {
      fetch(`${BASE}/data/papers/${d}.json`, { cache: "no-cache" })
        .then((r) => (r.ok ? r.json() : Promise.reject()))
        .then((j: PapersResponse) => {
          if (cancelled) return;
          setDayCounts((prev) => ({
            ...prev,
            [d]: j.total ?? j.papers.length,
          }));
        })
        .catch(() => {
          // leave as null → UI shows `—`
        });
    }

    return () => {
      cancelled = true;
    };
  }, [indexState]);

  // ─────────────────────────────────────────────────────
  // Derived bits
  // ─────────────────────────────────────────────────────
  const issueInfo = useMemo(() => {
    if (indexState.kind !== "ok") {
      return { num: "—", date: "—————", latest: "" };
    }
    const { dates, latest } = indexState.index;
    // Issue No. = position with newest = highest. dates is newest-first.
    const num = dates.length;
    return { num: String(num), date: formatIssueDate(latest), latest };
  }, [indexState]);

  const corpusLine = useMemo(() => {
    if (indexState.kind === "loading") return "加载中…";
    if (indexState.kind === "missing")
      return "数据暂未生成,可直接前往 论文 →";
    const { dates } = indexState.index;
    if (leadState.kind === "ok") {
      const top = Math.min(5, leadState.papers.length);
      return `今日 ${leadState.total} 篇 · ${dates.length} 天 · 5 个方向 · 今日精选 ${top} 篇`;
    }
    return `${dates.length} 天 · 5 个方向`;
  }, [indexState, leadState]);

  const rhythmMax = useMemo(() => {
    const values = Object.values(dayCounts).filter(
      (v): v is number => typeof v === "number"
    );
    return values.length ? Math.max(...values) : 0;
  }, [dayCounts]);

  const latest = indexState.kind === "ok" ? indexState.index.latest : "";
  const fallbackDate =
    indexState.kind === "ok" && indexState.index.dates.length > 1
      ? indexState.index.dates[1]
      : "";

  // ─────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────
  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-[1100px] mx-auto px-4 md:px-8 pb-32 md:pb-12">
        {/* MASTHEAD */}
        <header className="py-6 md:py-10">
          <div className="text-xs md:text-sm uppercase tracking-[0.2em] text-[color:var(--text-secondary)]">
            THE DAILY READ
          </div>
          <div className="mt-2 border-b border-[color:var(--border)]" />
          <div className="mt-5 flex flex-col md:flex-row md:items-end md:justify-between gap-2">
            <h1 className="text-2xl md:text-3xl font-semibold font-serif leading-tight text-[color:var(--text-primary)]">
              Issue No. {issueInfo.num} · {issueInfo.date}
            </h1>
            <div className="text-xs text-[color:var(--text-secondary)] md:text-right md:pb-1.5">
              {corpusLine}
            </div>
          </div>
        </header>

        {/* BODY GRID */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10">
          {/* LEAD COLUMN */}
          <section className="md:col-span-7">
            <div className="text-xs tracking-[0.2em] text-[color:var(--text-secondary)] mb-6">
              头版 LEAD
            </div>

            {indexState.kind === "missing" ? (
              <p className="text-sm text-[color:var(--text-secondary)] py-6">
                数据暂未生成,可直接前往{" "}
                <Link
                  href="/papers"
                  className="text-[color:var(--accent-blue)] hover:underline"
                >
                  论文 →
                </Link>
              </p>
            ) : leadState.kind === "missing" ? (
              <p className="text-sm text-[color:var(--text-secondary)] py-6">
                今日尚未生成,
                {fallbackDate ? (
                  <>
                    前往最近一日 →{" "}
                    <Link
                      href={`/papers?date=${fallbackDate}`}
                      className="text-[color:var(--accent-blue)] hover:underline"
                    >
                      {fallbackDate}
                    </Link>
                  </>
                ) : (
                  <Link
                    href="/papers"
                    className="text-[color:var(--accent-blue)] hover:underline"
                  >
                    {" "}
                    论文 →
                  </Link>
                )}
              </p>
            ) : leadState.kind === "ok" ? (
              <>
                {leadState.papers.map((p, i) => (
                  <LeadEntry
                    key={p.arxiv_id}
                    paper={p}
                    latest={latest}
                    withRule={i > 0}
                  />
                ))}
                <div className="mt-8 text-right md:text-right">
                  <Link
                    href="/papers"
                    className="text-sm text-[color:var(--accent-blue)] hover:underline inline-block"
                  >
                    进入今日全部 {leadState.total} 篇 →
                  </Link>
                </div>
              </>
            ) : (
              // skeleton — 5 placeholder entries
              <>
                {[0, 1, 2, 3, 4].map((i) => (
                  <LeadSkeletonEntry key={i} withRule={i > 0} />
                ))}
                <div className="mt-8 text-right">
                  <SkelBar className="h-3 inline-block" widthPct={30} />
                </div>
              </>
            )}
          </section>

          {/* SIDEBAR */}
          <aside className="md:col-span-5 md:col-start-8 self-start md:sticky md:top-8 mt-12 md:mt-0 border-t md:border-t-0 border-[color:var(--border)] pt-6 md:pt-0">
            {/* BY DIRECTION */}
            <div className="py-5">
              <div className="text-xs uppercase tracking-[0.2em] text-[color:var(--text-secondary)] mb-3">
                按方向 BY DIRECTION
              </div>
              <div className="space-y-1">
                {DIRECTION_ORDER.map((name) => {
                  const count =
                    leadState.kind === "ok"
                      ? leadState.domainCounts[name] ?? 0
                      : null;
                  const color = domainColor(name);
                  const href = latest
                    ? `/papers?date=${latest}&domain=${encodeURIComponent(name)}`
                    : "/papers";
                  return (
                    <Link
                      key={name}
                      href={href}
                      className="flex items-baseline gap-2 py-1 text-sm text-[color:var(--text-primary)] hover:text-[color:var(--accent-blue)] transition-colors"
                    >
                      <span style={{ color }}>{name}</span>
                      <span
                        className="flex-1 border-b border-dotted"
                        style={{ borderColor: color, opacity: 0.55 }}
                      />
                      <span className="tabular-nums text-[color:var(--text-secondary)]">
                        {count === null ? "—" : count}
                      </span>
                    </Link>
                  );
                })}
              </div>
            </div>

            {/* RHYTHM */}
            <div className="py-5 border-t border-[color:var(--border)]">
              <div className="text-xs uppercase tracking-[0.2em] text-[color:var(--text-secondary)] mb-3">
                节奏 RHYTHM · 近 14 天
              </div>
              {indexState.kind === "ok" ? (
                <div className="grid grid-cols-2 gap-x-4 md:grid-cols-1 md:gap-x-0">
                  {indexState.index.dates.slice(0, 14).map((d) => {
                    const count = dayCounts[d];
                    const known = typeof count === "number";
                    const dots = known ? dotsForCount(count!, rhythmMax) : "";
                    return (
                      <Link
                        key={d}
                        href={`/papers?date=${d}`}
                        className="flex items-baseline gap-2 py-1 text-sm text-[color:var(--text-primary)] hover:text-[color:var(--accent-blue)] transition-colors"
                      >
                        <span className="tabular-nums text-[color:var(--text-secondary)]">
                          {formatMMDD(d)}
                        </span>
                        <span
                          className="flex-1 truncate font-mono text-xs leading-none"
                          style={{
                            color: "var(--accent-blue)",
                            opacity: 0.5,
                          }}
                        >
                          {dots || "·"}
                        </span>
                        <span className="tabular-nums text-[color:var(--text-secondary)] text-xs">
                          {known ? `${count} 篇` : "— 篇"}
                        </span>
                      </Link>
                    );
                  })}
                </div>
              ) : (
                <div className="space-y-1.5">
                  {[...Array(6)].map((_, i) => (
                    <SkelBar key={i} className="h-3" widthPct={90 - i * 4} />
                  ))}
                </div>
              )}
            </div>

            {/* COLOPHON */}
            <div className="py-5 border-t border-[color:var(--border)]">
              <div className="text-xs uppercase tracking-[0.2em] text-[color:var(--text-secondary)] mb-3">
                关于 COLOPHON
              </div>
              {indexState.kind === "missing" ? (
                <p className="text-xs text-[color:var(--text-secondary)] leading-relaxed">
                  数据暂未生成,可直接前往{" "}
                  <Link
                    href="/papers"
                    className="text-[color:var(--accent-blue)] hover:underline"
                  >
                    论文 →
                  </Link>
                </p>
              ) : (
                <p className="text-xs text-[color:var(--text-secondary)] leading-relaxed">
                  每天清晨从 arXiv 抓取 VLA / World Model / WAM / VGGT / 多模态
                  五个方向新论文,由 Claude
                  阅读并给出中文摘要、亮点与推荐分。点开任意一篇即进入 Tinder
                  式快速浏览。
                </p>
              )}
              <div className="text-[10px] tracking-wide mt-3 flex gap-3 text-[color:var(--text-secondary)]">
                <a
                  href={REPO_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-[color:var(--accent-blue)] transition-colors"
                >
                  GitHub →
                </a>
                {indexState.kind === "ok" &&
                  indexState.index.generated_at && (
                    <span>
                      生成于 {formatGeneratedAt(indexState.index.generated_at)}
                    </span>
                  )}
              </div>
            </div>
          </aside>
        </div>
      </div>

      {/* STICKY MOBILE CTA */}
      <Link
        href="/papers"
        className="md:hidden fixed left-3 right-3 z-40 rounded-full py-3 text-center text-sm font-medium text-white shadow-[0_-4px_20px_rgba(0,0,0,0.08)] backdrop-blur-sm"
        style={{
          backgroundColor: "var(--accent-blue)",
          bottom: "calc(64px + env(safe-area-inset-bottom, 0px) + 8px)",
        }}
      >
        进入今日浏览 →
      </Link>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Lead entry
// ─────────────────────────────────────────────────────────────
function LeadEntry({
  paper,
  latest,
  withRule,
}: {
  paper: Paper;
  latest: string;
  withRule: boolean;
}) {
  const color = domainColor(paper.matched_domain);
  const rec = paper.scores?.recommendation ?? 0;
  const desc =
    paper.highlights?.contribution ||
    paper.summary ||
    (paper.original_abstract ?? "").slice(0, 180);
  const aff = (paper.affiliations ?? []).slice(0, 2).join(" · ");
  const venue = paper.venue ?? "arXiv";

  const footParts = [aff, venue].filter(Boolean);

  return (
    <article
      className={`py-6 ${
        withRule ? "border-t border-[color:var(--border)]" : ""
      }`}
    >
      <div className="text-xs uppercase tracking-wide">
        <span style={{ color }}>[{paper.matched_domain}]</span>
        <span className="text-[color:var(--text-secondary)] mx-1.5">·</span>
        <span className="text-[color:var(--text-primary)]">
          ★ {rec.toFixed(1)}
        </span>
      </div>
      <h2 className="mt-2 text-lg md:text-xl font-semibold font-serif leading-snug">
        <Link
          href={`/papers?date=${latest}&id=${encodeURIComponent(
            paper.arxiv_id
          )}`}
          className="text-[color:var(--text-primary)] hover:text-[color:var(--accent-blue)] transition-colors"
        >
          {paper.title}
        </Link>
      </h2>
      <p className="text-sm text-[color:var(--text-secondary)] line-clamp-3 mt-2 leading-relaxed">
        {desc}
      </p>
      {footParts.length > 0 && (
        <div className="text-[10px] md:text-xs uppercase tracking-[0.12em] text-[color:var(--text-secondary)] mt-3">
          {footParts.join(" · ")}
        </div>
      )}
    </article>
  );
}

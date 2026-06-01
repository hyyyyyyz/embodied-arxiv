#!/usr/bin/env python3
"""Merge raw arxiv pulls + Claude-written cards into the static web JSON
and write matching markdown into the Obsidian vault.

Usage:
    python scripts/build_web_data.py --date 2026-06-01

Inputs:
    data/raw/<date>.json     — produced by fetch_arxiv.py (+ lookup_venue.py)
    data/cards/<date>.json   — list of card stubs Claude fills in:
        [ { "arxiv_id", "summary", "highlights": {contribution,innovation,
                                                   method, results},
            "scores": { recommendation, relevance, recency, popularity, quality }
          }, ... ]
      (scores can be a single number 0-10; will be expanded to the full dict.)

Outputs:
    web/public/data/papers/<date>.json
    web/public/data/index.json  (dates list + latest)
    {OBSIDIAN_ROOT}/DailyPapers/<date>.md
    {OBSIDIAN_ROOT}/Papers/<arxiv_id>.md  (one file per kept paper)

Papers whose arxiv_id has no matching card entry are skipped with a warning,
so partial runs are safe.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (  # noqa: E402
    CARDS_DIR,
    OBSIDIAN_DAILY,
    OBSIDIAN_PAPERS,
    OBSIDIAN_ROOT,
    RAW_DIR,
    WEB_DATA_DIR,
    WEB_PAPERS_DIR,
    DIRECTIONS,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


SCORE_KEYS = ("relevance", "recency", "popularity", "quality", "recommendation")


def normalize_scores(s) -> dict:
    """Accept either a flat number or a partial dict; return full 5-key dict."""
    if isinstance(s, (int, float)):
        v = float(s)
        return {k: v for k in SCORE_KEYS}
    if not isinstance(s, dict):
        return {k: 7.0 for k in SCORE_KEYS}
    rec = float(s.get("recommendation", s.get("rec", 7.0)))
    out = {k: float(s.get(k, rec)) for k in SCORE_KEYS}
    out["recommendation"] = rec
    return out


def merge(raw_papers: list[dict], cards: dict[str, dict]) -> list[dict]:
    """Combine raw arxiv entries with Claude's highlights/summary/scores."""
    out: list[dict] = []
    for r in raw_papers:
        aid = r["arxiv_id"]
        c = cards.get(aid)
        if c is None:
            print(f"  ⚠ no card for {aid} — skipping", file=sys.stderr)
            continue
        highlights = c.get("highlights") or {}
        if not all(k in highlights for k in ("contribution", "innovation", "method", "results")):
            print(f"  ⚠ {aid} highlights incomplete — skipping", file=sys.stderr)
            continue
        out.append(
            {
                "arxiv_id": aid,
                "title": r["title"],
                "authors": r.get("authors", []),
                "affiliations": c.get("affiliations") or r.get("affiliations", []),
                "summary": c.get("summary", ""),
                "original_abstract": r.get("abstract", ""),
                "highlights": {
                    "contribution": highlights["contribution"],
                    "innovation": highlights["innovation"],
                    "method": highlights["method"],
                    "results": highlights["results"],
                },
                "images": c.get("images", []),
                "published_date": r.get("published_date", ""),
                "categories": r.get("categories", []),
                "matched_domain": r.get("matched_domain", "Multi-modal"),
                "matched_keywords": r.get("matched_keywords", []),
                "scores": normalize_scores(c.get("scores", 7.0)),
                "pdf_url": r.get("pdf_url", ""),
                "arxiv_url": r.get("arxiv_url", ""),
                "venue": r.get("venue") or c.get("venue"),
            }
        )
    return out


def write_papers_json(date: str, papers: list[dict]) -> Path:
    out = repo_root() / WEB_PAPERS_DIR / f"{date}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"date": date, "papers": papers, "total": len(papers)}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return out


def rebuild_index() -> Path:
    """Scan web/public/data/papers/*.json and rewrite index.json."""
    papers_dir = repo_root() / WEB_PAPERS_DIR
    dates: list[str] = []
    domains: set[str] = set()
    for f in papers_dir.glob("*.json"):
        if not re.match(r"\d{4}-\d{2}-\d{2}\.json$", f.name):
            continue
        date = f.stem
        try:
            payload = json.loads(f.read_text())
        except Exception:
            continue
        if not payload.get("papers"):
            continue
        dates.append(date)
        for p in payload["papers"]:
            domains.add(p.get("matched_domain", ""))
    dates.sort(reverse=True)
    index = {
        "dates": dates,
        "latest": dates[0] if dates else "",
        "domains": [d for d in DIRECTIONS] + sorted(domains - set(DIRECTIONS)),
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    out = repo_root() / WEB_DATA_DIR / "index.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    return out


# ------------------------------- Obsidian -------------------------------- #

def md_escape(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ").strip()


def write_obsidian(date: str, papers: list[dict]) -> tuple[int, int]:
    """Return (daily_written, paper_files_written)."""
    root = Path(OBSIDIAN_ROOT)
    if not root.exists():
        print(f"  ⚠ Obsidian vault not found at {root} — skipping md sync", file=sys.stderr)
        return 0, 0
    (root / OBSIDIAN_DAILY).mkdir(parents=True, exist_ok=True)
    (root / OBSIDIAN_PAPERS).mkdir(parents=True, exist_ok=True)

    # Group by direction
    by_dir: dict[str, list[dict]] = {}
    for p in papers:
        by_dir.setdefault(p["matched_domain"], []).append(p)

    # Daily digest
    lines: list[str] = []
    lines.append("---")
    lines.append(f"date: {date}")
    lines.append(f"count: {len(papers)}")
    tags = ["embodied-arxiv", f"daily/{date}"]
    lines.append("tags:")
    for t in tags:
        lines.append(f"  - {t}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {date} · embodied-arxiv ({len(papers)} 篇)")
    lines.append("")
    for direction in list(DIRECTIONS) + sorted(set(by_dir) - set(DIRECTIONS)):
        items = by_dir.get(direction)
        if not items:
            continue
        lines.append(f"## {direction} ({len(items)})")
        lines.append("")
        items.sort(key=lambda x: x["scores"]["recommendation"], reverse=True)
        for p in items:
            score = p["scores"]["recommendation"]
            venue = f"  ·  *{p['venue']}*" if p.get("venue") else ""
            authors = ", ".join(p["authors"][:3])
            if len(p["authors"]) > 3:
                authors += " et al."
            lines.append(
                f"- **[{md_escape(p['title'])}]({p['arxiv_url']})**  ·  ⭐ {score:.1f}{venue}"
            )
            lines.append(f"    - {authors}")
            if p["summary"]:
                lines.append(f"    - {md_escape(p['summary'])}")
            lines.append(f"    - [[{OBSIDIAN_PAPERS}/{p['arxiv_id']}|展开]]")
            lines.append("")
    daily_path = root / OBSIDIAN_DAILY / f"{date}.md"
    daily_path.write_text("\n".join(lines))

    # Per-paper notes
    n_papers = 0
    for p in papers:
        aid = p["arxiv_id"]
        out = root / OBSIDIAN_PAPERS / f"{aid}.md"
        if out.exists():
            # Don't clobber — Claude or the user may have annotated
            continue
        h = p["highlights"]
        kw = ", ".join(p.get("matched_keywords", []))
        body = [
            "---",
            f'arxiv_id: "{aid}"',
            f'title: "{p["title"].replace(chr(34), chr(39))}"',
            f"date: {p['published_date'][:10]}",
            f"direction: {p['matched_domain']}",
        ]
        if p.get("venue"):
            body.append(f'venue: "{p["venue"]}"')
        body.append(f"score: {p['scores']['recommendation']:.1f}")
        body.append("tags:")
        body.append("  - embodied-arxiv")
        body.append(f"  - direction/{p['matched_domain'].lower().replace(' ', '-')}")
        if p.get("venue"):
            body.append(f"  - venue/{re.sub(r'[^a-zA-Z0-9]', '-', p['venue']).strip('-').lower()}")
        body.append("---")
        body.append("")
        body.append(f"# {p['title']}")
        body.append("")
        body.append(f"- arXiv: [{aid}]({p['arxiv_url']})  ·  [PDF]({p['pdf_url']})")
        body.append(f"- 方向: **{p['matched_domain']}**" + (f"  ·  会议: **{p['venue']}**" if p.get("venue") else ""))
        body.append(f"- 推荐分: **{p['scores']['recommendation']:.1f}** / 10")
        body.append(f"- 关键词: {kw}")
        body.append(f"- 作者: {', '.join(p['authors'])}")
        body.append("")
        if p.get("summary"):
            body.append("## 中文摘要")
            body.append("")
            body.append(p["summary"])
            body.append("")
        body.append("## 💡 核心贡献")
        body.append("")
        body.append(h["contribution"])
        body.append("")
        body.append("## ✨ 创新点")
        body.append("")
        body.append(h["innovation"])
        body.append("")
        body.append("## 🔧 方法概要")
        body.append("")
        body.append(h["method"])
        body.append("")
        body.append("## 📊 关键结果")
        body.append("")
        body.append(h["results"])
        body.append("")
        body.append("## 原文摘要")
        body.append("")
        body.append("> " + (p.get("original_abstract") or "").replace("\n", "\n> "))
        body.append("")
        body.append(f"---  ·  [[{OBSIDIAN_DAILY}/{p['published_date'][:10]}|回到当日]]")
        out.write_text("\n".join(body))
        n_papers += 1
    return 1, n_papers


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--skip-obsidian", action="store_true")
    args = ap.parse_args()

    raw_p = repo_root() / RAW_DIR / f"{args.date}.json"
    cards_p = repo_root() / CARDS_DIR / f"{args.date}.json"
    if not raw_p.exists():
        print(f"[build_web_data] missing {raw_p}", file=sys.stderr)
        return 1
    if not cards_p.exists():
        print(f"[build_web_data] missing {cards_p}", file=sys.stderr)
        return 1

    raw_payload = json.loads(raw_p.read_text())
    cards_raw = json.loads(cards_p.read_text())
    if isinstance(cards_raw, dict) and "cards" in cards_raw:
        cards_list = cards_raw["cards"]
    else:
        cards_list = cards_raw
    cards = {c["arxiv_id"]: c for c in cards_list if "arxiv_id" in c}

    papers = merge(raw_payload["papers"], cards)
    # Sort: direction priority, then recommendation desc
    dir_order = {d: i for i, d in enumerate(DIRECTIONS)}
    papers.sort(key=lambda p: (dir_order.get(p["matched_domain"], 99), -p["scores"]["recommendation"]))

    out = write_papers_json(args.date, papers)
    idx = rebuild_index()
    print(f"[build_web_data] wrote {out.relative_to(repo_root())}  ({len(papers)} papers)", file=sys.stderr)
    print(f"[build_web_data] wrote {idx.relative_to(repo_root())}", file=sys.stderr)

    if not args.skip_obsidian:
        d, n = write_obsidian(args.date, papers)
        print(f"[build_web_data] Obsidian: {d} daily + {n} new paper notes", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

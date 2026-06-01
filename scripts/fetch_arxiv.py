#!/usr/bin/env python3
"""Query arXiv for new papers matching the configured DIRECTIONS.

Usage:
    python scripts/fetch_arxiv.py                       # last weekday batch
    python scripts/fetch_arxiv.py --date 2026-06-01     # specific date
    python scripts/fetch_arxiv.py --days 3              # last 3 weekdays

Writes data/raw/<date>.json with:
    {
      "date": "YYYY-MM-DD",
      "fetched_at": "...",
      "papers": [ { arxiv_id, title, abstract, authors, ... }, ... ]
    }

Also appends matched arxiv_ids to data/seen.json so subsequent runs skip them.
The output is candidate-only — Claude (via the /research-assistant skill)
reads each abstract, writes highlights & summary, and emits the final card.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

# Make `from config import ...` resolve when invoked as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (  # noqa: E402
    ARXIV_CATEGORIES,
    DIRECTIONS,
    MAX_PAPERS_PER_DAY,
    RAW_DIR,
    SEEN_DB,
    USER_AGENT,
)

ARXIV_API = "http://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_seen() -> set[str]:
    p = repo_root() / SEEN_DB
    if not p.exists():
        return set()
    try:
        return set(json.loads(p.read_text()))
    except Exception:
        return set()


def save_seen(seen: set[str]) -> None:
    p = repo_root() / SEEN_DB
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(sorted(seen), indent=2))


def match_directions(text: str) -> tuple[str | None, list[str]]:
    """Return (best_direction, hit_keywords). best_direction=None if no hit."""
    text_l = text.lower()
    scores: list[tuple[str, list[str]]] = []
    for direction, kws in DIRECTIONS.items():
        hits = [kw for kw in kws if kw in text_l]
        if hits:
            scores.append((direction, hits))
    if not scores:
        return None, []
    # Prefer the direction with the most hits; tie-break by DIRECTIONS order
    scores.sort(key=lambda x: (-len(x[1]), list(DIRECTIONS).index(x[0])))
    return scores[0][0], scores[0][1]


def arxiv_query(start: int = 0, batch: int = 200) -> str:
    cat_query = "+OR+".join(f"cat:{c}" for c in ARXIV_CATEGORIES)
    params = {
        "search_query": cat_query,
        "start": str(start),
        "max_results": str(batch),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    # Note: arxiv wants `search_query` with + literals; don't urlencode it.
    qs = (
        f"search_query={params['search_query']}"
        f"&start={params['start']}"
        f"&max_results={params['max_results']}"
        f"&sortBy={params['sortBy']}"
        f"&sortOrder={params['sortOrder']}"
    )
    return f"{ARXIV_API}?{qs}"


def http_get(url: str, timeout: float = 30.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_entry(entry: ET.Element) -> dict | None:
    def text(node: ET.Element | None) -> str:
        return (node.text or "").strip() if node is not None else ""

    id_node = entry.find("atom:id", NS)
    arxiv_url = text(id_node)
    if not arxiv_url:
        return None
    # arxiv id like "http://arxiv.org/abs/2605.12345v1" — strip version + prefix
    arxiv_id = arxiv_url.rsplit("/", 1)[-1].split("v")[0]

    title = text(entry.find("atom:title", NS)).replace("\n", " ").strip()
    abstract = text(entry.find("atom:summary", NS)).replace("\n", " ").strip()
    published = text(entry.find("atom:published", NS))
    updated = text(entry.find("atom:updated", NS))
    authors = [
        text(a.find("atom:name", NS)) for a in entry.findall("atom:author", NS)
    ]
    categories = [
        c.get("term", "") for c in entry.findall("atom:category", NS) if c.get("term")
    ]
    primary = entry.find("arxiv:primary_category", NS)
    primary_cat = primary.get("term", "") if primary is not None else (categories[0] if categories else "")
    pdf_url = ""
    arxiv_abs_url = ""
    for link in entry.findall("atom:link", NS):
        if link.get("title") == "pdf":
            pdf_url = link.get("href", "")
        if link.get("rel") == "alternate":
            arxiv_abs_url = link.get("href", "")

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "affiliations": [],  # arxiv API doesn't expose these; Claude can fill from PDF if needed
        "categories": categories,
        "primary_category": primary_cat,
        "published_date": published,
        "updated_date": updated,
        "arxiv_url": arxiv_abs_url or f"https://arxiv.org/abs/{arxiv_id}",
        "pdf_url": pdf_url or f"https://arxiv.org/pdf/{arxiv_id}",
    }


def paper_pub_date(paper: dict) -> dt.date | None:
    try:
        pub = dt.datetime.fromisoformat(paper["published_date"].replace("Z", "+00:00"))
    except Exception:
        return None
    return pub.date()


def in_date_window(paper: dict, start: dt.date, end_exclusive: dt.date) -> bool:
    d = paper_pub_date(paper)
    return d is not None and start <= d < end_exclusive


def default_target_date() -> dt.date:
    """The most recent arxiv announcement date (UTC).

    arxiv announces Mon–Fri at 00:00 UTC. We default to *yesterday* UTC if
    today's announcement hasn't landed yet (i.e. before 00:00 UTC). Caller
    can override with --date.
    """
    now_utc = dt.datetime.now(dt.timezone.utc)
    # If we're before 02:00 UTC, today's announcement may still be propagating.
    target = now_utc.date() if now_utc.hour >= 2 else (now_utc - dt.timedelta(days=1)).date()
    # Skip weekends
    while target.weekday() >= 5:
        target -= dt.timedelta(days=1)
    return target


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", help="YYYY-MM-DD (UTC). Default: last announcement.")
    ap.add_argument("--days", type=int, default=1, help="Window in days ending at --date.")
    ap.add_argument("--max", type=int, default=MAX_PAPERS_PER_DAY, help="Cap kept papers per day.")
    ap.add_argument("--pages", type=int, default=10, help="Max arxiv pages of 200 each.")
    ap.add_argument(
        "--ignore-seen",
        action="store_true",
        help="Don't filter out previously-seen arxiv_ids.",
    )
    args = ap.parse_args()

    if args.date:
        try:
            end_date = dt.date.fromisoformat(args.date)
        except ValueError:
            ap.error(f"--date must be YYYY-MM-DD, got {args.date!r}")
            return 2
    else:
        end_date = default_target_date()
    start_date = end_date - dt.timedelta(days=max(1, args.days) - 1)
    end_exclusive = end_date + dt.timedelta(days=1)
    print(
        f"[fetch_arxiv] window=[{start_date} .. {end_date}]  cats={ARXIV_CATEGORIES}  max={args.max}",
        file=sys.stderr,
    )

    seen = set() if args.ignore_seen else load_seen()
    kept: list[dict] = []
    older_streak = 0
    PAGE = 200

    for page in range(args.pages):
        url = arxiv_query(start=page * PAGE, batch=PAGE)
        try:
            xml = http_get(url)
        except Exception as e:
            print(f"[fetch_arxiv] page {page} request failed: {e}", file=sys.stderr)
            break
        root = ET.fromstring(xml)
        entries = root.findall("atom:entry", NS)
        if not entries:
            break
        page_kept = 0
        for entry in entries:
            paper = parse_entry(entry)
            if paper is None:
                continue
            if paper["arxiv_id"] in seen:
                continue
            d = paper_pub_date(paper)
            if d is None:
                continue
            if d >= end_exclusive:
                # Newer than the window — sort is desc, keep paginating without
                # tripping the older-than-window short-circuit.
                continue
            if d < start_date:
                older_streak += 1
                continue
            older_streak = 0
            direction, hits = match_directions(paper["title"] + "\n" + paper["abstract"])
            if direction is None:
                continue
            paper["matched_domain"] = direction
            paper["matched_keywords"] = hits[:6]
            kept.append(paper)
            seen.add(paper["arxiv_id"])
            page_kept += 1
        print(
            f"[fetch_arxiv] page {page + 1}: scanned {len(entries)}, kept {page_kept}, total kept {len(kept)}",
            file=sys.stderr,
        )
        # Stop once we've drifted well past the window
        if older_streak > 100:
            break
        # Stop early if we've hit the cap
        if len(kept) >= args.max * 2:
            break
        time.sleep(3.0)  # arxiv rate limit guidance

    # Cap: keep the most recent --max papers
    kept.sort(key=lambda p: p.get("published_date", ""), reverse=True)
    if len(kept) > args.max:
        dropped = len(kept) - args.max
        print(f"[fetch_arxiv] capping to --max={args.max} (dropped {dropped} older matches)", file=sys.stderr)
        kept = kept[: args.max]
    # Then sort by direction priority + date desc for nicer reading order
    direction_order = {d: i for i, d in enumerate(DIRECTIONS)}
    kept.sort(key=lambda p: (direction_order.get(p["matched_domain"], 99), -ord(p.get("published_date", "z")[0]) if p.get("published_date") else 0, p.get("published_date", ""), p["arxiv_id"]))

    out_path = repo_root() / RAW_DIR / f"{end_date.isoformat()}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": end_date.isoformat(),
        "window_start": start_date.isoformat(),
        "fetched_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "categories": ARXIV_CATEGORIES,
        "papers": kept,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    if not args.ignore_seen:
        save_seen(seen)
    print(
        f"[fetch_arxiv] wrote {out_path.relative_to(repo_root())} — {len(kept)} papers",
        file=sys.stderr,
    )
    # Direction breakdown
    by_dir: dict[str, int] = {}
    for p in kept:
        by_dir[p["matched_domain"]] = by_dir.get(p["matched_domain"], 0) + 1
    for d in DIRECTIONS:
        print(f"  - {d}: {by_dir.get(d, 0)}", file=sys.stderr)
    # Echo path on stdout so Claude can pipe / parse easily
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

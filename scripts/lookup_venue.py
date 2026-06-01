#!/usr/bin/env python3
"""Look up conference / journal venue for each paper in data/raw/<date>.json.

Queries Semantic Scholar's graph API (free tier, no key needed) and falls
back to DBLP. Writes results back into the same raw file (`venue` field on
each paper) so build_web_data.py can include them.

Usage:
    python scripts/lookup_venue.py --date 2026-06-01

Most arxiv preprints are not yet in any venue — that's fine. A missing
venue stays as null and the UI just hides the badge.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import RAW_DIR, USER_AGENT  # noqa: E402

S2_API = "https://api.semanticscholar.org/graph/v1/paper/arxiv:{aid}"
DBLP_API = "https://dblp.org/search/publ/api"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def http_get_json(url: str, timeout: float = 20.0) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ! HTTP fail: {e}", file=sys.stderr)
        return None


def lookup_semantic_scholar(arxiv_id: str) -> str | None:
    url = S2_API.format(aid=arxiv_id) + "?fields=venue,publicationVenue,year"
    data = http_get_json(url)
    if not data:
        return None
    pv = data.get("publicationVenue") or {}
    name = pv.get("name") or pv.get("alternate_names", [None])[0]
    if name:
        return name
    venue = data.get("venue")
    if venue:
        return venue
    return None


def lookup_dblp(title: str) -> str | None:
    # DBLP is title-search-based. Keep query terse.
    q = " ".join(title.split()[:8])
    url = f"{DBLP_API}?q={urllib.parse.quote(q)}&format=json&h=3"
    data = http_get_json(url)
    if not data:
        return None
    hits = (((data.get("result") or {}).get("hits") or {}).get("hit") or [])
    for h in hits:
        info = (h.get("info") or {})
        venue = info.get("venue")
        if venue and venue.lower() != "corr":  # CoRR = arxiv preprint, skip
            return venue
    return None


def normalize_venue(raw: str) -> str:
    s = raw.strip()
    # Common cleanups
    s = s.replace("Conference on ", "")
    s = s.replace("International Conference on ", "")
    if len(s) > 32:
        # Heuristic: if it looks like a full name, try the abbreviation in parens
        if "(" in s and ")" in s:
            inside = s[s.rfind("(") + 1 : s.rfind(")")].strip()
            if 2 <= len(inside) <= 12:
                return inside
        s = s[:32].rstrip() + "…"
    return s


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD matching data/raw/<date>.json")
    ap.add_argument("--sleep", type=float, default=1.2, help="Seconds between requests.")
    ap.add_argument("--limit", type=int, default=0, help="Max papers to look up (0 = all).")
    ap.add_argument("--skip-dblp", action="store_true", help="Don't fall back to DBLP.")
    args = ap.parse_args()

    raw_path = repo_root() / RAW_DIR / f"{args.date}.json"
    if not raw_path.exists():
        print(f"[lookup_venue] no raw file: {raw_path}", file=sys.stderr)
        return 1

    payload = json.loads(raw_path.read_text())
    papers = payload.get("papers", [])
    todo = papers if not args.limit else papers[: args.limit]
    hits = 0
    for i, p in enumerate(todo, 1):
        if p.get("venue"):
            continue  # already filled (rerun-safe)
        aid = p["arxiv_id"]
        venue = lookup_semantic_scholar(aid)
        if not venue and not args.skip_dblp:
            venue = lookup_dblp(p.get("title", ""))
        p["venue"] = normalize_venue(venue) if venue else None
        flag = "✓" if venue else "·"
        print(f"  [{i:3d}/{len(todo)}] {flag} {aid}  {p['venue'] or '—'}", file=sys.stderr)
        if venue:
            hits += 1
        time.sleep(args.sleep)

    raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"[lookup_venue] {hits}/{len(todo)} venues filled — wrote {raw_path.relative_to(repo_root())}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

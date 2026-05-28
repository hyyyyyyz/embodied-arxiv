"""OpenReview venue lookup — ground-truth conference acceptance info.

LLM-extracted venue from arXiv abstracts is unreliable (authors don't always
update). OpenReview has authoritative accepted-papers lists for ICLR /
NeurIPS / ICML / CoRL etc. This module:

1. Periodically fetches accepted papers per venue (cached to data/)
2. Provides title → venue lookup for arXiv papers

Cache TTL: 7 days. Forced refresh via `force_refresh=True`.
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
CACHE_PATH = ROOT / "data" / "openreview_cache.json"
CACHE_TTL_DAYS = 7

# Default venues to query (adjust to match user's interests).
# Format: OpenReview venue group ID.
DEFAULT_VENUES = [
    "ICLR.cc/2026/Conference",
    "ICLR.cc/2025/Conference",
    "NeurIPS.cc/2025/Conference",
    "NeurIPS.cc/2024/Conference",
    "ICML.cc/2026/Conference",
    "ICML.cc/2025/Conference",
    "robot-learning.org/CoRL/2025/Conference",
    "robot-learning.org/CoRL/2024/Conference",
]


def _normalize_title(title: str) -> str:
    """Lowercase + strip non-alphanumeric, for robust title matching."""
    return re.sub(r"[^a-z0-9]+", "", title.lower())


def _short_name(venue_id: str) -> str:
    """ICLR.cc/2026/Conference -> 'ICLR 2026'"""
    parts = venue_id.split("/")
    abbr = parts[0].split(".")[0]
    year = next((p for p in parts if p.isdigit() and len(p) == 4), "")
    return f"{abbr} {year}".strip()


def _load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {"timestamp": 0, "papers": {}}
    try:
        d = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        if isinstance(d, dict) and "papers" in d:
            return d
    except Exception as e:
        log.warning(f"OpenReview cache read failed: {e}")
    return {"timestamp": 0, "papers": {}}


def _save_cache(d: dict):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(d, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _extract_content_field(content, field: str) -> str:
    """OpenReview API2 wraps content fields as {value: ...}; API1 is bare."""
    v = content.get(field)
    if isinstance(v, dict):
        return v.get("value", "") or ""
    return v or ""


def _fetch_one_venue(client, venue_id: str) -> Dict[str, str]:
    """Returns {normalized_title: venue_short_name} for accepted papers."""
    short = _short_name(venue_id)
    out: Dict[str, str] = {}
    try:
        notes = client.get_all_notes(
            invitation=f"{venue_id}/-/Submission",
        )
    except Exception as e:
        log.warning(f"  {venue_id}: get_all_notes failed: {e}")
        return out

    for n in notes:
        content = getattr(n, "content", {}) or {}
        title = _extract_content_field(content, "title").strip()
        if not title:
            continue
        # "venue" or "venueid" field is populated only for accepted papers
        venue_val = _extract_content_field(content, "venue") or \
                    _extract_content_field(content, "venueid")
        if not venue_val:
            continue
        out[_normalize_title(title)] = short
    return out


def _fetch_all(venues: List[str]) -> Dict[str, str]:
    try:
        import openreview
    except ImportError:
        log.warning("openreview-py not installed; venue lookup disabled")
        return {}

    try:
        client = openreview.api.OpenReviewClient(
            baseurl="https://api2.openreview.net"
        )
    except Exception as e:
        log.warning(f"OpenReview client init failed: {e}")
        return {}

    combined: Dict[str, str] = {}
    for v in venues:
        log.info(f"OpenReview fetching {v}...")
        result = _fetch_one_venue(client, v)
        log.info(f"  {v}: {len(result)} accepted")
        combined.update(result)
    return combined


def get_venue_map(venues: Optional[List[str]] = None,
                  force_refresh: bool = False) -> Dict[str, str]:
    """Return {normalized_title: venue_short} dict, with disk cache."""
    venues = venues or DEFAULT_VENUES
    cache = _load_cache()
    age = time.time() - cache.get("timestamp", 0)

    if (not force_refresh and
        age < CACHE_TTL_DAYS * 86400 and
        cache.get("papers")):
        log.info(
            f"Using OpenReview cache: {len(cache['papers'])} papers, "
            f"{int(age / 86400)}d old"
        )
        return cache["papers"]

    log.info("Refreshing OpenReview cache (>=7d old)...")
    papers = _fetch_all(venues)
    if papers:
        _save_cache({"timestamp": time.time(), "papers": papers})
    return papers


def lookup_venue(title: str, venue_map: Dict[str, str]) -> Optional[str]:
    """Look up the OpenReview venue for a paper title. Returns None if not found."""
    if not title or not venue_map:
        return None
    return venue_map.get(_normalize_title(title))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    m = get_venue_map(force_refresh=True)
    print(f"total accepted papers: {len(m)}")
    for k, v in list(m.items())[:5]:
        print(f"  {v}: {k[:50]}")

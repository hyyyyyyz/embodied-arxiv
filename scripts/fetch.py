"""Fetch recent arXiv papers per config.yaml.

Key design:
- Primary categories (e.g. cs.RO) → fetch all, filter by date only
- Secondary categories (cs.CV/AI/LG) → fetch only papers matching keyword
  OR-query in the URL itself (drastically fewer results, avoids pagination
  and the 429 rate-limit hit that pagination triggers)
- Per-category try/except so one bad category doesn't sink the whole run
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

import arxiv
import yaml

log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent


def load_config() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def _build_query(category: str, is_primary: bool, keywords: List[str]) -> str:
    """Build an arXiv API search query.

    Primary: just the category.
    Secondary: category AND (any keyword in title OR abstract).
    """
    if is_primary:
        return f"cat:{category}"
    parts = []
    for kw in keywords:
        kw = kw.strip()
        if not kw:
            continue
        # Phrase queries (contain space or hyphen) need quotes
        if " " in kw or "-" in kw:
            parts.append(f'abs:"{kw}"')
            parts.append(f'ti:"{kw}"')
        else:
            parts.append(f"abs:{kw}")
            parts.append(f"ti:{kw}")
    kw_query = " OR ".join(parts)
    return f"cat:{category} AND ({kw_query})"


def fetch_recent_papers() -> List[Dict]:
    """Return a deduped list of candidate papers from the last N days.

    Failures on individual categories are logged and skipped — the function
    always returns whatever it could collect.
    """
    cfg = load_config()["arxiv"]
    cutoff = datetime.now(timezone.utc) - timedelta(days=cfg["lookback_days"])

    # arXiv tightened rate limits; 5s + more retries is safer
    client = arxiv.Client(
        page_size=100,
        delay_seconds=5,
        num_retries=5,
    )
    primary_cats = set(cfg["categories"]["primary"])
    secondary_cats = cfg["categories"]["secondary"]
    keywords = cfg["keywords"]

    all_cats = list(primary_cats) + secondary_cats
    papers: Dict[str, dict] = {}

    for category in all_cats:
        is_primary = category in primary_cats
        query = _build_query(category, is_primary, keywords)
        log.info(
            f"Querying arXiv: {category} "
            f"({'primary' if is_primary else 'secondary'}, "
            f"query length={len(query)})"
        )

        try:
            search = arxiv.Search(
                query=query,
                max_results=cfg["max_per_category"],
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )
            n_kept = 0
            for result in client.results(search):
                if result.published < cutoff:
                    break  # sorted desc, no more recent

                arxiv_id = result.entry_id.split("/abs/")[-1].split("v")[0]
                if arxiv_id in papers:
                    continue

                papers[arxiv_id] = {
                    "id": arxiv_id,
                    "title": result.title.strip().replace("\n", " "),
                    "authors": [a.name for a in result.authors],
                    "abstract": result.summary.replace("\n", " ").strip(),
                    "published": result.published.isoformat(),
                    "updated": result.updated.isoformat() if result.updated else None,
                    "categories": result.categories,
                    "primary_category": result.primary_category,
                    "pdf_url": result.pdf_url,
                    "arxiv_url": result.entry_id,
                    "matched_via": category,
                }
                n_kept += 1
            log.info(f"  kept {n_kept} from {category}")
        except Exception as e:
            log.warning(f"  {category} failed ({type(e).__name__}: {e}); skipping")
            continue

    log.info(f"Total unique candidates: {len(papers)}")
    return list(papers.values())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    import json
    out = fetch_recent_papers()
    print(json.dumps(out[:3], indent=2, ensure_ascii=False))
    print(f"\n{len(out)} total")

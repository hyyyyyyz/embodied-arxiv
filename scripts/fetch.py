"""Fetch recent arXiv papers per config.yaml."""
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


def _matches_keywords(text: str, keywords: List[str]) -> bool:
    low = text.lower()
    return any(kw.lower() in low for kw in keywords)


def fetch_recent_papers() -> List[Dict]:
    """Return a deduped list of candidate papers from the last N days."""
    cfg = load_config()["arxiv"]
    cutoff = datetime.now(timezone.utc) - timedelta(days=cfg["lookback_days"])

    client = arxiv.Client(page_size=100, delay_seconds=3, num_retries=3)
    primary_cats = set(cfg["categories"]["primary"])
    secondary_cats = cfg["categories"]["secondary"]
    keywords = cfg["keywords"]

    all_cats = list(primary_cats) + secondary_cats
    papers: Dict[str, dict] = {}

    for category in all_cats:
        log.info(f"Querying arXiv category {category}")
        search = arxiv.Search(
            query=f"cat:{category}",
            max_results=cfg["max_per_category"],
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )
        n_kept = 0
        for result in client.results(search):
            if result.published < cutoff:
                break  # results are sorted desc by date

            arxiv_id = result.entry_id.split("/abs/")[-1].split("v")[0]
            if arxiv_id in papers:
                continue

            is_primary = category in primary_cats
            text = f"{result.title} {result.summary}"
            if not is_primary and not _matches_keywords(text, keywords):
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

    log.info(f"Total unique candidates: {len(papers)}")
    return list(papers.values())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    import json
    out = fetch_recent_papers()
    print(json.dumps(out[:3], indent=2, ensure_ascii=False))
    print(f"\n{len(out)} total")

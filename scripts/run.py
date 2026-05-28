"""Daily pipeline orchestrator: fetch -> score -> figure -> build.

(Trigger marker: 2026-05-27 redeploy after filter merge)
"""
from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Make sibling modules importable when run as `python scripts/run.py`
sys.path.insert(0, str(Path(__file__).parent))

from fetch import fetch_recent_papers  # noqa: E402
from score import score_paper, summarize_paper, generate_briefing  # noqa: E402
from figure import get_all_figures, score_figures_heuristic, pick_with_vl  # noqa: E402
from build import build_daily, update_home, ASSETS_DIR  # noqa: E402
from openreview_venue import get_venue_map, lookup_venue  # noqa: E402

load_dotenv()  # local .env for dev; in Actions secrets come via env directly

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
log = logging.getLogger("run")

ROOT = Path(__file__).parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
SEEN_PATH = ROOT / "data" / "seen.json"


def load_seen() -> set:
    if SEEN_PATH.exists():
        try:
            return set(json.loads(SEEN_PATH.read_text()))
        except Exception:
            return set()
    return set()


def save_seen(seen: set):
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEEN_PATH.write_text(json.dumps(sorted(seen), ensure_ascii=False, indent=2))


def _pick_figure(paper: dict, work_dir: Path, use_vl: bool, vl_model: str, min_kb: int):
    """Return (chosen_fig_or_None, all_figs_sorted_by_score)."""
    all_figs = get_all_figures(paper, work_dir, min_kb=min_kb)
    if not all_figs:
        return None, []
    scored = score_figures_heuristic(all_figs)
    top_score = scored[0][0]
    runner = scored[1][0] if len(scored) > 1 else -1e9
    if top_score - runner >= 5 or not use_vl:
        chosen = scored[0][1]
    else:
        chosen = pick_with_vl([f for _, f in scored[:3]], paper, vl_model)
    return chosen, [f for _, f in scored]


def main():
    today = datetime.now(timezone.utc).date()
    date_str = today.isoformat()
    log.info(f"=== Run for {date_str} ===")

    seen = load_seen()
    log.info(f"Previously seen: {len(seen)} papers")

    candidates = fetch_recent_papers()
    new_papers = [p for p in candidates if p["id"] not in seen]
    log.info(f"Candidates: {len(candidates)} | new: {len(new_papers)}")

    site_title = CONFIG["site"]["title"]
    history_days = CONFIG["site"]["history_days_on_index"]

    if not new_papers:
        log.info("Nothing new today — refreshing home only")
        update_home(history_days=history_days, site_title=site_title)
        return

    score_cfg = CONFIG["scoring"]
    scored_papers = []
    for p in new_papers:
        try:
            s = score_paper(p, model=score_cfg["model"])
            p["score"] = s["score"]
            p["topic"] = s["topic"]
            p["score_reason"] = s["reason"]
            scored_papers.append(p)
            log.info(
                f"  scored {p['id']} = {p['score']:.1f} ({p['topic']}) — "
                f"{p['title'][:60]}"
            )
        except Exception as e:
            log.warning(f"  score failed for {p['id']}: {e}")

    # Mark every scored paper as seen so failures don't re-process next run
    seen.update(p["id"] for p in scored_papers)

    # Two-tier qualification: priority topics get lower threshold
    priority_topics = set(score_cfg.get("priority_topics", []))
    pri_min = score_cfg.get("priority_min_score", score_cfg.get("min_score", 6.0))
    non_pri_min = score_cfg.get("non_priority_min_score", score_cfg.get("min_score", 6.0))

    def is_qualified(p):
        return (p["score"] >= pri_min if p["topic"] in priority_topics
                else p["score"] >= non_pri_min)

    qualified = [p for p in scored_papers if is_qualified(p)]
    # Sort: priority topics first, then by score desc
    qualified.sort(key=lambda p: (
        0 if p["topic"] in priority_topics else 1,
        -p["score"],
    ))
    qualified = qualified[: score_cfg["max_published"]]
    n_pri = sum(1 for p in qualified if p["topic"] in priority_topics)
    log.info(
        f"Qualified: {len(qualified)} "
        f"({n_pri} priority topics @ >={pri_min}, "
        f"{len(qualified) - n_pri} other @ >={non_pri_min})"
    )

    if not qualified:
        save_seen(seen)
        update_home(history_days=history_days, site_title=site_title)
        return

    # OpenReview venue lookup (cached, refreshes weekly)
    try:
        venue_map = get_venue_map()
        log.info(f"OpenReview venue map: {len(venue_map)} papers indexed")
    except Exception as e:
        log.warning(f"OpenReview lookup failed: {e}")
        venue_map = {}

    fig_cfg = CONFIG["figure"]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for p in qualified:
            # Summary
            try:
                p["summary"] = summarize_paper(p, model=score_cfg["model"])
            except Exception as e:
                log.warning(f"  summarize failed for {p['id']}: {e}")
                p["summary"] = {
                    "tldr": p["title"][:35],
                    "trick": "（摘要生成失败，请查看原文）",
                    "summary": p["abstract"][:400],
                    "tags": [p.get("topic", "other")],
                    "comment": "",
                }

            # OpenReview overrides LLM-extracted venue when we have a hit
            or_venue = lookup_venue(p["title"], venue_map)
            if or_venue:
                old = p["summary"].get("venue")
                p["summary"]["venue"] = or_venue
                if old != or_venue:
                    log.info(f"  venue: OpenReview {or_venue} (was LLM={old})")

            # Figure
            try:
                chosen, all_figs = _pick_figure(
                    p, tmp,
                    use_vl=fig_cfg["enable_vl_fallback"],
                    vl_model=fig_cfg["vl_model"],
                    min_kb=fig_cfg["min_figure_kb"],
                )
                safe_id = p["id"].replace("/", "_")
                if chosen:
                    fig_dir = ASSETS_DIR / date_str
                    fig_dir.mkdir(parents=True, exist_ok=True)
                    main_path = fig_dir / f"{safe_id}.png"
                    main_path.write_bytes(chosen["bytes"])
                    # From docs/papers/<date>/index.md OR <id>.md → docs/assets/figures/<date>/<id>.png
                    # Both are 2 levels up
                    rel = f"../../assets/figures/{date_str}/{main_path.name}"
                    p["figure_path_in_index"] = rel
                    p["figure_path_in_detail"] = rel
                    p["figure_caption"] = chosen.get("caption") or ""
                    # User feedback: only the framework figure, no extras
                else:
                    p["figure_path_in_index"] = None
                    p["figure_path_in_detail"] = None
            except Exception as e:
                log.warning(f"  figure failed for {p['id']}: {e}")
                p["figure_path_in_index"] = None
                p["figure_path_in_detail"] = None

    # Daily AI briefing (optional)
    briefing = ""
    if CONFIG["scoring"].get("briefing", False) and qualified:
        try:
            log.info("Generating daily briefing...")
            briefing = generate_briefing(qualified, model=score_cfg["model"])
            log.info(f"  briefing ({len(briefing)} chars): {briefing[:80]}...")
        except Exception as e:
            log.warning(f"briefing failed: {e}")

    build_daily(date_str, qualified, history_days=history_days,
                site_title=site_title, briefing=briefing)
    save_seen(seen)

    log.info(f"=== Done: {len(qualified)} papers published for {date_str} ===")


if __name__ == "__main__":
    main()

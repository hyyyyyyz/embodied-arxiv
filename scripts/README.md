# scripts/

Stdlib-only Python helpers driven by the `/research-assistant` Claude Code
skill. None of them call an LLM API — Claude is the reading layer.

## Pipeline

```
                   ┌──────────────────────┐
1. fetch_arxiv.py  │ data/raw/<date>.json │     (arxiv → filtered candidates)
                   └──────────┬───────────┘
                              │
2. lookup_venue.py            │              (adds `venue` field in place)
                              ▼
                   ┌──────────────────────────┐
3. Claude reads abstracts  →  data/cards/<date>.json
                   └──────────┬───────────────┘
                              │
4. build_web_data.py          │
                              ▼
       web/public/data/{papers/<date>.json, index.json}
       + {OBSIDIAN_ROOT}/{DailyPapers, Papers}/*.md
```

## File contracts

### `data/raw/<date>.json` (produced by `fetch_arxiv.py`)
```json
{
  "date": "2026-06-01",
  "fetched_at": "...",
  "papers": [
    {
      "arxiv_id": "2606.00001",
      "title": "...",
      "abstract": "...",
      "authors": ["..."],
      "affiliations": [],
      "categories": ["cs.RO"],
      "published_date": "2026-06-01T00:00:00Z",
      "arxiv_url": "...", "pdf_url": "...",
      "matched_domain": "VLA",
      "matched_keywords": ["vla model", ...],
      "venue": null   ← filled by lookup_venue.py
    }
  ]
}
```

### `data/cards/<date>.json` (Claude writes)
```json
[
  {
    "arxiv_id": "2606.00001",
    "summary": "中文一段话总结，包含动机/方法/结果",
    "highlights": {
      "contribution": "...",
      "innovation": "...",
      "method": "...",
      "results": "..."
    },
    "scores": { "recommendation": 8.5, "relevance": 9, "recency": 10,
                "popularity": 6, "quality": 8 },
    "affiliations": ["Stanford", "Google DeepMind"]   ← optional override
  }
]
```

`scores` may also be just a single float (e.g. `7.5`) — it'll expand to all
five keys. Any paper missing from the cards file is skipped with a warning,
so partial runs are safe.

## Tuning coverage

Edit `scripts/config.py`:
- `DIRECTIONS` — keyword lists per research direction
- `ARXIV_CATEGORIES` — which arxiv top-level cats to sweep
- `MAX_PAPERS_PER_DAY` — daily cap (older matches drop off the top)

"""Generate the VitePress content tree from per-paper data.

Layout:
  docs/
    .vitepress/
      data/stats.json                  # aggregated stats for Dashboard.vue
      theme/components/*.vue           # custom components
    index.md                           # home (renders <Dashboard />)
    papers/
      <date>/
        index.md                       # card grid + <TopicFilter />
        <arxiv-id>.md                  # per-paper detail
"""
from __future__ import annotations

import json
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional


def _yaml_str(s: str) -> str:
    """Safely quote a string for YAML frontmatter.
    Uses json.dumps which produces YAML-compatible double-quoted strings
    (handles colons, quotes, newlines, unicode correctly)."""
    return json.dumps(s, ensure_ascii=False)

log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
PAPERS_DIR = DOCS / "papers"
# VitePress convention: docs/public/<x> is served at base-URL `/<x>`
ASSETS_DIR = DOCS / "public" / "figures"
STATS_PATH = DOCS / ".vitepress" / "data" / "stats.json"
PICKS_PATH = DOCS / ".vitepress" / "data" / "picks.json"

TOPIC_COLORS = {
    "VLA": "#7c3aed",
    "world-model": "#9333ea",
    "3d-foundation": "#06b6d4",
    "policy-learning": "#dc2626",
    "manipulation": "#ea580c",
    "navigation": "#16a34a",
    "locomotion": "#0d9488",
    "sim2real": "#0891b2",
    "grasping": "#ca8a04",
    "teleoperation": "#db2777",
    "tactile": "#be185d",
    "humanoid": "#0369a1",
    "other": "#64748b",
}

VERDICT_EMOJIS = {"🔥", "👀", "⚠️", "🫠", "💀", "🤡", "💤"}


def _topic_color(topic: str) -> str:
    return TOPIC_COLORS.get(topic, TOPIC_COLORS["other"])


def _short_authors(authors: List[str], n: int = 4) -> str:
    if not authors:
        return ""
    if len(authors) <= n:
        return ", ".join(authors)
    return ", ".join(authors[:n]) + f" 等 {len(authors)} 位"


def _safe_id(arxiv_id: str) -> str:
    return arxiv_id.replace("/", "_")


# ========================================================
# PER-PAPER DETAIL PAGE
# ========================================================

def write_paper_detail(date_str: str, paper: dict) -> Path:
    folder = PAPERS_DIR / date_str
    folder.mkdir(parents=True, exist_ok=True)
    page = folder / f"{_safe_id(paper['id'])}.md"

    s = paper["summary"]
    fig = paper.get("figure_path_in_detail")
    topic = paper.get("topic", "other")
    color = _topic_color(topic)
    venue = s.get("venue")
    verdict = s.get("verdict", "")
    if verdict not in VERDICT_EMOJIS:
        verdict = ""

    tricks = s.get("tricks") or []
    if not tricks and s.get("trick"):
        tricks = [{"text": s["trick"], "core": True}]

    abstract_zh = s.get("abstract_zh") or s.get("summary") or ""
    abstract_en = paper.get("abstract", "")
    critique_text = s.get("critique") or s.get("comment") or ""

    # VitePress frontmatter: hide sidebar/aside for focused reading.
    # Title quoted via json.dumps to handle colons/quotes safely.
    lines = [
        "---",
        f"title: {_yaml_str(s['tldr'])}",
        "sidebar: false",
        "aside: false",
        "outline: false",
        "---",
        "",
        f'<a class="back-btn" href="./">← 返回 {date_str}</a>',
        "",
        f"# {s['tldr']}",
        "",
        f'### {paper["title"]}',
        "",
        '<div class="paper-meta-row">',
    ]
    if verdict:
        lines.append(f'<span class="badge badge-verdict">{verdict}</span>')
    lines += [
        f'<span class="badge badge-score">⭐ {paper["score"]:.1f}</span>',
        f'<span class="badge badge-topic" style="background:{color}22;color:{color}">{topic}</span>',
    ]
    if venue:
        lines.append(f'<span class="badge badge-venue">{venue}</span>')
    lines += [
        f'<span class="paper-id">{paper["id"]}</span>',
        '</div>',
        "",
        f'<div class="paper-links">📄 <a href="{paper["arxiv_url"]}">arXiv 摘要页</a> &nbsp;·&nbsp; 📑 <a href="{paper["pdf_url"]}">PDF 全文</a></div>',
        "",
        f"*{_short_authors(paper['authors'])}*",
        "",
    ]

    if fig:
        # Absolute path served from public/; VitePress prefixes base URL
        lines.append(f"![framework]({fig})")
        if paper.get("figure_caption"):
            cap = paper["figure_caption"].replace("\n", " ").replace("|", "\\|")[:240]
            lines.append("")
            lines.append(f"<small>{cap}</small>")
        lines.append("")

    if tricks:
        lines += ["## 💡 关键 Tricks", ""]
        for t in tricks:
            txt = t.get("text", "").strip()
            if not txt:
                continue
            if t.get("core"):
                lines.append(f'- <span class="trick-core">⭐ 核心</span> — **{txt}**')
            else:
                lines.append(f"- {txt}")
        lines.append("")

    lines += [
        "## 📝 摘要",
        "",
        abstract_zh,
        "",
    ]

    if abstract_en:
        lines += [
            "<details>",
            "<summary>English (原文)</summary>",
            "",
            abstract_en,
            "",
            "</details>",
            "",
        ]

    if s.get("related"):
        lines += [
            "## 🔗 与已有工作的关系",
            "",
            s["related"],
            "",
        ]

    if critique_text:
        head_emoji = verdict if verdict else "📌"
        lines += [
            '<div class="critique-box">',
            f'<div class="critique-header"><span class="critique-emoji">{head_emoji}</span> 锐评</div>',
            f'<div class="critique-body">{critique_text}</div>',
            '</div>',
            "",
        ]

    if s.get("tags"):
        lines += [
            "---",
            "",
            "**Tags**: " + " ".join(f"`{t}`" for t in s["tags"]),
            "",
        ]

    page.write_text("\n".join(lines), encoding="utf-8")
    return page


# ========================================================
# DATE INDEX (CARD GRID) — DERIVED FROM DETAIL .md FILES
# ========================================================
# Detail .md files are the source of truth. The index.md is regenerated
# from them every time, so multiple runs on the same day can only ADD
# papers (via new detail files) — never silently drop earlier ones.

# Parsers for fields inside a single per-paper detail .md file.
_DETAIL_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_DETAIL_TITLE_LINE_RE = re.compile(r"^title:\s*(.+?)\s*$", re.MULTILINE)
_DETAIL_H3_RE = re.compile(r"^### (.+)$", re.MULTILINE)
_DETAIL_BADGE_VERDICT_RE = re.compile(r'<span class="badge badge-verdict">([^<]+)</span>')
_DETAIL_BADGE_SCORE_RE = re.compile(r'<span class="badge badge-score">⭐ ([\d.]+)</span>')
_DETAIL_BADGE_TOPIC_RE = re.compile(r'<span class="badge badge-topic"[^>]*>([^<]+)</span>')
_DETAIL_BADGE_VENUE_RE = re.compile(r'<span class="badge badge-venue">([^<]+)</span>')
_DETAIL_FIG_RE = re.compile(r'!\[framework\]\(([^)]+)\)')


def _parse_title_value(val: str) -> str:
    val = val.strip()
    if not val:
        return ""
    if val.startswith('"') and val.endswith('"'):
        try:
            return json.loads(val)
        except Exception:
            return val[1:-1]
    if val.startswith("'") and val.endswith("'"):
        return val[1:-1]
    return val


def parse_detail_md(md_path: Path) -> Optional[dict]:
    """Read a per-paper detail .md and return the card metadata dict.

    Returns None only if the file is unreadable. Missing optional fields
    fall back to safe defaults so a partially-broken detail still produces
    a working card (link works even if score/verdict missing).
    """
    try:
        src = md_path.read_text(encoding="utf-8")
    except Exception:
        return None

    paper_id = md_path.stem

    # Frontmatter title acts as the tldr (TLDR + linked label)
    tldr = paper_id
    fm = _DETAIL_FRONTMATTER_RE.match(src)
    if fm:
        m = _DETAIL_TITLE_LINE_RE.search(fm.group(1))
        if m:
            tldr = _parse_title_value(m.group(1)) or paper_id

    # ### {paper.title}
    h3 = _DETAIL_H3_RE.search(src)
    title = h3.group(1).strip() if h3 else tldr

    # Badges
    v = _DETAIL_BADGE_VERDICT_RE.search(src)
    verdict = v.group(1).strip() if v else ""
    if verdict not in VERDICT_EMOJIS:
        verdict = ""

    s = _DETAIL_BADGE_SCORE_RE.search(src)
    score = float(s.group(1)) if s else 0.0

    t = _DETAIL_BADGE_TOPIC_RE.search(src)
    topic = t.group(1).strip() if t else "other"

    vn = _DETAIL_BADGE_VENUE_RE.search(src)
    venue = vn.group(1).strip() if vn else ""

    f = _DETAIL_FIG_RE.search(src)
    figure_url = f.group(1).strip() if f else ""

    return {
        "id": paper_id,
        "title": title,
        "tldr": tldr,
        "topic": topic,
        "score": score,
        "verdict": verdict,
        "venue": venue,
        "figure_url": figure_url,
    }


def _build_card_html(c: dict) -> str:
    topic = c["topic"]
    color = _topic_color(topic)
    if c.get("figure_url"):
        img_html = (
            f'<img class="paper-card-img" src="{c["figure_url"]}" '
            f'alt="" loading="lazy">'
        )
    else:
        img_html = '<div class="paper-card-img no-img"></div>'
    venue_html = (
        f'<span class="paper-card-venue">{c["venue"]}</span>'
        if c.get("venue")
        else ""
    )
    verdict_html = (
        f'<span class="verdict-tag">{c["verdict"]}</span> '
        if c.get("verdict") in VERDICT_EMOJIS
        else ""
    )
    title = (c["title"] or c["id"]).replace("\n", " ").strip()
    tldr = (c.get("tldr") or "").replace("\n", " ").strip()
    return (
        f'<a class="paper-card" data-topic="{topic}" href="./{c["id"]}/">'
        f'{img_html}'
        f'<div class="paper-card-body">'
        f'{venue_html}'
        f'<div class="paper-card-title">{verdict_html}{title}</div>'
        f'<div class="paper-card-tldr">{tldr}</div>'
        f'<div class="paper-card-meta">'
        f'<span class="paper-card-score">⭐ {c["score"]:.1f}</span>'
        f'<span class="paper-card-topic" '
        f'style="background:{color}22;color:{color}">{topic}</span>'
        f'</div>'
        f'</div>'
        f'</a>'
    )


_BRIEFING_BODY_RE = re.compile(
    r'<div class="briefing-body">(.*?)</div>', re.DOTALL
)

PRIORITY_TOPICS = {"VLA", "world-model", "3d-foundation", "policy-learning"}


def write_date_index(date_str: str, briefing: str = "") -> Path:
    """Rebuild the date-index card grid from every detail .md in the folder.

    NEW papers are introduced by write_paper_detail() writing a new detail
    file BEFORE this function runs (see build_daily); this function then
    discovers them on disk along with all prior papers, so subsequent runs
    can only ADD — never silently drop — papers for the same day.

    If `briefing` is empty, we try to reuse the briefing already embedded
    in the existing index.md so it doesn't get blanked out on rebuild.
    """
    folder = PAPERS_DIR / date_str
    folder.mkdir(parents=True, exist_ok=True)
    page = folder / "index.md"

    # Collect cards from every per-paper detail file.
    cards: List[dict] = []
    for md_path in sorted(folder.glob("*.md")):
        if md_path.stem == "index":
            continue
        c = parse_detail_md(md_path)
        if c:
            cards.append(c)

    # Preserve existing briefing if caller didn't pass one.
    if not briefing and page.exists():
        try:
            existing = page.read_text(encoding="utf-8")
            m = _BRIEFING_BODY_RE.search(existing)
            if m:
                briefing = m.group(1).strip()
        except Exception:
            pass

    # Sort: priority topics first, then by score desc, then by id desc
    cards.sort(
        key=lambda c: (
            0 if c["topic"] in PRIORITY_TOPICS else 1,
            -c["score"],
            -float(re.sub(r"[^0-9.]", "", c["id"]) or 0),
        )
    )

    topic_counts = Counter(c["topic"] for c in cards)

    # Build filter chips
    filter_parts = [
        f'<button class="topic-filter-btn active" data-topic="all">'
        f'<span class="dot" style="background:#a78bfa"></span>'
        f'全部 <span class="cnt">{len(cards)}</span></button>'
    ]
    for topic, n in topic_counts.most_common():
        color = _topic_color(topic)
        filter_parts.append(
            f'<button class="topic-filter-btn" data-topic="{topic}">'
            f'<span class="dot" style="background:{color}"></span>'
            f'{topic} <span class="cnt">{n}</span></button>'
        )

    lines = [
        "---",
        f'title: "{date_str}"',
        "outline: false",
        "---",
        "",
        f"# {date_str}",
        "",
        f"今日精选 **{len(cards)}** 篇 · 按相关性降序 · 优先类（VLA / world-model / 3d-foundation / policy-learning）排前",
        "",
    ]
    if briefing:
        lines += [
            '<div class="briefing-box">',
            '<div class="briefing-header">📰 今日 AI 简报</div>',
            f'<div class="briefing-body">{briefing}</div>',
            '</div>',
            "",
        ]

    lines.append("<TopicFilter />")
    lines.append("")
    lines.append('<div class="paper-grid">')
    for c in cards:
        lines.append(_build_card_html(c))
    lines += ["</div>", ""]

    page.write_text("\n".join(lines), encoding="utf-8")
    return page


def rebuild_all_date_indexes() -> int:
    """Rebuild every date's index.md from its detail .md files.

    Idempotent recovery step — safe to call on every run. Use this to
    repair indexes that were truncated by the destructive-overwrite bug
    that existed prior to deriving index.md from disk.
    """
    if not PAPERS_DIR.exists():
        return 0
    n = 0
    for date_dir in sorted(PAPERS_DIR.iterdir()):
        if not date_dir.is_dir():
            continue
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_dir.name):
            continue
        # Skip directories with no detail files.
        details = [p for p in date_dir.glob("*.md") if p.stem != "index"]
        if not details:
            continue
        write_date_index(date_dir.name)
        n += 1
    log.info(f"rebuild_all_date_indexes: {n} date indexes refreshed from disk")
    return n


# ========================================================
# STATS AGGREGATION (for Dashboard.vue)
# ========================================================

CARD_RE = re.compile(
    r'<a class="paper-card" data-topic="([^"]+)" href="\./([^"/]+)/?">'
    r'.*?'
    r'(?:url\(([^)]+)\))?'  # figure URL (optional)
    r'.*?'
    r'<div class="paper-card-body">'
    r'(?:<span class="paper-card-venue">[^<]+</span>)?'
    r'<div class="paper-card-title">'
    r'(?:<span class="verdict-tag">([^<]*)</span>\s*)?'
    r'([^<]+)'
    r'</div>'
    r'<div class="paper-card-tldr">([^<]*)</div>'
    r'.*?'
    r'<span class="paper-card-score">⭐ ([\d.]+)</span>'
    r'.*?'
    r'</a>',
    re.DOTALL,
)


def aggregate_all_papers() -> List[dict]:
    """Parse all per-date index.md files and extract per-paper info."""
    papers = []
    if not PAPERS_DIR.exists():
        return papers
    for date_dir in sorted(PAPERS_DIR.iterdir()):
        if not date_dir.is_dir():
            continue
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_dir.name):
            continue
        index = date_dir / "index.md"
        if not index.exists():
            continue
        try:
            content = index.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in CARD_RE.finditer(content):
            topic, paper_id, fig_url, verdict, title, tldr, score = m.groups()
            papers.append({
                "date": date_dir.name,
                "id": paper_id,
                "topic": topic,
                "verdict": (verdict or "").strip(),
                "title": title.strip(),
                "tldr": tldr.strip(),
                "score": float(score),
                "figure_url": (fig_url or "").strip(),
            })
    return papers


def write_stats_json():
    """Aggregate all papers into stats.json consumed by Dashboard.vue."""
    papers = aggregate_all_papers()

    topics = Counter(p["topic"] for p in papers)
    verdicts = Counter(p["verdict"] for p in papers if p["verdict"])

    # Highlights: 🔥 first, then most-recent 👀/⚠️, then by score; top 6
    verdict_priority = {"🔥": 100, "👀": 50, "⚠️": 10}
    highlights = [p for p in papers if p["verdict"] in verdict_priority]
    highlights.sort(
        key=lambda p: (
            -verdict_priority.get(p["verdict"], 0),
            -int(p["date"].replace("-", "")),
            -p["score"],
        )
    )
    highlights = highlights[:6]

    by_date = Counter(p["date"] for p in papers)
    date_counts = sorted(by_date.items(), key=lambda x: x[0], reverse=True)

    stats = {
        "total_papers": len(papers),
        "total_days": len(by_date),
        "topics": dict(topics.most_common()),
        "verdicts": dict(verdicts),
        "highlights": highlights,
        "latest_date": date_counts[0][0] if date_counts else None,
        "date_counts": date_counts,
    }

    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATS_PATH.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log.info(
        f"stats: {stats['total_papers']} papers across {stats['total_days']} days, "
        f"{len(stats['topics'])} topics, {len(stats['highlights'])} highlights"
    )

    # picks.json — full list of high-verdict papers for the /picks/ page.
    # (Kept separate from stats.json so the home dashboard stays lean;
    #  this file is only imported by the picks-page component.)
    verdict_rank = {"🔥": 3, "👀": 2, "⚠️": 1}
    picks = [
        {
            "date": p["date"],
            "id": p["id"],
            "topic": p["topic"],
            "verdict": p["verdict"],
            "title": p["title"],
            "tldr": p["tldr"],
            "score": p["score"],
            "figure_url": p.get("figure_url", ""),
        }
        for p in papers
        if p["verdict"] in verdict_rank
    ]
    picks.sort(
        key=lambda p: (
            -verdict_rank.get(p["verdict"], 0),
            -int(p["date"].replace("-", "")),
            -p["score"],
        )
    )
    PICKS_PATH.write_text(
        json.dumps(picks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    n_fire = sum(1 for p in picks if p["verdict"] == "🔥")
    log.info(f"picks.json: {len(picks)} papers ({n_fire} 🔥)")


# ========================================================
# LEGACY-FORMAT MIGRATION (one-off, idempotent)
# ========================================================

def migrate_legacy_format():
    """Migrate old MkDocs syntax to VitePress-compatible.

    - Detail pages: convert `=== "中文"` / `=== "English"` tabs to plain
      paragraph + <details>.
    - Date index pages: strip hardcoded <div class="topic-filter"> and
      replace with <TopicFilter /> component.

    Idempotent — files already in new format are skipped.
    """
    if not PAPERS_DIR.exists():
        return

    n_detail = 0
    n_index = 0

    tab_re = re.compile(
        r'=== "([^"]+)"\s*\n+'
        r'((?:    [^\n]*\n|[ \t]*\n)+)',
        re.MULTILINE,
    )

    def dedent(text: str) -> str:
        lines = []
        for ln in text.splitlines():
            if ln.startswith("    "):
                lines.append(ln[4:])
            else:
                lines.append(ln)
        return "\n".join(lines).strip()

    for date_dir in PAPERS_DIR.iterdir():
        if not date_dir.is_dir():
            continue
        for md in date_dir.glob("*.md"):
            try:
                src = md.read_text(encoding="utf-8")
            except Exception:
                continue

            if md.stem == "index":
                # Strip old topic-filter block
                new = re.sub(
                    r'<div class="topic-filter">.*?</div>\s*\n',
                    "<TopicFilter />\n\n",
                    src,
                    flags=re.DOTALL,
                )
                # Insert TopicFilter if missing entirely
                if "<TopicFilter />" not in new and '<div class="paper-grid">' in new:
                    new = new.replace(
                        '<div class="paper-grid">',
                        "<TopicFilter />\n\n<div class=\"paper-grid\">",
                        1,
                    )
                # Fix old href "<paper-id>/" → "./paper-id/"
                new = re.sub(
                    r'<a class="paper-card" data-topic="([^"]+)" href="([0-9][^"/]+)/"',
                    r'<a class="paper-card" data-topic="\1" href="./\2/"',
                    new,
                )
                if new != src:
                    md.write_text(new, encoding="utf-8")
                    n_index += 1
            else:
                # Detail page: migrate tabs
                matches = list(tab_re.finditer(src))
                if not matches:
                    continue
                # Build replacement
                zh, en = None, None
                for m in matches:
                    label = m.group(1)
                    content = dedent(m.group(2))
                    if "中文" in label or label.lower() == "chinese":
                        zh = content
                    elif "English" in label or "英文" in label:
                        en = content
                if zh is None and en is None:
                    continue
                replacement = ""
                if zh:
                    replacement += zh + "\n\n"
                if en:
                    replacement += f"<details>\n<summary>English (原文)</summary>\n\n{en}\n\n</details>\n"
                # Replace from first tab to last
                start = matches[0].start()
                end = matches[-1].end()
                new = src[:start] + replacement + src[end:]

                # Also fix back-button href: old `index.md` → `./`
                new = re.sub(
                    r'<a class="back-btn" href="index\.md">',
                    '<a class="back-btn" href="./">',
                    new,
                )

                # Strip old mkdocs frontmatter that VitePress doesn't need
                new = re.sub(
                    r'^---\nhide:\n  - navigation\n---\n',
                    '---\nsidebar: false\naside: false\n---\n',
                    new,
                    count=1,
                )

                if new != src:
                    md.write_text(new, encoding="utf-8")
                    n_detail += 1

    if n_detail or n_index:
        log.info(f"migrate: {n_detail} detail pages + {n_index} indexes converted")

    # --- Quote frontmatter `title:` lines containing colons/quotes ---
    # YAML parses `title: A: B` as a nested mapping. Wrap in JSON-quoted.
    n_title_fix = 0
    title_re = re.compile(r'^(title:\s*)(?!["\'])([^\n]*)$', re.MULTILINE)

    for md in PAPERS_DIR.glob("**/*.md"):
        try:
            src = md.read_text(encoding="utf-8")
        except Exception:
            continue
        # Only the FIRST frontmatter title (within --- ... ---)
        front_match = re.match(r'^(---\n.*?\n---)\n', src, re.DOTALL)
        if not front_match:
            continue
        front = front_match.group(1)
        # Find unquoted title with a colon or quote inside the value
        def fix_title(m):
            prefix, val = m.group(1), m.group(2).strip()
            if val.startswith('"') or val.startswith("'"):
                return m.group(0)
            if ':' in val or '"' in val or "'" in val:
                return f'{prefix}{_yaml_str(val)}'
            return m.group(0)
        new_front = title_re.sub(fix_title, front)
        if new_front != front:
            new = new_front + src[front_match.end(1):]
            md.write_text(new, encoding="utf-8")
            n_title_fix += 1
    if n_title_fix:
        log.info(f"migrate: {n_title_fix} title frontmatters quoted")

    # --- Migrate asset locations: assets/figures → public/figures ---
    legacy_figs = DOCS / "assets" / "figures"
    new_figs = DOCS / "public" / "figures"
    if legacy_figs.exists():
        new_figs.parent.mkdir(parents=True, exist_ok=True)
        new_figs.mkdir(exist_ok=True)
        for date_dir in list(legacy_figs.iterdir()):
            if not date_dir.is_dir():
                continue
            target = new_figs / date_dir.name
            target.mkdir(exist_ok=True)
            for f in list(date_dir.iterdir()):
                tgt = target / f.name
                if not tgt.exists():
                    try:
                        f.rename(tgt)
                    except Exception as e:
                        log.warning(f"  failed move {f}: {e}")
            try:
                date_dir.rmdir()
            except OSError:
                pass
        try:
            legacy_figs.rmdir()
            (DOCS / "assets").rmdir() if (DOCS / "assets").exists() else None
        except OSError:
            pass
        log.info(f"migrate: assets/figures → public/figures")

    # --- Migrate path refs in all paper markdown ---
    n_path = 0
    for md in PAPERS_DIR.glob("**/*.md"):
        try:
            src = md.read_text(encoding="utf-8")
        except Exception:
            continue
        new = src
        # Old relative paths → new absolute
        new = re.sub(r'\.\./\.\./assets/figures/', '/figures/', new)
        # Convert background-image cards → <img>
        new = re.sub(
            r'<div class="paper-card-img" style="background-image: url\(([^)]+)\)[^"]*"></div>',
            r'<img class="paper-card-img" src="\1" alt="" loading="lazy">',
            new,
        )
        if new != src:
            md.write_text(new, encoding="utf-8")
            n_path += 1
    if n_path:
        log.info(f"migrate: {n_path} files had asset paths updated")


# ========================================================
# TOP-LEVEL
# ========================================================

def build_daily(date_str: str, papers: list, history_days: int = 60,
                site_title: str = "embodied-arxiv", briefing: str = ""):
    """Called by run.py for one date's qualified papers.

    Order matters: write each per-paper detail file FIRST so that
    write_date_index() — which derives the card grid from every detail
    .md on disk — picks up the newly-added papers alongside any
    previously-published ones from the same day. This is the fix for the
    destructive-overwrite bug where a second daily run would replace the
    morning's cards with only the afternoon's batch.
    """
    for p in papers:
        write_paper_detail(date_str, p)
    write_date_index(date_str, briefing=briefing)
    # Rebuild stats and the home dashboard JSON every run
    write_stats_json()


# Back-compat: run.py / older code may still call this; now it's just stats.
def update_home(history_days: int = 60, site_title: str = "embodied-arxiv"):
    write_stats_json()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_legacy_format()
    rebuild_all_date_indexes()
    write_stats_json()

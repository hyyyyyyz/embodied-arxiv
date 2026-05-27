"""Generate the static-site content tree.

Layout:
  docs/
    index.md                              # landing page (regenerated each run)
    .pages                                # top-level nav order
    papers/
      .pages                              # title='论文归档', order: desc
      <date>/                             # one folder per day
        .pages                            # only index.md in nav
        index.md                          # card grid
        <arxiv-id>.md                     # per-paper detail page

Per-paper detail pages are excluded from nav via `not_in_nav` glob in mkdocs.yml.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
PAPERS_DIR = DOCS / "papers"
ASSETS_DIR = DOCS / "assets" / "figures"

TOPIC_COLORS = {
    "VLA": "#7c3aed",
    "manipulation": "#ea580c",
    "navigation": "#16a34a",
    "locomotion": "#0d9488",
    "world-model": "#9333ea",
    "sim2real": "#0891b2",
    "grasping": "#ca8a04",
    "teleoperation": "#db2777",
    "policy-learning": "#dc2626",
    "perception": "#1e40af",
    "other": "#64748b",
}


def _topic_color(topic: str) -> str:
    return TOPIC_COLORS.get(topic, TOPIC_COLORS["other"])


def _short_authors(authors: List[str], n: int = 4) -> str:
    if not authors:
        return ""
    if len(authors) <= n:
        return ", ".join(authors)
    return ", ".join(authors[:n]) + f" 等 {len(authors)} 位"


def _safe_id(arxiv_id: str) -> str:
    """File-system-safe arxiv id (old-style IDs may contain '/')."""
    return arxiv_id.replace("/", "_")


# -------------------- PER-PAPER DETAIL PAGE --------------------

def write_paper_detail(date_str: str, paper: dict) -> Path:
    folder = PAPERS_DIR / date_str
    folder.mkdir(parents=True, exist_ok=True)
    page = folder / f"{_safe_id(paper['id'])}.md"

    s = paper["summary"]
    fig = paper.get("figure_path_in_detail")
    topic = paper.get("topic", "other")
    color = _topic_color(topic)

    lines = [
        "---",
        f"title: {s['tldr']}",
        "hide:",
        "  - navigation",
        "---",
        "",
        f"# {s['tldr']}",
        "",
        f'[← 返回 {date_str} 列表](index.md){{ .back-link }}',
        "",
        f'### {paper["title"]}',
        "",
        f'<div class="paper-meta-row">',
        f'  <span class="badge badge-score">⭐ {paper["score"]:.1f}</span>',
        f'  <span class="badge badge-topic" style="background:{color}22;color:{color}">{topic}</span>',
        f'  <span class="paper-id">{paper["id"]}</span>',
        f'</div>',
        "",
        f"*{_short_authors(paper['authors'])}*",
        "",
    ]

    if fig:
        lines.append("<figure markdown>")
        lines.append(f"  ![framework]({fig})")
        if paper.get("figure_caption"):
            cap = paper["figure_caption"].replace("\n", " ").replace("|", "\\|")[:240]
            lines.append(f"  <figcaption>{cap}</figcaption>")
        lines.append("</figure>")
        lines.append("")

    lines += [
        '!!! tip "💡 Trick — 关键技术 insight"',
        f"    {s['trick']}",
        "",
        "## 摘要",
        "",
        s["summary"],
        "",
    ]

    if s.get("tags"):
        lines += [
            "**Tags**: " + " ".join(f"`{t}`" for t in s["tags"]),
            "",
        ]

    if s.get("comment"):
        lines += [
            "## 📝 我的评价",
            "",
            s["comment"],
            "",
        ]

    if paper.get("extra_figures_in_detail"):
        lines += ["## 📷 论文中其他图", ""]
        for i, ef in enumerate(paper["extra_figures_in_detail"], 1):
            lines += [f"![fig{i}]({ef})", ""]

    lines += [
        "---",
        "",
        f"[📄 arXiv 摘要页]({paper['arxiv_url']}) &nbsp;·&nbsp; [📑 PDF 全文]({paper['pdf_url']})",
        "",
    ]

    page.write_text("\n".join(lines), encoding="utf-8")
    return page


# -------------------- DATE INDEX (CARD GRID) --------------------

def write_date_index(date_str: str, papers: list) -> Path:
    folder = PAPERS_DIR / date_str
    folder.mkdir(parents=True, exist_ok=True)
    page = folder / "index.md"

    lines = [
        "---",
        f"title: {date_str}",
        "hide:",
        "  - toc",
        "---",
        "",
        f"# {date_str}",
        "",
        f"今日精选 **{len(papers)}** 篇 · 按 DeepSeek 相关性评分降序 · 点击卡片查看详情",
        "",
        # IMPORTANT: NO `markdown` attribute on this div.
        # With `markdown`, python-markdown wraps each <a> in <p> and the
        # nested <div> closes <p> early, destroying the card layout.
        # Without it (md_in_html default), the inner HTML stays raw.
        '<div class="paper-grid">',
    ]

    for p in papers:
        s = p["summary"]
        fig_path = p.get("figure_path_in_index")
        topic = p.get("topic", "other")
        color = _topic_color(topic)
        title = p["title"].replace("\n", " ").strip()

        if fig_path:
            img_html = f'<div class="paper-card-img" style="background-image: url({fig_path});"></div>'
        else:
            img_html = '<div class="paper-card-img no-img"></div>'

        # Emit as one tight HTML block — no blank lines anywhere inside
        # the .paper-grid container (blank lines re-trigger paragraph mode).
        card = (
            f'<a class="paper-card" href="{_safe_id(p["id"])}/">'
            f'{img_html}'
            f'<div class="paper-card-body">'
            f'<div class="paper-card-title">{title}</div>'
            f'<div class="paper-card-tldr">{s["tldr"]}</div>'
            f'<div class="paper-card-meta">'
            f'<span class="paper-card-score">⭐ {p["score"]:.1f}</span>'
            f'<span class="paper-card-topic" style="background:{color}22;color:{color}">{topic}</span>'
            f'</div>'
            f'</div>'
            f'</a>'
        )
        lines.append(card)

    lines += ['</div>', '']

    page.write_text("\n".join(lines), encoding="utf-8")
    return page


# -------------------- .pages SCAFFOLDING --------------------

def write_date_pages_file(date_str: str):
    folder = PAPERS_DIR / date_str
    folder.mkdir(parents=True, exist_ok=True)
    # Quote the date — without quotes YAML parses 2026-05-27 as datetime.date,
    # which breaks mkdocs-awesome-pages plugin (expects string title).
    (folder / ".pages").write_text(
        f'title: "{date_str}"\n'
        f"nav:\n"
        f"  - 卡片列表: index.md\n",
        encoding="utf-8",
    )


def ensure_papers_pages_file():
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    pages = PAPERS_DIR / ".pages"
    if not pages.exists():
        pages.write_text(
            "title: 论文归档\n"
            "order: desc\n"
            "sort_type: natural\n",
            encoding="utf-8",
        )


def ensure_top_pages_file():
    pages = DOCS / ".pages"
    if not pages.exists():
        pages.write_text(
            "nav:\n"
            "  - 首页: index.md\n"
            "  - 论文归档: papers\n"
            "  - 关于: about.md\n",
            encoding="utf-8",
        )


# -------------------- HOMEPAGE --------------------

def update_home(history_days: int = 60, site_title: str = "embodied-arxiv"):
    """Home page = meta-refresh redirect to the latest date's card grid.

    This matches the intended UX: user visits the site → immediately lands
    on the most recent day's papers. The left sidebar always shows the
    full date list, so they can jump to any day from there.
    """
    DOCS.mkdir(parents=True, exist_ok=True)
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)

    date_folders = sorted(
        [d for d in PAPERS_DIR.iterdir() if d.is_dir() and d.name[0].isdigit()],
        key=lambda d: d.name,
        reverse=True,
    )

    if date_folders:
        latest = date_folders[0].name
        lines = [
            "---",
            f"title: {site_title}",
            "hide:",
            "  - toc",
            "---",
            "",
            f'<meta http-equiv="refresh" content="0; url=papers/{latest}/">',
            "",
            f"# {site_title}",
            "",
            f'正在跳转到最新一天 → **[{latest}](papers/{latest}/)** …',
            "",
            '<small>如果没有自动跳转，点击上面链接，或在左侧栏选任意一天。</small>',
            "",
        ]
    else:
        lines = [
            "---",
            f"title: {site_title}",
            "hide:",
            "  - toc",
            "---",
            "",
            f"# {site_title}",
            "",
            "_首次构建中，等待第一次 cron 触发……_",
            "",
        ]

    (DOCS / "index.md").write_text("\n".join(lines), encoding="utf-8")
    log.info(f"Updated home — {len(date_folders)} days, latest = "
             f"{date_folders[0].name if date_folders else 'none'}")


# -------------------- TOP-LEVEL ENTRY --------------------

def build_daily(date_str: str, papers: list, history_days: int = 60, site_title: str = "Embodied arXiv 雷达"):
    """Top-level helper called by run.py for a single date's papers."""
    ensure_top_pages_file()
    ensure_papers_pages_file()
    write_date_pages_file(date_str)
    write_date_index(date_str, papers)
    for p in papers:
        write_paper_detail(date_str, p)
    update_home(history_days=history_days, site_title=site_title)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    update_home()
    ensure_top_pages_file()
    ensure_papers_pages_file()

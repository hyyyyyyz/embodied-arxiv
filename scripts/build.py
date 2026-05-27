"""Generate per-day markdown page + refresh index."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List

log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
PAPERS_DIR = DOCS / "papers"
ASSETS_DIR = DOCS / "assets" / "figures"


def _short_authors(authors: List[str], n: int = 4) -> str:
    if not authors:
        return ""
    if len(authors) <= n:
        return ", ".join(authors)
    return ", ".join(authors[:n]) + f" 等 {len(authors)} 位"


def _topic_badge(topic: str) -> str:
    color_map = {
        "VLA": "blueviolet", "manipulation": "orange", "navigation": "green",
        "locomotion": "teal", "world-model": "purple", "sim2real": "cyan",
        "grasping": "yellow", "teleoperation": "pink",
        "policy-learning": "red", "perception": "navy", "other": "gray",
    }
    color = color_map.get(topic, "gray")
    return f'![{topic}](https://img.shields.io/badge/{topic.replace("-", "--")}-{color}?style=flat-square)'


def write_daily_page(date_str: str, papers: list) -> Path:
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    page = PAPERS_DIR / f"{date_str}.md"

    lines = [
        f"# {date_str} · 具身智能 arXiv 雷达",
        "",
        f"精选 **{len(papers)}** 篇 · 按 DeepSeek 相关性评分降序",
        "",
        "[← 回首页](../index.md)",
        "",
        "---",
        "",
    ]

    for p in papers:
        s = p["summary"]
        fig_path = p.get("figure_path")
        tags = " ".join(f"`{t}`" for t in s.get("tags", []))

        lines.append(f'## {s["tldr"]}')
        lines.append("")
        lines.append(
            f'**[{p["title"]}]({p["arxiv_url"]})** '
            f'&nbsp; {_topic_badge(p.get("topic", "other"))} '
            f'&nbsp; ⭐ **{p["score"]:.1f}** '
            f'&nbsp; `{p["id"]}`'
        )
        lines.append("")
        lines.append(f"*{_short_authors(p['authors'])}*")
        lines.append("")

        if fig_path:
            lines.append(f'<figure markdown>')
            lines.append(f'![framework]({fig_path})')
            cap = (p.get("figure_caption") or "Framework").replace("\n", " ")[:200]
            lines.append(f'  <figcaption>{cap}</figcaption>')
            lines.append('</figure>')
            lines.append("")

        lines.append(f'> 💡 **Trick** — {s["trick"]}')
        lines.append("")
        lines.append(s["summary"])
        lines.append("")

        if tags:
            lines.append(f"**Tags**: {tags}")
            lines.append("")

        if s.get("comment"):
            lines.append(f'??? note "📝 我的评价"')
            lines.append(f'    {s["comment"]}')
            lines.append("")

        if p.get("extra_figures"):
            lines.append('??? abstract "📷 论文中其他图"')
            lines.append("")
            for i, ef in enumerate(p["extra_figures"], start=1):
                lines.append(f'    ![fig{i}]({ef})')
                lines.append("")

        lines.append(f"[📄 arXiv]({p['arxiv_url']}) · [📑 PDF]({p['pdf_url']})")
        lines.append("")
        lines.append("---")
        lines.append("")

    page.write_text("\n".join(lines), encoding="utf-8")
    log.info(f"Wrote {page} ({len(papers)} papers)")
    return page


def update_index(history_days: int = 60, site_title: str = "Embodied arXiv 雷达"):
    DOCS.mkdir(parents=True, exist_ok=True)
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)

    pages = sorted(
        [p for p in PAPERS_DIR.glob("*.md")],
        key=lambda p: p.stem,
        reverse=True,
    )

    lines = [
        f"# {site_title}",
        "",
        "> **每日具身智能 arXiv 论文 · DeepSeek V4 摘要 + Trick 提炼 + Framework 图自动抓取**",
        "",
        "覆盖 VLA / Manipulation / Navigation / Locomotion / Sim2Real / World Model / Diffusion Policy 等方向。",
        "每天北京时间 10:00 自动更新（arXiv 美东 20:00 放新论文）。",
        "",
        "---",
        "",
        "## 📅 历史归档",
        "",
    ]

    if not pages:
        lines.append("_首次构建中，等待第一次 cron 触发……_")
        lines.append("")
    else:
        for page in pages[:history_days]:
            date = page.stem
            # Count papers by counting "## " level headings
            try:
                content = page.read_text(encoding="utf-8")
                n = len(re.findall(r"^## ", content, re.MULTILINE))
            except Exception:
                n = 0
            lines.append(f"- [**{date}**](papers/{date}.md) — {n} 篇")

        if len(pages) > history_days:
            lines.append("")
            lines.append(f"<small>另有 {len(pages) - history_days} 天更早的归档（见 GitHub 仓库 `docs/papers/`）</small>")

    lines += [
        "",
        "---",
        "",
        "## 🔍 怎么读",
        "",
        "- **TLDR**：一句话告诉你这篇做了什么",
        "- **Trick**：核心技术 trick，看完决定要不要精读",
        "- **Framework 图**：自动从 PDF 抽取的架构图",
        "- **Tags**：跨日搜索某个主题（用顶栏搜索框）",
        "- **我的评价**：折叠区域，主观判断仅供参考",
        "",
    ]

    index = DOCS / "index.md"
    index.write_text("\n".join(lines), encoding="utf-8")
    log.info(f"Wrote {index} ({len(pages)} historic days)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    update_index()

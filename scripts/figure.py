"""Framework-figure extraction from PDF.

Pipeline:
  1. Download PDF
  2. PyMuPDF extracts all embedded images + nearest caption
  3. Heuristic scoring (caption keywords, page position, size, aspect ratio)
  4. If top-1 dominates → return it.
     Else if VL fallback enabled → ask DeepSeek-VL to pick among top-3.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import List, Optional, Tuple

import fitz  # PyMuPDF
import requests
from openai import OpenAI

log = logging.getLogger(__name__)

FRAMEWORK_KEYWORDS = [
    "framework", "architecture", "overview", "pipeline",
    "system overview", "our approach", "our method", "our model",
    "proposed method", "proposed approach", "proposed framework",
    "schematic", "illustration of",
]

EXCLUDE_KEYWORDS = [
    "qualitative results", "qualitative example", "qualitative comparison",
    "ablation", "loss curve", "training curve", "scaling law",
]


def download_pdf(url: str, dest: Path, timeout: int = 60) -> bool:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "embodied-arxiv-bot/1.0"})
        r.raise_for_status()
        dest.write_bytes(r.content)
        return True
    except Exception as e:
        log.warning(f"PDF download failed: {url}: {e}")
        return False


def _gather_captions(page) -> List[Tuple[float, str]]:
    """Return list of (y0, caption_text) for figure/table captions on the page."""
    out = []
    blocks = page.get_text("blocks")
    for b in blocks:
        if len(b) < 5:
            continue
        x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4]
        t = text.strip().replace("\n", " ")
        if re.match(r"^(Fig(ure)?\.?\s*\d+|图\s*\d+)", t, re.IGNORECASE):
            out.append((y0, t))
    return out


def extract_figures(pdf_path: Path, min_kb: int = 5) -> List[dict]:
    """Return list of figure dicts: {page, area, width, height, caption, bytes}."""
    figures = []
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        log.warning(f"Open PDF failed: {e}")
        return figures

    for page_num, page in enumerate(doc, start=1):
        captions = _gather_captions(page)
        try:
            images = page.get_images(full=True)
        except Exception:
            continue

        for img in images:
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha >= 4:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                if pix.width < 100 or pix.height < 100:
                    continue
                img_bytes = pix.tobytes("png")
                if len(img_bytes) < min_kb * 1024:
                    continue

                # Find caption immediately below image
                rects = page.get_image_rects(xref)
                img_y_bottom = rects[0].y1 if rects else 0
                caption_text = None
                best_dy = 1e9
                for cy, ctext in captions:
                    dy = cy - img_y_bottom
                    if 0 <= dy < best_dy:
                        best_dy = dy
                        caption_text = ctext

                figures.append({
                    "page": page_num,
                    "width": pix.width,
                    "height": pix.height,
                    "area": pix.width * pix.height,
                    "caption": caption_text,
                    "bytes": img_bytes,
                })
            except Exception as e:
                log.debug(f"Skip xref {xref}: {e}")

    doc.close()
    return figures


def score_figures_heuristic(figures: List[dict]) -> List[Tuple[float, dict]]:
    """Higher score = more likely the framework/architecture figure."""
    scored = []
    for f in figures:
        s = 0.0

        # Page position: 2-4 is typical for architecture figure
        if f["page"] in (2, 3):
            s += 4
        elif f["page"] == 4:
            s += 2
        elif f["page"] in (1, 5):
            s += 1

        cap = (f.get("caption") or "").lower()

        # Caption keyword bonuses
        if any(kw in cap for kw in FRAMEWORK_KEYWORDS):
            s += 10
        if any(kw in cap for kw in EXCLUDE_KEYWORDS):
            s -= 5

        # Figure number: 1 > 2 > others
        m = re.search(r"fig(?:ure)?\.?\s*(\d+)", cap)
        if m:
            n = int(m.group(1))
            if n == 1:
                s += 6
            elif n == 2:
                s += 4
            elif n == 3:
                s += 1

        # Size: prefer larger
        s += min(f["area"] / (400 * 300), 4)

        # Aspect: framework figures often wide
        ar = f["width"] / max(f["height"], 1)
        if ar > 1.6:
            s += 2
        elif ar > 1.2:
            s += 1

        scored.append((s, f))

    scored.sort(key=lambda x: -x[0])
    return scored


def pick_with_vl(top: List[dict], paper: dict, model: str) -> Optional[dict]:
    """DeepSeek-VL fallback to pick from top candidates."""
    if not top:
        return None
    try:
        client = OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com",
        )
        content = [{
            "type": "text",
            "text": f"""候选图来自这篇论文：
标题：{paper['title']}
摘要（节选）：{paper['abstract'][:400]}

请选出最能代表论文方法/系统架构（framework / pipeline / overview）的一张。
严格输出 JSON：{{"choice": 1..{len(top)}, "reason": "≤20字"}}"""
        }]
        for i, fig in enumerate(top, start=1):
            b64 = base64.b64encode(fig["bytes"]).decode()
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            })
            content.append({
                "type": "text",
                "text": f"^ 候选 {i}（page {fig['page']}, caption: {fig.get('caption') or 'N/A'}）",
            })

        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": content}],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=150,
        )
        result = json.loads(resp.choices[0].message.content)
        idx = int(result.get("choice", 1)) - 1
        if 0 <= idx < len(top):
            return top[idx]
    except Exception as e:
        log.warning(f"VL fallback failed ({e}); using heuristic top-1")
    return top[0]


def get_framework_figure(
    paper: dict,
    work_dir: Path,
    use_vl: bool = False,
    vl_model: str = "deepseek-chat",
    min_kb: int = 5,
) -> Optional[dict]:
    """Top-level: returns the chosen figure dict, or None."""
    pdf_path = work_dir / f"{paper['id'].replace('/', '_')}.pdf"
    if not download_pdf(paper["pdf_url"], pdf_path):
        return None

    figs = extract_figures(pdf_path, min_kb=min_kb)
    try:
        pdf_path.unlink()
    except Exception:
        pass

    if not figs:
        return None

    scored = score_figures_heuristic(figs)
    if not scored:
        return None

    top_score = scored[0][0]
    runner_up = scored[1][0] if len(scored) > 1 else -1e9

    # Clear winner — skip VL to save cost
    if top_score - runner_up >= 5:
        return scored[0][1]

    if use_vl:
        top_candidates = [f for _, f in scored[:3]]
        return pick_with_vl(top_candidates, paper, vl_model)

    return scored[0][1]


def get_all_figures(paper: dict, work_dir: Path, min_kb: int = 5) -> List[dict]:
    """Return all extracted figures (caller decides what to do with them)."""
    pdf_path = work_dir / f"{paper['id'].replace('/', '_')}.pdf"
    if not download_pdf(paper["pdf_url"], pdf_path):
        return []
    figs = extract_figures(pdf_path, min_kb=min_kb)
    try:
        pdf_path.unlink()
    except Exception:
        pass
    return figs

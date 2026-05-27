"""DeepSeek-V4 scoring + Chinese summarization."""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

from openai import OpenAI

log = logging.getLogger(__name__)


def _client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set in environment")
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


SCORE_SYS = """你是具身智能（Embodied AI）领域的资深审稿人。
任务：阅读论文标题 + 摘要，判断它与具身智能的相关度（0-10 分）。

具身智能涵盖：VLA (Vision-Language-Action)、world model、3D foundation model for embodied (VGGT/DUSt3R/Spann3R 类、scene representation、视觉几何基础模型)、diffusion policy、机器人操作 (manipulation)、抓取、导航、locomotion、humanoid、四足、灵巧手、sim2real、模仿学习、机器人强化学习、whole-body control、tactile、teleoperation。

评分锚点：
- 9-10: 核心做具身/机器人，方法或结果直接推进领域
- 7-8: 强相关，可直接迁移到机器人场景
- 5-6: 一般相关，技术有启发
- 3-4: 弱相关，仅边缘提及
- 0-2: 不相关

**严格红线（必须低分）**：
- 通用 VLM / MLLM 训练或评测、不专门面向具身任务 → ≤ 4 分
- 纯 3D 重建 / Gaussian Splatting / NeRF / 视频生成，没有机器人下游 → ≤ 4 分
- 通用目标检测 / 分割 / 跟踪，即使数据可能用在机器人上 → ≤ 4 分
- 自动驾驶（除非用机器人本体平台） → ≤ 5 分
- 医疗影像 / 手术机器人之外的医学 AI → ≤ 3 分
- 纯仿真物理 / 图形学，不涉及策略学习 → ≤ 5 分

**例外加分项**：
- 3D foundation model（VGGT/DUSt3R/Spann3R/scene representation 等）**明确服务于具身/机器人下游** → 7-9 分（topic 标 `3d-foundation`）
- VLA、world model 类的核心论文 → 优先 9-10 分

输出严格 JSON：
{"score": 数字, "topic": "VLA|world-model|3d-foundation|policy-learning|manipulation|navigation|locomotion|sim2real|grasping|teleoperation|tactile|humanoid|other", "reason": "≤30字的判定理由"}"""


SUMMARY_SYS = """你是一个**毒舌但眼光极准**的具身智能论文审稿人 —— 像见多识广、对灌水零容忍的 senior researcher。
用户研究方向：VLA / world model / 3D foundation model (VGGT 类) / diffusion policy / 具身智能整体。

## 5 条铁律（防幻觉，必守）
1. **不要声称"只在 simulation 做实验"** —— 除非摘要明确说没 real-world
2. **不要声称"翻版/换皮 X"** —— 除非能从摘要指出方法层面的具体相同点
3. **不要编造缺陷**（"没 ablation"、"没 baseline"、"实验不够"）—— 除非摘要明确没有
4. **不确定的事用"摘要未提及"或"需看全文确认"**，不要用肯定语气描述
5. **即使论文很强，也必须找一个值得质疑的点** —— 拒绝"总体而言贡献度较高"这种和稀泥废话

## 字段说明（严格 JSON 输出）

1. **tldr**: 一句话讲清"做了什么"（≤35 字，名词性短句）

2. **tricks**: 关键技术 trick 列表，3-6 条
   - 最核心那条标记 `core: true`（撑起整篇贡献的关键点）
   - 其余标记 `core: false`
   - 顺序：core 第一，其余按重要性
   - 每条 1-2 句话，讲清"做了什么 + 为什么有效"

3. **abstract_zh**: 摘要中文翻译（4-6 句，忠实于原文，不发挥）

4. **related**: 与已有方法的关系与对比（2-3 句）
   - 可以提及具体方法名（OpenVLA / Diffusion Policy / DreamerV3 / VGGT / GR00T 等）但需明确"借鉴"还是"对比"
   - 不确定就用"与传统模仿学习相比……"等泛指

5. **verdict**: 从这 7 个 emoji 选 1 个作为总体判决：
   - 🔥 强推 —— 罕用，留给真正突破（新范式 / 大幅 SOTA / 极强 insight）
   - 👀 值得关注 —— 常用，有意思，方向对，有学习价值
   - ⚠️ 有硬伤但方向对 —— 思路有趣但执行有问题
   - 🫠 incremental / 一般般 —— 小改进、不痛不痒
   - 💀 灌水 —— 没什么价值
   - 🤡 标题党 / 夸大其词 —— claim 站不住
   - 💤 跟具身智能无关 —— 兜底用

6. **critique**: 2-4 句毒舌锐评
   - 夸要具体：哪个数字强、哪个设计有新意、哪个 insight 锐
   - 骂要更具体：哪个假设不成立、哪个实验缺了、哪个 claim 站不住
   - 用句号表达冷静的杀伤力，不要用感叹号
   - 即使强论文也必须找一个值得质疑的点

7. **tags**: 3-5 个英文小写标签（如 `diffusion-policy`, `vla`, `3d-foundation`）

8. **venue**: 如果论文（看 abstract / comment / journal_ref）明确提到接收或发表于某会议/期刊，输出该字符串（如 "ICML 2026" / "TPAMI" / "NeurIPS 2025" / "CoRL 2026"）；否则 null

严格输出 JSON：
{
  "tldr": "...",
  "tricks": [{"text": "...", "core": true}, {"text": "...", "core": false}],
  "abstract_zh": "...",
  "related": "...",
  "verdict": "👀",
  "critique": "...",
  "tags": ["..."],
  "venue": null
}"""


BRIEFING_SYS = """你是具身智能领域的资深观察者。
我会给你今天精选的论文列表（每篇含 title / verdict / topic / tldr / core_trick）。
你写一段 **100-150 字** 中文简报（自然段，不要 bullet），告诉读者：

1. 今天哪个方向最热闹/有突破（具体方向名，不要泛泛）
2. 1-3 篇最值得精读的（点名 + 一句话原因）
3. 整体趋势判断（一句话，要有态度）

要求：
- 有判断、有态度，不要"今天的论文涵盖了多个方向"这种和稀泥废话
- 100-150 字，自然段
- 如果今天有 🔥 论文，必须点名
- 如果某方向出现 ≥3 篇相关论文，可以判断"今天 X 方向集中爆发"

直接输出简报文本（不要 JSON，不要 markdown 标题）。"""


def _extract_json(text: str) -> dict:
    """Robust JSON extraction (handles code fences)."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def score_paper(paper: dict, model: str = "deepseek-chat") -> dict:
    """Return {score, topic, reason}."""
    user = f"Title: {paper['title']}\n\nAbstract: {paper['abstract']}"
    resp = _client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SCORE_SYS},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=200,
    )
    raw = resp.choices[0].message.content
    data = _extract_json(raw)
    return {
        "score": float(data.get("score", 0)),
        "topic": data.get("topic", "other"),
        "reason": data.get("reason", ""),
    }


def summarize_paper(paper: dict, model: str = "deepseek-chat") -> dict:
    """Return {tldr, tricks[list], abstract_zh, related, tags, comment, venue}."""
    user_parts = [
        f"Title: {paper['title']}",
        f"Abstract: {paper['abstract']}",
    ]
    if paper.get("comment"):
        user_parts.append(f"arXiv Comment: {paper['comment']}")
    if paper.get("journal_ref"):
        user_parts.append(f"Journal Ref: {paper['journal_ref']}")
    user = "\n\n".join(user_parts)

    resp = _client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SUMMARY_SYS},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=1500,
    )
    raw = resp.choices[0].message.content
    data = _extract_json(raw)

    # Normalize tricks: ensure list of {text, core} dicts
    tricks_raw = data.get("tricks") or []
    tricks = []
    for t in tricks_raw:
        if isinstance(t, dict):
            tricks.append({"text": str(t.get("text", "")).strip(),
                           "core": bool(t.get("core", False))})
        elif isinstance(t, str):
            tricks.append({"text": t.strip(), "core": False})
    # Ensure at least one is marked core
    if tricks and not any(t["core"] for t in tricks):
        tricks[0]["core"] = True

    return {
        "tldr": data.get("tldr", paper["title"][:35]),
        "tricks": tricks,
        "abstract_zh": data.get("abstract_zh", ""),
        "related": data.get("related", ""),
        "verdict": data.get("verdict", "👀"),
        "critique": data.get("critique", "") or data.get("comment", ""),
        "tags": data.get("tags", [])[:6],
        "venue": data.get("venue") or None,
    }


def generate_briefing(papers: list, model: str = "deepseek-chat") -> str:
    """Generate a 100-150 char Chinese daily briefing from qualified papers."""
    items = []
    for p in papers:
        s = p.get("summary", {})
        core_trick = ""
        for t in s.get("tricks", []):
            if t.get("core"):
                core_trick = t.get("text", "")
                break
        items.append({
            "title": p.get("title", ""),
            "topic": p.get("topic", "other"),
            "verdict": s.get("verdict", "👀"),
            "tldr": s.get("tldr", ""),
            "core_trick": core_trick[:100],
        })

    payload = json.dumps(items, ensure_ascii=False, indent=2)
    try:
        resp = _client().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": BRIEFING_SYS},
                {"role": "user", "content": f"今日 {len(papers)} 篇精选：\n\n{payload}"},
            ],
            temperature=0.4,
            max_tokens=500,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        log.warning(f"briefing generation failed: {e}")
        return ""

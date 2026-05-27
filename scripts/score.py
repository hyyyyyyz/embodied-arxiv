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

具身智能涵盖：VLA (Vision-Language-Action)、机器人操作 (manipulation)、抓取 (grasping)、导航 (navigation)、locomotion、humanoid、四足、灵巧手、sim2real、世界模型 (world model)、扩散策略 (diffusion policy)、模仿学习、机器人强化学习、whole-body control、tactile sensing、teleoperation、mobile manipulation。

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

输出严格 JSON：
{"score": 数字, "topic": "VLA|manipulation|navigation|locomotion|world-model|sim2real|grasping|teleoperation|policy-learning|tactile|humanoid|other", "reason": "≤30字的判定理由"}"""


SUMMARY_SYS = """你是具身智能领域的论文阅读助手。读完论文标题 + 摘要（如有 comment/journal_ref 也参考），输出**结构化中文笔记 JSON**。

字段说明：
1. tldr: 一句话讲清"做了什么"（≤35 字，名词性短句）
2. tricks: 列出论文中**所有**关键技术 trick / insight，5-10 条；每条用 1-2 句话讲清"做了什么 + 为什么有效"
   - 其中**最核心的那一条**（撑起整篇论文贡献的关键点）标记 `core: true`
   - 其余标记 `core: false`
   - 顺序：core 那条放第一，其他按重要性降序
3. abstract_zh: 摘要的中文翻译（4-6 句，覆盖问题/方法/实验/结论；忠实于原文，不发挥）
4. related: 与该方向已有方法的**关系与对比**（2-3 句，描述思路差异点；避免具体引用论文名以防幻觉，可说"与传统模仿学习方法相比……" 这种泛指）
5. tags: 3-5 个英文小写标签
6. comment: 你的判断（2-3 句，是否值得精读 / 贡献度评价）
7. venue: 如果标题/摘要/comment/journal_ref 明确提到论文被接收或发表于某会议/期刊，输出该字符串（格式："ICML 2026" / "TPAMI" / "NeurIPS 2025" / "ICRA 2026" 等）；如果没有明确提及，输出 null

严格输出 JSON：
{
  "tldr": "...",
  "tricks": [
    {"text": "核心 trick...", "core": true},
    {"text": "次要 trick...", "core": false}
  ],
  "abstract_zh": "...",
  "related": "...",
  "tags": ["..."],
  "comment": "...",
  "venue": "ICML 2026" 或 null
}"""


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
        "tags": data.get("tags", [])[:6],
        "comment": data.get("comment", ""),
        "venue": data.get("venue") or None,
    }

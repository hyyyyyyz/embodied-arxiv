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


SUMMARY_SYS = """你是具身智能领域的论文阅读助手。读完论文摘要后，输出**结构化中文笔记**。

要求：
1. tldr: 一句话讲清"做了什么"（≤35 字，名词性短句即可）
2. trick: **核心技术 trick / 关键 insight**，告诉读者"为什么这篇能 work / 跟过去工作的本质区别在哪"（2-4 句，技术干货为主，避免空话）
3. summary: 中文翻译摘要，3-5 句，覆盖问题、方法、实验、结论
4. tags: 3-5 个英文小写标签，便于检索（如 "diffusion-policy", "vla", "sim2real"）
5. comment: 你的判断："是否值得精读"、"贡献度"、"与已有工作对比"（2-3 句）

严格输出 JSON：
{"tldr": "...", "trick": "...", "summary": "...", "tags": ["...", "..."], "comment": "..."}"""


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
    """Return {tldr, trick, summary, tags, comment}."""
    user = f"Title: {paper['title']}\n\nAbstract: {paper['abstract']}"
    resp = _client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SUMMARY_SYS},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=900,
    )
    raw = resp.choices[0].message.content
    data = _extract_json(raw)
    return {
        "tldr": data.get("tldr", paper["title"][:35]),
        "trick": data.get("trick", ""),
        "summary": data.get("summary", paper["abstract"][:300]),
        "tags": data.get("tags", [])[:6],
        "comment": data.get("comment", ""),
    }

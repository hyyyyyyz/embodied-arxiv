---
title: 关于
outline: false
---

# 关于 embodied-arxiv

## 这是什么

**embodied-arxiv** 每天自动从 arXiv 抓取**具身智能（Embodied AI）**相关的新论文，调用 DeepSeek V4 生成中文摘要、提炼核心 trick、给毒舌锐评，并用 PyMuPDF + 启发式自动抽取论文中的 framework 图，部署为 VitePress 静态站点。

## 数据流

```
GitHub Actions（cron 02:00 UTC = 10:00 北京）
    ↓
fetch.py      arXiv API → 候选论文（去重 + 关键词过滤）
    ↓
score.py      DeepSeek V4 评分（perception/通用 CV 严格红线）
    ↓
score.py      DeepSeek V4 中文笔记（多 tricks / 中英文 / 毒舌锐评 / 简报）
    ↓
openreview_venue.py    OpenReview 查会议（覆盖 LLM 猜的 venue）
    ↓
figure.py     PyMuPDF 抽图 + 启发式选 framework
    ↓
build.py      生成 VitePress 内容 + stats.json
    ↓
npm run docs:build → GitHub Pages
```

## 标签体系

**优先类**（评分门槛 ≥6.0，多放一些）：

- 🟣 **VLA**: Vision-Language-Action 模型
- 🟪 **world-model**: 世界模型 / WAM
- 🔵 **3d-foundation**: VGGT / DUSt3R / scene representation 类
- 🔴 **policy-learning**: Diffusion policy / 模仿学习 / RL

**标准类**（评分门槛 ≥7.5，只留高质量）：

- 🟠 manipulation / 🟢 navigation / 🩵 locomotion / 🟡 grasping
- 🔵 sim2real / 🩷 teleoperation / 💗 tactile / 🔷 humanoid
- 灰色 other

## Verdict 判决系统

每篇必须给一个 emoji 判决，秒判优劣：

- 🔥 **强推** —— 罕用，留给真正突破
- 👀 **值得关注** —— 方向对，有学习价值
- ⚠️ **有硬伤但方向对**
- 🫠 incremental / 一般般
- 💀 灌水
- 🤡 标题党
- 💤 跟具身智能无关

## 字段说明

每篇笔记包含：

1. **TLDR** —— 一句话讲清"做了什么"
2. **关键 Tricks** —— 3-6 条，核心那条带 ⭐ 核心 徽章
3. **中文摘要** —— 忠实翻译
4. **English original** —— arXiv 原文，可折叠
5. **与已有工作的关系** —— 思路对比，避免幻觉
6. **🔪 锐评** —— 毒舌但准的 senior researcher 视角

## Fork 追自己方向

仓库 MIT 开源：[github.com/hyyyyyyz/embodied-arxiv](https://github.com/hyyyyyyz/embodied-arxiv)

1. 改 `config.yaml` 里的 `categories` + `keywords` + `priority_topics`
2. 改 `scripts/score.py` 里两个 system prompt（你领域的知识）
3. 在 fork 的 repo 加 `DEEPSEEK_API_KEY` secret
4. 启用 GitHub Pages（Source: GitHub Actions）

## 鸣谢

- 论文数据：[arXiv.org](https://arxiv.org)
- 会议数据：[OpenReview](https://openreview.net)
- LLM：[DeepSeek](https://www.deepseek.com)
- PDF 解析：[PyMuPDF](https://pymupdf.readthedocs.io)
- 站点框架：[VitePress](https://vitepress.dev/)

## 免责声明

本站所有 AI 生成的中文摘要、trick 提炼、毒舌锐评仅供参考，可能存在误读。研究决策请以原论文为准。

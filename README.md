# Embodied arXiv 雷达

> 每日自动抓取 arXiv 上**具身智能（Embodied AI）**相关论文 → DeepSeek V4 生成中文摘要 + 核心 Trick 提炼 + 自动抽取 Framework 图 → 部署为 GitHub Pages 静态网站。

[![Daily digest](https://github.com/hyyyyyyz/embodied-arxiv/actions/workflows/daily.yml/badge.svg)](https://github.com/hyyyyyyz/embodied-arxiv/actions/workflows/daily.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Site](https://img.shields.io/badge/site-online-brightgreen)](https://hyyyyyyz.github.io/embodied-arxiv/)

🌐 **在线访问**：<https://hyyyyyyz.github.io/embodied-arxiv/>

---

## ✨ 它做什么

- ⏰ 每天北京时间 **10:00** 自动跑（arXiv 美东 20:00 放新论文）
- 🎯 覆盖 `cs.RO` 全量 + `cs.AI / cs.CV / cs.LG` 中含 VLA / manipulation / navigation 等关键词的论文
- ⭐ DeepSeek V4 对每篇 0-10 分相关性评分，只保留 ≥ 6 分的
- 📝 每篇生成：**TLDR / Trick / 中文摘要 / Tags / 我的评价**
- 🖼 PyMuPDF + 启发式自动抽取 **framework 图**（可选 DeepSeek-VL 兜底）
- 🆓 部署 100% 免费：GitHub Actions（150 min/月）+ GitHub Pages
- 🔌 配置驱动：改 `config.yaml` 就能换成自己研究方向的雷达

---

## 🏗 架构

```
GitHub Actions (cron 02:00 UTC)
    │
    ├─ fetch.py    arXiv API → 候选论文（去重）
    ├─ score.py    DeepSeek V4 评分 + 中文摘要
    ├─ figure.py   PyMuPDF 抽图 → 启发式选 framework 图
    ├─ build.py    生成 docs/papers/YYYY-MM-DD.md
    ├─ git commit & push（增量更新 docs/ 和 data/）
    ├─ mkdocs build → site/
    └─ deploy-pages → <user>.github.io/embodied-arxiv
```

**核心理念**：静态网站 + build-time AI 计算。访问网页时**零计算、零延迟、零成本**。

---

## 🚀 快速搭建（fork 用户）

### 1. Fork & 修改

```bash
# 在 GitHub 上 fork 这个 repo
git clone https://github.com/<你的用户名>/embodied-arxiv.git
cd embodied-arxiv
```

编辑 `config.yaml`：把 `keywords` 改成你方向的关键词；如果不是机器人，把 `categories.primary` 也换掉。
编辑 `scripts/score.py`：把两个 system prompt 中的"具身智能"换成你的领域。

### 2. 配置 Secret

GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**：
- Name: `DEEPSEEK_API_KEY`
- Value: 你在 [platform.deepseek.com](https://platform.deepseek.com) 拿到的 API key（建议为这个项目单独建一个）

### 3. 启用 GitHub Pages

GitHub repo → **Settings** → **Pages**：
- **Source**: `GitHub Actions`（不是 `Deploy from a branch`）

### 4. 修改 `mkdocs.yml` 中的 URL

把 `site_url` 和 `repo_url` 换成你自己的。

### 5. 触发首次运行

- GitHub repo → **Actions** → 选 `Daily arXiv Digest` → **Run workflow**
- 等 3-5 分钟，访问 `https://<你的用户名>.github.io/<repo-name>/`

---

## 🔧 本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API key（本地用 .env，git 已忽略）
cp .env.example .env
echo "DEEPSEEK_API_KEY=sk-your-real-key" > .env

# 3. 本地跑一次
python scripts/run.py

# 4. 本地预览
mkdocs serve   # 打开 http://127.0.0.1:8000
```

---

## ⚙️ 配置项

`config.yaml` 关键字段：

| 字段 | 作用 |
|---|---|
| `arxiv.categories.primary` | 这些分类的论文全部保留（默认只 `cs.RO`） |
| `arxiv.categories.secondary` | 这些分类的论文必须命中 `keywords` 才保留 |
| `arxiv.keywords` | 关键词列表，大小写不敏感 |
| `arxiv.lookback_days` | 抓取最近 N 天的论文（默认 2，覆盖周末） |
| `scoring.min_score` | 评分门槛（默认 6.0） |
| `scoring.max_published` | 每日发布上限（默认 25） |
| `figure.enable_vl_fallback` | 启发式打分接近时是否调多模态兜底（默认 false） |
| `figure.vl_model` | 多模态模型名（默认 `deepseek-chat`，需 DeepSeek 开放 VL API） |

---

## 💰 成本估算

| 项目 | 用量 | 月费 |
|---|---|---|
| GitHub Actions | ~5 min/天 = 150 min/月（免费 2000 min） | $0 |
| GitHub Pages | 免费 | $0 |
| DeepSeek V4 评分 + 摘要 | ~$0.04/天 | **~$1.2** |
| DeepSeek-VL 兜底（可选） | ~$0.12 | （如启用） |
| **合计** | | **~$1.2/月** |

---

## 🔒 关于 API key 安全

- `DEEPSEEK_API_KEY` 只存在两个地方：DeepSeek 控制台 + GitHub Secrets（加密存储）
- 本地 `.env` 在 `.gitignore` 内，永不进 git
- GitHub Actions 日志自动脱敏（即使代码 `print(api_key)` 也只显示 `***`）
- Fork PR 默认拿不到 secret，防恶意 PR 偷 key

---

## 📜 License

MIT — 自由 fork、修改、商用。

---

## 🙏 致谢

- 论文数据：[arXiv.org](https://arxiv.org)
- LLM：[DeepSeek](https://www.deepseek.com)
- PDF 解析：[PyMuPDF](https://pymupdf.readthedocs.io)
- 站点：[MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
- 灵感：[arxiv-sanity](https://arxiv-sanity-lite.com)、[Hugging Face Daily Papers](https://huggingface.co/papers)

---
name: research-assistant
description: 每日具身智能 arXiv 论文跑批 — fetch → Claude 阅读 → 同步 Obsidian + GitHub Pages 部署。覆盖 VLA / World Model / WAM / VGGT / 多模态 五个方向。User triggers daily; reads abstracts in chat, scores them, writes Chinese highlights, pushes to https://hyyyyyyz.github.io/embodied-arxiv/. No remote LLM API in the runtime — Claude is the reading layer.
argument-hint: [date | --rerun | --skip-build | --skip-venue]
allowed-tools: Bash(*), Read, Write, Edit, Glob, Grep
---

# /research-assistant — Daily embodied-AI digest

User input: `$ARGUMENTS`

You are running the daily research digest for **`hyyyyyyz/embodied-arxiv`**.
The repo lives at **`/Users/jacksonhuang/project/arxiv_ws`**. From now on,
use absolute paths or `cd` to that repo at every step.

## 1 — Parse arguments

Argument shapes you might see:

- *(empty)* → use today's UTC announcement date (or yesterday if before 02:00 UTC).
- `2026-06-01` → use this date explicitly.
- `--rerun` (optionally with a date) → ignore `data/seen.json` when fetching.
- `--skip-venue` → skip Semantic Scholar / DBLP lookup.
- `--skip-build` → write cards + web JSON + obsidian, but don't run the Next.js build.

Compute:

```bash
TARGET_DATE=<resolved YYYY-MM-DD>    # echo to confirm
```

If the user said only "继续" or "今天的论文" or similar, fall back to today.

## 2 — Fetch arxiv candidates

```bash
cd /Users/jacksonhuang/project/arxiv_ws
python3 scripts/fetch_arxiv.py --date "$TARGET_DATE" [--ignore-seen]
```

This writes `data/raw/$TARGET_DATE.json`. Read its `papers[]` array.

If the count is 0 (arxiv announcement was empty / weekend / dedup ate
everything), tell the user, ask whether to widen the window (`--days 3`),
and stop.

If the count is ≥ 60 you've hit the cap. That's fine — config caps to keep
the daily list focused; tell the user the cap fired and continue.

## 3 — Look up conference venues (optional but default-on)

```bash
python3 scripts/lookup_venue.py --date "$TARGET_DATE"
```

This patches each paper with `"venue": "..."` or `null`. The script is
re-run-safe — papers already filled are skipped. Use `--skip-dblp` if
DBLP is rate-limiting you. Skip the whole step if the user said
`--skip-venue` or if the network is flaky (the dashboard handles a
missing venue gracefully — the badge just disappears).

## 4 — Read & score each paper (the actual Claude work)

For every paper in `data/raw/$TARGET_DATE.json`, produce one card entry.
Collect them in a JS array and `Write` the final list to
`data/cards/$TARGET_DATE.json`.

### Card schema

```json
{
  "arxiv_id": "2606.00001",
  "summary": "中文 2–4 句话总结：动机 → 方法 → 结果。读起来要像同事跟你聊到这篇 paper，别复制摘要。",
  "highlights": {
    "contribution": "核心贡献：一句话讲清楚作者声称解决了什么。",
    "innovation":   "创新点：相对已有工作的关键差异（取最关键的 1–2 点）。",
    "method":       "方法概要：实际怎么做的 — 输入 / 模型 / 损失 / 训练设置。",
    "results":      "关键结果：在哪个 benchmark 上、提升了多少、是否 SOTA。"
  },
  "scores": {
    "relevance": 8.5,
    "recency":   10,
    "popularity": 6,
    "quality":   8,
    "recommendation": 8.2
  },
  "affiliations": ["Stanford", "Google DeepMind"]
}
```

- `summary` — **中文，自然口语化**。不要逐句翻译摘要。
- `highlights.*` — 每条 1–3 句，中文。`method` 不写公式，写读者要点。
- `scores` — 0–10 整数或一位小数。`recommendation` 是你给出的加权综合分，是唯一会出现在卡片角标和列表里的分数。
  - **relevance**：跟用户兴趣方向（VLA / World Model / WAM / VGGT / 多模态）的贴合度
  - **recency**：基本就是 10（今天发的）；旧文回填时按周衰减到 5
  - **popularity**：从 author / lab / 引用势头估，未知给 5–6
  - **quality**：写作清晰度 + 实验完整度
  - **recommendation**：你的总评，**别全给 7**——区分度本身就是信号
- `affiliations` — 看摘要 / 作者 metadata 时如果能从 footer 或第一作者推出来就填，没有就留空数组（`fetch_arxiv.py` 不会自动填）。

### 阅读顺序

按 `matched_domain` 分组依次读：先读 VLA → World Model → WAM → VGGT → 多模态。
同方向内按推荐分高 → 低或时间新 → 旧。读完一个方向汇报一次进度。

### 量大时怎么办

- 如果当日 ≤ 20 篇：一篇一篇线性读、写。
- 如果当日 > 20 篇：用 **Agent (Explore 子代理)** 并行分批阅读，每批 6–10 篇。
  - 给子代理传：raw json 中那一批的 paper 数组 + 卡片 schema + 评分规则
  - 让子代理直接 `Write` `data/cards/$TARGET_DATE.json.partial.N`
  - 主对话最后合并成完整 cards 文件
  - 这是用户明确要求的工作模式（Claude Max 不在乎 token 量）

### 输出位置

最终落盘：

```
data/cards/$TARGET_DATE.json   # 一个 JSON 数组，包含所有 card
```

`build_web_data.py` 也接受形如 `{"cards": [...]}` 的容器，但纯数组更省事。

## 5 — Build web JSON + Obsidian markdown

```bash
python3 scripts/build_web_data.py --date "$TARGET_DATE"
```

这一步会：
- 把 raw + cards 合成 `web/public/data/papers/$TARGET_DATE.json`
- 重建 `web/public/data/index.json`（扫描全部已发布日期）
- 写 `$OBSIDIAN_ROOT/DailyPapers/$TARGET_DATE.md`（覆盖）
- 写 `$OBSIDIAN_ROOT/Papers/<arxiv_id>.md`（**已存在的不覆盖**，保留人工注释）

Obsidian 根目录默认是 `/Users/jacksonhuang/ObsidianVault-arxiv/embodied-arxiv`，
不存在就跳过 md 同步（脚本会打印一条警告，不中断）。

## 6 — Build the static export (unless `--skip-build`)

```bash
cd /Users/jacksonhuang/project/arxiv_ws/web
npm ci --no-audit --no-fund      # only first run / after package.json edit
npm run build
```

Pass `NODE_ENV=production` is set by `npm run build` itself in Next 16, so no
extra envs. Build outputs to `web/out/`. If TypeScript or ESLint fails,
**fix the actual code**, don't `--no-verify`.

If the user said `--skip-build`, skip this — CI will rebuild on push anyway.

## 7 — Commit + push (ask before pushing)

```bash
cd /Users/jacksonhuang/project/arxiv_ws
git status
git diff --stat
```

Show the user the changeset summary (新增日期、论文数、覆盖方向分布)，然后问是否提交。
拿到同意后：

```bash
git add web/public/data data/raw data/cards data/seen.json scripts/ .github/workflows/ 2>/dev/null
# 也可以一次性：git add -A 但要先看清楚 git status，避免误传 web/out 之类
git commit -m "$(cat <<'EOF'
📰 Daily digest <TARGET_DATE> · <N> papers (<dir-breakdown>)

🤖 Generated with Claude Code (/research-assistant)
EOF
)"
git push
```

注意：
- `web/out/` 在 `.gitignore` 里，**不要提交**。CI 自己重新构建。
- `data/seen.json` 必须提交，否则下次 fetch 会重新拉一遍同样的论文。
- Obsidian 仓库不在这个 git 里，不需要也不能 `git add`。

## 8 — Report

最后给用户一段中文小结：
- 当日处理多少篇、各方向分布
- 推荐分 ≥ 8 的论文标题（≤ 5 篇）
- 在线地址：**https://hyyyyyyz.github.io/embodied-arxiv/**（push 后约 1–2 分钟 CI 部署）
- Obsidian 入口：`DailyPapers/$TARGET_DATE.md`
- 如果 venue lookup 命中很少，提醒用户多数预印本就是没接收 → 这是正常的

## 失败处理 / 常见状态

- **arxiv 拉取 0 篇**：周末或刚停摆，建议 `--days 3` 跑回填。
- **lookup_venue 卡住**：S2 限流；`--sleep 3.0` 或直接 `--skip-venue`。
- **某篇 card 写不全**（缺 highlights.results）：`build_web_data.py` 会自动跳过并打印警告。补全后重跑即可。
- **`npm run build` 失败**：读错误信息修代码；常见原因是新增 paper 字段没在 types.ts 反映。
- **重复运行同一天**：`data/seen.json` 让 fetch 直接拿到 0 篇 → 用 `--rerun` (传 `--ignore-seen`) 强制重抓。
- **想强制重建 index 但不重抓**：`python3 scripts/build_web_data.py --date <日期>` 单独跑就行。

## 永远不做的事

- ❌ 调任何远端 LLM API（DeepSeek/GPT/Gemini）。Claude **本对话**就是阅读层。
- ❌ 改 `web/src/lib/api.ts` 让它发 HTTP 到外部服务。整站是 static export。
- ❌ `git push --force` / `--no-verify` / `--amend` 已 push 的 commit。
- ❌ 自动 push 不先问用户。
- ❌ 修 `scripts/config.py` 的 `DIRECTIONS` 列表除非用户明确要调整覆盖面。

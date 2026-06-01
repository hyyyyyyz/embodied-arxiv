# embodied-arxiv

> 每日具身智能 arXiv 论文 · Claude Code 阅读 · Tinder 风格 swipe 浏览

**在线地址 👉 https://hyyyyyyz.github.io/embodied-arxiv/**

每天清晨你在 Claude Code 里敲一句 `/research-assistant`，它会：

1. 从 arXiv 拉当天的新论文（按关键词命中过滤）
2. **Claude（就是当前对话）在 chat 里逐篇读摘要**，写中文总结 + 4 项 highlight + 打分
3. 同步到 Obsidian（每日 digest + 单篇 markdown）
4. 静态导出整个 Next.js 站点，push 到 GitHub Pages

**整条流水线运行时不调任何远端 LLM API**（不是 DeepSeek，不是 GPT，不是 Gemini） — 你的 Claude Code 订阅就是阅读层。

---

## 这是怎么跑的

```
                                   你
                                   │
                       /research-assistant
                                   │
                                   ▼
   ┌──────────────────────────────────────────────────────────────┐
   │  Claude Code（本地对话）— 编排 + 阅读 + 评分                  │
   └────────┬──────────────────────────────────────┬──────────────┘
            │                                       │
            ▼                                       ▼
   ┌────────────────────┐                ┌──────────────────────┐
   │ Python 助手 (stdlib)│                │  Obsidian Vault       │
   ├────────────────────┤                │  ├ DailyPapers/       │
   │ fetch_arxiv.py     │ ── arXiv API   │  └ Papers/<id>.md     │
   │ lookup_venue.py    │ ── S2 + DBLP   └──────────────────────┘
   │ build_web_data.py  │
   └─────────┬──────────┘
             ▼
   ┌──────────────────────────────┐         ┌────────────────────────┐
   │ web/public/data/*.json       │  push   │ GitHub Actions          │
   │ (静态 paper JSON + 索引)      │ ──────▶ │ Next.js export → Pages  │
   └──────────────────────────────┘         └────────────────────────┘
```

零运行时 LLM 调用，零云函数 — 一切发生在你本机的 Claude Code 对话里。

## 覆盖的五个研究方向

| | 关键词样例 |
|---|---|
| **VLA** | vision-language-action, OpenVLA, RT-2, π-0, robotic manipulation |
| **World Model** | world model, latent dynamics, video generation for robotics |
| **WAM** | world action model, unified action model |
| **VGGT** | vggt, dust3r/mast3r, feed-forward 3D, gaussian splatting |
| **Multi-modal** | MLLM, VLM, embodied chain-of-thought, spatial reasoning |

全部关键词列表在 [`scripts/config.py`](scripts/config.py) 的 `DIRECTIONS` 里，自己改即可。

---

## 自己跑一个：Fork 后的设置步骤

### 0. 前置依赖

- **Claude Code** 装好且有 Claude Max 订阅（量大管够）
- **Node.js 22+** 装好（webview build 需要）
- **Python 3.10+**（脚本只用 stdlib，不用 pip install）
- **Obsidian**（可选；不装就只有网页，无本地知识库）
- **GitHub 账号** + Pages 开启

### 1. Fork & clone

```bash
git clone git@github.com:<your-username>/embodied-arxiv.git
cd embodied-arxiv
```

### 2. 调整你自己的路径

编辑 [`scripts/config.py`](scripts/config.py):

```python
OBSIDIAN_ROOT = "/path/to/your/ObsidianVault/embodied-arxiv"  # 改成你自己的
```

编辑 [`skills/research-assistant/SKILL.md`](skills/research-assistant/SKILL.md)
里的两个绝对路径：
- `/Users/jacksonhuang/project/arxiv_ws` → 你 clone 出来的路径
- `https://hyyyyyyz.github.io/embodied-arxiv/` → 你自己的 Pages URL

如果你只想要网页不要 Obsidian：不用动 `OBSIDIAN_ROOT`，
路径不存在时 `build_web_data.py` 会自动跳过 md 同步。

### 3. 安装 skill 到 Claude Code

```bash
# macOS / Linux
mkdir -p ~/.claude/skills
ln -s "$PWD/skills/research-assistant" ~/.claude/skills/research-assistant

# 或者直接 cp（之后不会跟着 git pull 自动更新）
# cp -r skills/research-assistant ~/.claude/skills/
```

打开 Claude Code，敲 `/` 应该能看到 `research-assistant`。

### 4. 装 web 依赖

```bash
cd web && npm install
cd ..
```

### 5. 开 GitHub Pages

仓库 Settings → Pages → **Source** 选 **GitHub Actions**（不是 branch）。
之后每次 push 到 `main`，CI 会自动 build + 部署。

### 6. 第一次跑

```
/research-assistant --days 7
```

回填过去一周。Claude 会问你是否 push — 同意后等 1-2 分钟，
Pages 上线。

---

## 日常用法

```
/research-assistant                # 跑今天的论文
/research-assistant --days 3       # 回填过去 3 天
/research-assistant 2026-06-01     # 指定日期
/research-assistant --rerun        # 忽略 data/seen.json 强制重抓
/research-assistant --skip-venue   # 跳过会议查询（S2 限流时）
/research-assistant --skip-build   # 写完数据但不本地 build（CI 反正会重 build）
```

跑完 Claude 会给你：
- 当日论文数 + 方向分布
- 推荐分 ≥ 8 的论文标题
- 是否 push 的确认

push 完就完事了。

---

## 仓库结构

```
embodied-arxiv/
├── web/                      Next.js 16 + React 19 + Tailwind 4
│   ├── public/data/          静态 paper JSON（前端唯一数据源）
│   └── src/
│       ├── app/              4 个路由: /, /papers, /favorites, /settings
│       ├── components/       PaperCard / SwipeContainer / Context / NavBar
│       └── lib/              api.ts (localStorage 层) + i18n + types
├── scripts/                  Python stdlib 助手
│   ├── config.py             方向 + 关键词 + Obsidian 路径
│   ├── fetch_arxiv.py        从 arXiv API 拉候选
│   ├── lookup_venue.py       Semantic Scholar + DBLP 查会议
│   └── build_web_data.py     合并 raw + cards → web JSON + Obsidian md
├── skills/
│   └── research-assistant/SKILL.md   Claude Code skill 定义
├── data/                     每日工作目录（自动生成）
│   ├── raw/<date>.json       arxiv 原始候选
│   ├── cards/<date>.json     Claude 写的中文卡片
│   └── seen.json             已处理 arxiv id 去重表
├── .github/workflows/deploy.yml      Pages 部署
└── README.md                          ← 你正在看
```

## 收藏 / 反馈数据存在哪

**全部在浏览器 localStorage**（key 前缀 `embodied-arxiv/`）。
没有后端，换设备会丢，清缓存会丢。
`/settings` 页有一个"清除全部本地数据"按钮。

## 常见问题

**Q: arxiv 拉到 0 篇？**
A: 周末或节假日 arxiv 不公告。试 `--days 3` 或 `--days 7` 回填。

**Q: 会议查询全是空？**
A: 预印本本来就大多没会议。Semantic Scholar 偶尔 503，等会儿单独跑一次
   `python3 scripts/lookup_venue.py --date <X>` 补即可。

**Q: 想换覆盖方向？**
A: 改 [`scripts/config.py`](scripts/config.py) 的 `DIRECTIONS`。前端的
   `DOMAIN_COLORS` 在 `web/src/components/PaperCard.tsx` 和
   `PaperListItem.tsx`，加新方向时一起加颜色映射。

**Q: 同一篇论文想重新让 Claude 读？**
A: 删掉 `data/cards/<date>.json` 里对应的条目，重跑 `/research-assistant`。
   或整天重跑：`/research-assistant --rerun --date <X>`。

**Q: 不想用 Obsidian？**
A: 不动 `OBSIDIAN_ROOT` 也行，路径不存在脚本会跳过 md 同步。

## License

MIT — 详见 [LICENSE](LICENSE)。

Fork、改、商用都 OK。如果觉得有用麻烦给个 star ⭐。

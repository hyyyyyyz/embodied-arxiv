# 一次性搭建指南

按这个清单走一遍，10 分钟跑起整个雷达。

## ① 推送代码到你刚建的 GitHub repo

假设你已经在 GitHub 上手动创建了空 repo（Public，可以勾上 README 但**不要**勾 .gitignore / LICENSE，避免冲突；其实啥都不勾最干净）：

```bash
cd /Users/jacksonhuang/project/arxiv_ws

# 初始化 git
git init
git branch -M main

# 把本地文件全部加入
git add .
git commit -m "🎉 initial commit: arxiv embodied daily digest"

# 关联远程（注意：如果你 GitHub 上的 repo 已有 README，先 pull --rebase）
git remote add origin https://github.com/hyyyyyyz/embodied-arxiv.git
git push -u origin main
```

如果远程已有 README 报冲突，用：
```bash
git pull --rebase origin main --allow-unrelated-histories
git push -u origin main
```

## ② 配置 GitHub Secret（API key）

1. 打开 <https://github.com/hyyyyyyz/embodied-arxiv/settings/secrets/actions>
2. 点 **New repository secret**
3. Name: `DEEPSEEK_API_KEY`
4. Secret: 粘贴你的 DeepSeek API key（来自 <https://platform.deepseek.com/api_keys>）
5. **Add secret**

> 💡 建议在 DeepSeek 控制台为这个项目**单独**建一个 key，命名 `embodied-arxiv`，方便万一泄漏单独 revoke。

## ③ 启用 GitHub Pages

1. 打开 <https://github.com/hyyyyyyz/embodied-arxiv/settings/pages>
2. **Build and deployment** → **Source** 选 **`GitHub Actions`**（注意不是 `Deploy from a branch`）
3. 保存

## ④ 触发第一次构建

两种方式，任选其一：

**方式 A：等定时任务**
明天北京时间 10:00 会自动跑。

**方式 B：手动触发（推荐先跑一次验证）**
1. 打开 <https://github.com/hyyyyyyz/embodied-arxiv/actions>
2. 左侧选 **Daily arXiv Digest**
3. 右上角 **Run workflow** → **Run workflow**
4. 等 3-5 分钟

## ⑤ 查看结果

构建成功后访问：

🌐 <https://hyyyyyyz.github.io/embodied-arxiv/>

第一次部署可能要等 1-2 分钟 DNS 生效。

---

## 🐛 常见问题排查

### Actions 跑红：`DEEPSEEK_API_KEY not set`
→ 回到 ② 检查 Secret 名字必须**完全**是 `DEEPSEEK_API_KEY`，区分大小写。

### Actions 跑红：`Permission denied (git push)`
→ 打开 <https://github.com/hyyyyyyz/embodied-arxiv/settings/actions>
→ 拉到底 **Workflow permissions** → 选 **Read and write permissions** → 保存

### Pages 404
→ 第一次部署慢，等 5 分钟。仍然 404 检查 ③ 中 Source 是否选了 `GitHub Actions`。

### 想立刻看看本地能跑通吗
```bash
cd /Users/jacksonhuang/project/arxiv_ws
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY=...
python scripts/run.py
mkdocs serve
# 打开 http://127.0.0.1:8000
```

---

## 后续维护

- **每天**：什么都不用做，10:00 自动更新
- **想换关键词 / 主题**：编辑 `config.yaml`，commit & push 即可
- **想加 / 换 LLM**：改 `scripts/score.py` 里的 prompt 或 `_client()` 的 base_url
- **想要更细致的 framework 图选择**：把 `config.yaml` 里 `figure.enable_vl_fallback` 设为 `true`（需 DeepSeek 开放 VL API，或在 `figure.py` 中改用 Qwen-VL / GPT-4o）

有 bug 或想要新功能就在 repo 里开 issue。

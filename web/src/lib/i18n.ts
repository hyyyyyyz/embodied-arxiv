export type Language = "zh" | "en";

const translations: Record<Language, Record<string, string>> = {
  zh: {
    // Nav
    "nav.papers": "论文",
    "nav.favorites": "收藏",
    "nav.settings": "关于",

    // Paper card sections
    "paper.coreContribution": "核心贡献",
    "paper.innovation": "创新点",
    "paper.methodSummary": "方法概要",
    "paper.keyResults": "关键结果",
    "paper.deepDive": "展开详细分析",
    "paper.loadingAnalysis": "正在加载...",
    "paper.venue": "会议",

    // Feedback buttons
    "feedback.like": "喜欢",
    "feedback.neutral": "一般",
    "feedback.dislike": "不感兴趣",
    "feedback.viewOriginal": "原文",

    // Papers page
    "papers.today": "最新",
    "papers.thisWeek": "最近一周",
    "papers.thisMonth": "最近一个月",
    "papers.pickDate": "选日期",
    "papers.allDates": "最新",
    "papers.loadingDate": "正在加载 {date} 的论文...",
    "papers.loadingLatest": "正在加载...",
    "papers.retry": "重试",
    "papers.noResultsDate": "{date} 暂无论文",
    "papers.noResultsLatest": "暂无内容（arxiv 周末停摆中，下次更新等周二早上）",

    // Favorites page
    "favorites.title": "收藏夹",
    "favorites.count": "{count} 篇",
    "favorites.folderName": "文件夹名称",
    "favorites.confirm": "确定",
    "favorites.cancel": "取消",
    "favorites.newFolder": "+ 新建文件夹",
    "favorites.empty": "还没有收藏的论文，去 swipe 几张吧",
    "favorites.dragHint": "拖拽论文到此文件夹",
    "favorites.uncategorized": "未分类",
    "favorites.all": "全部收藏",
    "favorites.removeFavorite": "取消收藏",
    "favorites.rename": "重命名",
    "favorites.deleteFolder": "删除文件夹",

    // About / settings page
    "about.title": "关于 embodied-arxiv",
    "about.tagline": "每日具身智能 arXiv 论文 · Claude 阅读 · Tinder 风格浏览",
    "about.workflow": "工作流",
    "about.workflowDesc":
      "由 /research-assistant skill 每天在 Claude Code 对话里手动执行：拉取当日论文 → Claude 阅读分析 → 同步到 Obsidian + 部署到 GitHub Pages。",
    "about.directions": "覆盖方向",
    "about.directionsList": "VLA · World Model · WAM · VGGT · 多模态",
    "about.appearance": "外观",
    "about.themeLight": "浅色",
    "about.themeDark": "深色",
    "about.themeSystem": "跟随系统",
    "about.language": "语言",
    "about.languageZh": "中文",
    "about.languageEn": "English",
    "about.storage": "本地存储",
    "about.storageDesc":
      "收藏、文件夹、反馈记录全部存在你浏览器的 localStorage，没有任何后端。换设备或清缓存会丢失。",
    "about.clearAllData": "清除全部本地数据",
    "about.confirmClear": "确认清除？此操作不可撤销。",
    "about.source": "源代码",
    "about.lastUpdate": "数据最近更新",
  },
  en: {
    // Nav
    "nav.papers": "Papers",
    "nav.favorites": "Favorites",
    "nav.settings": "About",

    // Paper card sections
    "paper.coreContribution": "Core Contribution",
    "paper.innovation": "Innovation",
    "paper.methodSummary": "Method Overview",
    "paper.keyResults": "Key Results",
    "paper.deepDive": "Expand Analysis",
    "paper.loadingAnalysis": "Loading...",
    "paper.venue": "Venue",

    // Feedback buttons
    "feedback.like": "Like",
    "feedback.neutral": "OK",
    "feedback.dislike": "Not Interested",
    "feedback.viewOriginal": "Paper",

    // Papers page
    "papers.today": "Latest",
    "papers.thisWeek": "Past Week",
    "papers.thisMonth": "Past Month",
    "papers.pickDate": "Pick date",
    "papers.allDates": "Latest",
    "papers.loadingDate": "Loading papers for {date}...",
    "papers.loadingLatest": "Loading...",
    "papers.retry": "Retry",
    "papers.noResultsDate": "No papers for {date}",
    "papers.noResultsLatest":
      "Nothing yet (arXiv pauses on weekends; next batch lands Tuesday morning HKT).",

    // Favorites page
    "favorites.title": "Favorites",
    "favorites.count": "{count} papers",
    "favorites.folderName": "Folder name",
    "favorites.confirm": "OK",
    "favorites.cancel": "Cancel",
    "favorites.newFolder": "+ New Folder",
    "favorites.empty": "No favorites yet — swipe a few papers first.",
    "favorites.dragHint": "Drag papers to this folder",
    "favorites.uncategorized": "Uncategorized",
    "favorites.all": "All Favorites",
    "favorites.removeFavorite": "Remove from favorites",
    "favorites.rename": "Rename",
    "favorites.deleteFolder": "Delete folder",

    // About / settings page
    "about.title": "About embodied-arxiv",
    "about.tagline":
      "Daily embodied-AI arXiv · Claude-read summaries · Tinder-style swipe",
    "about.workflow": "Workflow",
    "about.workflowDesc":
      "A /research-assistant Claude Code skill that runs manually each day: fetch arXiv → Claude reads in chat → sync to Obsidian + deploy to GitHub Pages.",
    "about.directions": "Coverage",
    "about.directionsList": "VLA · World Model · WAM · VGGT · Multi-modal",
    "about.appearance": "Appearance",
    "about.themeLight": "Light",
    "about.themeDark": "Dark",
    "about.themeSystem": "System",
    "about.language": "Language",
    "about.languageZh": "中文",
    "about.languageEn": "English",
    "about.storage": "Local Storage",
    "about.storageDesc":
      "All favorites, folders, and feedback live in your browser's localStorage. No backend. Switching devices or clearing storage wipes them.",
    "about.clearAllData": "Clear all local data",
    "about.confirmClear": "Confirm clear? This cannot be undone.",
    "about.source": "Source code",
    "about.lastUpdate": "Last data refresh",
  },
};

export function translate(
  lang: Language,
  key: string,
  params?: Record<string, string | number>
): string {
  const str = translations[lang]?.[key] ?? translations.zh[key] ?? key;
  if (!params) return str;
  return str.replace(/\{(\w+)\}/g, (_, k) =>
    params[k] !== undefined ? String(params[k]) : `{${k}}`
  );
}

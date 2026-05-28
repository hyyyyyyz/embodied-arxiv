import { defineConfig } from 'vitepress'
import { readdirSync, existsSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))

// Auto-generate the date-list sidebar from docs/papers/<date>/ folders.
// Newest first.
function genPapersSidebar() {
  const papersDir = join(__dirname, '..', 'papers')
  if (!existsSync(papersDir)) return []

  const dates = readdirSync(papersDir, { withFileTypes: true })
    .filter((d) => d.isDirectory() && /^\d{4}-\d{2}-\d{2}$/.test(d.name))
    .map((d) => d.name)
    .sort()
    .reverse()

  return [
    {
      text: '论文归档',
      collapsed: false,
      items: dates.map((d) => ({ text: d, link: `/papers/${d}/` })),
    },
  ]
}

export default defineConfig({
  title: 'embodied-arxiv',
  description: '每日 arXiv 具身智能论文雷达 · DeepSeek V4 中文摘要 + 毒舌锐评 + Framework 图自动抓取',
  lang: 'zh-CN',
  base: '/embodied-arxiv/',
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: true,

  head: [
    ['link', { rel: 'icon', type: 'image/png', sizes: '128x128', href: '/embodied-arxiv/favicon.png' }],
    ['link', { rel: 'icon', type: 'image/png', sizes: '32x32', href: '/embodied-arxiv/favicon-32.png' }],
    ['link', { rel: 'apple-touch-icon', href: '/embodied-arxiv/favicon.png' }],
    ['meta', { name: 'theme-color', content: '#a78bfa' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'embodied-arxiv' }],
    ['meta', { property: 'og:description', content: '每日 arXiv 具身智能论文雷达' }],
    ['meta', { property: 'og:image', content: '/embodied-arxiv/logo.png' }],
  ],

  themeConfig: {
    // The logo image already contains the wordmark "embodied arxiv";
    // hiding siteTitle text avoids visual duplication next to it.
    // (width/height aren't valid ThemeableImage props — size is CSS-driven.)
    logo: { src: '/logo.png', alt: 'embodied-arxiv' },
    siteTitle: false,

    nav: [
      { text: '首页', link: '/' },
      { text: '论文', link: '/papers/' },
      { text: '关于', link: '/about' },
    ],

    sidebar: {
      '/papers/': genPapersSidebar(),
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/hyyyyyyz/embodied-arxiv' },
    ],

    outline: { level: [2, 3], label: '本页' },

    docFooter: { prev: '上一篇', next: '下一篇' },

    lastUpdatedText: '上次更新',

    darkModeSwitchLabel: '主题',
    sidebarMenuLabel: '菜单',
    returnToTopLabel: '返回顶部',
    externalLinkIcon: true,

    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
          modal: {
            displayDetails: '显示详情',
            resetButtonTitle: '清除',
            backButtonTitle: '返回',
            noResultsText: '无结果',
            footer: {
              selectText: '选择',
              navigateText: '切换',
              closeText: '关闭',
            },
          },
        },
      },
    },

    footer: {
      message: 'MIT License · 改 config.yaml 即可 fork 追自己方向',
      copyright: '© 2026 hyyyyyyz',
    },
  },

  vite: {
    // Allow .json imports from anywhere in docs/
    resolve: {
      alias: {},
    },
  },
})

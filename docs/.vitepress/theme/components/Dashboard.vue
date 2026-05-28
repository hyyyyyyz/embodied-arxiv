<script setup lang="ts">
import { withBase } from 'vitepress'
import HeroStats from './HeroStats.vue'
import TrendChart from './TrendChart.vue'
import TopicChart from './TopicChart.vue'
import HighlightGrid from './HighlightGrid.vue'
import stats from '../../data/stats.json'

type DateCount = [string, number]
const dateCounts: DateCount[] = (stats as any).date_counts ?? []
const latestDate: string = (stats as any).latest_date ?? ''
const latestCount: number = dateCounts[0]?.[1] ?? 0
const topics: Record<string, number> = (stats as any).topics ?? {}
const highlights: any[] = (stats as any).highlights ?? []
const verdictCounts: Record<string, number> = (stats as any).verdicts ?? {}
const totalPapers: number = (stats as any).total_papers ?? 0
const totalDays: number = (stats as any).total_days ?? 0
const topicCount = Object.keys(topics).length
const fireCount = verdictCounts['🔥'] ?? 0
</script>

<template>
  <div class="dashboard">
    <header class="hero">
      <h1 class="hero-title">embodied-arxiv</h1>
      <p class="hero-tagline">
        每日 arXiv 具身智能论文雷达 · DeepSeek V4 中文摘要 + 毒舌锐评 + Framework 图自动抓取
      </p>

      <HeroStats
        :days="totalDays"
        :papers="totalPapers"
        :topics="topicCount"
        :fire="fireCount"
      />

      <div v-if="latestDate" class="home-cta">
        📰 最新 <strong>{{ latestDate }}</strong>
        &nbsp;·&nbsp; {{ latestCount }} 篇
        &nbsp;·&nbsp;
        <a :href="withBase(`/papers/${latestDate}/`)">看今日精选 →</a>
      </div>
    </header>

    <section v-if="dateCounts.length" class="dash-section">
      <h2>📈 每日篇数趋势</h2>
      <TrendChart :data="dateCounts" />
    </section>

    <section v-if="highlights.length" class="dash-section">
      <h2>🌟 近期亮点</h2>
      <HighlightGrid :papers="highlights" />
    </section>

    <section v-if="Object.keys(topics).length" class="dash-section">
      <h2>📊 主题分布</h2>
      <TopicChart :topics="topics" />
    </section>

    <section v-if="dateCounts.length" class="dash-section">
      <h2>📅 历史归档</h2>
      <div class="date-archive">
        <a
          v-for="[date, count] in dateCounts.slice(0, 60)"
          :key="date"
          :href="withBase(`/papers/${date}/`)"
          class="date-link"
        >
          <span class="date-link-date">{{ date }}</span>
          <span class="date-link-count">{{ count }} 篇</span>
        </a>
      </div>
    </section>

    <p class="home-footer">
      <a href="/about">关于本站</a> ·
      <a href="https://github.com/hyyyyyyz/embodied-arxiv">GitHub</a> ·
      MIT · 改 <code>config.yaml</code> 即可 fork 追自己方向
    </p>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1100px;
  margin: 0 auto;
  padding: 1rem 1.5rem 4rem;
}

@media (max-width: 768px) {
  .dashboard { padding: 1rem 1rem 3rem; }
}

.hero { padding: 1.5rem 0 2rem; }

.hero-title {
  font-size: 2.6rem;
  font-weight: 700;
  letter-spacing: -0.035em;
  line-height: 1.05;
  margin: 0 0 0.6rem;
  background: linear-gradient(135deg, var(--vp-c-text-1), #a78bfa);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  display: inline-block;
}

.hero-tagline {
  font-size: 1.05rem;
  color: var(--vp-c-text-2);
  margin: 0 0 1.8rem;
  line-height: 1.6;
}

.home-cta {
  margin: 1.4rem 0 0;
  padding: 1rem 1.3rem;
  background: linear-gradient(135deg, rgba(167,139,250,0.1), rgba(124,58,237,0.04));
  border: 1px solid rgba(167, 139, 250, 0.3);
  border-radius: 10px;
  font-size: 0.95rem;
}

.home-cta a {
  color: var(--vp-c-brand-1) !important;
  font-weight: 600;
  text-decoration: none;
}

.home-cta strong {
  font-family: var(--vp-font-family-mono);
  font-weight: 600;
}

.dash-section { margin: 3.5rem 0; }

.dash-section h2 {
  font-size: 1.35rem;
  font-weight: 600;
  margin: 0 0 1.2rem;
  letter-spacing: -0.02em;
  border-top: none;
  padding-top: 0;
}

.date-archive {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 0.6rem;
}

.date-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.7rem 1rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  text-decoration: none !important;
  color: inherit !important;
  transition: all 0.15s;
}

.date-link:hover {
  border-color: var(--vp-c-brand-1);
  background: var(--vp-c-brand-soft);
  transform: translateY(-1px);
}

.date-link-date {
  font-family: var(--vp-font-family-mono);
  font-weight: 600;
  font-size: 0.88rem;
  font-feature-settings: 'tnum';
}

.date-link-count {
  font-family: var(--vp-font-family-mono);
  font-size: 0.72rem;
  color: var(--vp-c-text-3);
}

.home-footer {
  text-align: center;
  font-size: 0.8rem;
  color: var(--vp-c-text-3);
  margin: 4rem 0 0;
  padding-top: 2rem;
  border-top: 1px solid var(--vp-c-divider);
}

.home-footer a {
  color: var(--vp-c-text-2) !important;
  text-decoration: none;
}

.home-footer a:hover { color: var(--vp-c-brand-1) !important; }

.home-footer code {
  font-family: var(--vp-font-family-mono);
  font-size: 0.85em;
  padding: 0.1em 0.4em;
  background: var(--vp-c-bg-soft);
  border-radius: 3px;
}
</style>

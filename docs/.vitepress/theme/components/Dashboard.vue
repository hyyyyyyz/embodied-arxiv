<script setup lang="ts">
import { computed } from 'vue'
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

// --- arxiv release-cadence note ---
// arxiv 公告时间：周一-周五美东 20:00 → UTC 次日 01:00 → 北京次日 09:00。
// 周六公告周五批；周日 / 周一 arxiv 停摆，本站无新内容。
// 我们 cron 在 UTC 02:00 / 04:00 / 06:00 = 北京 10:00 / 12:00 / 14:00 抓取。
const WEEKDAY_LABEL = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
const UPDATE_UTC_DAYS = new Set([2, 3, 4, 5, 6])  // Tue–Sat: 当天 02:00 UTC 抓到新内容

const todayUTC = computed(() => {
  const now = new Date()
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()))
})
const todayUTCStr = computed(() =>
  todayUTC.value.toISOString().slice(0, 10)
)

const daysSinceLatest = computed(() => {
  if (!latestDate) return 0
  const [y, m, d] = latestDate.split('-').map(Number)
  const last = Date.UTC(y, m - 1, d)
  return Math.max(0, Math.round((todayUTC.value.getTime() - last) / 86400000))
})

// Next UTC date when an update is expected. Skip "quiet" days (Sun/Mon UTC).
const nextUpdateUTCDate = computed(() => {
  const now = new Date()
  const cronAlreadyRan = now.getUTCHours() >= 7  // past 06:00 UTC = past our last cron
  const startOffset = cronAlreadyRan ? 1 : 0
  for (let i = startOffset; i <= 8; i++) {
    const cand = new Date(todayUTC.value)
    cand.setUTCDate(cand.getUTCDate() + i)
    if (UPDATE_UTC_DAYS.has(cand.getUTCDay())) {
      // If today is itself an update day AND we already have today's content, skip
      if (i === 0) {
        if (latestDate === todayUTCStr.value) continue
      }
      return cand
    }
  }
  return null
})

const nextUpdateLabel = computed(() => {
  const d = nextUpdateUTCDate.value
  if (!d) return ''
  // UTC midnight + 8h = Beijing 08:00 of same calendar date. Our cron at
  // UTC 02:00 = Beijing 10:00 of same date — no day-boundary shift.
  const dow = WEEKDAY_LABEL[d.getUTCDay()]
  const m = d.getUTCMonth() + 1
  const day = d.getUTCDate()
  return `${dow} ${m}/${day} 早上`
})

const isUpToDate = computed(
  () => latestDate === todayUTCStr.value
)
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

      <div class="schedule-note" v-if="latestDate">
        <div class="schedule-status">
          <span v-if="isUpToDate" class="schedule-fresh">✅ 今日已是最新</span>
          <span v-else class="schedule-stale">
            ⏳ 上次更新 <strong class="mono">{{ latestDate }}</strong>
            <span class="schedule-ago">（{{ daysSinceLatest }} 天前）</span>
          </span>
          <span v-if="nextUpdateLabel" class="schedule-next">
            · 下次预计 <strong>{{ nextUpdateLabel }}</strong>（北京 10:00 前后）
          </span>
        </div>

        <div v-if="!isUpToDate" class="schedule-why">
          🌙 <strong>为什么没更新？</strong> arxiv 是美国的预印本平台，
          <strong>美国周末（周六、周日）不公告新论文</strong>；
          对应到北京时间 <strong>周日和周一通常也没有新内容</strong>。
          要等美国周一晚 20:00（北京 <strong>周二早上 09:00</strong>）arxiv 重新开张，
          我们 10:00 拉取后才会有下一批。
        </div>

        <details class="schedule-details">
          <summary>arxiv 更新节奏（完整对照）</summary>
          <ul>
            <li>arxiv（在美国）每周一–周五 <strong>美东 20:00</strong>（≈ 北京次日 <strong>09:00</strong>）公告当天接收的新论文</li>
            <li>美国周六、周日是双休日，<strong>arxiv 不公告新论文</strong></li>
            <li>本站在 UTC 02:00 / 04:00 / 06:00（北京 <strong>10:00 / 12:00 / 14:00</strong>）拉取并发布</li>
            <li>北京周几对照：
              <ul>
                <li><strong>周二–周六早上：有新内容</strong>（来自美国前一天工作日晚的公告）</li>
                <li><strong>周日、周一：通常无新内容</strong>（美国前一天是周末，没公告）</li>
              </ul>
            </li>
            <li>所以连续 2 天没更新（北京周日 + 周一）是 <strong>正常现象</strong>，不是 bug</li>
          </ul>
        </details>
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

/* --- arxiv release-cadence note --- */
.schedule-note {
  margin: 0.9rem 0 0;
  padding: 0.85rem 1.1rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  font-size: 0.86rem;
  line-height: 1.6;
}

.schedule-status {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.3rem;
  color: var(--vp-c-text-2);
}

.schedule-fresh {
  color: #16a34a;
  font-weight: 600;
}

.schedule-stale {
  color: var(--vp-c-text-2);
  font-weight: 500;
}

.schedule-stale strong.mono {
  font-family: var(--vp-font-family-mono);
  color: var(--vp-c-text-1);
  font-weight: 600;
}

.schedule-ago {
  color: var(--vp-c-text-3);
  font-size: 0.95em;
}

.schedule-why {
  margin-top: 0.55rem;
  padding: 0.65rem 0.85rem;
  background: rgba(167, 139, 250, 0.06);
  border-left: 3px solid var(--vp-c-brand-1);
  border-radius: 6px;
  font-size: 0.84rem;
  line-height: 1.65;
  color: var(--vp-c-text-2);
}

.schedule-why strong {
  color: var(--vp-c-text-1);
  font-weight: 600;
}

.schedule-next {
  color: var(--vp-c-text-2);
}

.schedule-next strong {
  color: var(--vp-c-brand-1);
  font-family: var(--vp-font-family-mono);
  font-weight: 600;
}

.schedule-details {
  margin-top: 0.55rem;
  font-size: 0.82rem;
  color: var(--vp-c-text-3);
}

.schedule-details summary {
  cursor: pointer;
  font-family: var(--vp-font-family-mono);
  font-size: 0.74rem;
  color: var(--vp-c-text-3);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  user-select: none;
  list-style: none;
}

.schedule-details summary::before {
  content: '▸ ';
  display: inline-block;
  transition: transform 0.15s;
}

.schedule-details[open] summary::before {
  content: '▾ ';
}

.schedule-details summary:hover {
  color: var(--vp-c-brand-1);
}

.schedule-details ul {
  margin: 0.55rem 0 0;
  padding-left: 1.2rem;
}

.schedule-details li {
  margin: 0.25rem 0;
  color: var(--vp-c-text-2);
}

.schedule-details strong {
  color: var(--vp-c-text-1);
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

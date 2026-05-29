<script setup lang="ts">
import { withBase } from 'vitepress'
import { computed, onMounted, ref } from 'vue'
import picks from '../../data/picks.json'

interface Paper {
  date: string
  id: string
  title: string
  tldr: string
  topic: string
  score: number
  verdict: string
  figure_url?: string
}

const all = picks as Paper[]

const VERDICTS = [
  { key: '🔥', label: '🔥 强推' },
  { key: '👀', label: '👀 值得关注' },
  { key: '⚠️', label: '⚠️ 有硬伤但方向对' },
]

const TOPIC_COLORS: Record<string, string> = {
  VLA: '#7c3aed',
  'world-model': '#9333ea',
  '3d-foundation': '#06b6d4',
  'policy-learning': '#dc2626',
  manipulation: '#ea580c',
  navigation: '#16a34a',
  locomotion: '#0d9488',
  sim2real: '#0891b2',
  grasping: '#ca8a04',
  teleoperation: '#db2777',
  tactile: '#be185d',
  humanoid: '#0369a1',
  other: '#64748b',
}

const active = ref('🔥')

const counts = computed(() => {
  const m: Record<string, number> = {}
  for (const p of all) m[p.verdict] = (m[p.verdict] || 0) + 1
  return m
})

const filtered = computed(() => all.filter((p) => p.verdict === active.value))

function color(t: string) {
  return TOPIC_COLORS[t] || '#64748b'
}
function href(p: Paper) {
  return withBase(`/papers/${p.date}/${p.id}/`)
}
function fig(p: Paper) {
  // figure_url (when present) is stored base-less ('/figures/...'); wrap both
  // branches in withBase so the site base '/embodied-arxiv/' is applied.
  return withBase(p.figure_url || `/figures/${p.date}/${p.id}.png`)
}

// Allow deep-linking a verdict via ?v=fire|eye|warn
const HASH_MAP: Record<string, string> = { fire: '🔥', eye: '👀', warn: '⚠️' }
onMounted(() => {
  const params = new URLSearchParams(location.search)
  const v = params.get('v')
  if (v && HASH_MAP[v]) active.value = HASH_MAP[v]
})
</script>

<template>
  <div class="picks">
    <h1 class="picks-title">🔥 精选 · 强推</h1>
    <p class="picks-sub">跨所有日期的高判决论文。默认显示 🔥 强推，可切换查看 👀 / ⚠️。</p>

    <div class="picks-tabs">
      <button
        v-for="v in VERDICTS"
        :key="v.key"
        class="picks-tab"
        :class="{ active: active === v.key }"
        @click="active = v.key"
      >
        {{ v.label }} <span class="cnt">{{ counts[v.key] || 0 }}</span>
      </button>
    </div>

    <div v-if="filtered.length" class="paper-grid">
      <a
        v-for="p in filtered"
        :key="`${p.date}-${p.id}`"
        class="paper-card"
        :data-topic="p.topic"
        :href="href(p)"
      >
        <img class="paper-card-img" :src="fig(p)" alt="" loading="lazy" />
        <div class="paper-card-body">
          <div class="paper-card-title">
            <span class="verdict-tag">{{ p.verdict }}</span> {{ p.title }}
          </div>
          <div class="paper-card-tldr">{{ p.tldr }}</div>
          <div class="paper-card-meta">
            <span class="paper-card-score">⭐ {{ p.score.toFixed(1) }}</span>
            <span
              class="paper-card-topic"
              :style="{ background: color(p.topic) + '22', color: color(p.topic) }"
            >{{ p.topic }}</span>
            <span class="paper-card-date">{{ p.date }}</span>
          </div>
        </div>
      </a>
    </div>

    <p v-else class="picks-empty">这个分类暂时还没有论文，等明天的更新～</p>
  </div>
</template>

<style scoped>
.picks {
  max-width: 1100px;
  margin: 0 auto;
  padding: 1.5rem 1.5rem 4rem;
}

.picks-title {
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin: 0 0 0.4rem;
}

.picks-sub {
  color: var(--vp-c-text-2);
  margin: 0 0 1.5rem;
  font-size: 0.95rem;
}

.picks-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.8rem;
  padding-bottom: 1.2rem;
  border-bottom: 1px solid var(--vp-c-divider);
}

.picks-tab {
  font-family: var(--vp-font-family-mono);
  font-size: 0.82rem;
  font-weight: 600;
  padding: 0.5rem 1rem;
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-2);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.picks-tab:hover {
  color: var(--vp-c-text-1);
  border-color: var(--vp-c-brand-1);
}

.picks-tab.active {
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-text-1);
  border-color: var(--vp-c-brand-1);
}

.picks-tab .cnt {
  font-size: 0.72rem;
  color: var(--vp-c-text-3);
  padding: 0.05rem 0.4rem;
  background: rgba(127, 127, 127, 0.12);
  border-radius: 3px;
  margin-left: 0.2rem;
}

.picks-tab.active .cnt {
  color: var(--vp-c-brand-1);
  background: rgba(167, 139, 250, 0.15);
}

.picks-empty {
  color: var(--vp-c-text-3);
  font-size: 0.95rem;
  padding: 2rem 0;
  text-align: center;
}
</style>

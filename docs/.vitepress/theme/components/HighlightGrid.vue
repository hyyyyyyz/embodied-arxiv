<script setup lang="ts">
import { withBase } from 'vitepress'
import { computed } from 'vue'

interface Paper {
  id: string
  date: string
  title: string
  tldr: string
  topic: string
  score: number
  verdict?: string
  figure_url?: string
}

const props = defineProps<{ papers: Paper[] }>()

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

function color(topic: string) {
  return TOPIC_COLORS[topic] || '#64748b'
}

function href(p: Paper) {
  return withBase(`/papers/${p.date}/${p.id}/`)
}

function fig(p: Paper) {
  return p.figure_url || withBase(`/figures/${p.date}/${p.id}.png`)
}
</script>

<template>
  <div class="paper-grid">
    <a v-for="p in papers" :key="`${p.date}-${p.id}`"
       class="paper-card"
       :data-topic="p.topic"
       :href="href(p)"
    >
      <img class="paper-card-img" :src="fig(p)" alt="" loading="lazy" />
      <div class="paper-card-body">
        <div class="paper-card-title">
          <span v-if="p.verdict" class="verdict-tag">{{ p.verdict }}</span>
          {{ p.title }}
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
</template>

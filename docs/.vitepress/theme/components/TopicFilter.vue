<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

// Client-side filter for .paper-card elements on the date pages.
// Bound after VitePress mounts the page; rebound on route changes.

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

const active = ref('all')
const counts = ref<[string, number][]>([])
const total = ref(0)

function applyFilter(topic: string) {
  active.value = topic
  const cards = document.querySelectorAll<HTMLElement>('.paper-card')
  cards.forEach((c) => {
    const t = c.getAttribute('data-topic') || ''
    if (topic === 'all' || t === topic) c.classList.remove('hidden')
    else c.classList.add('hidden')
  })
}

function scan() {
  const cards = document.querySelectorAll<HTMLElement>('.paper-grid .paper-card')
  const map = new Map<string, number>()
  cards.forEach((c) => {
    const t = c.getAttribute('data-topic') || 'other'
    map.set(t, (map.get(t) || 0) + 1)
  })
  total.value = cards.length
  counts.value = Array.from(map.entries()).sort((a, b) => b[1] - a[1])
}

onMounted(() => {
  scan()
  active.value = 'all'
})
</script>

<template>
  <div v-if="total > 0" class="topic-filter">
    <button
      class="topic-filter-btn"
      :class="{ active: active === 'all' }"
      @click="applyFilter('all')"
    >
      <span class="dot" style="background: #a78bfa"></span>
      全部 <span class="cnt">{{ total }}</span>
    </button>
    <button
      v-for="[topic, n] in counts"
      :key="topic"
      class="topic-filter-btn"
      :class="{ active: active === topic }"
      @click="applyFilter(topic)"
    >
      <span class="dot" :style="{ background: TOPIC_COLORS[topic] || '#64748b' }"></span>
      {{ topic }} <span class="cnt">{{ n }}</span>
    </button>
  </div>
</template>

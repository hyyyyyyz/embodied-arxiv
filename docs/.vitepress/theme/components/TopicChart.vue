<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ topics: Record<string, number> }>()

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

const sorted = computed(() => {
  return Object.entries(props.topics).sort((a, b) => b[1] - a[1])
})

const maxCount = computed(() => Math.max(1, ...Object.values(props.topics)))

function color(topic: string) {
  return TOPIC_COLORS[topic] || '#64748b'
}

function pct(n: number) {
  return (n / maxCount.value) * 100
}
</script>

<template>
  <div class="topic-chart">
    <div v-for="[topic, count] in sorted" :key="topic" class="topic-bar">
      <div class="topic-bar-label">
        <span class="topic-dot" :style="{ background: color(topic) }"></span>
        {{ topic }}
      </div>
      <div class="topic-bar-track">
        <div
          class="topic-bar-fill"
          :style="{ width: `${pct(count)}%`, background: color(topic) }"
        ></div>
      </div>
      <div class="topic-bar-count">{{ count }}</div>
    </div>
  </div>
</template>

<style scoped>
.topic-chart {
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 1rem 1.2rem;
}

.topic-bar {
  display: grid;
  grid-template-columns: 150px 1fr 45px;
  gap: 0.8rem;
  align-items: center;
  padding: 0.45rem 0;
}

.topic-bar + .topic-bar {
  border-top: 1px solid var(--vp-c-divider);
}

.topic-bar-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-family: var(--vp-font-family-mono);
  font-size: 0.82rem;
  color: var(--vp-c-text-1);
  font-weight: 500;
}

.topic-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex: 0 0 auto;
}

.topic-bar-track {
  height: 8px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 4px;
  overflow: hidden;
}

.topic-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.topic-bar-count {
  font-family: var(--vp-font-family-mono);
  font-size: 0.78rem;
  color: var(--vp-c-text-2);
  text-align: right;
  font-feature-settings: 'tnum';
}

@media (max-width: 600px) {
  .topic-bar { grid-template-columns: 110px 1fr 35px; gap: 0.5rem; }
  .topic-bar-label { font-size: 0.75rem; }
}
</style>

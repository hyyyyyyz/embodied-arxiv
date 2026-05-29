<script setup lang="ts">
import { withBase } from 'vitepress'

defineProps<{
  days: number
  papers: number
  topics: number
  fire: number
}>()
</script>

<template>
  <div class="hero-stats">
    <div class="stat">
      <div class="stat-num">{{ days }}</div>
      <div class="stat-label">天</div>
    </div>
    <div class="stat">
      <div class="stat-num">{{ papers }}</div>
      <div class="stat-label">篇收录</div>
    </div>
    <div class="stat">
      <div class="stat-num">{{ topics }}</div>
      <div class="stat-label">topic</div>
    </div>
    <a class="stat stat-link" :href="withBase('/picks/')">
      <div class="stat-num">{{ fire }}</div>
      <div class="stat-label">🔥 强推</div>
      <div class="stat-cta">查看全部 →</div>
    </a>
  </div>
</template>

<style scoped>
.hero-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 0.7rem;
  margin: 1.5rem 0 0;
}

.stat {
  position: relative;
  padding: 1rem 1.1rem 0.95rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  text-align: center;
  transition: border-color 0.15s, transform 0.15s;
}

.stat:hover {
  border-color: var(--vp-c-brand-1);
  transform: translateY(-1px);
}

/* The 🔥 card is a link into /picks/ */
.stat-link {
  display: block;
  text-decoration: none !important;
  color: inherit !important;
  cursor: pointer;
}

.stat-link:hover {
  background: var(--vp-c-brand-soft);
}

.stat-num {
  font-family: var(--vp-font-family-mono);
  font-size: 2.1rem;
  font-weight: 700;
  color: var(--vp-c-text-1);
  letter-spacing: -0.04em;
  font-feature-settings: 'tnum';
  line-height: 1;
}

.stat-label {
  font-family: var(--vp-font-family-mono);
  font-size: 0.7rem;
  color: var(--vp-c-text-3);
  margin-top: 0.45rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.stat-cta {
  font-family: var(--vp-font-family-mono);
  font-size: 0.62rem;
  color: var(--vp-c-brand-1);
  margin-top: 0.5rem;
  opacity: 0;
  transition: opacity 0.15s;
}

.stat-link:hover .stat-cta {
  opacity: 1;
}

/* On touch devices (no hover), always show the CTA hint */
@media (hover: none) {
  .stat-cta { opacity: 0.8; }
}
</style>

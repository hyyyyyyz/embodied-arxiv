<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ data: [string, number][] }>()

// Reverse so oldest first (left-to-right)
const points = computed(() => [...props.data].reverse())

// Chart geometry
const W = 800
const H = 200
const PAD_L = 36
const PAD_R = 16
const PAD_T = 18
const PAD_B = 26
const plotW = W - PAD_L - PAD_R
const plotH = H - PAD_T - PAD_B

const yMax = computed(() => {
  const maxC = Math.max(...points.value.map((p) => p[1]), 5)
  // round up to a nice number
  if (maxC <= 10) return 10
  if (maxC <= 25) return 25
  if (maxC <= 50) return 50
  return Math.ceil(maxC / 25) * 25
})

const xs = computed(() => {
  const n = points.value.length
  if (n === 0) return []
  if (n === 1) return [PAD_L + plotW / 2]
  return points.value.map((_, i) => PAD_L + (plotW * i) / (n - 1))
})

const ys = computed(() =>
  points.value.map(([, c]) => PAD_T + plotH * (1 - c / yMax.value))
)

const linePath = computed(() => xs.value.map((x, i) => `${x},${ys.value[i]}`).join(' '))

const areaPath = computed(() => {
  if (xs.value.length === 0) return ''
  const bottomY = PAD_T + plotH
  let d = `M ${xs.value[0]},${bottomY}`
  xs.value.forEach((x, i) => {
    d += ` L ${x},${ys.value[i]}`
  })
  d += ` L ${xs.value[xs.value.length - 1]},${bottomY} Z`
  return d
})

// 4 gridlines + labels at 0/25/50/75/100%
const gridlines = [0.25, 0.5, 0.75, 1.0].map((f) => ({
  y: PAD_T + plotH * (1 - f),
  val: Math.round(yMax.value * f),
}))

function shortDate(d: string) {
  // 2026-05-27 → 5/27
  const m = d.match(/^\d{4}-(\d{2})-(\d{2})$/)
  return m ? `${parseInt(m[1])}/${m[2]}` : d
}

// Sample x-axis labels — show every Nth to avoid overlap
const xLabelEvery = computed(() => {
  const n = points.value.length
  if (n <= 7) return 1
  if (n <= 14) return 2
  if (n <= 30) return 4
  return Math.ceil(n / 10)
})
</script>

<template>
  <div class="trend-wrap">
    <svg
      :viewBox="`0 0 ${W} ${H}`"
      class="trend-chart"
      preserveAspectRatio="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="trend-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="rgba(167,139,250,0.45)" />
          <stop offset="100%" stop-color="rgba(167,139,250,0.02)" />
        </linearGradient>
      </defs>

      <!-- Gridlines + Y labels -->
      <g class="grid">
        <line
          v-for="(g, i) in gridlines"
          :key="`g-${i}`"
          :x1="PAD_L"
          :y1="g.y"
          :x2="PAD_L + plotW"
          :y2="g.y"
        />
        <text
          v-for="(g, i) in gridlines"
          :key="`l-${i}`"
          :x="PAD_L - 6"
          :y="g.y + 4"
          class="axis-label"
          text-anchor="end"
        >{{ g.val }}</text>
      </g>

      <!-- Area + line -->
      <path :d="areaPath" fill="url(#trend-grad)" />
      <polyline
        :points="linePath"
        fill="none"
        stroke="#a78bfa"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      />

      <!-- Markers -->
      <g class="markers">
        <g v-for="(p, i) in points" :key="`m-${i}`">
          <circle
            :cx="xs[i]"
            :cy="ys[i]"
            r="4"
            fill="var(--vp-c-bg)"
            stroke="#a78bfa"
            stroke-width="2"
          />
          <title>{{ p[0] }}: {{ p[1] }} 篇</title>
        </g>
      </g>

      <!-- X-axis labels -->
      <g class="xaxis">
        <text
          v-for="(p, i) in points"
          :key="`x-${i}`"
          v-show="i === 0 || i === points.length - 1 || i % xLabelEvery === 0"
          :x="xs[i]"
          :y="H - 6"
          class="axis-label"
          text-anchor="middle"
        >{{ shortDate(p[0]) }}</text>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.trend-wrap {
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 1rem;
}

.trend-chart {
  width: 100%;
  height: auto;
  max-height: 220px;
  display: block;
  overflow: visible;
}

.grid line {
  stroke: var(--vp-c-divider);
  stroke-dasharray: 2 3;
}

.axis-label {
  font-family: var(--vp-font-family-mono);
  font-size: 10px;
  fill: var(--vp-c-text-3);
  font-feature-settings: 'tnum';
}

.markers circle {
  transition: r 0.15s;
}

.markers circle:hover {
  r: 6;
  cursor: pointer;
}
</style>

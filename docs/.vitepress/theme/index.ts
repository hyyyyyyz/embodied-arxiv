import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'

import Dashboard from './components/Dashboard.vue'
import HeroStats from './components/HeroStats.vue'
import TrendChart from './components/TrendChart.vue'
import TopicChart from './components/TopicChart.vue'
import HighlightGrid from './components/HighlightGrid.vue'
import TopicFilter from './components/TopicFilter.vue'
import PicksList from './components/PicksList.vue'

import './style.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('Dashboard', Dashboard)
    app.component('HeroStats', HeroStats)
    app.component('TrendChart', TrendChart)
    app.component('TopicChart', TopicChart)
    app.component('HighlightGrid', HighlightGrid)
    app.component('TopicFilter', TopicFilter)
    app.component('PicksList', PicksList)
  },
} satisfies Theme

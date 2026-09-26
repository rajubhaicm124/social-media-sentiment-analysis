/** Chart set for the analysis dashboard. All series come from real API output. */

import { useMemo } from 'react'
import type { EChartsOption } from 'echarts'
import { EChart, useChartTheme } from './EChart'
import type { AnalysisCharts, SentimentCounts, TimeSeriesPoint } from '../../types'

const SENTIMENT_COLORS = { positive: '#22c55e', neutral: '#a3aed0', negative: '#ef4444' }
const SERIES_COLORS = ['#4f7cff', '#8a5cff', '#22d3ee', '#f59e0b', '#ec4899', '#10b981']

type LabelItem = { name: string; value: number }
/** The word-cloud series uses `text` as its label key. */
type CloudTerm = { text: string; value: number }

function tooltipBase(muted: string) {
  return {
    backgroundColor: 'rgba(13,18,33,0.94)',
    borderColor: 'rgba(148,162,196,0.25)',
    textStyle: { color: '#e9eefa', fontSize: 12 },
    extraCssText: 'border-radius:10px;box-shadow:0 12px 30px rgba(0,0,0,.35);',
    axisPointer: { lineStyle: { color: muted } },
  }
}

function compact(value: number): string {
  const abs = Math.abs(value)
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
  if (abs >= 1_000) return `${(value / 1_000).toFixed(1)}K`
  return String(Math.round(value))
}

/* ------------------------------------------------------- Engagement bars */

export function EngagementBarChart({ charts }: { charts: AnalysisCharts }) {
  const { text, muted, line } = useChartTheme()
  const { categories, values } = charts.engagement_bars

  const option = useMemo<EChartsOption>(() => {
    // Nulls must stay null: ECharts would otherwise draw a zero-height bar and
    // imply a measured value of 0 for a metric the API never returned.
    const plotted = values.map((value) => (value === null ? null : value))
    return {
      grid: { left: 8, right: 16, top: 24, bottom: 8, containLabel: true },
      tooltip: {
        ...tooltipBase(muted),
        trigger: 'axis',
        formatter: (params: unknown) => {
          const list = params as { name: string; value: number | null }[]
          return list
            .map(
              (item) =>
                `${item.name}: ${
                  item.value === null || item.value === undefined
                    ? 'Data unavailable through the current platform API.'
                    : Number(item.value).toLocaleString()
                }`,
            )
            .join('<br/>')
        },
      },
      xAxis: {
        type: 'category',
        data: categories,
        axisLabel: { color: muted },
        axisLine: { lineStyle: { color: line } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: muted, formatter: (v: number) => compact(v) },
        splitLine: { lineStyle: { color: line, type: 'dashed' } },
      },
      series: [
        {
          type: 'bar',
          data: plotted.map((value, index) => ({
            value,
            itemStyle: {
              color: SERIES_COLORS[index % SERIES_COLORS.length],
              borderRadius: [8, 8, 0, 0],
            },
          })),
          barMaxWidth: 58,
          label: {
            show: true,
            position: 'top',
            color: text,
            fontSize: 11,
            formatter: (params: unknown) => {
              const value = (params as { value?: number | null }).value
              return value === null || value === undefined ? 'n/a' : compact(value)
            },
          },
          animationDuration: 900,
        },
      ],
    }
  }, [categories, values, text, muted, line])

  return <EChart option={option} height={300} ariaLabel="Engagement metrics by type" />
}

/* -------------------------------------------------------- Sentiment donut */

export function SentimentDonutChart({ summary }: { summary: SentimentCounts }) {
  const { text, muted } = useChartTheme()
  const option = useMemo<EChartsOption>(
    () => ({
      tooltip: { ...tooltipBase(muted), trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: {
        bottom: 0,
        textStyle: { color: text },
        icon: 'circle',
        itemWidth: 9,
        itemHeight: 9,
      },
      series: [
        {
          type: 'pie',
          radius: ['52%', '76%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: true,
          itemStyle: { borderRadius: 8, borderColor: 'transparent', borderWidth: 3 },
          label: {
            show: true,
            color: text,
            formatter: '{b}\n{d}%',
            fontSize: 12,
          },
          labelLine: { length: 12, length2: 10 },
          data: summary.distribution.map((item) => ({
            name: item.name,
            value: item.value,
            itemStyle: { color: SENTIMENT_COLORS[item.key] },
          })),
          animationDuration: 1000,
        },
      ],
    }),
    [summary, text, muted],
  )
  return <EChart option={option} height={320} ariaLabel="Sentiment distribution donut chart" />
}

/* ------------------------------------------------------ Sentiment scores */

export function SentimentScoreChart({ summary }: { summary: SentimentCounts }) {
  const { text, muted, line } = useChartTheme()
  const option = useMemo<EChartsOption>(
    () => ({
      grid: { left: 8, right: 16, top: 20, bottom: 8, containLabel: true },
      tooltip: { ...tooltipBase(muted), trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: ['Positive', 'Neutral', 'Negative', 'Avg compound', 'Avg polarity', 'Avg subjectivity'],
        axisLabel: { color: muted, interval: 0, rotate: 18, fontSize: 10 },
        axisLine: { lineStyle: { color: line } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: muted },
        splitLine: { lineStyle: { color: line, type: 'dashed' } },
      },
      series: [
        {
          type: 'bar',
          barMaxWidth: 46,
          data: [
            summary.positive,
            summary.neutral,
            summary.negative,
            summary.avg_compound,
            summary.avg_polarity,
            summary.avg_subjectivity,
          ].map((value, index) => ({
            value: Number(value.toFixed(4)),
            itemStyle: {
              color:
                index < 3
                  ? [SENTIMENT_COLORS.positive, SENTIMENT_COLORS.neutral, SENTIMENT_COLORS.negative][index]
                  : SERIES_COLORS[index % SERIES_COLORS.length],
              borderRadius: [8, 8, 0, 0],
            },
          })),
          label: { show: true, position: 'top', color: text, fontSize: 10 },
          animationDuration: 900,
        },
      ],
    }),
    [summary, text, muted, line],
  )
  return <EChart option={option} height={300} ariaLabel="Sentiment score comparison" />
}

/* --------------------------------------------------- Sentiment over time */

export function SentimentTrendChart({ points }: { points: TimeSeriesPoint[] }) {
  const { text, muted, line } = useChartTheme()
  const option = useMemo<EChartsOption>(
    () => ({
      grid: { left: 8, right: 16, top: 30, bottom: 8, containLabel: true },
      tooltip: { ...tooltipBase(muted), trigger: 'axis' },
      legend: { top: 0, textStyle: { color: text }, icon: 'roundRect', itemWidth: 10, itemHeight: 10 },
      xAxis: {
        type: 'category',
        data: points.map((point) => point.period),
        axisLabel: { color: muted, fontSize: 10 },
        axisLine: { lineStyle: { color: line } },
      },
      yAxis: {
        type: 'value',
        name: 'Comments',
        nameTextStyle: { color: muted },
        axisLabel: { color: muted },
        splitLine: { lineStyle: { color: line, type: 'dashed' } },
      },
      series: (['positive', 'neutral', 'negative'] as const).map((key) => ({
        name: key.charAt(0).toUpperCase() + key.slice(1),
        type: 'line' as const,
        stack: 'total',
        smooth: true,
        showSymbol: false,
        areaStyle: { opacity: 0.28 },
        lineStyle: { width: 2 },
        itemStyle: { color: SENTIMENT_COLORS[key] },
        data: points.map((point) => point[key]),
        animationDuration: 900,
      })),
    }),
    [points, text, muted, line],
  )
  return <EChart option={option} height={320} ariaLabel="Sentiment over time" />
}

/* ------------------------------------------------ Engagement vs sentiment */

export function SentimentScatterChart({ charts }: { charts: AnalysisCharts }) {
  const { text, muted, line } = useChartTheme()
  const option = useMemo<EChartsOption>(() => {
    const groups = (['positive', 'neutral', 'negative'] as const).map((key) => ({
      name: key.charAt(0).toUpperCase() + key.slice(1),
      type: 'scatter' as const,
      symbolSize: 9,
      itemStyle: { color: SENTIMENT_COLORS[key], opacity: 0.68 },
      data: charts.likes_vs_sentiment
        .filter((point) => point.sentiment_label === key)
        .map((point) => [point.likes, Number(point.sentiment.toFixed(4)), point.text]),
    }))

    return {
      grid: { left: 8, right: 20, top: 30, bottom: 8, containLabel: true },
      tooltip: {
        ...tooltipBase(muted),
        trigger: 'item',
        formatter: (params: unknown) => {
          const point = (params as { data?: unknown[] }).data
          if (!Array.isArray(point)) return ''
          const [likes, sentiment, label] = point as [number, number, string]
          return `${likes} likes · sentiment ${sentiment}<br/><span style="color:#94a2c4">${String(
            label,
          ).slice(0, 70)}…</span>`
        },
      },
      legend: { top: 0, textStyle: { color: text }, icon: 'circle', itemWidth: 9, itemHeight: 9 },
      xAxis: {
        type: 'value',
        name: 'Likes',
        nameTextStyle: { color: muted },
        axisLabel: { color: muted, formatter: (v: number) => compact(v) },
        splitLine: { lineStyle: { color: line, type: 'dashed' } },
      },
      yAxis: {
        type: 'value',
        name: 'Sentiment',
        nameTextStyle: { color: muted },
        axisLabel: { color: muted },
        splitLine: { lineStyle: { color: line, type: 'dashed' } },
      },
      series: groups,
      animationDuration: 900,
    }
  }, [charts, text, muted, line])

  return <EChart option={option} height={340} ariaLabel="Likes versus sentiment scatter plot" />
}

/* --------------------------------------------------------- Comment length */

export function CommentLengthChart({ charts }: { charts: AnalysisCharts }) {
  const { text, muted, line } = useChartTheme()
  const option = useMemo<EChartsOption>(
    () => ({
      grid: { left: 8, right: 16, top: 24, bottom: 8, containLabel: true },
      tooltip: { ...tooltipBase(muted), trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: charts.comment_length_histogram.map((row) => row.label),
        axisLabel: { color: muted, fontSize: 10 },
        axisLine: { lineStyle: { color: line } },
      },
      yAxis: {
        type: 'value',
        name: 'Comments',
        nameTextStyle: { color: muted },
        axisLabel: { color: muted },
        splitLine: { lineStyle: { color: line, type: 'dashed' } },
      },
      series: [
        {
          type: 'bar',
          barMaxWidth: 44,
          data: charts.comment_length_histogram.map((row) => ({
            value: row.count,
            itemStyle: { color: SERIES_COLORS[0], borderRadius: [8, 8, 0, 0] },
          })),
          label: { show: true, position: 'top', color: text, fontSize: 10 },
        },
      ],
    }),
    [charts.comment_length_histogram, text, muted, line],
  )
  return <EChart option={option} height={280} ariaLabel="Comment length distribution" />
}

/* ------------------------------------------------------------ Hourly load */

export function HourlyActivityChart({ charts }: { charts: AnalysisCharts }) {
  const { text, muted, line } = useChartTheme()
  const option = useMemo<EChartsOption>(
    () => ({
      grid: { left: 8, right: 16, top: 20, bottom: 8, containLabel: true },
      tooltip: { ...tooltipBase(muted), trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: charts.hourly_activity.map((row) => row.hour),
        axisLabel: { color: muted, fontSize: 9, interval: 1 },
        axisLine: { lineStyle: { color: line } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: muted },
        splitLine: { lineStyle: { color: line, type: 'dashed' } },
      },
      series: [
        {
          type: 'line',
          smooth: true,
          areaStyle: { opacity: 0.22, color: SERIES_COLORS[2] },
          lineStyle: { width: 2, color: SERIES_COLORS[2] },
          itemStyle: { color: SERIES_COLORS[2] },
          data: charts.hourly_activity.map((row) => row.count),
        },
      ],
    }),
    [charts.hourly_activity, text, muted, line],
  )
  return <EChart option={option} height={260} ariaLabel="Comment activity by hour of day" />
}

/* -------------------------------------------------------------- Keywords */

/** Horizontal keyword-frequency bars. */
export function KeywordChart({ keywords }: { keywords: LabelItem[] }) {
  const { text, muted, line } = useChartTheme()
  const option = useMemo<EChartsOption>(
    () => ({
      grid: { left: 8, right: 40, top: 10, bottom: 10, containLabel: true },
      tooltip: { ...tooltipBase(muted), trigger: 'item' },
      xAxis: {
        type: 'value',
        axisLabel: { color: muted },
        splitLine: { lineStyle: { color: line, type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: keywords.map((row) => row.name).reverse(),
        axisLabel: { color: text, fontSize: 11 },
        axisLine: { lineStyle: { color: line } },
        axisTick: { show: false },
      },
      series: [
        {
          type: 'bar',
          barMaxWidth: 15,
          data: keywords
            .map((row) => ({
              value: row.value,
              itemStyle: { color: SERIES_COLORS[1], borderRadius: [0, 6, 6, 0] },
            }))
            .reverse(),
          label: { show: true, position: 'right', color: text, fontSize: 10 },
          animationDuration: 800,
        },
      ],
    }),
    [keywords, text, muted, line],
  )
  return (
    <EChart
      option={option}
      height={Math.max(240, keywords.length * 24)}
      ariaLabel="Top keyword frequency"
    />
  )
}

/** Horizontal hashtag-frequency bars. */
export function HashtagChart({ hashtags }: { hashtags: LabelItem[] }) {
  const { text, muted, line } = useChartTheme()
  const option = useMemo<EChartsOption>(
    () => ({
      grid: { left: 8, right: 40, top: 10, bottom: 10, containLabel: true },
      tooltip: { ...tooltipBase(muted), trigger: 'item' },
      xAxis: {
        type: 'value',
        axisLabel: { color: muted },
        splitLine: { lineStyle: { color: line, type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: hashtags.map((row) => `#${row.name}`).reverse(),
        axisLabel: { color: text, fontSize: 11 },
        axisLine: { lineStyle: { color: line } },
        axisTick: { show: false },
      },
      series: [
        {
          type: 'bar',
          barMaxWidth: 15,
          data: hashtags
            .map((row) => ({
              value: row.value,
              itemStyle: { color: SERIES_COLORS[2], borderRadius: [0, 6, 6, 0] },
            }))
            .reverse(),
          label: { show: true, position: 'right', color: text, fontSize: 10 },
        },
      ],
    }),
    [hashtags, text, muted, line],
  )
  return (
    <EChart
      option={option}
      height={Math.max(200, hashtags.length * 24)}
      ariaLabel="Hashtag frequency"
    />
  )
}

/* ------------------------------------------------------------ Word cloud */

/**
 * A CSS-based tag cloud. ECharts' `wordCloud` series is a separate extension
 * package, and a flex-wrap layout is both lighter and fully responsive.
 */
export function WordCloud({ terms }: { terms: CloudTerm[] }) {
  const { isDark } = useChartTheme()
  if (!terms.length) {
    return <p className="py-8 text-center text-sm text-muted">No keywords were extracted.</p>
  }
  const max = Math.max(...terms.map((term) => term.value))
  const min = Math.min(...terms.map((term) => term.value))
  const palette = isDark
    ? ['#8fb0ff', '#b79bff', '#6ee7f5', '#fcd34d', '#f9a8d4', '#6ee7b7']
    : ['#3b5bdb', '#7048e8', '#0e7490', '#b45309', '#be185d', '#047857']

  return (
    <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-2 py-4" role="list">
      {terms.map((term, index) => {
        const ratio = max === min ? 1 : (term.value - min) / (max - min)
        const size = 12 + ratio * 22
        return (
          <span
            key={`${term.text}-${index}`}
            role="listitem"
            title={`${term.text}: ${term.value} occurrence(s)`}
            className="cursor-default font-semibold leading-none transition-transform duration-200 hover:scale-110"
            style={{
              fontSize: `${size}px`,
              color: palette[index % palette.length],
              opacity: 0.55 + ratio * 0.45,
            }}
          >
            {term.text}
          </span>
        )
      })}
    </div>
  )
}

/* ------------------------------------------------------ Correlation heatmap */

export function CorrelationHeatmap({
  fields,
  matrix,
}: {
  fields: string[]
  matrix: (number | null)[][]
}) {
  const { text, muted } = useChartTheme()
  const option = useMemo<EChartsOption>(() => {
    const data: [number, number, number][] = []
    matrix.forEach((row, x) => {
      row.forEach((value, y) => {
        if (value !== null) data.push([x, y, value])
      })
    })
    return {
      grid: { left: 8, right: 60, top: 10, bottom: 8, containLabel: true },
      tooltip: {
        ...tooltipBase(muted),
        trigger: 'item',
        formatter: (params: unknown) => {
          const point = (params as { data?: unknown[] }).data
          if (!Array.isArray(point)) return ''
          const [x, y, value] = point as [number, number, number]
          return `${fields[x]} vs ${fields[y]}<br/>Pearson r = <b>${value}</b>`
        },
      },
      xAxis: {
        type: 'category',
        data: fields,
        axisLabel: { color: muted, rotate: 24, fontSize: 10 },
        splitArea: { show: true },
      },
      yAxis: {
        type: 'category',
        data: fields,
        axisLabel: { color: muted, fontSize: 10 },
        splitArea: { show: true },
      },
      visualMap: {
        min: -1,
        max: 1,
        calculable: true,
        orient: 'vertical',
        right: 0,
        top: 'center',
        inRange: { color: ['#ef4444', '#fbbf24', '#22c55e'] },
        textStyle: { color: text },
      },
      series: [
        {
          type: 'heatmap',
          data,
          label: {
            show: true,
            color: text,
            fontSize: 10,
            formatter: (params: unknown) => {
              const point = (params as { data?: unknown[] }).data
              return Array.isArray(point) ? String(point[2]) : ''
            },
          },
          itemStyle: { borderColor: 'transparent', borderWidth: 3 },
          emphasis: { itemStyle: { shadowBlur: 12, shadowColor: 'rgba(0,0,0,.4)' } },
        },
      ],
    }
  }, [fields, matrix, text, muted])
  return <EChart option={option} height={300} ariaLabel="Correlation heatmap" />
}

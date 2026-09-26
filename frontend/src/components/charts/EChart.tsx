/** Thin, typed React wrapper around Apache ECharts. */

import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { useApp } from '../../context/app-context'

interface EChartProps {
  option: EChartsOption
  height?: number | string
  className?: string
  /** Accessible description of what the chart shows. */
  ariaLabel?: string
  onReady?: (instance: echarts.ECharts) => void
}

/**
 * ECharts is imported per-component (not tree-shaken per chart type) because
 * the dashboard renders many different chart types; the bundle is a single
 * cohesive charting module rather than dozens of tiny ones.
 */
export function EChart({ option, height = 320, className = '', ariaLabel, onReady }: EChartProps) {
  const container = useRef<HTMLDivElement | null>(null)
  const instance = useRef<echarts.ECharts | null>(null)
  const ready = useRef(onReady)
  ready.current = onReady

  useEffect(() => {
    if (!container.current) return

    const chart = echarts.init(container.current, undefined, { renderer: 'canvas' })
    instance.current = chart
    ready.current?.(chart)

    const observer = new ResizeObserver(() => chart.resize())
    observer.observe(container.current)

    return () => {
      observer.disconnect()
      chart.dispose()
      instance.current = null
    }
  }, [])

  // `notMerge` keeps stale series from lingering when switching chart types.
  useEffect(() => {
    instance.current?.setOption(option, { notMerge: true, lazyUpdate: false })
  }, [option])

  return (
    <div
      ref={container}
      className={className}
      style={{ height: typeof height === 'number' ? `${height}px` : height, width: '100%' }}
      role="img"
      aria-label={ariaLabel}
    />
  )
}

/** Chart palette derived from the active app theme, so it re-renders on toggle. */
export function useChartTheme(): { text: string; muted: string; line: string; isDark: boolean } {
  const { theme } = useApp()
  return theme === 'dark'
    ? { text: '#e9eefa', muted: '#94a2c4', line: '#27324e', isDark: true }
    : { text: '#111a2e', muted: '#64748b', line: '#e2e8f0', isDark: false }
}

export { echarts }
export type { EChartsOption }

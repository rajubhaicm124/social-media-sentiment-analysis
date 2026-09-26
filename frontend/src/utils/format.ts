/** Formatting helpers shared across pages. */

const UNAVAILABLE = 'Data unavailable through the current platform API.'

/** Render a metric that may legitimately be missing because the API omits it. */
export function formatMetric(
  value: number | null | undefined,
  options: { suffix?: string; decimals?: number; unavailable?: string } = {},
): { text: string; available: boolean } {
  const { suffix = '', decimals = 0, unavailable = UNAVAILABLE } = options
  if (value === null || value === undefined || Number.isNaN(value)) {
    return { text: unavailable, available: false }
  }
  const text =
    decimals > 0
      ? value.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
      : Math.round(value).toLocaleString()
  return { text: `${text}${suffix}`, available: true }
}

/** Compact number formatting for KPI tiles (12K, 1.2M). */
export function compactNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  const abs = Math.abs(value)
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(abs >= 10_000_000 ? 0 : 1)}M`
  if (abs >= 1_000) return `${(value / 1_000).toFixed(abs >= 10_000 ? 0 : 1)}K`
  return String(Math.round(value))
}

export function formatPercent(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined) return '—'
  return `${value.toFixed(decimals)}%`
}

export function formatScore(value: number | null | undefined, decimals = 3): string {
  if (value === null || value === undefined) return '—'
  return value.toFixed(decimals)
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** Relative time for history rows ("2 hours ago"). */
export function timeAgo(value: string | null | undefined): string {
  if (!value) return '—'
  const then = new Date(value).getTime()
  if (Number.isNaN(then)) return value
  const seconds = Math.floor((Date.now() - then) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days} day${days > 1 ? 's' : ''} ago`
  return formatDate(value)
}

export function sentimentColor(sentiment: string): string {
  switch (sentiment) {
    case 'positive':
      return '#22c55e'
    case 'negative':
      return '#ef4444'
    default:
      return '#a3aed0'
  }
}

export function platformLabel(platform: string | null | undefined): string {
  if (!platform) return 'Unknown'
  return platform.charAt(0).toUpperCase() + platform.slice(1)
}

export function truncate(value: string, max = 90): string {
  if (!value) return ''
  return value.length <= max ? value : `${value.slice(0, max - 1)}…`
}

/** Truncate a long URL for display while keeping it recognisable. */
export function shortUrl(url: string, max = 48): string {
  try {
    const parsed = new URL(url)
    const tail = parsed.pathname.length > 24 ? `…${parsed.pathname.slice(-24)}` : parsed.pathname
    const combined = `${parsed.hostname}${tail}${parsed.search}`
    return combined.length <= max ? combined : `${combined.slice(0, max - 1)}…`
  } catch {
    return truncate(url, max)
  }
}

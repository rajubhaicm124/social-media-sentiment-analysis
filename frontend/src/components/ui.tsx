/** Reusable presentational primitives (buttons, cards, badges, states). */

import { useEffect, useState } from 'react'
import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { AlertTriangle, CheckCircle2, Info, Loader2, XCircle } from 'lucide-react'
import { motion } from 'framer-motion'
import { formatMetric } from '../utils/format'

/* ---------------------------------------------------------------- Button */

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'success'
type Size = 'sm' | 'md' | 'lg'

const VARIANTS: Record<Variant, string> = {
  primary:
    'text-white shadow-lg shadow-brand/25 bg-linear-to-r from-brand to-brand-2 hover:brightness-110 active:brightness-95',
  secondary: 'glass text-ink hover:border-brand/60 hover:shadow-lg',
  ghost: 'text-muted hover:text-ink hover:bg-ink/5',
  danger: 'text-white bg-negative hover:brightness-110 shadow-lg shadow-negative/25',
  success: 'text-white bg-positive hover:brightness-110 shadow-lg shadow-positive/25',
}

const SIZES: Record<Size, string> = {
  sm: 'px-3 py-1.5 text-xs gap-1.5',
  md: 'px-4 py-2.5 text-sm gap-2',
  lg: 'px-6 py-3.5 text-base gap-2.5',
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
  icon?: ReactNode
  fullWidth?: boolean
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  fullWidth = false,
  className = '',
  children,
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center rounded-xl font-semibold transition-all duration-200
        disabled:cursor-not-allowed disabled:opacity-55 disabled:shadow-none
        ${VARIANTS[variant]} ${SIZES[size]} ${fullWidth ? 'w-full' : ''} ${className}`}
    >
      {loading ? <Loader2 size={16} className="animate-spin-slow" aria-hidden /> : icon}
      {children}
    </button>
  )
}

/* ------------------------------------------------------------------ Card */

interface CardProps {
  children: ReactNode
  className?: string
  /** Adds the hover-lift 3D treatment. */
  interactive?: boolean
  as?: 'div' | 'section' | 'article'
}

export function Card({ children, className = '', interactive = false, as = 'div' }: CardProps) {
  const Tag = as
  return (
    <Tag
      className={`surface-card card-3d ${interactive ? 'card-3d-hover' : ''} ${className}`}
    >
      {children}
    </Tag>
  )
}

export function CardHeader({
  title,
  subtitle,
  icon,
  action,
}: {
  title: string
  subtitle?: string
  icon?: ReactNode
  action?: ReactNode
}) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-line px-5 py-4">
      <div className="flex min-w-0 items-start gap-3">
        {icon ? (
          <span className="mt-0.5 grid size-9 shrink-0 place-items-center rounded-xl bg-brand/12 text-brand">
            {icon}
          </span>
        ) : null}
        <div className="min-w-0">
          <h3 className="truncate text-sm font-bold text-ink">{title}</h3>
          {subtitle ? <p className="mt-0.5 text-xs text-muted">{subtitle}</p> : null}
        </div>
      </div>
      {action}
    </div>
  )
}

/* ----------------------------------------------------------------- Badge */

type Tone = 'brand' | 'positive' | 'neutral' | 'negative' | 'muted' | 'warning'

const TONES: Record<Tone, string> = {
  brand: 'bg-brand/12 text-brand ring-brand/25',
  positive: 'bg-positive/12 text-positive ring-positive/25',
  neutral: 'bg-neutral/15 text-muted ring-neutral/25',
  negative: 'bg-negative/12 text-negative ring-negative/25',
  muted: 'bg-ink/6 text-muted ring-ink/10',
  warning: 'bg-amber-500/12 text-amber-500 ring-amber-500/25',
}

export function Badge({
  children,
  tone = 'muted',
  className = '',
}: {
  children: ReactNode
  tone?: Tone
  className?: string
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ring-1 ${TONES[tone]} ${className}`}
    >
      {children}
    </span>
  )
}

export function SentimentBadge({ sentiment }: { sentiment: string }) {
  const tone: Tone =
    sentiment === 'positive' ? 'positive' : sentiment === 'negative' ? 'negative' : 'neutral'
  return <Badge tone={tone}>{sentiment}</Badge>
}

/* ----------------------------------------------------------- Metric tile */

interface MetricProps {
  label: string
  value: number | null | undefined
  icon?: ReactNode
  suffix?: string
  decimals?: number
  hint?: string
  accent?: string
  delay?: number
}

/**
 * A KPI tile that animates its number and states plainly when the underlying
 * metric was not supplied by the platform API.
 */
export function MetricTile({
  label,
  value,
  icon,
  suffix = '',
  decimals = 0,
  hint,
  accent = 'text-brand',
  delay = 0,
}: MetricProps) {
  const { available } = formatMetric(value, { suffix, decimals })
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card interactive className="group relative overflow-hidden p-4">
        <div
          className="absolute -right-6 -top-6 size-20 rounded-full opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-40"
          style={{ background: accent.includes('positive') ? '#22c55e' : accent.includes('negative') ? '#ef4444' : '#4f7cff' }}
          aria-hidden
        />
        <div className="flex items-center justify-between gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">{label}</p>
          {icon ? <span className={`${accent} opacity-80`}>{icon}</span> : null}
        </div>

        {available ? (
          <AnimatedNumber value={value as number} decimals={decimals} suffix={suffix} />
        ) : (
          <p className="mt-2 text-[11px] leading-snug font-medium text-muted/85 italic">
            Data unavailable through the current platform API.
          </p>
        )}

        {hint && available ? <p className="mt-1 text-[11px] text-muted">{hint}</p> : null}
      </Card>
    </motion.div>
  )
}

/**
 * Counts up to `value` on mount, then settles on the real number.
 *
 * requestAnimationFrame is paused while the tab is hidden, so the final value is
 * rendered immediately in that case rather than leaving a misleading zero on
 * screen. The animation is an enhancement; the number itself is never withheld.
 */
export function AnimatedNumber({
  value,
  decimals = 0,
  suffix = '',
  duration = 900,
}: {
  value: number
  decimals?: number
  suffix?: string
  duration?: number
}) {
  const canAnimate = typeof document === 'undefined' || document.visibilityState !== 'hidden'
  const [display, setDisplay] = useState(canAnimate ? 0 : value)

  useEffect(() => {
    if (typeof document !== 'undefined' && document.visibilityState === 'hidden') {
      setDisplay(value)
      return
    }
    let frame = 0
    const start = performance.now()
    const step = (now: number) => {
      const progress = Math.min(1, (now - start) / duration)
      const eased = 1 - (1 - progress) ** 3 // easeOutCubic
      setDisplay(value * eased)
      if (progress < 1) frame = requestAnimationFrame(step)
      else setDisplay(value)
    }
    frame = requestAnimationFrame(step)
    return () => cancelAnimationFrame(frame)
  }, [value, duration])

  return (
    <p className="mt-1.5 text-2xl font-extrabold tracking-tight text-ink tabular-nums">
      {decimals > 0
        ? display.toLocaleString(undefined, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
          })
        : Math.round(display).toLocaleString()}
      {suffix}
    </p>
  )
}

/* ---------------------------------------------------------------- states */

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-10 text-muted">
      <Loader2 size={20} className="animate-spin-slow" aria-hidden />
      {label ? <span className="text-sm">{label}</span> : null}
    </div>
  )
}

export function Skeleton({ className = 'h-4 w-full' }: { className?: string }) {
  return <div className={`skeleton ${className}`} aria-hidden />
}

export function CardSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <Card className="space-y-3 p-5">
      <Skeleton className="h-4 w-1/3" />
      {Array.from({ length: rows }).map((_, index) => (
        <Skeleton key={index} className="h-3 w-full" />
      ))}
    </Card>
  )
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
      {icon ? (
        <span className="grid size-14 place-items-center rounded-2xl bg-brand/10 text-brand">
          {icon}
        </span>
      ) : null}
      <h3 className="text-base font-bold text-ink">{title}</h3>
      {description ? <p className="max-w-md text-sm text-muted">{description}</p> : null}
      {action}
    </div>
  )
}

const TONE_STYLES = {
  error: { icon: <XCircle size={18} />, ring: 'ring-negative/30', text: 'text-negative' },
  success: { icon: <CheckCircle2 size={18} />, ring: 'ring-positive/30', text: 'text-positive' },
  info: { icon: <Info size={18} />, ring: 'ring-brand/30', text: 'text-brand' },
  warning: { icon: <AlertTriangle size={18} />, ring: 'ring-amber-500/30', text: 'text-amber-500' },
}

export function Alert({
  tone = 'info',
  title,
  children,
  action,
}: {
  tone?: keyof typeof TONE_STYLES
  title?: string
  children?: ReactNode
  action?: ReactNode
}) {
  const style = TONE_STYLES[tone]
  return (
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      className={`flex items-start gap-3 rounded-xl bg-ink/4 p-4 ring-1 ${style.ring}`}
    >
      <span className={`mt-0.5 shrink-0 ${style.text}`}>{style.icon}</span>
      <div className="min-w-0 flex-1 text-sm">
        {title ? <p className="font-semibold text-ink">{title}</p> : null}
        {children ? <div className="text-muted">{children}</div> : null}
      </div>
      {action}
    </div>
  )
}

/** The prominent, unmissable banner shown for every demo analysis. */
export function DemoBanner({ message }: { message?: string }) {
  return (
    <div
      role="status"
      className="flex items-start gap-3 rounded-xl border border-amber-500/35 bg-amber-500/10 p-4"
    >
      <AlertTriangle size={18} className="mt-0.5 shrink-0 text-amber-500" />
      <div className="text-sm">
        <p className="font-bold text-amber-600 dark:text-amber-400">
          DEMO DATA — This dataset is included for demonstration purposes and is not live
          social-media data.
        </p>
        {message ? <p className="mt-1 text-xs text-muted">{message}</p> : null}
      </div>
    </div>
  )
}

/* -------------------------------------------------------------- controls */

export function Select({
  label,
  value,
  onChange,
  options,
  className = '',
  id,
}: {
  label?: string
  value: string
  onChange: (value: string) => void
  options: { value: string; label: string }[]
  className?: string
  id?: string
}) {
  const selectId = id ?? `select-${label?.toLowerCase().replace(/\s+/g, '-')}`
  return (
    <div className={className}>
      {label ? (
        <label htmlFor={selectId} className="mb-1.5 block text-[11px] font-semibold text-muted">
          {label}
        </label>
      ) : null}
      <select
        id={selectId}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-xl border border-line bg-surface px-3 py-2.5 text-sm text-ink outline-none transition focus:border-brand"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}

export function SearchInput({
  value,
  onChange,
  placeholder = 'Search…',
  className = '',
}: {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}) {
  return (
    <div className={`relative ${className}`}>
      <input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
        className="w-full rounded-xl border border-line bg-surface px-3.5 py-2.5 pr-9 text-sm text-ink outline-none transition placeholder:text-muted/70 focus:border-brand"
      />
      {value ? (
        <button
          type="button"
          onClick={() => onChange('')}
          aria-label="Clear search"
          className="absolute top-1/2 right-2.5 -translate-y-1/2 text-muted transition hover:text-ink"
        >
          <XCircle size={15} />
        </button>
      ) : null}
    </div>
  )
}

export function ProgressBar({ value, tone = 'brand' }: { value: number; tone?: 'brand' | 'positive' | 'negative' }) {
  const colors = { brand: 'from-brand to-brand-2', positive: 'from-positive to-emerald-400', negative: 'from-negative to-rose-400' }
  return (
    <div
      className="h-2 w-full overflow-hidden rounded-full bg-ink/8"
      role="progressbar"
      aria-valuenow={Math.round(value)}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className={`h-full rounded-full bg-linear-to-r ${colors[tone]} transition-[width] duration-700 ease-out`}
        style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
      />
    </div>
  )
}

export function SectionTitle({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle?: string
  action?: ReactNode
}) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 className="text-lg font-extrabold tracking-tight text-ink">{title}</h2>
        {subtitle ? <p className="mt-0.5 text-sm text-muted">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  )
}

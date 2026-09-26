import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import {
  AlertCircle,
  Check,
  CheckCircle2,
  Link2,
  Loader2,
  Play,
  Sparkles,
  Youtube,
  Facebook,
  Instagram,
} from 'lucide-react'
import { useApp } from '../context/app-context'
import { ApiError, analyzeUrl, detectPlatform, runDemo } from '../services/api'
import type { DetectResult, PlatformKey } from '../types'
import { Alert, Badge, Button, Card, DemoBanner, SectionTitle } from '../components/ui'

const PLATFORM_ICONS: Record<PlatformKey, typeof Youtube> = {
  youtube: Youtube,
  facebook: Facebook,
  instagram: Instagram,
}

/** The nine pipeline stages, shown as a live checklist while the API runs. */
const STAGES = [
  'Validating URL',
  'Detecting platform',
  'Collecting available data',
  'Cleaning dataset',
  'Processing comments',
  'Running sentiment analysis',
  'Calculating engagement metrics',
  'Generating visualizations',
  'Preparing downloadable dataset',
]

const EXAMPLE_URLS: Record<PlatformKey, string> = {
  youtube: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
  facebook: 'https://www.facebook.com/1234567890/posts/1234567890',
  instagram: 'https://www.instagram.com/p/C1AbCdEfGhI/',
}

export function NewAnalysisPage() {
  const { userName, platforms, demoModeEnabled, pushToast } = useApp()
  const navigate = useNavigate()

  const [url, setUrl] = useState('')
  const [detected, setDetected] = useState<DetectResult | null>(null)
  const [detectError, setDetectError] = useState('')
  const [detecting, setDetecting] = useState(false)

  const [running, setRunning] = useState(false)
  const [runError, setRunError] = useState('')
  const [stageIndex, setStageIndex] = useState(0)
  const [done, setDone] = useState(false)

  const detectTimer = useRef<number | null>(null)
  const stageTimer = useRef<number | null>(null)

  // Clear timers on unmount so no state update happens after navigation.
  useEffect(
    () => () => {
      if (detectTimer.current) window.clearTimeout(detectTimer.current)
      if (stageTimer.current) window.clearTimeout(stageTimer.current)
    },
    [],
  )

  /** Debounced live detection so the user sees the platform while typing. */
  useEffect(() => {
    if (detectTimer.current) window.clearTimeout(detectTimer.current)
    const candidate = url.trim()
    if (!candidate) {
      setDetected(null)
      setDetectError('')
      return
    }
    setDetecting(true)
    detectTimer.current = window.setTimeout(async () => {
      try {
        const result = await detectPlatform(candidate)
        setDetected(result)
        setDetectError('')
      } catch (error) {
        setDetected(null)
        setDetectError(error instanceof ApiError ? error.message : 'Could not read that URL.')
      } finally {
        setDetecting(false)
      }
    }, 550)
  }, [url])

  /** Advance the visible checklist while the server-side pipeline runs. */
  const startStageTicker = useCallback(() => {
    setStageIndex(0)
    let index = 0
    const advance = () => {
      index += 1
      if (index >= STAGES.length) return
      setStageIndex(index)
      stageTimer.current = window.setTimeout(advance, 420)
    }
    stageTimer.current = window.setTimeout(advance, 420)
  }, [])

  const stopStageTicker = () => {
    if (stageTimer.current) window.clearTimeout(stageTimer.current)
    stageTimer.current = null
  }

  const runLive = async () => {
    if (!url.trim()) return
    setRunning(true)
    setRunError('')
    setDone(false)
    startStageTicker()
    try {
      const analysis = await analyzeUrl(url.trim(), userName ?? undefined)
      setDone(true)
      pushToast('Analysis complete', 'success')
      // Let the final checklist item render before navigating.
      setTimeout(() => navigate(`/analysis/${analysis.analysis_id}`), 900)
    } catch (error) {
      stopStageTicker()
      setRunError(
        error instanceof ApiError
          ? error.message
          : 'The analysis could not be completed. Please try again.',
      )
      setDone(false)
      pushToast('Analysis failed', 'error')
    } finally {
      setRunning(false)
    }
  }

  const runDemoAnalysis = async (platform: PlatformKey) => {
    setRunning(true)
    setRunError('')
    setDone(false)
    startStageTicker()
    try {
      const analysis = await runDemo(platform, userName ?? undefined)
      setDone(true)
      pushToast('Demo analysis complete', 'success')
      setTimeout(() => navigate(`/analysis/${analysis.analysis_id}`), 900)
    } catch (error) {
      stopStageTicker()
      setRunError(error instanceof ApiError ? error.message : 'The demo analysis could not be run.')
      pushToast('Demo analysis failed', 'error')
    } finally {
      setRunning(false)
    }
  }

  const platformConfigured = (key: PlatformKey) => platforms.find((item) => item.key === key)?.configured

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <SectionTitle
        title="New Analysis"
        subtitle="Paste a public YouTube, Facebook or Instagram link to begin."
      />

      <Card className="overflow-visible p-6 sm:p-8">
        <label htmlFor="social-url" className="mb-2.5 block text-xs font-semibold text-muted">
          Paste your YouTube, Facebook or Instagram URL
        </label>

        <div className="relative">
          <Link2
            size={19}
            className="pointer-events-none absolute top-1/2 left-4 -translate-y-1/2 text-muted"
            aria-hidden
          />
          <input
            id="social-url"
            type="url"
            inputMode="url"
            value={url}
            onChange={(event) => {
              setUrl(event.target.value)
              setRunError('')
            }}
            placeholder="https://www.youtube.com/watch?v=…"
            disabled={running}
            className="w-full rounded-2xl border border-line bg-surface-2 py-4 pr-14 pl-12 text-base text-ink outline-none transition placeholder:text-muted/60 focus:border-brand focus:ring-2 focus:ring-brand/25 disabled:opacity-60"
          />
          <div className="absolute top-1/2 right-4 -translate-y-1/2">
            {detecting ? (
              <Loader2 size={17} className="animate-spin-slow text-muted" aria-label="Detecting platform" />
            ) : null}
          </div>
        </div>

        {/* Detection result */}
        <div className="mt-3 min-h-[26px]" aria-live="polite">
          <AnimatePresence mode="wait">
            {detected ? (
              <motion.div
                key={`detected-${detected.platform}`}
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                className="flex flex-wrap items-center gap-2"
              >
                <Badge tone="positive" className="px-3 py-1 text-xs">
                  <Check size={12} /> Platform detected successfully
                </Badge>
                <span className="flex items-center gap-1.5 text-sm font-semibold text-ink">
                  {(() => {
                    const Icon = PLATFORM_ICONS[detected.platform]
                    return <Icon size={15} className="text-brand" />
                  })()}
                  Detected Platform: {detected.platform_label}
                </span>
                {!detected.configured ? (
                  <Badge tone="warning">API not configured</Badge>
                ) : (
                  <Badge tone="brand">API ready</Badge>
                )}
              </motion.div>
            ) : detectError ? (
              <motion.p
                key="detect-error"
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                className="flex items-center gap-1.5 text-sm font-medium text-negative"
              >
                <AlertCircle size={14} />
                {detectError}
              </motion.p>
            ) : null}
          </AnimatePresence>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <Button
            size="lg"
            fullWidth
            onClick={runLive}
            loading={running}
            disabled={!url.trim() || !detected}
            icon={<Play size={17} />}
            className="animate-pulse-ring"
          >
            Analyze Now
          </Button>
        </div>

        {!detected && url.trim() ? (
          <p className="mt-3 text-xs text-muted">
            Enter a supported URL to enable live analysis. Detection happens automatically.
          </p>
        ) : null}
      </Card>

      {runError ? (
        <Alert tone="error" title="Analysis could not start">
          {runError}
        </Alert>
      ) : null}

      {/* Progress checklist */}
      <AnimatePresence>
        {running || done ? (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <Card className="p-6">
              <div className="mb-4 flex items-center gap-3">
                {!done ? (
                  <Loader2 size={18} className="animate-spin-slow text-brand" aria-hidden />
                ) : (
                  <CheckCircle2 size={18} className="text-positive" aria-hidden />
                )}
                <h3 className="text-sm font-bold text-ink">
                  {done ? 'Analysis Complete 🎉' : 'Analyzing your content…'}
                </h3>
              </div>

              <ol className="grid gap-2 sm:grid-cols-2">
                {STAGES.map((stage, index) => {
                  const complete = done || index < stageIndex
                  const active = !done && index === stageIndex
                  return (
                    <motion.li
                      key={stage}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.04 }}
                      className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors ${
                        active ? 'bg-brand/10 text-ink' : complete ? 'text-positive' : 'text-muted'
                      }`}
                    >
                      <span className="grid size-5 shrink-0 place-items-center">
                        {complete ? (
                          <Check size={14} className="text-positive" />
                        ) : active ? (
                          <Loader2 size={14} className="animate-spin-slow text-brand" />
                        ) : (
                          <span className="size-1.5 rounded-full bg-current opacity-40" />
                        )}
                      </span>
                      {stage}
                    </motion.li>
                  )
                })}
              </ol>
            </Card>
          </motion.div>
        ) : null}
      </AnimatePresence>

      {/* Demo mode */}
      {demoModeEnabled ? (
        <Card className="p-6">
          <div className="mb-4 flex items-center gap-2.5">
            <Sparkles size={17} className="text-brand" aria-hidden />
            <h3 className="text-sm font-bold text-ink">Demo Mode</h3>
            <Badge tone="warning">Synthetic data</Badge>
          </div>

          <DemoBanner message="Run the full pipeline on a bundled sample dataset. Useful for demonstrations and for testing before API keys are configured." />

          <p className="mt-4 text-sm text-muted">
            Choose a platform to analyse its bundled sample dataset. Every metric produced will be
            clearly marked as demo data, including inside the CSV, Excel and report exports.
          </p>

          <div className="mt-4 grid gap-2.5 sm:grid-cols-3">
            {(['youtube', 'facebook', 'instagram'] as PlatformKey[]).map((platform) => {
              const Icon = PLATFORM_ICONS[platform]
              return (
                <Button
                  key={platform}
                  variant="secondary"
                  loading={running}
                  onClick={() => runDemoAnalysis(platform)}
                  icon={<Icon size={15} />}
                >
                  {platform.charAt(0).toUpperCase() + platform.slice(1)}
                </Button>
              )
            })}
          </div>

          <details className="mt-5">
            <summary className="cursor-pointer text-xs font-semibold text-muted hover:text-ink">
              Example live URLs
            </summary>
            <ul className="mt-2.5 space-y-1.5">
              {(Object.keys(EXAMPLE_URLS) as PlatformKey[]).map((platform) => (
                <li key={platform} className="flex items-center gap-2 text-xs">
                  <Badge tone={platformConfigured(platform) ? 'brand' : 'muted'}>
                    {platform.charAt(0).toUpperCase() + platform.slice(1)}
                  </Badge>
                  <code className="truncate text-muted">{EXAMPLE_URLS[platform]}</code>
                </li>
              ))}
            </ul>
          </details>
        </Card>
      ) : null}
    </div>
  )
}

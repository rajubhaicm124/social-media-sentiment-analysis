import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Database, Eye, Gauge, History as HistoryIcon, Trash2 } from 'lucide-react'
import { useHistory } from '../hooks/useAnalysis'
import { downloadExport } from '../services/api'
import { useApp } from '../context/app-context'
import {
  Alert,
  Badge,
  Button,
  Card,
  CardSkeleton,
  DemoBanner,
  EmptyState,
  SearchInput,
  Select,
  SectionTitle,
} from '../components/ui'
import { formatDateTime, formatPercent, formatScore, platformLabel, shortUrl } from '../utils/format'

export function HistoryPage() {
  const { data: history, loading, error, remove } = useHistory()
  const { pushToast } = useApp()
  const [search, setSearch] = useState('')
  const [platform, setPlatform] = useState('all')
  const [confirming, setConfirming] = useState<string | null>(null)
  const [busyExport, setBusyExport] = useState<string | null>(null)

  const filtered = (history ?? []).filter((item) => {
    if (platform !== 'all' && item.platform !== platform) return false
    if (!search.trim()) return true
    const needle = search.toLowerCase()
    return (
      (item.title ?? '').toLowerCase().includes(needle) ||
      item.url.toLowerCase().includes(needle) ||
      (item.author ?? '').toLowerCase().includes(needle)
    )
  })

  const deleteItem = async (id: string) => {
    setConfirming(id)
    try {
      await remove(id)
      pushToast('Analysis deleted', 'success')
    } catch {
      pushToast('The analysis could not be deleted.', 'error')
    } finally {
      setConfirming(null)
    }
  }

  const exportCsv = async (id: string, platformKey: string) => {
    setBusyExport(id)
    try {
      await downloadExport(id, 'csv', { platform: platformKey })
      pushToast('CSV downloaded', 'success')
    } catch (error) {
      pushToast(error instanceof Error ? error.message : 'The export failed.', 'error')
    } finally {
      setBusyExport(null)
    }
  }

  return (
    <div className="space-y-6">
      <SectionTitle
        title="Analysis History"
        subtitle="Every saved run with its sentiment summary, downloadable or removable."
      />

      {error ? (
        <Alert tone="error" title="Could not load history">
          {error}
        </Alert>
      ) : null}

      {loading ? (
        <CardSkeleton rows={6} />
      ) : !history || history.length === 0 ? (
        <Card>
          <EmptyState
            icon={<HistoryIcon size={24} />}
            title="No saved analyses"
            description="Analyses are saved automatically and listed here with their sentiment summary."
            action={
              <Link to="/analyze" className="mt-1">
                <Button icon={<Gauge size={15} />}>Run an analysis</Button>
              </Link>
            }
          />
        </Card>
      ) : (
        <>
          <Card className="flex flex-wrap items-center gap-3 p-4">
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder="Search by title, URL or author…"
              className="min-w-[220px] flex-1"
            />
            <Select
              value={platform}
              onChange={setPlatform}
              options={[
                { value: 'all', label: 'All platforms' },
                { value: 'youtube', label: 'YouTube' },
                { value: 'facebook', label: 'Facebook' },
                { value: 'instagram', label: 'Instagram' },
              ]}
              className="w-44"
            />
            <Badge tone="muted">
              {filtered.length} of {history.length}
            </Badge>
          </Card>

          {history.some((item) => item.data_mode === 'demo') ? (
            <DemoBanner message="Demo analyses are stored alongside live runs and are clearly marked in the list and in every export." />
          ) : null}

          <div className="space-y-3">
            <AnimatePresence initial={false}>
              {filtered.map((item) => (
                <motion.div
                  key={item.analysis_id}
                  layout
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                >
                  <Card className="p-5">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge tone="brand">{platformLabel(item.platform)}</Badge>
                          {item.data_mode === 'demo' ? (
                            <Badge tone="warning">Demo</Badge>
                          ) : (
                            <Badge tone="positive">Live</Badge>
                          )}
                          <span className="text-[11px] text-muted">
                            {formatDateTime(item.created_at)}
                          </span>
                        </div>

                        <Link
                          to={`/analysis/${item.analysis_id}`}
                          className="mt-2 block truncate text-sm font-semibold text-ink hover:text-brand"
                        >
                          {item.title ?? shortUrl(item.url, 60)}
                        </Link>
                        <p className="mt-0.5 truncate text-[11px] text-muted">{shortUrl(item.url, 70)}</p>
                      </div>

                      <div className="flex flex-wrap items-center gap-5 text-right">
                        {[
                          { label: 'Records', value: item.total_records.toLocaleString() },
                          { label: 'Positive', value: formatPercent(item.positive_pct, 0) },
                          { label: 'Negative', value: formatPercent(item.negative_pct, 0) },
                          { label: 'Sentiment', value: formatScore(item.avg_sentiment, 2) },
                        ].map((stat) => (
                          <div key={stat.label}>
                            <p className="text-[10px] text-muted">{stat.label}</p>
                            <p className="text-sm font-bold tabular-nums text-ink">{stat.value}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Sentiment split bar */}
                    <div className="mt-4 flex h-2 overflow-hidden rounded-full bg-ink/6">
                      {(['positive_pct', 'neutral_pct', 'negative_pct'] as const).map((key) => {
                        const value = item[key] ?? 0
                        const colors = {
                          positive_pct: 'bg-positive',
                          neutral_pct: 'bg-neutral',
                          negative_pct: 'bg-negative',
                        }
                        return value > 0 ? (
                          <div
                            key={key}
                            className={colors[key]}
                            style={{ width: `${value}%` }}
                            title={`${key.replace('_pct', '')}: ${formatPercent(value)}`}
                          />
                        ) : null
                      })}
                    </div>

                    <div className="mt-4 flex flex-wrap items-center gap-2">
                      <Link to={`/analysis/${item.analysis_id}`}>
                        <Button size="sm" variant="secondary" icon={<Eye size={13} />}>
                          View
                        </Button>
                      </Link>
                      <Button
                        size="sm"
                        variant="secondary"
                        loading={busyExport === item.analysis_id}
                        onClick={() => exportCsv(item.analysis_id, item.platform)}
                        icon={<Database size={13} />}
                      >
                        CSV
                      </Button>
                      {confirming === item.analysis_id ? (
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="danger"
                            onClick={() => deleteItem(item.analysis_id)}
                            icon={<Trash2 size={13} />}
                          >
                            Confirm delete
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => setConfirming(null)}>
                            Cancel
                          </Button>
                        </div>
                      ) : (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setConfirming(item.analysis_id)}
                          icon={<Trash2 size={13} />}
                        >
                          Delete
                        </Button>
                      )}
                    </div>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>

            {filtered.length === 0 ? (
              <Card>
                <EmptyState
                  title="No matching analyses"
                  description="Try a different search term or platform filter."
                />
              </Card>
            ) : null}
          </div>
        </>
      )}
    </div>
  )
}

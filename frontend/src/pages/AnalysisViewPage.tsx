import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  AlertTriangle,
  Clock,
  Database,
  Download,
  Eye,
  FileSpreadsheet,
  FileText,
  Gauge,
  Heart,
  MessageSquare,
  Repeat,
  Share2,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
import { useAnalysis, useHistory } from '../hooks/useAnalysis'
import { downloadExport } from '../services/api'
import { useApp } from '../context/app-context'
import {
  Alert,
  Badge,
  Button,
  Card,
  CardHeader,
  CardSkeleton,
  DemoBanner,
  EmptyState,
  MetricTile,
  ProgressBar,
  SectionTitle,
} from '../components/ui'
import {
  CommentLengthChart,
  CorrelationHeatmap,
  EngagementBarChart,
  HashtagChart,
  HourlyActivityChart,
  KeywordChart,
  SentimentDonutChart,
  SentimentScoreChart,
  SentimentTrendChart,
  WordCloud,
} from '../components/charts'
import { RecordsTable } from '../components/RecordsTable'
import { formatDateTime, formatPercent, formatScore, platformLabel, shortUrl } from '../utils/format'
import type { TimeSeriesPoint } from '../types'

export function AnalysisViewPage() {
  const { analysisId } = useParams<{ analysisId: string }>()
  const { data: history } = useHistory()

  // With no id in the route (e.g. /analytics), fall back to the newest analysis.
  const resolvedId = analysisId ?? history?.[0]?.analysis_id
  const { data: analysis, loading, error } = useAnalysis(resolvedId)
  const { userName, pushToast } = useApp()
  const [exporting, setExporting] = useState<string | null>(null)

  const exportFile = async (
    kind: 'csv' | 'excel' | 'report',
    options: { dataset?: 'clean' | 'raw'; format?: 'html' | 'pdf' } = {},
  ) => {
    if (!analysis) return
    const key = `${kind}-${options.dataset ?? options.format ?? ''}`
    setExporting(key)
    try {
      await downloadExport(analysis.analysis_id, kind, { ...options, platform: analysis.platform })
      pushToast(`${kind.toUpperCase()} downloaded`, 'success')
    } catch (err) {
      pushToast(err instanceof Error ? err.message : 'The export failed.', 'error')
    } finally {
      setExporting(null)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-8 w-56" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, index) => (
            <CardSkeleton key={index} rows={2} />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Alert tone="error" title="Analysis unavailable">
        <p>{error}</p>
        <Link to="/analyze" className="mt-2 inline-block font-semibold text-brand hover:underline">
          Start a new analysis
        </Link>
      </Alert>
    )
  }

  if (!analysis) {
    return (
      <Card>
        <EmptyState
          icon={<Gauge size={24} />}
          title="No analysis selected"
          description="Run an analysis or pick one from your history to see charts, statistics and exports."
          action={
            <Link to="/analyze" className="mt-2">
              <Button icon={<Sparkles size={15} />}>New Analysis</Button>
            </Link>
          }
        />
      </Card>
    )
  }

  const { engagement, sentiment_summary: summary, statistics, charts } = analysis
  const content = analysis.content as Record<string, string | number | null>
  const title = (content.title as string) || (content.caption as string) || 'Untitled content'
  const author =
    (content.channel_name as string) ||
    (content.page_name as string) ||
    (content.username as string) ||
    '—'
  const dailyPoints = (analysis.trends as { daily?: { points: TimeSeriesPoint[] } }).daily?.points ?? []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="brand">{platformLabel(analysis.platform)}</Badge>
            {analysis.data_mode === 'demo' ? (
              <Badge tone="warning">Demo data</Badge>
            ) : (
              <Badge tone="positive">Live API</Badge>
            )}
            <Badge tone="muted">{analysis.sentiment_method ?? 'n/a'}</Badge>
          </div>
          <h1 className="mt-2 truncate text-2xl font-extrabold tracking-tight text-ink">{title}</h1>
          <p className="mt-1 text-sm text-muted">
            {author} · {formatDateTime(analysis.created_at)} · analysed by{' '}
            {analysis.user_name ?? userName ?? 'unknown'}
          </p>
          <a
            href={analysis.source_url}
            target="_blank"
            rel="noreferrer noopener"
            className="mt-1 inline-block text-xs text-brand hover:underline"
          >
            {shortUrl(analysis.source_url, 64)}
          </a>
        </div>
      </div>

      {analysis.data_mode === 'demo' ? <DemoBanner message={analysis.demo_notice} /> : null}

      {/* Exports */}
      <Card className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="flex items-center gap-2 text-sm font-bold text-ink">
              <Download size={16} className="text-brand" /> Download
            </h2>
            <p className="mt-1 text-xs text-muted">
              Generated from this stored analysis. Unavailable metrics are left blank, never zero.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant="secondary"
              loading={exporting === 'csv-clean'}
              onClick={() => exportFile('csv', { dataset: 'clean' })}
              icon={<FileText size={14} />}
            >
              CSV
            </Button>
            <Button
              size="sm"
              variant="secondary"
              loading={exporting === 'csv-raw'}
              onClick={() => exportFile('csv', { dataset: 'raw' })}
              icon={<Database size={14} />}
            >
              Raw CSV
            </Button>
            <Button
              size="sm"
              variant="secondary"
              loading={exporting === 'excel'}
              onClick={() => exportFile('excel')}
              icon={<FileSpreadsheet size={14} />}
            >
              Excel
            </Button>
            <Button
              size="sm"
              variant="secondary"
              loading={exporting === 'report-pdf'}
              onClick={() => exportFile('report', { format: 'pdf' })}
              icon={<FileText size={14} />}
            >
              Report (PDF)
            </Button>
            <Button
              size="sm"
              variant="secondary"
              loading={exporting === 'report-html'}
              onClick={() => exportFile('report', { format: 'html' })}
              icon={<FileText size={14} />}
            >
              Report (HTML)
            </Button>
          </div>
        </div>
      </Card>

      {/* Overview metrics */}
      <div>
        <SectionTitle
          title="Overview"
          subtitle="Counters animate on load; missing metrics are labelled."
        />
        <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
          <MetricTile label="Views" value={engagement.views} icon={<Eye size={15} />} delay={0.02} />
          <MetricTile
            label="Likes"
            value={engagement.likes}
            icon={<Heart size={15} />}
            accent="text-negative"
            delay={0.05}
          />
          <MetricTile
            label="Comments"
            value={engagement.comments}
            icon={<MessageSquare size={15} />}
            accent="text-brand-3"
            delay={0.08}
          />
          <MetricTile
            label="Shares"
            value={engagement.shares}
            icon={<Share2 size={15} />}
            accent="text-brand-2"
            delay={0.11}
          />
          <MetricTile
            label="Engagement Rate"
            value={engagement.engagement_rate}
            suffix="%"
            decimals={2}
            icon={<TrendingUp size={15} />}
            delay={0.14}
            hint={
              engagement.engagement_rate_available
                ? `(${engagement.interactions_included.join(' + ')}) / views x 100`
                : undefined
            }
          />
          <MetricTile
            label="Positive %"
            value={summary.positive_pct}
            suffix="%"
            decimals={1}
            accent="text-positive"
            delay={0.17}
          />
          <MetricTile label="Neutral %" value={summary.neutral_pct} suffix="%" decimals={1} delay={0.2} />
          <MetricTile
            label="Negative %"
            value={summary.negative_pct}
            suffix="%"
            decimals={1}
            accent="text-negative"
            delay={0.23}
          />
          <MetricTile
            label="Text Records"
            value={analysis.total_records}
            icon={<Database size={15} />}
            delay={0.26}
            hint={`${analysis.removed_records} removed while cleaning`}
          />
          <MetricTile
            label="Analysis Time"
            value={analysis.analysis_seconds}
            suffix="s"
            decimals={2}
            icon={<Clock size={15} />}
            delay={0.29}
          />
          <MetricTile
            label="Avg Sentiment"
            value={summary.avg_compound}
            decimals={3}
            icon={<Sparkles size={15} />}
            delay={0.32}
          />
          <MetricTile
            label="Avg Subjectivity"
            value={summary.avg_subjectivity}
            decimals={3}
            delay={0.35}
          />
        </div>
      </div>

      {/* Data availability notice */}
      {analysis.unavailable_fields.length > 0 ? (
        <Alert tone="warning" title="Some fields are unavailable for this content">
          <p>
            The following were not returned by the {platformLabel(analysis.platform)} API and are
            reported as unavailable rather than estimated:{' '}
            <span className="font-semibold">{analysis.unavailable_fields.join(', ')}</span>.
          </p>
        </Alert>
      ) : null}

      {/* Engagement + sentiment */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader
            title="Engagement"
            subtitle="Blank bars mean the API did not return that metric."
            icon={<TrendingUp size={16} />}
          />
          <div className="p-4">
            <EngagementBarChart charts={charts} />
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Sentiment Distribution"
            subtitle="Share of analysed text records"
            icon={<Sparkles size={16} />}
          />
          <div className="p-4">
            <SentimentDonutChart summary={summary} />
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Sentiment Score"
            subtitle="VADER scores with TextBlob comparison"
            icon={<Gauge size={16} />}
          />
          <div className="p-4">
            <SentimentScoreChart summary={summary} />
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Sentiment Over Time"
            subtitle="Daily volume by sentiment"
            icon={<Clock size={16} />}
            action={charts.sentiment_timeline.available ? undefined : <Badge tone="muted">No timestamps</Badge>}
          />
          <div className="p-4">
            {charts.sentiment_timeline.available ? (
              <SentimentTrendChart points={dailyPoints} />
            ) : (
              <EmptyState
                icon={<Clock size={22} />}
                title="No timestamps available"
                description="The platform did not return usable publication timestamps, so a trend cannot be calculated."
              />
            )}
          </div>
        </Card>
      </div>

      {/* Text & comment characteristics */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader
            title="Comment Length"
            subtitle="Distribution of cleaned text length"
            icon={<MessageSquare size={16} />}
          />
          <div className="p-4">
            <CommentLengthChart charts={charts} />
            <dl className="mt-4 grid grid-cols-3 gap-3 text-center">
              {[
                { label: 'Mean', value: statistics.comment_length.characters.mean },
                { label: 'Min', value: statistics.comment_length.characters.min },
                { label: 'Max', value: statistics.comment_length.characters.max },
              ].map((row) => (
                <div key={row.label} className="rounded-xl bg-ink/4 p-3">
                  <dt className="text-[11px] text-muted">{row.label}</dt>
                  <dd className="mt-1 text-sm font-bold text-ink tabular-nums">
                    {row.value === null ? '—' : Math.round(row.value).toLocaleString()}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Activity by Hour"
            subtitle={
              statistics.hourly.peak_hour
                ? `Peak around ${statistics.hourly.peak_hour}`
                : 'No timestamp data'
            }
            icon={<Clock size={16} />}
          />
          <div className="p-4">
            {statistics.hourly.available ? (
              <HourlyActivityChart charts={charts} />
            ) : (
              <EmptyState title="No timestamps available" />
            )}
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Top Keywords"
            subtitle="Stopwords removed, TF-IDF weighted"
            icon={<Sparkles size={16} />}
          />
          <div className="p-4">
            {analysis.keywords.length ? (
              <KeywordChart keywords={charts.keyword_bars} />
            ) : (
              <EmptyState title="No keywords extracted" />
            )}
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Word Cloud"
            subtitle={`${charts.word_cloud.length} frequent terms`}
            icon={<Sparkles size={16} />}
          />
          <div className="p-4">
            <WordCloud terms={charts.word_cloud} />
          </div>
        </Card>
      </div>

      {/* Hashtags */}
      {analysis.hashtags.length > 0 ? (
        <Card>
          <CardHeader
            title="Hashtag Analysis"
            subtitle="Frequency with mean sentiment of records using each hashtag"
            icon={<Repeat size={16} />}
          />
          <div className="grid gap-4 p-4 lg:grid-cols-2">
            <HashtagChart hashtags={charts.hashtag_bars} />
            <div className="max-h-[300px] overflow-y-auto">
              <table className="data-table w-full text-sm">
                <thead>
                  <tr className="border-b border-line text-left text-[11px] tracking-wide text-muted uppercase">
                    <th className="py-2 pr-3">Hashtag</th>
                    <th className="py-2 pr-3">Count</th>
                    <th className="py-2 pr-3">Avg Sentiment</th>
                    <th className="py-2">Tone</th>
                  </tr>
                </thead>
                <tbody>
                  {analysis.hashtags.map((row) => (
                    <tr key={row.hashtag} className="border-b border-line/60 last:border-0">
                      <td className="py-2 pr-3 font-medium text-ink">#{row.hashtag}</td>
                      <td className="py-2 pr-3 tabular-nums text-muted">{row.count}</td>
                      <td className="py-2 pr-3 tabular-nums text-muted">
                        {formatScore(row.avg_sentiment)}
                      </td>
                      <td className="py-2">
                        <Badge
                          tone={
                            row.sentiment === 'positive'
                              ? 'positive'
                              : row.sentiment === 'negative'
                                ? 'negative'
                                : 'neutral'
                          }
                        >
                          {row.sentiment}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </Card>
      ) : null}

      {/* Correlations */}
      {statistics.correlations.pairs.length > 0 ? (
        <Card>
          <CardHeader
            title="Correlation Matrix"
            subtitle="Pearson r between numeric fields"
            icon={<TrendingUp size={16} />}
          />
          <div className="grid gap-4 p-4 lg:grid-cols-2">
            <CorrelationHeatmap
              fields={statistics.correlations.fields}
              matrix={statistics.correlations.matrix}
            />
            <div className="space-y-2.5">
              {statistics.correlations.pairs.slice(0, 6).map((pair) => (
                <div key={`${pair.x}-${pair.y}`} className="rounded-xl bg-ink/4 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs font-semibold text-ink">
                      {pair.x} vs {pair.y}
                    </p>
                    <span className="text-xs font-bold tabular-nums text-brand">
                      {pair.coefficient}
                    </span>
                  </div>
                  <div className="mt-2">
                    <ProgressBar
                      value={Math.abs(pair.coefficient) * 100}
                      tone={pair.direction === 'positive' ? 'positive' : 'negative'}
                    />
                  </div>
                  <p className="mt-1.5 text-[11px] text-muted">
                    {pair.strength} {pair.direction} relationship
                  </p>
                </div>
              ))}
            </div>
          </div>
        </Card>
      ) : null}

      {/* Cleaning report */}
      <Card>
        <CardHeader
          title="Data Cleaning Pipeline"
          subtitle={`${analysis.cleaning_report.input_count} collected -> ${analysis.cleaning_report.output_count} analysable`}
          icon={<Database size={16} />}
        />
        <div className="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: 'Collected', value: analysis.cleaning_report.input_count },
            { label: 'Empty removed', value: analysis.cleaning_report.removed_empty },
            { label: 'Duplicates removed', value: analysis.cleaning_report.removed_duplicate },
            { label: 'Spam removed', value: analysis.cleaning_report.removed_spam },
          ].map((item) => (
            <div key={item.label} className="rounded-xl bg-ink/4 p-4 text-center">
              <p className="text-[11px] text-muted">{item.label}</p>
              <p className="mt-1 text-xl font-extrabold tabular-nums text-ink">{item.value}</p>
              <div className="mt-2">
                <ProgressBar
                  value={
                    analysis.cleaning_report.input_count
                      ? (item.value / analysis.cleaning_report.input_count) * 100
                      : 0
                  }
                  tone={item.label === 'Collected' ? 'brand' : 'negative'}
                />
              </div>
            </div>
          ))}
        </div>
        <ol className="space-y-1.5 border-t border-line px-5 py-4">
          {analysis.cleaning_report.steps.map((step) => (
            <li key={step.step} className="flex items-center justify-between gap-3 text-xs">
              <span className="font-medium text-ink">{step.step}</span>
              <span className="text-right text-muted">{step.detail}</span>
            </li>
          ))}
        </ol>
      </Card>

      {/* Insights */}
      <Card>
        <CardHeader
          title="Insights"
          subtitle="Generated from calculated values; AI-summarised statements are kept separate from raw statistics"
          icon={<Sparkles size={16} />}
        />
        <div className="grid gap-3 p-5 sm:grid-cols-2">
          {analysis.insights.map((insight, index) => (
            <motion.div
              key={insight.title}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="rounded-xl border border-line bg-ink/3 p-4"
            >
              <p className="text-xs font-bold text-brand">{insight.title}</p>
              <p className="mt-1.5 text-sm leading-relaxed text-muted">{insight.text}</p>
            </motion.div>
          ))}
        </div>
      </Card>

      {/* Top comments */}
      <div className="grid gap-4 lg:grid-cols-3">
        {(
          [
            { key: 'most_liked', title: 'Most Liked' },
            { key: 'most_positive', title: 'Most Positive' },
            { key: 'most_negative', title: 'Most Negative' },
          ] as const
        ).map((group) => {
          const items = charts.top_comments[group.key]
          return (
            <Card key={group.key}>
              <CardHeader title={group.title} icon={<MessageSquare size={16} />} />
              <div className="space-y-2.5 p-4">
                {items.length ? (
                  items.map((comment, index) => (
                    <div key={`${group.key}-${index}`} className="rounded-xl bg-ink/4 p-3">
                      <p className="line-clamp-3 text-xs leading-relaxed text-ink">{comment.text}</p>
                      <div className="mt-2 flex items-center justify-between text-[11px] text-muted">
                        <span className="truncate">{comment.author_name ?? 'Unknown'}</span>
                        <span className="flex shrink-0 items-center gap-2">
                          {comment.like_count !== null ? (
                            <span className="flex items-center gap-1">
                              <Heart size={10} /> {comment.like_count}
                            </span>
                          ) : null}
                          <Badge
                            tone={
                              comment.sentiment === 'positive'
                                ? 'positive'
                                : comment.sentiment === 'negative'
                                  ? 'negative'
                                  : 'neutral'
                            }
                          >
                            {formatScore(comment.compound, 2)}
                          </Badge>
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="py-6 text-center text-xs text-muted">No comments in this category.</p>
                )}
              </div>
            </Card>
          )
        })}
      </div>

      {/* Records table */}
      <Card>
        <CardHeader
          title="Dataset Records"
          subtitle="Search, filter, sort and copy rows"
          icon={<Database size={16} />}
        />
        <RecordsTable analysisId={analysis.analysis_id} initialRecords={analysis.records} />
      </Card>

      {/* Limitations */}
      <Card>
        <CardHeader
          title="Data Limitations"
          subtitle="Read this before citing any figure from this analysis"
          icon={<AlertTriangle size={16} className="text-amber-500" />}
        />
        <ul className="space-y-2.5 p-5">
          {analysis.limitations.map((item, index) => (
            <li key={index} className="flex items-start gap-2.5 text-sm text-muted">
              <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-amber-500" aria-hidden />
              <span>{item}</span>
            </li>
          ))}
        </ul>
        {analysis.notes.length > 0 ? (
          <div className="border-t border-line px-5 py-4">
            <p className="mb-2 text-xs font-bold text-ink">Collection notes</p>
            <ul className="space-y-1.5">
              {analysis.notes.map((note, index) => (
                <li key={index} className="text-xs text-muted">
                  {note}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </Card>

      <p className="text-center text-xs text-muted">
        Positive {formatPercent(summary.positive_pct)} · Neutral {formatPercent(summary.neutral_pct)} ·
        Negative {formatPercent(summary.negative_pct)} of {summary.total} analysed records
      </p>
    </div>
  )
}

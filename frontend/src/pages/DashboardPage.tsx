import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Activity,
  BarChart3,
  Database,
  Eye,
  Gauge,
  History as HistoryIcon,
  MessageSquare,
  Play,
  Smile,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
import { useHistory, useProfile } from '../hooks/useAnalysis'
import { useApp } from '../context/app-context'
import {
  Alert,
  Badge,
  Button,
  Card,
  CardHeader,
  CardSkeleton,
  EmptyState,
  MetricTile,
} from '../components/ui'
import { formatPercent, formatScore, platformLabel, timeAgo } from '../utils/format'

export function DashboardPage() {
  const { userName, platforms } = useApp()
  const { data: history, loading: historyLoading } = useHistory()
  const { data: profile, loading: profileLoading } = useProfile()

  const configuredCount = platforms.filter((platform) => platform.configured).length

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="surface-card card-3d relative overflow-hidden p-6 sm:p-8"
      >
        <div
          className="absolute -top-20 -right-16 size-56 rounded-full bg-brand/15 blur-3xl"
          aria-hidden
        />
        <div className="relative flex flex-wrap items-center justify-between gap-5">
          <div>
            <p className="text-xs font-semibold tracking-wide text-brand uppercase">
              Data Analysis Essentials
            </p>
            <h1 className="mt-2 text-3xl font-extrabold tracking-tight text-ink">
              Welcome, {userName} <span aria-hidden>👋</span>
            </h1>
            <p className="mt-2 max-w-xl text-sm text-muted">
              Paste a public social-media URL to collect, clean and analyse its data — or open a
              labelled demo dataset to explore the dashboard first.
            </p>
          </div>
          <Link to="/analyze">
            <Button size="lg" icon={<Play size={17} />} className="animate-pulse-ring">
              Quick Analysis
            </Button>
          </Link>
        </div>
      </motion.div>

      {/* Aggregate stats */}
      {profileLoading ? (
        <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <CardSkeleton key={index} rows={2} />
          ))}
        </div>
      ) : (
        <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
          <MetricTile
            label="Total Analyses"
            value={profile?.total_analyses ?? 0}
            icon={<Activity size={15} />}
            delay={0.02}
          />
          <MetricTile
            label="Records Analyzed"
            value={profile?.total_records_analyzed ?? 0}
            icon={<Database size={15} />}
            delay={0.05}
          />
          <MetricTile
            label="Average Sentiment"
            value={profile?.average_sentiment}
            decimals={3}
            icon={<Smile size={15} />}
            delay={0.08}
            hint="Mean compound score across analyses"
          />
          <div className="sm:col-span-2 lg:col-span-1">
            <Card interactive className="h-full p-4">
              <p className="text-[11px] font-semibold tracking-wide text-muted uppercase">
                Most Analysed Platform
              </p>
              <p className="mt-2 text-2xl font-extrabold text-ink">
                {profile?.favorite_platform
                  ? platformLabel(profile.favorite_platform)
                  : '—'}
              </p>
              {profile?.platform_breakdown ? (
                <div className="mt-2.5 flex flex-wrap gap-1.5">
                  {Object.entries(profile.platform_breakdown).map(([key, count]) => (
                    <Badge key={key} tone="brand">
                      {platformLabel(key)} · {count}
                    </Badge>
                  ))}
                </div>
              ) : null}
            </Card>
          </div>
        </div>
      )}

      {/* API configuration status */}
      <Card>
        <CardHeader
          title="Platform API Status"
          subtitle="Live analysis requires a credential for the target platform"
          icon={<Gauge size={16} />}
        />
        <div className="grid gap-3 p-5 sm:grid-cols-3">
          {platforms.length === 0 ? (
            <Alert tone="warning" title="Backend unreachable">
              <p>
                Start the API with <code>uvicorn app.main:app --reload</code> to see live platform
                status. Demo analysis is unavailable while the API is offline.
              </p>
            </Alert>
          ) : (
            platforms.map((platform) => (
              <div
                key={platform.key}
                className="rounded-xl border border-line bg-ink/3 p-4 transition hover:border-brand/40"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-bold text-ink">{platform.label}</p>
                  <Badge tone={platform.configured ? 'positive' : 'muted'}>
                    {platform.configured ? 'Configured' : 'Not configured'}
                  </Badge>
                </div>
                {!platform.configured ? (
                  <p className="mt-2 text-[11px] leading-relaxed text-muted">
                    Set <code className="font-semibold text-brand">{platform.credential_env_var}</code>{' '}
                    in <code>backend/.env</code> to analyse live {platform.label} content.
                  </p>
                ) : (
                  <p className="mt-2 text-[11px] text-muted">Ready for live collection.</p>
                )}
              </div>
            ))
          )}
        </div>
        {configuredCount === 0 && platforms.length > 0 ? (
          <div className="px-5 pb-5">
            <Alert tone="info" title="No live credentials configured">
              <p>
                You can still explore every feature using the bundled demo dataset on the New
                Analysis page. Demo results are labelled as synthetic everywhere they appear,
                including inside every export.
              </p>
            </Alert>
          </div>
        ) : null}
      </Card>

      {/* Recent analyses */}
      <Card>
        <CardHeader
          title="Recent Analyses"
          subtitle="Your five most recent runs"
          icon={<HistoryIcon size={16} />}
          action={
            <Link to="/history">
              <Button size="sm" variant="ghost">
                View all
              </Button>
            </Link>
          }
        />
        {historyLoading ? (
          <div className="p-5">
            <CardSkeleton rows={4} />
          </div>
        ) : history && history.length > 0 ? (
          <div className="divide-y divide-line">
            {history.slice(0, 5).map((item) => (
              <Link
                key={item.analysis_id}
                to={`/analysis/${item.analysis_id}`}
                className="flex flex-wrap items-center gap-4 px-5 py-3.5 transition hover:bg-ink/3"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone="brand">{platformLabel(item.platform)}</Badge>
                    {item.data_mode === 'demo' ? <Badge tone="warning">Demo</Badge> : null}
                    <span className="text-[11px] text-muted">{timeAgo(item.created_at)}</span>
                  </div>
                  <p className="mt-1 truncate text-sm font-medium text-ink">
                    {item.title ?? item.url}
                  </p>
                </div>
                <div className="flex items-center gap-5 text-right">
                  <div>
                    <p className="text-[10px] text-muted">Records</p>
                    <p className="text-sm font-bold tabular-nums text-ink">
                      {item.total_records.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] text-muted">Positive</p>
                    <p className="text-sm font-bold tabular-nums text-positive">
                      {formatPercent(item.positive_pct, 0)}
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] text-muted">Sentiment</p>
                    <p className="text-sm font-bold tabular-nums text-ink">
                      {formatScore(item.avg_sentiment, 2)}
                    </p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={<BarChart3 size={24} />}
            title="No analyses yet"
            description="Run your first analysis to populate the dashboard, charts and history."
            action={
              <Link to="/analyze" className="mt-1">
                <Button icon={<Sparkles size={15} />}>Start your first analysis</Button>
              </Link>
            }
          />
        )}
      </Card>

      {/* Quick links */}
      <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { to: '/analytics', label: 'Analytics', body: 'Full dashboard of charts and statistics', icon: BarChart3 },
          { to: '/comments', label: 'Comments', body: 'Search and filter every analysed record', icon: MessageSquare },
          { to: '/engagement', label: 'Engagement', body: 'Interaction metrics and correlations', icon: TrendingUp },
          { to: '/datasets', label: 'Datasets', body: 'Download CSV, Excel and reports', icon: Eye },
        ].map((item) => (
          <Link key={item.to} to={item.to}>
            <Card interactive className="h-full p-5">
              <span className="grid size-10 place-items-center rounded-xl bg-brand/12 text-brand">
                <item.icon size={18} />
              </span>
              <p className="mt-3 text-sm font-bold text-ink">{item.label}</p>
              <p className="mt-1 text-xs text-muted">{item.body}</p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}

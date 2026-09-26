import { Link } from 'react-router-dom'
import { Database, Gauge } from 'lucide-react'
import type { ReactNode } from 'react'
import { useCurrentAnalysis } from '../hooks/useCurrentAnalysis'
import { useAnalysis } from '../hooks/useAnalysis'
import { Alert, Button, Card, CardSkeleton, EmptyState, SectionTitle } from '../components/ui'
import { platformLabel, timeAgo } from '../utils/format'

/**
 * Wraps a page that operates on one analysis: resolves the current analysis,
 * handles its loading and error states, and provides a picker when the user has
 * more than one saved run.
 */
export function AnalysisScopedPage({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle: string
  children: (context: { analysis: NonNullable<ReturnType<typeof useAnalysis>['data']> }) => ReactNode
}) {
  const { analysisId, history, loading: listLoading, error: listError } = useCurrentAnalysis()
  const { data: analysis, loading, error } = useAnalysis(analysisId)

  if (listError) {
    return (
      <Alert tone="error" title="Could not load your analyses">
        {listError}
      </Alert>
    )
  }

  if (listLoading || loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-64 skeleton" />
        <CardSkeleton rows={6} />
      </div>
    )
  }

  if (error) {
    return (
      <Alert tone="error" title="Analysis unavailable">
        {error}
      </Alert>
    )
  }

  if (!analysis) {
    return (
      <div className="space-y-6">
        <SectionTitle title={title} subtitle={subtitle} />
        <Card>
          <EmptyState
            icon={<Gauge size={24} />}
            title="No analysis available"
            description="Run an analysis first — this page reads the results of your most recent run."
            action={
              <Link to="/analyze" className="mt-1">
                <Button>Start an analysis</Button>
              </Link>
            }
          />
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <SectionTitle title={title} subtitle={subtitle} />

      {history.length > 1 ? <AnalysisSwitcher history={history} activeId={analysis.analysis_id} /> : null}

      {children({ analysis })}
    </div>
  )
}

function AnalysisSwitcher({
  history,
  activeId,
}: {
  history: { analysis_id: string; platform: string; title: string | null; created_at: string | null }[]
  activeId: string
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="flex items-center gap-1.5 text-[11px] font-semibold text-muted">
        <Database size={13} /> Showing
      </span>
      {history.slice(0, 5).map((item) => (
        <Link
          key={item.analysis_id}
          to={`/analysis/${item.analysis_id}`}
          className={`rounded-xl px-3 py-1.5 text-[11px] font-semibold transition ${
            item.analysis_id === activeId
              ? 'bg-brand text-white shadow-md shadow-brand/25'
              : 'bg-ink/6 text-muted hover:text-ink'
          }`}
          title={item.title ?? undefined}
        >
          {platformLabel(item.platform)} · {timeAgo(item.created_at)}
        </Link>
      ))}
    </div>
  )
}

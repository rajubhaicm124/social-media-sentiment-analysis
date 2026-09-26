import { MessageSquare } from 'lucide-react'
import { AnalysisScopedPage } from '../components/AnalysisScopedPage'
import { RecordsTable } from '../components/RecordsTable'
import { Card, CardHeader, MetricTile, DemoBanner } from '../components/ui'

export function CommentsPage() {
  return (
    <AnalysisScopedPage
      title="Comments"
      subtitle="Search, filter, sort and expand every analysed text record."
    >
      {({ analysis }) => (
        <>
          {analysis.data_mode === 'demo' ? <DemoBanner /> : null}

          <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
            <MetricTile label="Total Records" value={analysis.total_records} icon={<MessageSquare size={15} />} />
            <MetricTile label="Comments Analysed" value={analysis.sentiment_summary.total} />
            <MetricTile label="Records Removed" value={analysis.removed_records} accent="text-negative" />
            <MetricTile
              label="Avg Length"
              value={analysis.statistics.comment_length.characters.mean}
              decimals={1}
              hint="characters per cleaned record"
            />
          </div>

          <Card>
            <CardHeader
              title="Dataset Records"
              subtitle="Filters run on the server, so paging stays fast on large datasets"
              icon={<MessageSquare size={16} />}
            />
            <RecordsTable analysisId={analysis.analysis_id} initialRecords={analysis.records} />
          </Card>
        </>
      )}
    </AnalysisScopedPage>
  )
}

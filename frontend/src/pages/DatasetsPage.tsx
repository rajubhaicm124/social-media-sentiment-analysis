import { useState } from 'react'
import { Database, Download, FileSpreadsheet, FileText, Layers } from 'lucide-react'
import { AnalysisScopedPage } from '../components/AnalysisScopedPage'
import { downloadExport } from '../services/api'
import { useApp } from '../context/app-context'
import { Badge, Button, Card, CardHeader, DemoBanner, SectionTitle } from '../components/ui'
import { formatDateTime, platformLabel } from '../utils/format'

const EXPORTS = [
  {
    key: 'csv' as const,
    title: 'Clean CSV',
    body: 'Every cleaned, scored record as a flat table using the documented DAE column convention. Unavailable metrics are left blank.',
    icon: FileText,
    formatLabel: 'CSV',
  },
  {
    key: 'csv-raw' as const,
    title: 'Raw CSV',
    body: 'Records exactly as the platform API returned them, before any cleaning step. Preserved for auditability.',
    icon: Layers,
    formatLabel: 'CSV',
  },
  {
    key: 'excel' as const,
    title: 'Excel Workbook',
    body: 'Eight formatted worksheets: Summary, Raw Data, Clean Data, Sentiment, Engagement, Keywords, Hashtags and Limitations.',
    icon: FileSpreadsheet,
    formatLabel: 'XLSX',
  },
  {
    key: 'report-html' as const,
    title: 'Analysis Report (HTML)',
    body: 'A styled, printable report with the full analysis, observations and data limitations.',
    icon: FileText,
    formatLabel: 'HTML',
  },
  {
    key: 'report-pdf' as const,
    title: 'Analysis Report (PDF)',
    body: 'The same report rendered as a paginated PDF suitable for submission.',
    icon: FileText,
    formatLabel: 'PDF',
  },
]

export function DatasetsPage() {
  return (
    <AnalysisScopedPage
      title="Datasets & Exports"
      subtitle="Download the analysed dataset and the written report for the selected analysis."
    >
      {({ analysis }) => <DatasetPanel analysis={analysis} />}
    </AnalysisScopedPage>
  )
}

/** Minimal shape the export panel needs from an analysis. */
type ExportContext = {
  analysis_id: string
  platform: string
  data_mode: 'live' | 'demo'
  total_records: number
  created_at: string | null
  source_url: string
  content: Record<string, unknown>
}

function DatasetPanel({ analysis }: { analysis: ExportContext }) {
  const { pushToast } = useApp()
  const [busy, setBusy] = useState<string | null>(null)

  const run = async (key: string, kind: 'csv' | 'excel' | 'report', options: Parameters<typeof downloadExport>[2]) => {
    setBusy(key)
    try {
      await downloadExport(analysis.analysis_id, kind, { ...options, platform: analysis.platform })
      pushToast('Download started', 'success')
    } catch (error) {
      pushToast(error instanceof Error ? error.message : 'The export failed.', 'error')
    } finally {
      setBusy(null)
    }
  }

  return (
    <>
      {analysis.data_mode === 'demo' ? <DemoBanner /> : null}

      <Card>
        <CardHeader
          title="Source Dataset"
          subtitle="What these files were generated from"
          icon={<Database size={16} />}
        />
        <dl className="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: 'Platform', value: platformLabel(analysis.platform) },
            { label: 'Data mode', value: analysis.data_mode === 'demo' ? 'Demo (synthetic)' : 'Live API' },
            { label: 'Records', value: analysis.total_records.toLocaleString() },
            { label: 'Analysed', value: formatDateTime(analysis.created_at) },
          ].map((item) => (
            <div key={item.label}>
              <dt className="text-[11px] text-muted">{item.label}</dt>
              <dd className="mt-0.5 text-sm font-semibold text-ink">{item.value}</dd>
            </div>
          ))}
        </dl>
        <div className="border-t border-line px-5 py-4">
          <p className="text-xs leading-relaxed text-muted">{analysis.source_url}</p>
        </div>
      </Card>

      <SectionTitle
        title="Download an export"
        subtitle="Every file is generated from the stored analysis on the server."
      />

      <div className="grid gap-3.5 sm:grid-cols-2">
        {EXPORTS.map((item) => (
          <ExportCard
            key={item.key}
            exportInfo={item}
            analysis={analysis}
            busy={busy === item.key}
            onDownload={() => {
              if (item.key.startsWith('csv')) {
                void run(item.key, 'csv', { dataset: item.key === 'csv-raw' ? 'raw' : 'clean' })
              } else if (item.key === 'excel') {
                void run(item.key, 'excel', {})
              } else {
                void run(item.key, 'report', { format: item.key.endsWith('pdf') ? 'pdf' : 'html' })
              }
            }}
          />
        ))}
      </div>

      {/* Column documentation */}
      <Card>
        <CardHeader
          title="CSV column reference"
          subtitle="Blank cells mean the field was unavailable — they are never zeros"
          icon={<Database size={16} />}
        />
        <div className="grid gap-2.5 p-5 sm:grid-cols-2 lg:grid-cols-3">
          {COLUMN_GROUPS.map((group) => (
            <div key={group.title} className="rounded-xl bg-ink/4 p-3.5">
              <p className="text-[11px] font-bold tracking-wide text-brand uppercase">{group.title}</p>
              <ul className="mt-2 space-y-0.5">
                {group.columns.map((column) => (
                  <li key={column} className="font-mono text-[11px] text-muted">
                    {column}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Card>
    </>
  )
}

const COLUMN_GROUPS = [
  { title: 'Source', columns: ['platform', 'data_mode', 'source_url', 'content_id', 'post_id', 'video_id', 'channel_id', 'username'] },
  { title: 'Content', columns: ['author_id', 'author_name', 'title', 'description', 'caption', 'record_type'] },
  { title: 'Text', columns: ['comment_id', 'parent_id', 'comment_text', 'cleaned_comment', 'published_at', 'language', 'word_count', 'char_count'] },
  { title: 'Engagement', columns: ['likes', 'comments', 'shares', 'views', 'replies', 'engagement_rate'] },
  { title: 'Sentiment', columns: ['sentiment', 'sentiment_score', 'compound_score', 'positive_score', 'negative_score', 'neutral_score'] },
  { title: 'Comparison', columns: ['polarity', 'subjectivity', 'confidence', 'emotion', 'vader_compound', 'textblob_polarity'] },
  { title: 'NLP extras', columns: ['hashtags', 'mentions', 'keywords'] },
  { title: 'Quality flags', columns: ['is_duplicate', 'is_spam', 'is_outlier', 'flags'] },
]

function ExportCard({
  exportInfo,
  analysis,
  busy,
  onDownload,
}: {
  exportInfo: (typeof EXPORTS)[number]
  analysis: ExportContext
  busy: boolean
  onDownload: () => void
}) {
  return (
    <Card interactive className="flex h-full flex-col p-5">
      <div className="flex items-start justify-between gap-3">
        <span className="grid size-11 place-items-center rounded-xl bg-linear-to-br from-brand/15 to-brand-2/15 text-brand">
          <exportInfo.icon size={20} />
        </span>
        <Badge tone="brand">{exportInfo.formatLabel}</Badge>
      </div>
      <h3 className="mt-4 text-sm font-bold text-ink">{exportInfo.title}</h3>
      <p className="mt-1.5 flex-1 text-xs leading-relaxed text-muted">{exportInfo.body}</p>
      <Button
        className="mt-4"
        fullWidth
        loading={busy}
        onClick={onDownload}
        icon={<Download size={15} />}
      >
        Download {exportInfo.formatLabel}
      </Button>
      <p className="mt-2 text-center text-[10px] text-muted">
        socialscope_{analysis.platform}_{analysis.analysis_id.slice(0, 8)}.{exportInfo.formatLabel.toLowerCase()}
      </p>
    </Card>
  )
}

import { Smile, Sparkles } from 'lucide-react'
import { AnalysisScopedPage } from '../components/AnalysisScopedPage'
import {
  Badge,
  Card,
  CardHeader,
  DemoBanner,
  EmptyState,
  MetricTile,
  SentimentBadge,
} from '../components/ui'
import {
  SentimentDonutChart,
  SentimentScoreChart,
  SentimentTrendChart,
  WordCloud,
} from '../components/charts'
import { formatScore, truncate } from '../utils/format'
import type { SentimentComparisonRow } from '../types'

export function SentimentPage() {
  return (
    <AnalysisScopedPage
      title="Sentiment Analysis"
      subtitle="VADER classification with a TextBlob polarity and subjectivity comparison."
    >
      {({ analysis }) => {
        const summary = analysis.sentiment_summary
        const comparison = analysis.sentiment_comparison as SentimentComparisonRow[]
        const hasTimestamps = analysis.charts.sentiment_timeline.available
        const daily = (analysis.trends as Record<string, { points: never[] }>).daily

        return (
          <>
            {analysis.data_mode === 'demo' ? <DemoBanner /> : null}

            <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
              <MetricTile label="Positive %" value={summary.positive_pct} suffix="%" decimals={1} accent="text-positive" />
              <MetricTile label="Neutral %" value={summary.neutral_pct} suffix="%" decimals={1} />
              <MetricTile label="Negative %" value={summary.negative_pct} suffix="%" decimals={1} accent="text-negative" />
              <MetricTile label="Avg Compound" value={summary.avg_compound} decimals={3} icon={<Smile size={15} />} />
              <MetricTile label="Avg Polarity" value={summary.avg_polarity} decimals={3} hint="TextBlob" />
              <MetricTile label="Avg Subjectivity" value={summary.avg_subjectivity} decimals={3} hint="TextBlob" />
              <div className="sm:col-span-1">
                <Card className="h-full p-4">
                  <p className="text-[11px] font-semibold tracking-wide text-muted uppercase">
                    Sentiment Engine
                  </p>
                  <p className="mt-1.5 text-lg font-extrabold text-ink capitalize">
                    {analysis.sentiment_method ?? 'n/a'}
                  </p>
                  <p className="mt-1 text-[11px] text-muted">
                    {String((analysis.sentiment_status as { description?: string })?.description ?? '')}
                  </p>
                </Card>
              </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader title="Distribution" subtitle="Share of analysed records" icon={<Smile size={16} />} />
                <div className="p-4">
                  <SentimentDonutChart summary={summary} />
                </div>
              </Card>

              <Card>
                <CardHeader title="Scores" subtitle="VADER counts with TextBlob averages" icon={<Sparkles size={16} />} />
                <div className="p-4">
                  <SentimentScoreChart summary={summary} />
                </div>
              </Card>

              <Card className="lg:col-span-2">
                <CardHeader
                  title="Sentiment Over Time"
                  subtitle="Daily record volume split by sentiment"
                  icon={<Sparkles size={16} />}
                />
                <div className="p-4">
                  {hasTimestamps ? (
                    <SentimentTrendChart points={daily.points} />
                  ) : (
                    <EmptyState
                      title="No timestamps available"
                      description="The platform did not return usable publication timestamps for this content."
                    />
                  )}
                </div>
              </Card>
            </div>

            {/* VADER vs TextBlob comparison table */}
            <Card>
              <CardHeader
                title="VADER vs TextBlob Comparison"
                subtitle="Both engines scored the same cleaned text — a sanity check on the classification"
                icon={<Sparkles size={16} />}
                action={<Badge tone="muted">{comparison.length} rows</Badge>}
              />
              {comparison.length === 0 ? (
                <EmptyState title="No comparison data" />
              ) : (
                <div className="max-h-[520px] overflow-auto">
                  <table className="data-table w-full min-w-[760px] text-sm">
                    <thead className="border-b border-line">
                      <tr className="text-[11px] font-bold tracking-wide text-muted uppercase">
                        <th className="px-4 py-2.5 text-left">Comment</th>
                        <th className="px-4 py-2.5 text-right">VADER</th>
                        <th className="px-4 py-2.5 text-right">TextBlob polarity</th>
                        <th className="px-4 py-2.5 text-right">Subjectivity</th>
                        <th className="px-4 py-2.5 text-left">Final</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.slice(0, 200).map((row, index) => (
                        <tr
                          key={row.comment_id ?? index}
                          className="border-b border-line/60 last:border-0 hover:bg-ink/3"
                        >
                          <td className="max-w-sm px-4 py-2.5">
                            <span className="block truncate text-[13px] text-ink">
                              {truncate(row.text, 90)}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 text-right tabular-nums text-ink">
                            {formatScore(row.vader_compound)}
                          </td>
                          <td className="px-4 py-2.5 text-right tabular-nums text-muted">
                            {formatScore(row.textblob_polarity)}
                          </td>
                          <td className="px-4 py-2.5 text-right tabular-nums text-muted">
                            {formatScore(row.textblob_subjectivity)}
                          </td>
                          <td className="px-4 py-2.5">
                            <SentimentBadge sentiment={row.sentiment} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {comparison.length > 200 ? (
                <p className="border-t border-line px-4 py-2.5 text-[11px] text-muted">
                  Showing the first 200 of {comparison.length} rows. Download the Excel workbook for
                  the complete comparison.
                </p>
              ) : null}
            </Card>

            {/* Keywords by sentiment */}
            <div className="grid gap-4 lg:grid-cols-2">
              {analysis.statistics.sentiment_keywords.map((group) => (
                <Card key={group.sentiment}>
                  <CardHeader
                    title={`Words in ${group.sentiment} comments`}
                    subtitle="Most frequent content words"
                    icon={<Sparkles size={16} />}
                  />
                  <div className="p-4">
                    {group.keywords.length ? (
                      <div className="flex flex-wrap gap-2">
                        {group.keywords.map((word) => (
                          <Badge key={word} tone={group.sentiment === 'positive' ? 'positive' : 'negative'}>
                            {word}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="py-4 text-center text-xs text-muted">
                        No {group.sentiment} comments in this dataset.
                      </p>
                    )}
                  </div>
                </Card>
              ))}
            </div>

            <Card>
              <CardHeader title="Word Cloud" subtitle="Most frequent analysed terms" icon={<Sparkles size={16} />} />
              <div className="p-4">
                <WordCloud terms={analysis.charts.word_cloud} />
              </div>
            </Card>
          </>
        )
      }}
    </AnalysisScopedPage>
  )
}

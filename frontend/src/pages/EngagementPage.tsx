import { AlertTriangle, Eye, Heart, MessageSquare, Share2, TrendingUp } from 'lucide-react'
import { AnalysisScopedPage } from '../components/AnalysisScopedPage'
import { Alert, Card, CardHeader, DemoBanner, MetricTile, ProgressBar, SectionTitle } from '../components/ui'
import { CommentLengthChart, EngagementBarChart, SentimentScatterChart } from '../components/charts'

export function EngagementPage() {
  return (
    <AnalysisScopedPage
      title="Engagement Analysis"
      subtitle="Interaction metrics, the engagement-rate formula, and how engagement relates to sentiment."
    >
      {({ analysis }) => {
        const { engagement, statistics, charts } = analysis

        return (
          <>
            {analysis.data_mode === 'demo' ? <DemoBanner /> : null}

            <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
              <MetricTile label="Views" value={engagement.views} icon={<Eye size={15} />} />
              <MetricTile label="Likes" value={engagement.likes} icon={<Heart size={15} />} accent="text-negative" />
              <MetricTile label="Comments" value={engagement.comments} icon={<MessageSquare size={15} />} />
              <MetricTile label="Shares" value={engagement.shares} icon={<Share2 size={15} />} />
              <MetricTile label="Total Interactions" value={engagement.total_interactions} />
              <MetricTile
                label="Engagement Rate"
                value={engagement.engagement_rate}
                suffix="%"
                decimals={2}
                icon={<TrendingUp size={15} />}
              />
            </div>

            {/* The formula, stated explicitly. */}
            <Card>
              <CardHeader
                title="How the engagement rate was calculated"
                subtitle="Only computed when every required input was returned by the API"
                icon={<TrendingUp size={16} />}
              />
              <div className="space-y-3 p-5">
                {engagement.engagement_rate_available ? (
                  <div className="rounded-xl bg-positive/8 p-4 ring-1 ring-positive/25">
                    <p className="text-sm font-semibold text-ink">
                      (
                      {engagement.interactions_included.length
                        ? engagement.interactions_included.join(' + ')
                        : 'no interactions returned'}
                      ) ÷ views × 100 ={' '}
                      <span className="text-positive">{engagement.engagement_rate?.toFixed(2)}%</span>
                    </p>
                  </div>
                ) : (
                  <Alert tone="warning" title="Engagement rate unavailable">
                    <p>
                      The platform API did not return every input this formula needs, so no rate was
                      calculated. No substitute or estimated value is shown.
                    </p>
                  </Alert>
                )}

                {engagement.notes.map((note, index) => (
                  <p key={index} className="text-xs leading-relaxed text-muted">
                    {note}
                  </p>
                ))}

                {engagement.unavailable_fields.length > 0 ? (
                  <div className="flex items-start gap-2.5 rounded-xl bg-amber-500/8 p-3.5 ring-1 ring-amber-500/25">
                    <AlertTriangle size={15} className="mt-0.5 shrink-0 text-amber-500" />
                    <p className="text-xs text-muted">
                      Unavailable through the current platform API:{' '}
                      <span className="font-semibold text-ink">
                        {engagement.unavailable_fields.join(', ')}
                      </span>
                      . These fields are excluded from the calculation above.
                    </p>
                  </div>
                ) : null}
              </div>
            </Card>

            <Card>
              <CardHeader
                title="Engagement Breakdown"
                subtitle="Missing metrics appear as gaps, not zeros"
                icon={<TrendingUp size={16} />}
              />
              <div className="p-4">
                <EngagementBarChart charts={charts} />
              </div>
            </Card>

            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader
                  title="Likes vs Sentiment"
                  subtitle="Each point is one comment with a like count from the API"
                  icon={<Heart size={16} />}
                />
                <div className="p-4">
                  {charts.likes_vs_sentiment.length ? (
                    <SentimentScatterChart charts={charts} />
                  ) : (
                    <p className="py-10 text-center text-sm text-muted">
                      Comment-level like counts were not available through the platform API, so this
                      relationship cannot be plotted.
                    </p>
                  )}
                </div>
              </Card>

              <Card>
                <CardHeader title="Comment Length" subtitle="Longer comments may carry stronger opinion" icon={<MessageSquare size={16} />} />
                <div className="p-4">
                  <CommentLengthChart charts={charts} />
                </div>
              </Card>
            </div>

            {statistics.correlations.pairs.length > 0 ? (
              <Card>
                <CardHeader
                  title="Relationships with Engagement"
                  subtitle="Pearson correlation between numeric fields"
                  icon={<TrendingUp size={16} />}
                />
                <div className="space-y-3 p-5">
                  {statistics.correlations.pairs.map((pair) => (
                    <div key={`${pair.x}-${pair.y}`}>
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-medium text-ink">
                          {pair.x} vs {pair.y}
                        </p>
                        <span className="text-sm font-bold tabular-nums text-brand">
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
                        {pair.strength} {pair.direction} relationship (n = {analysis.total_records} records)
                      </p>
                    </div>
                  ))}
                </div>
              </Card>
            ) : null}

            <SectionTitle
              title="Interpretation notes"
              subtitle="Correlation does not imply causation"
            />
            <ul className="space-y-2 text-xs leading-relaxed text-muted">
              <li>
                <strong className="text-ink">Sample size matters.</strong> A correlation computed
                from fewer than three usable pairs is not reported at all, because the coefficient
                would be meaningless.
              </li>
              <li>
                <strong className="text-ink">Comment likes are often missing.</strong> Several
                platforms only return a comment like count to the content owner, so this relationship
                is frequently unplottable — that is an API limitation, not a bug.
              </li>
              <li>
                <strong className="text-ink">Sentiment is estimated.</strong> Lexicon scoring of
                short, sarcastic or emoji-heavy comments is imperfect.
              </li>
            </ul>
          </>
        )
      }}
    </AnalysisScopedPage>
  )
}

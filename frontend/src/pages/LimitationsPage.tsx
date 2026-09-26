import { AlertTriangle, CheckCircle2, KeyRound, Lock, Scale, Server, ShieldCheck, XCircle } from 'lucide-react'
import { useApp } from '../context/app-context'
import { Badge, Card, CardHeader, SectionTitle } from '../components/ui'
import { getHealth } from '../services/api'
import { useEffect, useState } from 'react'

const PLATFORM_FACTS: Record<string, { provided: string[]; missing: string[] }> = {
  youtube: {
    provided: [
      'Video title, description and published date',
      'Channel name and channel ID',
      'View count, like count and comment count',
      'Public comment text, author, date and reply count',
      'Video duration and category ID',
      'Official thumbnail URLs',
    ],
    missing: [
      'Share count — not exposed by the Data API v3 at all',
      'Comment like count — only returned to the content owner',
      'Channel subscriber count — only for the authenticated owner’s own channel',
      'Video tags — usually absent from the API response',
      'Removed, held-for-review and creator-hidden comments',
    ],
  },
  facebook: {
    provided: [
      'Post text and creation time',
      'Page name and Page ID',
      'Reaction totals, share count and comment count',
      'Public comment text, author, date and like count',
      'Video view count for video posts',
    ],
    missing: [
      'Posts on personal profiles — the Graph API cannot read them',
      'Insights for content the Page token does not own',
      'Comment moderation status and private content',
      'Detailed reaction breakdowns without extra permissions',
    ],
  },
  instagram: {
    provided: [
      'Caption, timestamp and media type',
      'Like count and comment count',
      'Media insights: reach, impressions and views (owner only)',
      'Comment text for media owned by the authorised account',
    ],
    missing: [
      'Share count — not exposed by the Instagram Graph API',
      'Any public post by shortcode — the API cannot resolve it',
      'Hashtag and mention insights for accounts you do not own',
      'Content from personal (non-professional) accounts',
    ],
  },
}

const GENERAL_LIMITATIONS = [
  {
    icon: KeyRound,
    title: 'Authentication is always required',
    body: 'No platform provides public analytics without a credential. SocialScope AI therefore needs an API key or access token in backend/.env before live analysis is possible. Credentials are never sent to the browser.',
  },
  {
    icon: Lock,
    title: 'No authentication or privacy bypass',
    body: 'The application uses only documented API endpoints. It does not scrape pages, reverse-engineer private endpoints, spoof identities, or attempt to access content that a platform has made non-public.',
  },
  {
    icon: Server,
    title: 'Quota and rate limits',
    body: 'The YouTube Data API charges quota units per call, so comment retrieval is capped by MAX_COMMENT_PAGES and sampled when a thread is larger than the cap. SocialScope AI additionally applies its own request rate limit per client.',
  },
  {
    icon: Scale,
    title: 'Moderation and deletion are permanent',
    body: 'Comments removed by moderators, hidden by creators, or deleted by authors cannot be recovered through any permitted method, so comment datasets are always a lower bound on the true audience response.',
  },
  {
    icon: ShieldCheck,
    title: 'Sentiment is an estimate',
    body: 'Lexicon-based scoring is deterministic and reproducible, but it is not a human judgement. Sarcasm, emoji-only comments, mixed languages and very short text all reduce accuracy.',
  },
]

export function LimitationsPage() {
  const { platforms } = useApp()
  const [health, setHealth] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null))
  }, [])

  return (
    <div className="space-y-6">
      <SectionTitle
        title="API Limitations & Data Ethics"
        subtitle="What each platform genuinely provides, and what it cannot."
      />

      <Card className="border-l-4 border-l-brand">
        <div className="flex items-start gap-3 p-5">
          <ShieldCheck size={20} className="mt-0.5 shrink-0 text-positive" />
          <div>
            <h2 className="text-sm font-bold text-ink">Privacy &amp; ethics notice</h2>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              SocialScope AI analyses data available through supported platform APIs and permitted
              public sources. It does not bypass privacy settings, authentication, security
              controls, or platform restrictions. No private user information is collected beyond what
              a platform itself publishes on public content, and API credentials are stored only in
              the server environment.
            </p>
          </div>
        </div>
      </Card>

      {/* Live configuration status */}
      <Card>
        <CardHeader
          title="Your current configuration"
          subtitle="Read from the running backend — secrets are never exposed"
          icon={<Server size={16} />}
        />
        <div className="p-5">
          {!health ? (
            <p className="text-sm text-muted">
              The backend is not reachable, so configuration status is unavailable.
            </p>
          ) : (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {(platforms.length ? platforms : []).map((platform) => (
                  <Badge key={platform.key} tone={platform.configured ? 'positive' : 'muted'}>
                    {platform.configured ? (
                      <CheckCircle2 size={11} />
                    ) : (
                      <XCircle size={11} />
                    )}
                    {platform.label}: {platform.configured ? 'configured' : 'not configured'}
                  </Badge>
                ))}
                {platforms.length === 0 ? (
                  <Badge tone="muted">Platform status unavailable</Badge>
                ) : null}
              </div>
              <p className="text-xs text-muted">
                Sentiment engine:{' '}
                <span className="font-semibold text-ink">
                  {String((health.sentiment as { primary_engine?: string })?.primary_engine ?? 'unknown')}
                </span>{' '}
                · VADER{' '}
                {String((health.sentiment as { vader_available?: boolean })?.vader_available) ? 'available' : 'unavailable'}{' '}
                · TextBlob{' '}
                {String((health.sentiment as { textblob_available?: boolean })?.textblob_available)
                  ? 'available'
                  : 'unavailable'}
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Per-platform detail */}
      {(['youtube', 'facebook', 'instagram'] as const).map((key) => {
        const facts = PLATFORM_FACTS[key]
        return (
          <Card key={key}>
            <CardHeader
              title={key.charAt(0).toUpperCase() + key.slice(1)}
              subtitle={
                key === 'youtube'
                  ? 'YouTube Data API v3'
                  : `Meta Graph API (${key === 'facebook' ? 'Facebook Pages' : 'Instagram professional accounts'})`
              }
              icon={<AlertTriangle size={16} className="text-amber-500" />}
              action={
                <Badge tone={platforms.find((p) => p.key === key)?.configured ? 'positive' : 'muted'}>
                  {platforms.find((p) => p.key === key)?.configured ? 'Configured' : 'Not configured'}
                </Badge>
              }
            />
            <div className="grid gap-5 p-5 lg:grid-cols-2">
              <div>
                <p className="flex items-center gap-2 text-xs font-bold tracking-wide text-positive uppercase">
                  <CheckCircle2 size={13} /> Available through the API
                </p>
                <ul className="mt-2.5 space-y-1.5">
                  {facts.provided.map((item) => (
                    <li key={item} className="flex items-start gap-2 text-xs leading-relaxed text-muted">
                      <span className="mt-1.5 size-1 shrink-0 rounded-full bg-positive" aria-hidden />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="flex items-center gap-2 text-xs font-bold tracking-wide text-negative uppercase">
                  <XCircle size={13} /> Not available
                </p>
                <ul className="mt-2.5 space-y-1.5">
                  {facts.missing.map((item) => (
                    <li key={item} className="flex items-start gap-2 text-xs leading-relaxed text-muted">
                      <span className="mt-1.5 size-1 shrink-0 rounded-full bg-negative" aria-hidden />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            {platforms.find((p) => p.key === key)?.limitations.length ? (
              <div className="border-t border-line px-5 py-4">
                <p className="text-xs font-bold text-ink">Documented platform constraints</p>
                <ul className="mt-2 space-y-1.5">
                  {platforms
                    .find((p) => p.key === key)!
                    .limitations.map((item) => (
                      <li key={item} className="text-xs leading-relaxed text-muted">
                        • {item}
                      </li>
                    ))}
                </ul>
              </div>
            ) : null}
          </Card>
        )
      })}

      {/* General limitations */}
      <SectionTitle title="General constraints" subtitle="Applies to every platform" />
      <div className="grid gap-3.5 md:grid-cols-2">
        {GENERAL_LIMITATIONS.map((item) => (
          <Card key={item.title} className="p-5">
            <span className="grid size-10 place-items-center rounded-xl bg-brand/12 text-brand">
              <item.icon size={18} />
            </span>
            <h3 className="mt-3.5 text-sm font-bold text-ink">{item.title}</h3>
            <p className="mt-1.5 text-xs leading-relaxed text-muted">{item.body}</p>
          </Card>
        ))}
      </div>

      <Card className="p-5">
        <h2 className="text-sm font-bold text-ink">Academic honesty note</h2>
        <p className="mt-2 text-xs leading-relaxed text-muted">
          Where this project could not obtain a metric through a permitted method, it displays{' '}
          <span className="font-semibold text-ink">
            “Data unavailable through the current platform API.”
          </span>{' '}
          rather than an approximation. The bundled demo dataset exists only to demonstrate the
          pipeline before credentials are available; it is synthetic, is labelled{' '}
          <span className="font-semibold text-ink">DEMO DATA</span> in the interface and in every
          export, and must never be presented as a real platform metric.
        </p>
      </Card>
    </div>
  )
}

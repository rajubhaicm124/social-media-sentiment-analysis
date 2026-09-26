import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Database, Moon, Palette, RotateCcw, Server, Sun, User } from 'lucide-react'
import { useApp } from '../context/app-context'
import { useProfile } from '../hooks/useAnalysis'
import { getHealth, renameProfile } from '../services/api'
import {
  Alert,
  Badge,
  Button,
  Card,
  CardHeader,
  CardSkeleton,
  SectionTitle,
} from '../components/ui'
import { formatDateTime, formatScore, platformLabel } from '../utils/format'

const SAMPLE_KEYS = ['socialscope.userName', 'socialscope.theme']

export function SettingsPage() {
  const { userName, setUserName, theme, toggleTheme, clearUserName, platforms, demoModeEnabled, pushToast } =
    useApp()
  const { data: profile, loading, reload } = useProfile()
  const [name, setName] = useState(userName ?? '')
  const [saving, setSaving] = useState(false)
  const [health, setHealth] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null))
  }, [])

  const saveName = async (event: React.FormEvent) => {
    event.preventDefault()
    const trimmed = name.trim()
    if (!trimmed || trimmed === userName) return
    setSaving(true)
    try {
      const result = await renameProfile(trimmed, userName ?? undefined)
      setUserName(trimmed)
      reload()
      pushToast(
        result.analyses_moved
          ? `Name updated — ${result.analyses_moved} analysis record(s) reassigned.`
          : 'Display name updated.',
        'success',
      )
    } catch {
      pushToast('The display name could not be updated on the server.', 'error')
    } finally {
      setSaving(false)
    }
  }

  const resetLocalData = () => {
    SAMPLE_KEYS.forEach((key) => {
      try {
        window.localStorage.removeItem(key)
      } catch {
        /* ignore */
      }
    })
    pushToast('Local preferences cleared. Reloading…', 'info')
    window.setTimeout(() => window.location.reload(), 700)
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <SectionTitle title="Settings" subtitle="Profile, appearance and local data." />

      {/* Profile */}
      <Card>
        <CardHeader
          title="Your profile"
          subtitle="Stored locally in this browser and attached to your analyses"
          icon={<User size={16} />}
        />
        <form onSubmit={saveName} className="p-5">
          <label htmlFor="profile-name" className="mb-2 block text-xs font-semibold text-muted">
            Display name
          </label>
          <div className="flex flex-col gap-2.5 sm:flex-row">
            <input
              id="profile-name"
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              maxLength={80}
              className="flex-1 rounded-xl border border-line bg-surface-2 px-4 py-3 text-sm text-ink outline-none focus:border-brand focus:ring-2 focus:ring-brand/25"
            />
            <Button
              type="submit"
              loading={saving}
              disabled={!name.trim() || name.trim() === userName}
            >
              Save name
            </Button>
          </div>

          <div className="mt-5 grid gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
            {loading ? (
              <CardSkeleton rows={2} />
            ) : (
              <>
                {[
                  { label: 'Analyses', value: profile?.total_analyses ?? 0 },
                  { label: 'Records analyzed', value: profile?.total_records_analyzed ?? 0 },
                  {
                    label: 'Average sentiment',
                    value: formatScore(profile?.average_sentiment),
                  },
                  {
                    label: 'Favorite platform',
                    value: profile?.favorite_platform
                      ? platformLabel(profile.favorite_platform)
                      : '—',
                  },
                ].map((item) => (
                  <div key={item.label} className="rounded-xl bg-ink/4 p-3.5">
                    <p className="text-[11px] text-muted">{item.label}</p>
                    <p className="mt-1 text-base font-bold text-ink">{item.value}</p>
                  </div>
                ))}
              </>
            )}
          </div>

          {profile?.last_analysis ? (
            <p className="mt-4 text-xs text-muted">
              Last analysis: {profile.last_analysis.title ?? profile.last_analysis.url} ·{' '}
              {formatDateTime(profile.last_analysis.created_at)}
            </p>
          ) : null}

          <div className="mt-5">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                clearUserName()
                pushToast('Name cleared', 'info')
              }}
              icon={<RotateCcw size={14} />}
            >
              Forget my name
            </Button>
          </div>
        </form>
      </Card>

      {/* Appearance */}
      <Card>
        <CardHeader title="Appearance" subtitle="Applies immediately and is remembered" icon={<Palette size={16} />} />
        <div className="p-5">
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => theme !== 'dark' && toggleTheme()}
              className={`flex flex-1 items-center gap-3 rounded-xl border p-4 text-left transition sm:max-w-[220px] ${
                theme === 'dark' ? 'border-brand bg-brand/10' : 'border-line hover:border-brand/40'
              }`}
            >
              <Moon size={18} className="text-brand" />
              <span>
                <span className="block text-sm font-semibold text-ink">Dark</span>
                <span className="text-[11px] text-muted">Default for data work</span>
              </span>
            </button>
            <button
              type="button"
              onClick={() => theme !== 'light' && toggleTheme()}
              className={`flex flex-1 items-center gap-3 rounded-xl border p-4 text-left transition sm:max-w-[220px] ${
                theme === 'light' ? 'border-brand bg-brand/10' : 'border-line hover:border-brand/40'
              }`}
            >
              <Sun size={18} className="text-amber-500" />
              <span>
                <span className="block text-sm font-semibold text-ink">Light</span>
                <span className="text-[11px] text-muted">Bright and printable</span>
              </span>
            </button>
          </div>
        </div>
      </Card>

      {/* Platform configuration */}
      <Card>
        <CardHeader
          title="Platform API configuration"
          subtitle="Set these in backend/.env — never in the browser"
          icon={<Server size={16} />}
        />
        <div className="space-y-3 p-5">
          {!health ? (
            <Alert tone="warning" title="Backend unreachable">
              <p>
                Start the API to view live configuration. Start it with{' '}
                <code>uvicorn app.main:app --reload</code>.
              </p>
            </Alert>
          ) : (
            <>
              {platforms.length === 0 ? (
                <Alert tone="warning" title="Platform status unavailable" />
              ) : (
                platforms.map((platform) => (
                  <div
                    key={platform.key}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-ink/4 p-3.5"
                  >
                    <div>
                      <p className="text-sm font-semibold text-ink">{platform.label}</p>
                      <code className="text-[11px] text-brand">{platform.credential_env_var}</code>
                    </div>
                    <Badge tone={platform.configured ? 'positive' : 'muted'}>
                      {platform.configured ? 'Configured' : 'Not set'}
                    </Badge>
                  </div>
                ))
              )}

              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-ink/4 p-3.5">
                <div>
                  <p className="text-sm font-semibold text-ink">Demo Mode</p>
                  <span className="text-[11px] text-muted">
                    Bundled synthetic dataset for testing without credentials
                  </span>
                </div>
                <Badge tone={demoModeEnabled ? 'positive' : 'muted'}>
                  {demoModeEnabled ? 'Enabled' : 'Disabled'}
                </Badge>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-ink/4 p-3.5">
                <div>
                  <p className="text-sm font-semibold text-ink">Database</p>
                  <span className="text-[11px] text-muted">
                    {String(health.database ?? 'unknown')} · SQLite by default
                  </span>
                </div>
                <Badge tone="brand">{String(health.environment ?? 'development')}</Badge>
              </div>
            </>
          )}
        </div>
      </Card>

      {/* Local data */}
      <Card>
        <CardHeader
          title="Local data"
          subtitle="Analyses are stored server-side; only preferences live in this browser"
          icon={<Database size={16} />}
        />
        <div className="p-5">
          <p className="text-xs leading-relaxed text-muted">
            Your display name and theme preference are saved in this browser's local storage. No
            tracking or third-party analytics are used. Clearing these keys does not delete your
            saved analyses — delete them individually from{' '}
            <Link to="/history" className="font-semibold text-brand hover:underline">
              History
            </Link>
            .
          </p>
          <Button className="mt-4" variant="secondary" size="sm" onClick={resetLocalData} icon={<RotateCcw size={14} />}>
            Clear local preferences
          </Button>
        </div>
      </Card>
    </div>
  )
}

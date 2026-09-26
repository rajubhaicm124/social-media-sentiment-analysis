import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowRight,
  BarChart3,
  Database,
  Gauge,
  Github,
  MessageSquare,
  Moon,
  ShieldCheck,
  Sparkles,
  Sun,
} from 'lucide-react'
import { useApp } from '../context/app-context'
import { Button } from '../components/ui'
import { ThemeToggleButton } from '../components/ThemeToggleButton'

/** Static preview values. Explicitly labelled as sample data, not real metrics. */
const PREVIEW_CARDS = [
  { label: '85% Positive', accent: 'from-emerald-400 to-green-600', icon: '😊', delay: 0.15 },
  { label: '12K Comments', accent: 'from-sky-400 to-indigo-600', icon: '💬', delay: 0.3 },
  { label: '1.2M Views', accent: 'from-violet-400 to-purple-600', icon: '👁', delay: 0.45 },
  { label: '73% Engagement', accent: 'from-amber-400 to-orange-600', icon: '📊', delay: 0.6 },
]

const FEATURES = [
  {
    icon: ShieldCheck,
    title: 'Honest data provenance',
    body: 'Official platform APIs only. Any metric an API does not return is labelled unavailable — never estimated or invented.',
  },
  {
    icon: MessageSquare,
    title: 'Dual-engine sentiment',
    body: 'VADER valence scoring with a TextBlob polarity and subjectivity comparison for every analysed record.',
  },
  {
    icon: BarChart3,
    title: 'Interactive analytics',
    body: 'Engagement, sentiment distribution, trends, correlations, keyword frequency and hashtag analysis.',
  },
  {
    icon: Database,
    title: 'Clean exports',
    body: 'Download CSV, a formatted multi-sheet Excel workbook, and a full PDF or HTML report in one click.',
  },
]

const PIPELINE = [
  { step: '01', label: 'URL & Detection' },
  { step: '02', label: 'Collection' },
  { step: '03', label: 'Cleaning' },
  { step: '04', label: 'Sentiment' },
  { step: '05', label: 'Statistics' },
  { step: '06', label: 'Visualisation' },
  { step: '07', label: 'Export' },
]

export function LandingPage() {
  const { userName, theme } = useApp()
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div className="relative min-h-screen overflow-x-hidden">
      {/* Animated background orbs */}
      <div className="pointer-events-none fixed inset-0 -z-10" aria-hidden>
        <div className="animate-drift absolute -top-40 -left-32 size-[38rem] rounded-full bg-brand/18 blur-3xl" />
        <div
          className="animate-drift absolute top-1/4 -right-40 size-[34rem] rounded-full bg-brand-2/16 blur-3xl"
          style={{ animationDelay: '-8s' }}
        />
        <div
          className="animate-drift absolute -bottom-52 left-1/3 size-[30rem] rounded-full bg-brand-3/12 blur-3xl"
          style={{ animationDelay: '-15s' }}
        />
      </div>

      {/* Nav */}
      <header
        className={`sticky top-0 z-40 border-b transition-all duration-300 ${
          scrolled ? 'border-line bg-surface/80 backdrop-blur-xl' : 'border-transparent'
        }`}
      >
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-3 px-5 sm:px-8">
          <span className="grid size-9 place-items-center rounded-xl bg-linear-to-br from-brand to-brand-2 text-white shadow-lg shadow-brand/30">
            <Gauge size={18} />
          </span>
          <div className="mr-auto">
            <p className="text-sm font-extrabold tracking-tight text-ink">SocialScope AI</p>
            <p className="hidden text-[10px] text-muted sm:block">From Social Data to Smart Insights.</p>
          </div>

          <nav className="hidden items-center gap-6 md:flex" aria-label="Landing">
            <a href="#features" className="text-sm text-muted transition hover:text-ink">
              Features
            </a>
            <a href="#pipeline" className="text-sm text-muted transition hover:text-ink">
              How it works
            </a>
            <a href="#ethics" className="text-sm text-muted transition hover:text-ink">
              Ethics
            </a>
          </nav>

          <ThemeToggleButton />
          <Link to={userName ? '/dashboard' : '/welcome'}>
            <Button size="sm" icon={<ArrowRight size={14} />}>
              {userName ? 'Dashboard' : 'Get Started'}
            </Button>
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-7xl px-5 pt-14 pb-20 sm:px-8 sm:pt-20">
        <div className="grid items-center gap-14 lg:grid-cols-2">
          <div>
            <motion.span
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 rounded-full border border-brand/25 bg-brand/10 px-3.5 py-1.5 text-xs font-semibold text-brand"
            >
              <Sparkles size={13} />
              Data Analysis Essentials project
            </motion.span>

            <motion.h1
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.06 }}
              className="mt-5 text-4xl leading-[1.1] font-extrabold tracking-tight text-ink sm:text-5xl lg:text-6xl"
            >
              Turn Social Media Data Into <span className="text-gradient">Meaningful Insights</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.12 }}
              className="mt-5 max-w-xl text-base leading-relaxed text-muted sm:text-lg"
            >
              Analyse public social-media data, discover audience sentiment, visualise engagement
              trends, and export clean datasets in seconds.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.18 }}
              className="mt-8 flex flex-wrap items-center gap-3"
            >
              <Link to={userName ? '/analyze' : '/welcome'}>
                <Button size="lg" icon={<Sparkles size={17} />}>
                  Start Analysis
                </Button>
              </Link>
              <Link to="/welcome">
                <Button size="lg" variant="secondary" icon={<BarChart3 size={17} />}>
                  Explore Dashboard
                </Button>
              </Link>
            </motion.div>

            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.26 }}
              className="mt-5 flex items-start gap-2 text-xs leading-relaxed text-muted"
            >
              <ShieldCheck size={14} className="mt-0.5 shrink-0 text-positive" />
              Uses official YouTube and Meta Graph APIs. No scraping, no authentication bypass, and
              no fabricated engagement figures.
            </motion.p>
          </div>

          {/* Floating preview */}
          <motion.div
            initial={{ opacity: 0, scale: 0.94 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="relative"
          >
            <div className="surface-card card-3d relative overflow-hidden p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-bold text-ink">Engagement Overview</p>
                  <p className="text-[11px] text-muted">Sample preview</p>
                </div>
                <span className="rounded-lg bg-brand/12 px-2 py-1 text-[10px] font-bold text-brand">
                  DEMO
                </span>
              </div>

              {/* Mini bar chart drawn with divs */}
              <div className="mt-6 flex h-36 items-end gap-3">
                {[42, 68, 91, 55, 78, 63].map((height, index) => (
                  <motion.div
                    key={index}
                    initial={{ height: 0 }}
                    animate={{ height: `${height}%` }}
                    transition={{ duration: 0.7, delay: 0.35 + index * 0.08 }}
                    className="flex-1 rounded-t-lg bg-linear-to-t from-brand to-brand-3"
                  />
                ))}
              </div>

              <div className="mt-5 grid grid-cols-3 gap-3">
                {[
                  { label: 'Sentiment', width: 82 },
                  { label: 'Keywords', width: 64 },
                  { label: 'Reach', width: 91 },
                ].map((bar) => (
                  <div key={bar.label} className="rounded-xl bg-ink/4 p-3">
                    <p className="text-[10px] text-muted">{bar.label}</p>
                    <div className="mt-2 h-1.5 rounded-full bg-ink/8">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${bar.width}%` }}
                        transition={{ duration: 0.8, delay: 0.5 }}
                        className="h-full rounded-full bg-linear-to-r from-brand to-brand-2"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Floating KPI chips */}
            <div className="pointer-events-none absolute -inset-6 -z-10">
              {PREVIEW_CARDS.map((card) => (
                <motion.div
                  key={card.label}
                  initial={{ opacity: 0, scale: 0.85 }}
                  animate={{ opacity: 1, scale: 1, y: [0, -10, 0] }}
                  transition={{
                    opacity: { duration: 0.5, delay: card.delay },
                    scale: { duration: 0.5, delay: card.delay },
                    y: { duration: 5.5, repeat: Infinity, ease: 'easeInOut', delay: card.delay },
                  }}
                  className={`animate-float absolute rounded-2xl bg-linear-to-br ${card.accent} px-3.5 py-2.5 text-white shadow-xl`}
                >
                  <p className="text-[11px] font-bold">
                    <span className="mr-1.5" aria-hidden>
                      {card.icon}
                    </span>
                    {card.label}
                  </p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        <p className="mt-10 rounded-xl border border-amber-500/30 bg-amber-500/8 p-3.5 text-center text-xs text-amber-700 dark:text-amber-400">
          <strong>Demo preview.</strong> The figures shown on this page are illustrative sample
          data for layout purposes and are not real platform metrics. Run an analysis to see your
          own data, or use the labelled demo dataset inside the app.
        </p>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-7xl px-5 py-16 sm:px-8">
        <h2 className="text-center text-3xl font-extrabold tracking-tight text-ink">
          Built for defensible analysis
        </h2>
        <p className="mx-auto mt-3 max-w-2xl text-center text-muted">
          Every result is traceable to an official API response or visibly marked as synthetic
          demonstration data.
        </p>

        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.45, delay: index * 0.07 }}
            >
              <div className="surface-card card-3d card-3d-hover h-full p-5">
                <span className="grid size-11 place-items-center rounded-xl bg-linear-to-br from-brand/15 to-brand-2/15 text-brand">
                  <feature.icon size={20} />
                </span>
                <h3 className="mt-4 text-sm font-bold text-ink">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{feature.body}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Pipeline */}
      <section id="pipeline" className="mx-auto max-w-7xl px-5 py-16 sm:px-8">
        <h2 className="text-center text-3xl font-extrabold tracking-tight text-ink">
          The analysis pipeline
        </h2>
        <p className="mx-auto mt-3 max-w-2xl text-center text-muted">
          Every run follows the same reproducible sequence, from a pasted URL to a downloadable
          dataset.
        </p>

        <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {PIPELINE.map((item, index) => (
            <motion.div
              key={item.step}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: index * 0.06 }}
              className="surface-card flex items-center gap-3 p-4"
            >
              <span className="text-gradient text-lg font-extrabold">{item.step}</span>
              <span className="text-sm font-semibold text-ink">{item.label}</span>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Ethics */}
      <section id="ethics" className="mx-auto max-w-4xl px-5 py-16 sm:px-8">
        <div className="surface-card card-3d p-7">
          <span className="grid size-12 place-items-center rounded-2xl bg-positive/12 text-positive">
            <ShieldCheck size={24} />
          </span>
          <h2 className="mt-4 text-xl font-extrabold text-ink">Privacy &amp; ethics</h2>
          <p className="mt-3 text-sm leading-relaxed text-muted">
            SocialScope AI analyses data available through supported platform APIs and permitted
            public sources. It does not bypass privacy settings, authentication, security controls,
            or platform restrictions. No private data is collected, no credentials are exposed to the
            browser, and content that an API refuses to return is reported as unavailable rather
            than approximated.
          </p>
          <Link
            to="/limitations"
            className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-brand hover:underline"
          >
            Read the full API limitations page
            <ArrowRight size={14} />
          </Link>
        </div>
      </section>

      <footer className="border-t border-line py-9">
        <div className="mx-auto flex max-w-7xl flex-col items-center gap-3 px-5 text-center sm:flex-row sm:justify-between sm:px-8 sm:text-left">
          <p className="text-xs text-muted">
            SocialScope AI — Data Analysis Essentials project. Built with FastAPI, React and ECharts.
          </p>
          <div className="flex items-center gap-4 text-muted">
            <span className="flex items-center gap-1.5 text-xs">
              <Github size={14} /> Academic project
            </span>
            <span className="flex items-center gap-1.5 text-xs">
              {theme === 'dark' ? <Moon size={12} /> : <Sun size={12} />}
              {theme === 'dark' ? 'Dark' : 'Light'} mode
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}

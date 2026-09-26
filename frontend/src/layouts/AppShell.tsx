import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import {
  BarChart3,
  Database,
  Gauge,
  History,
  LayoutDashboard,
  LineChart,
  MessageSquare,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Settings,
  ShieldCheck,
  Smile,
  Sun,
  X,
} from 'lucide-react'
import { useApp } from '../context/app-context'
import { Avatar } from '../components/Avatar'
import { ToastStack } from '../components/ToastStack'

interface NavItem {
  to: string
  label: string
  icon: typeof Gauge
  end?: boolean
}

const PRIMARY_NAV: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/analyze', label: 'New Analysis', icon: Search },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/comments', label: 'Comments', icon: MessageSquare },
  { to: '/sentiment', label: 'Sentiment', icon: Smile },
  { to: '/engagement', label: 'Engagement', icon: LineChart },
]

const SECONDARY_NAV: NavItem[] = [
  { to: '/datasets', label: 'Datasets', icon: Database },
  { to: '/history', label: 'History', icon: History },
  { to: '/limitations', label: 'API Limitations', icon: ShieldCheck },
  { to: '/settings', label: 'Settings', icon: Settings },
]

function NavLinks({ items, onNavigate }: { items: NavItem[]; onNavigate?: () => void }) {
  return (
    <nav className="space-y-1" aria-label="Main navigation">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          onClick={onNavigate}
          className={({ isActive }) =>
            `group relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-200 ${
              isActive
                ? 'bg-linear-to-r from-brand/16 to-brand-2/8 text-ink shadow-sm'
                : 'text-muted hover:bg-ink/5 hover:text-ink'
            }`
          }
        >
          {({ isActive }) => (
            <>
              {isActive ? (
                <motion.span
                  layoutId="nav-active"
                  className="absolute top-1/2 left-0 h-6 w-1 -translate-y-1/2 rounded-r-full bg-brand"
                />
              ) : null}
              <item.icon size={17} className={isActive ? 'text-brand' : ''} aria-hidden />
              <span className="truncate">{item.label}</span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}

export function AppShell() {
  const { userName, theme, toggleTheme, sidebarOpen, setSidebarOpen, toasts, dismissToast } = useApp()
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  // Close the mobile drawer whenever the route changes.
  useEffect(() => {
    setSidebarOpen(false)
  }, [location.pathname, setSidebarOpen])

  return (
    <div className="relative flex min-h-screen">
      {/* Decorative background */}
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden>
        <div className="animate-drift absolute -top-32 -left-24 size-[34rem] rounded-full bg-brand/16 blur-3xl" />
        <div
          className="animate-drift absolute -right-32 top-1/3 size-[30rem] rounded-full bg-brand-2/14 blur-3xl"
          style={{ animationDelay: '-7s' }}
        />
        <div
          className="animate-drift absolute -bottom-40 left-1/3 size-[28rem] rounded-full bg-brand-3/10 blur-3xl"
          style={{ animationDelay: '-14s' }}
        />
      </div>

      {/* Sidebar — desktop */}
      <aside
        className={`sticky top-0 hidden h-screen shrink-0 flex-col border-r border-line bg-surface/70 backdrop-blur-xl transition-[width] duration-300 lg:flex ${
          collapsed ? 'w-[76px]' : 'w-[248px]'
        }`}
      >
        <div className="flex h-16 items-center gap-2.5 px-4">
          <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-linear-to-br from-brand to-brand-2 text-white shadow-lg shadow-brand/30">
            <Gauge size={18} />
          </span>
          {!collapsed ? (
            <div className="min-w-0">
              <p className="truncate text-sm font-extrabold tracking-tight text-ink">SocialScope AI</p>
              <p className="truncate text-[10px] text-muted">From data to insights</p>
            </div>
          ) : null}
        </div>

        <div className="flex-1 space-y-6 overflow-y-auto px-3 py-4">
          <NavLinks items={PRIMARY_NAV} />
          {!collapsed ? (
            <>
              <div className="mx-2 border-t border-line" />
              <NavLinks items={SECONDARY_NAV} />
            </>
          ) : null}
        </div>

        <div className="space-y-2 border-t border-line p-3">
          <button
            type="button"
            onClick={toggleTheme}
            className="flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium text-muted transition hover:bg-ink/5 hover:text-ink"
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
            {!collapsed ? <span>{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span> : null}
          </button>
          <button
            type="button"
            onClick={() => setCollapsed((value) => !value)}
            className="hidden w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium text-muted transition hover:bg-ink/5 hover:text-ink lg:flex"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}
            {!collapsed ? <span>Collapse</span> : null}
          </button>
        </div>
      </aside>

      {/* Sidebar — mobile drawer */}
      <AnimatePresence>
        {sidebarOpen ? (
          <>
            <motion.div
              className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSidebarOpen(false)}
              aria-hidden
            />
            <motion.aside
              className="fixed inset-y-0 left-0 z-50 flex w-[268px] flex-col border-r border-line bg-surface lg:hidden"
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'spring', stiffness: 320, damping: 32 }}
            >
              <div className="flex h-16 items-center justify-between px-4">
                <p className="text-sm font-extrabold text-ink">SocialScope AI</p>
                <button
                  type="button"
                  onClick={() => setSidebarOpen(false)}
                  className="rounded-lg p-2 text-muted hover:bg-ink/5 hover:text-ink"
                  aria-label="Close navigation"
                >
                  <X size={18} />
                </button>
              </div>
              <div className="flex-1 space-y-6 overflow-y-auto px-3 py-3">
                <NavLinks items={PRIMARY_NAV} onNavigate={() => setSidebarOpen(false)} />
                <div className="mx-2 border-t border-line" />
                <NavLinks items={SECONDARY_NAV} onNavigate={() => setSidebarOpen(false)} />
              </div>
            </motion.aside>
          </>
        ) : null}
      </AnimatePresence>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-line bg-surface/80 px-4 backdrop-blur-xl sm:px-6">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="rounded-lg p-2 text-muted transition hover:bg-ink/5 hover:text-ink lg:hidden"
            aria-label="Open navigation"
          >
            <PanelLeftOpen size={19} />
          </button>

          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-ink">
              {userName ? `Welcome back, ${userName}` : 'SocialScope AI'}
            </p>
          </div>

          <button
            type="button"
            onClick={toggleTheme}
            className="rounded-xl border border-line p-2.5 text-muted transition hover:border-brand/50 hover:text-brand lg:hidden"
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
          </button>
          <Avatar name={userName} />
        </header>

        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.28 }}
          >
            <Outlet />
          </motion.div>
        </main>

        <footer className="border-t border-line px-6 py-5 text-center text-xs text-muted">
          SocialScope AI — analyses only data available through supported platform APIs and
          permitted public sources. It never bypasses privacy settings, authentication or platform
          restrictions.
        </footer>
      </div>

      <ToastStack toasts={toasts} onDismiss={dismissToast} />
    </div>
  )
}

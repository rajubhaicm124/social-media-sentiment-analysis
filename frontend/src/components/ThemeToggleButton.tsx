import { Moon, Sun } from 'lucide-react'
import { useApp } from '../context/app-context'

/** Standalone theme toggle used on the public landing page. */
export function ThemeToggleButton({ className = '' }: { className?: string }) {
  const { theme, toggleTheme } = useApp()
  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`grid size-9 place-items-center rounded-xl border border-line text-muted transition hover:border-brand/50 hover:text-brand ${className}`}
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
    >
      {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  )
}

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { getPlatforms } from '../services/api'
import type { PlatformInfo } from '../types'
import { AppContext } from './app-context'
import type { Theme, Toast } from './app-context'

const NAME_KEY = 'socialscope.userName'
const THEME_KEY = 'socialscope.theme'

function readName(): string | null {
  try {
    return window.localStorage.getItem(NAME_KEY)
  } catch {
    return null
  }
}

function readTheme(): Theme {
  try {
    const stored = window.localStorage.getItem(THEME_KEY)
    if (stored === 'light' || stored === 'dark') return stored
  } catch {
    /* localStorage unavailable */
  }
  return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

let toastId = 0

export function AppProvider({ children }: { children: ReactNode }) {
  const [userName, setUserNameState] = useState<string | null>(readName)
  const [theme, setTheme] = useState<Theme>(readTheme)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [toasts, setToasts] = useState<Toast[]>([])
  const [platforms, setPlatforms] = useState<PlatformInfo[]>([])
  const [demoModeEnabled, setDemoModeEnabled] = useState(true)
  const timers = useRef<number[]>([])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    document.documentElement.style.colorScheme = theme
    try {
      window.localStorage.setItem(THEME_KEY, theme)
    } catch {
      /* ignore */
    }
  }, [theme])

  const reloadPlatforms = useCallback(async () => {
    try {
      const data = await getPlatforms()
      setPlatforms(data.platforms)
      setDemoModeEnabled(data.demo_mode_enabled)
    } catch {
      // The banner above the form already explains an unreachable API.
      setPlatforms([])
    }
  }, [])

  useEffect(() => {
    void reloadPlatforms()
  }, [reloadPlatforms])

  useEffect(() => {
    const pending = timers.current
    return () => pending.forEach((id) => window.clearTimeout(id))
  }, [])

  const setUserName = useCallback((name: string) => {
    const trimmed = name.trim()
    setUserNameState(trimmed)
    try {
      window.localStorage.setItem(NAME_KEY, trimmed)
    } catch {
      /* ignore */
    }
  }, [])

  const clearUserName = useCallback(() => {
    setUserNameState(null)
    try {
      window.localStorage.removeItem(NAME_KEY)
    } catch {
      /* ignore */
    }
  }, [])

  const dismissToast = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const pushToast = useCallback(
    (message: string, tone: Toast['tone'] = 'info') => {
      const id = ++toastId
      setToasts((current) => [...current, { id, message, tone }])
      const timer = window.setTimeout(() => dismissToast(id), 5200)
      timers.current.push(timer)
    },
    [dismissToast],
  )

  const value = useMemo(
    () => ({
      userName,
      setUserName,
      clearUserName,
      theme,
      toggleTheme: () => setTheme((current) => (current === 'dark' ? 'light' : 'dark')),
      sidebarOpen,
      setSidebarOpen,
      toasts,
      pushToast,
      dismissToast,
      platforms,
      reloadPlatforms,
      demoModeEnabled,
    }),
    [
      userName,
      setUserName,
      clearUserName,
      theme,
      sidebarOpen,
      toasts,
      pushToast,
      dismissToast,
      platforms,
      reloadPlatforms,
      demoModeEnabled,
    ],
  )

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

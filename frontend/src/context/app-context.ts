import { createContext, useContext } from 'react'
import type { PlatformInfo } from '../types'

export type Theme = 'dark' | 'light'

export interface Toast {
  id: number
  message: string
  tone: 'success' | 'error' | 'info'
}

export interface AppState {
  userName: string | null
  setUserName: (name: string) => void
  clearUserName: () => void

  theme: Theme
  toggleTheme: () => void

  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void

  toasts: Toast[]
  pushToast: (message: string, tone?: Toast['tone']) => void
  dismissToast: (id: number) => void

  platforms: PlatformInfo[]
  reloadPlatforms: () => Promise<void>
  demoModeEnabled: boolean
}

export const AppContext = createContext<AppState | null>(null)

export function useApp(): AppState {
  const context = useContext(AppContext)
  if (!context) throw new Error('useApp must be used inside <AppProvider>')
  return context
}

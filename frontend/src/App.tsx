import { useEffect } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AppShell } from './layouts/AppShell'
import { useApp } from './context/app-context'
import { ErrorBoundary } from './components/ErrorBoundary'

import { LandingPage } from './pages/LandingPage'
import { WelcomePage } from './pages/WelcomePage'
import { DashboardPage } from './pages/DashboardPage'
import { NewAnalysisPage } from './pages/NewAnalysisPage'
import { AnalysisViewPage } from './pages/AnalysisViewPage'
import { CommentsPage } from './pages/CommentsPage'
import { SentimentPage } from './pages/SentimentPage'
import { EngagementPage } from './pages/EngagementPage'
import { DatasetsPage } from './pages/DatasetsPage'
import { HistoryPage } from './pages/HistoryPage'
import { LimitationsPage } from './pages/LimitationsPage'
import { SettingsPage } from './pages/SettingsPage'
import { NotFoundPage } from './pages/NotFoundPage'

/** Redirects to the welcome step until a display name has been provided. */
function RequireName({ children }: { children: React.ReactNode }) {
  const { userName } = useApp()
  const location = useLocation()
  if (!userName) {
    return <Navigate to="/welcome" replace state={{ from: location.pathname }} />
  }
  return <>{children}</>
}

export default function App() {
  const location = useLocation()

  // Reflect the route in the document title for browser history and tabs.
  useEffect(() => {
    const titles: Record<string, string> = {
      '/': 'SocialScope AI — Social Media Sentiment & Analytics',
      '/welcome': 'Welcome — SocialScope AI',
      '/dashboard': 'Dashboard — SocialScope AI',
      '/analyze': 'New Analysis — SocialScope AI',
      '/analytics': 'Analytics — SocialScope AI',
      '/comments': 'Comments — SocialScope AI',
      '/sentiment': 'Sentiment — SocialScope AI',
      '/engagement': 'Engagement — SocialScope AI',
      '/datasets': 'Datasets — SocialScope AI',
      '/history': 'History — SocialScope AI',
      '/limitations': 'API Limitations — SocialScope AI',
      '/settings': 'Settings — SocialScope AI',
    }
    document.title = titles[location.pathname] ?? 'SocialScope AI'
  }, [location.pathname])

  return (
    <ErrorBoundary>
      <Routes>
        {/* Public */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/welcome" element={<WelcomePage />} />

        {/* Authenticated shell */}
        <Route
          element={
            <RequireName>
              <AppShell />
            </RequireName>
          }
        >
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/analyze" element={<NewAnalysisPage />} />
          <Route path="/analytics" element={<AnalysisViewPage />} />
          <Route path="/analysis/:analysisId" element={<AnalysisViewPage />} />
          <Route path="/comments" element={<CommentsPage />} />
          <Route path="/sentiment" element={<SentimentPage />} />
          <Route path="/engagement" element={<EngagementPage />} />
          <Route path="/datasets" element={<DatasetsPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/limitations" element={<LimitationsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>

        <Route
          path="*"
          element={
            <div className="grid min-h-screen place-items-center p-6">
              <div className="w-full max-w-md">
                <NotFoundPage />
              </div>
            </div>
          }
        />
      </Routes>
    </ErrorBoundary>
  )
}

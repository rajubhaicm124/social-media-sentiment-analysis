import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { AlertOctagon, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

/**
 * Catches render-time crashes so a single broken component never leaves the
 * user with a blank page. Production builds show no stack trace.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error('SocialScope AI render error:', error, info.componentStack)
  }

  private reset = () => this.setState({ error: null })

  render() {
    const { error } = this.state
    if (!error) return this.props.children

    return (
      <div className="grid min-h-screen place-items-center p-6">
        <div className="surface-card card-3d w-full max-w-lg p-7 text-center">
          <span className="mx-auto mb-4 grid size-14 place-items-center rounded-2xl bg-negative/12 text-negative">
            <AlertOctagon size={26} />
          </span>
          <h1 className="text-xl font-extrabold text-ink">Something went wrong</h1>
          <p className="mt-2 text-sm text-muted">
            The interface hit an unexpected error. Your saved analyses are unaffected.
          </p>
          <button
            type="button"
            onClick={this.reset}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-linear-to-r from-brand to-brand-2 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-brand/25 transition hover:brightness-110"
          >
            <RefreshCw size={15} />
            Try again
          </button>
        </div>
      </div>
    )
  }
}

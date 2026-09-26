import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, Gauge, Sparkles, User } from 'lucide-react'
import { useApp } from '../context/app-context'
import { Button } from '../components/ui'
import { ThemeToggleButton } from '../components/ThemeToggleButton'

const MAX_NAME = 80

export function WelcomePage() {
  const { userName, setUserName } = useApp()
  const [name, setName] = useState(userName ?? '')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const trimmed = name.trim()
  const canContinue = trimmed.length > 0 && trimmed.length <= MAX_NAME

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    if (!canContinue) {
      setError('Please enter a name to continue.')
      return
    }
    setUserName(trimmed)
    navigate('/dashboard', { replace: true })
  }

  return (
    <div className="relative grid min-h-screen place-items-center overflow-hidden px-5 py-12">
      <div className="pointer-events-none fixed inset-0 -z-10" aria-hidden>
        <div className="animate-drift absolute -top-32 -left-24 size-[34rem] rounded-full bg-brand/18 blur-3xl" />
        <div
          className="animate-drift absolute -right-32 -bottom-24 size-[30rem] rounded-full bg-brand-2/14 blur-3xl"
          style={{ animationDelay: '-9s' }}
        />
      </div>

      <div className="absolute top-5 right-5">
        <ThemeToggleButton />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55 }}
        className="w-full max-w-md"
      >
        <div className="mb-7 text-center">
          <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-linear-to-br from-brand to-brand-2 text-white shadow-xl shadow-brand/30">
            <Gauge size={26} />
          </span>
          <h1 className="mt-5 text-3xl font-extrabold tracking-tight text-ink">What should we call you?</h1>
          <p className="mt-2 text-sm text-muted">
            This name is stored locally in your browser and is attached to your analyses.
          </p>
        </div>

        <form onSubmit={submit} className="surface-card card-3d p-6">
          <label htmlFor="display-name" className="mb-2 block text-xs font-semibold text-muted">
            Enter your name
          </label>

          <div className="relative">
            <User
              size={17}
              className="pointer-events-none absolute top-1/2 left-3.5 -translate-y-1/2 text-muted"
              aria-hidden
            />
            <input
              id="display-name"
              type="text"
              value={name}
              onChange={(event) => {
                setName(event.target.value)
                if (error) setError('')
              }}
              maxLength={MAX_NAME}
              autoFocus
              autoComplete="name"
              placeholder="e.g. Aarav"
              aria-invalid={Boolean(error)}
              aria-describedby={error ? 'name-error' : undefined}
              className="w-full rounded-xl border border-line bg-surface-2 py-3.5 pr-3.5 pl-11 text-base text-ink outline-none transition placeholder:text-muted/60 focus:border-brand focus:ring-2 focus:ring-brand/25"
            />
          </div>

          {error ? (
            <p id="name-error" role="alert" className="mt-2 text-xs font-medium text-negative">
              {error}
            </p>
          ) : null}

          <Button
            type="submit"
            size="lg"
            fullWidth
            className="mt-5"
            disabled={!canContinue}
            icon={<ArrowRight size={17} />}
          >
            Continue
          </Button>

          <p className="mt-4 flex items-start gap-2 text-[11px] leading-relaxed text-muted">
            <Sparkles size={12} className="mt-0.5 shrink-0" />
            You will only be asked once — your name is remembered for your next visit.
          </p>
        </form>
      </motion.div>
    </div>
  )
}

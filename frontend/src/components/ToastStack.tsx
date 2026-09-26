import { AnimatePresence, motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, Info, X } from 'lucide-react'
import type { Toast } from '../context/app-context'

const TONES = {
  success: { icon: CheckCircle2, className: 'text-positive', ring: 'ring-positive/30' },
  error: { icon: AlertTriangle, className: 'text-negative', ring: 'ring-negative/30' },
  info: { icon: Info, className: 'text-brand', ring: 'ring-brand/30' },
}

export function ToastStack({
  toasts,
  onDismiss,
}: {
  toasts: Toast[]
  onDismiss: (id: number) => void
}) {
  return (
    <div
      className="pointer-events-none fixed right-4 bottom-4 z-[60] flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-2"
      aria-live="polite"
      aria-atomic="false"
    >
      <AnimatePresence initial={false}>
        {toasts.map((toast) => {
          const tone = TONES[toast.tone]
          return (
            <motion.div
              key={toast.id}
              layout
              initial={{ opacity: 0, y: 18, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 40, scale: 0.97 }}
              transition={{ duration: 0.22 }}
              className={`pointer-events-auto flex items-start gap-3 rounded-xl bg-surface p-3.5 shadow-xl ring-1 ${tone.ring}`}
            >
              <tone.icon size={17} className={`mt-0.5 shrink-0 ${tone.className}`} />
              <p className="min-w-0 flex-1 text-sm text-ink">{toast.message}</p>
              <button
                type="button"
                onClick={() => onDismiss(toast.id)}
                className="shrink-0 rounded-md p-1 text-muted transition hover:text-ink"
                aria-label="Dismiss notification"
              >
                <X size={14} />
              </button>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}

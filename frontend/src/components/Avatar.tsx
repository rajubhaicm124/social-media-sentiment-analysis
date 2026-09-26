import { Link } from 'react-router-dom'
import { useApp } from '../context/app-context'

const SIZES = {
  sm: 'size-8 text-xs',
  md: 'size-10 text-sm',
  lg: 'size-16 text-xl',
}

/** Initial-based avatar; falls back to a neutral glyph with no name. */
export function Avatar({
  name,
  size = 'md',
}: {
  name: string | null
  size?: keyof typeof SIZES
}) {
  const { setSidebarOpen } = useApp()
  const initial = name?.trim()?.charAt(0).toUpperCase()

  const avatar = (
    <span
      className={`grid shrink-0 place-items-center rounded-full bg-linear-to-br from-brand to-brand-2 font-bold text-white shadow-md shadow-brand/25 ${SIZES[size]}`}
      title={name ?? 'Not signed in'}
    >
      {initial ?? '?'}
    </span>
  )

  if (!name) {
    return (
      <Link to="/welcome" aria-label="Set your display name">
        {avatar}
      </Link>
    )
  }

  return (
    <Link
      to="/settings"
      aria-label={`Profile settings for ${name}`}
      onClick={() => setSidebarOpen(false)}
    >
      {avatar}
    </Link>
  )
}

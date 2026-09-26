import { useCallback, useEffect, useState } from 'react'
import { ApiError, deleteAnalysis, getAnalysis, getHistory, getProfile } from '../services/api'
import type { Analysis, HistoryItem, ProfileStats } from '../types'
import { useApp } from '../context/app-context'

interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string
  reload: () => void
}

/** Loads a single analysis by id, with loading and friendly error state. */
export function useAnalysis(analysisId: string | undefined): AsyncState<Analysis> {
  const [data, setData] = useState<Analysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [nonce, setNonce] = useState(0)

  useEffect(() => {
    if (!analysisId) {
      setLoading(false)
      setError('No analysis was selected.')
      return
    }
    let cancelled = false
    setLoading(true)
    setError('')

    getAnalysis(analysisId)
      .then((analysis) => {
        if (cancelled) return
        setData(analysis)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        setData(null)
        setError(
          err instanceof ApiError ? err.message : 'The analysis could not be loaded.',
        )
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [analysisId, nonce])

  const reload = useCallback(() => setNonce((value) => value + 1), [])
  return { data, loading, error, reload }
}

/** Saved analyses for the current user, newest first. */
export function useHistory(): AsyncState<HistoryItem[]> & { remove: (id: string) => Promise<void> } {
  const { userName } = useApp()
  const [data, setData] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [nonce, setNonce] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')

    getHistory(userName ?? undefined)
      .then((response) => {
        if (!cancelled) setData(response.analyses)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        setData([])
        setError(err instanceof ApiError ? err.message : 'History could not be loaded.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [userName, nonce])

  const remove = useCallback(async (id: string) => {
    await deleteAnalysis(id)
    setData((current) => current.filter((item) => item.analysis_id !== id))
  }, [])

  const reload = useCallback(() => setNonce((value) => value + 1), [])
  return { data, loading, error, reload, remove }
}

/** Aggregate profile statistics for the signed-in user. */
export function useProfile(): AsyncState<ProfileStats> {
  const { userName } = useApp()
  const [data, setData] = useState<ProfileStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [nonce, setNonce] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)

    getProfile(userName ?? undefined)
      .then((profile) => {
        if (!cancelled) {
          setData(profile)
          setError('')
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return
        setData(null)
        setError(err instanceof ApiError ? err.message : 'Profile could not be loaded.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [userName, nonce])

  const reload = useCallback(() => setNonce((value) => value + 1), [])
  return { data, loading, error, reload }
}

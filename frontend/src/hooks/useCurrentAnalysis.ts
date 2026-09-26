import { useMemo } from 'react'
import { useHistory } from './useAnalysis'

/**
 * Resolves which analysis the secondary pages should display: the newest one
 * belonging to the signed-in user.
 */
export function useCurrentAnalysis() {
  const { data: history, loading, error } = useHistory()
  const analysisId = useMemo(() => history?.[0]?.analysis_id, [history])
  return { analysisId, history: history ?? [], loading, error }
}

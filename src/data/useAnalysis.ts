import { useEffect, useState } from 'react'
import { apiFetch } from './api'
import type { AnalysisResponse } from './analysisTypes'

export function useAnalysis() {
  const [state, setState] = useState<{
    response: AnalysisResponse | null
    loading: boolean
    error: string | null
  }>({ response: null, loading: true, error: null })
  useEffect(() => {
    let current = true
    apiFetch<AnalysisResponse>('/api/analysis').then(
      response => {
        if (current) setState({ response, loading: false, error: null })
      },
      (error: Error) => {
        if (current) setState({ response: null, loading: false, error: error.message })
      }
    )
    return () => { current = false }
  }, [])
  return state
}

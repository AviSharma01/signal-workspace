import { useEffect, useState } from 'react'
import { apiFetch } from './api'
import type { AnalysisResponse, CohortResponse } from './analysisTypes'

export function useAnalysis() {
  const [state, setState] = useState<{
    response: AnalysisResponse | null
    loading: boolean
    error: string | null
    cohortResponse: CohortResponse | null
    cohortLoading: boolean
    cohortError: string | null
  }>({ response: null, loading: true, error: null, cohortResponse: null, cohortLoading: true, cohortError: null })
  useEffect(() => {
    let current = true
    apiFetch<AnalysisResponse>('/api/analysis').then(
      response => {
        if (current) setState(previous => ({ ...previous, response, loading: false, error: null }))
      },
      (error: Error) => {
        if (current) setState(previous => ({ ...previous, response: null, loading: false, error: error.message }))
      }
    )
    apiFetch<CohortResponse>('/api/analysis/cohorts').then(
      cohortResponse => {
        if (current) setState(previous => ({ ...previous, cohortResponse, cohortLoading: false, cohortError: null }))
      },
      (error: Error) => {
        if (current) setState(previous => ({ ...previous, cohortResponse: null, cohortLoading: false, cohortError: error.message }))
      }
    )
    return () => { current = false }
  }, [])
  return state
}

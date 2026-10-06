import { useReducer, useEffect, useRef, useState, useCallback } from 'react'
import type { Finding } from '../shared/types'
import type { CapabilityState, ResultStatus } from '../capabilities/types'
import { apiFetch } from './api'

interface FindingsResponse {
  findings: Finding[]
  capability: CapabilityState
  result: ResultStatus
  legacyDataExcluded: boolean
}

interface FindingsResult {
  findings: Finding[]
  capability: CapabilityState | null
  result: ResultStatus | null
  loading: boolean
  error: string | null
  refetch: () => void
}

type State = Omit<FindingsResult, 'refetch'>

type Action =
  | { type: 'start' }
  | { type: 'success'; response: FindingsResponse }
  | { type: 'error'; error: string }

function reducer(_state: State, action: Action): State {
  switch (action.type) {
    case 'start':
      return { findings: [], capability: null, result: null, loading: true, error: null }
    case 'success':
      return {
        findings: action.response.findings,
        capability: action.response.capability,
        result: action.response.result,
        loading: false,
        error: null,
      }
    case 'error':
      return { findings: [], capability: null, result: null, loading: false, error: action.error }
  }
}

const initialState: State = {
  findings: [],
  capability: null,
  result: null,
  loading: true,
  error: null,
}

export function useFindings(companyId: string | null): FindingsResult {
  const [state, dispatch] = useReducer(reducer, initialState)
  const generationRef = useRef(0)
  const [tick, setTick] = useState(0)

  const refetch = useCallback(() => setTick((t) => t + 1), [])

  useEffect(() => {
    if (!companyId) return

    const generation = ++generationRef.current
    dispatch({ type: 'start' })

    apiFetch<FindingsResponse>(`/api/findings?ticker=${companyId}&limit=10`)
      .then((data) => {
        if (generation !== generationRef.current) return
        dispatch({ type: 'success', response: data })
      })
      .catch((err: unknown) => {
        if (generation !== generationRef.current) return
        dispatch({
          type: 'error',
          error: err instanceof Error ? err.message : 'Unknown error',
        })
      })
  }, [companyId, tick])

  return { ...state, refetch }
}

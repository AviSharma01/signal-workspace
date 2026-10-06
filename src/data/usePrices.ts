import { useReducer, useEffect, useRef } from 'react'
import type { PricePoint } from '../shared/types'
import type { CapabilityState, ResultStatus } from '../capabilities/types'
import { apiFetch } from './api'

export type PriceRange = '1D' | '1W' | '1M' | '3M'

interface PricesResult {
  prices: PricePoint[]
  capability: CapabilityState | null
  result: ResultStatus | null
  loading: boolean
  error: string | null
}

interface PricesResponse {
  capability: CapabilityState
  result: ResultStatus
  prices: PricePoint[]
  legacyDataExcluded: boolean
}

type State = PricesResult

type Action =
  | { type: 'start' }
  | { type: 'success'; response: PricesResponse }
  | { type: 'error'; error: string }

function reducer(_state: State, action: Action): State {
  switch (action.type) {
    case 'start':
      return { prices: [], capability: null, result: null, loading: true, error: null }
    case 'success':
      return {
        prices: action.response.prices,
        capability: action.response.capability,
        result: action.response.result,
        loading: false,
        error: null,
      }
    case 'error':
      return { prices: [], capability: null, result: null, loading: false, error: action.error }
  }
}

const initialState: State = {
  prices: [],
  capability: null,
  result: null,
  loading: true,
  error: null,
}

export function usePrices(companyId: string, range: PriceRange): PricesResult {
  const [state, dispatch] = useReducer(reducer, initialState)

  // Track fetch generation so stale responses from previous companyId/range are dropped
  const generationRef = useRef(0)

  useEffect(() => {
    const generation = ++generationRef.current
    dispatch({ type: 'start' })

    apiFetch<PricesResponse>(`/api/prices/${companyId}?range=${range}`)
      .then((data) => {
        if (generation !== generationRef.current) return
        dispatch({
          type: 'success',
          response: {
            ...data,
            prices: [...data.prices].sort((a, b) => a.timestamp - b.timestamp),
          },
        })
      })
      .catch((err: unknown) => {
        if (generation !== generationRef.current) return
        dispatch({
          type: 'error',
          error: err instanceof Error ? err.message : 'Unknown error',
        })
      })
  }, [companyId, range])

  return state
}

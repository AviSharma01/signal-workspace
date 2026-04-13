import { useReducer, useEffect, useRef } from 'react'
import type { PricePoint } from '../shared/types'
import { apiFetch } from './api'

export type PriceRange = '1D' | '1W' | '1M' | '3M'

interface PricesResult {
  prices: PricePoint[]
  loading: boolean
  error: string | null
}

type State = PricesResult

type Action =
  | { type: 'start' }
  | { type: 'success'; prices: PricePoint[] }
  | { type: 'error'; error: string }

function reducer(_state: State, action: Action): State {
  switch (action.type) {
    case 'start':
      return { prices: [], loading: true, error: null }
    case 'success':
      return { prices: action.prices, loading: false, error: null }
    case 'error':
      return { prices: [], loading: false, error: action.error }
  }
}

const initialState: State = { prices: [], loading: false, error: null }

export function usePrices(companyId: string, range: PriceRange): PricesResult {
  const [state, dispatch] = useReducer(reducer, initialState)

  // Track fetch generation so stale responses from previous companyId/range are dropped
  const generationRef = useRef(0)

  useEffect(() => {
    const generation = ++generationRef.current
    dispatch({ type: 'start' })

    apiFetch<PricePoint[]>(`/api/prices/${companyId}?range=${range}`)
      .then((data) => {
        if (generation !== generationRef.current) return
        dispatch({
          type: 'success',
          prices: [...data].sort((a, b) => a.timestamp - b.timestamp),
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

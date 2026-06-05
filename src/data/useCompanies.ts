import { useReducer, useEffect, useRef } from 'react'
import type { Company } from '../shared/types'
import { apiFetch } from './api'

interface CompaniesResult {
  companies: Company[]
  loading: boolean
  error: string | null
}

type State = CompaniesResult

type Action =
  | { type: 'start' }
  | { type: 'success'; companies: Company[] }
  | { type: 'error'; error: string }

function reducer(_state: State, action: Action): State {
  switch (action.type) {
    case 'start':
      return { companies: [], loading: true, error: null }
    case 'success':
      return { companies: action.companies, loading: false, error: null }
    case 'error':
      return { companies: [], loading: false, error: action.error }
  }
}

const initialState: State = { companies: [], loading: false, error: null }

export function useCompanies(): CompaniesResult {
  const [state, dispatch] = useReducer(reducer, initialState)
  const generationRef = useRef(0)

  useEffect(() => {
    const generation = ++generationRef.current
    dispatch({ type: 'start' })

    apiFetch<Company[]>('/api/companies')
      .then((data) => {
        if (generation !== generationRef.current) return
        dispatch({ type: 'success', companies: data })
      })
      .catch((err: unknown) => {
        if (generation !== generationRef.current) return
        dispatch({
          type: 'error',
          error: err instanceof Error ? err.message : 'Unknown error',
        })
      })
  }, [])

  return state
}

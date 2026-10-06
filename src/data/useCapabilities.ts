import { useEffect, useReducer } from 'react'
import type { CapabilityResponse, CapabilityState } from '../capabilities/types'
import { apiFetch } from './api'

interface State {
  response: CapabilityResponse | null
  loading: boolean
  error: string | null
}

type Action = { type: 'success'; response: CapabilityResponse } | { type: 'error'; error: string }

function reducer(state: State, action: Action): State {
  return action.type === 'success'
    ? { response: action.response, loading: false, error: null }
    : { ...state, loading: false, error: action.error }
}

export function useCapabilities(): State & {
  getCapability: (id: string) => CapabilityState | null
} {
  const [state, dispatch] = useReducer(reducer, {
    response: null,
    loading: true,
    error: null,
  })

  useEffect(() => {
    let disposed = false
    apiFetch<CapabilityResponse>('/api/capabilities')
      .then(response => {
        if (!disposed) dispatch({ type: 'success', response })
      })
      .catch((error: unknown) => {
        if (!disposed) {
          dispatch({
            type: 'error',
            error: error instanceof Error ? error.message : 'Unable to load capability status',
          })
        }
      })
    return () => {
      disposed = true
    }
  }, [])

  return {
    ...state,
    getCapability: (id: string) =>
      state.response?.capabilities.find(capability => capability.id === id) ?? null,
  }
}

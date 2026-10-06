import { useCallback, useEffect, useReducer, useState } from 'react'
import { apiFetch, apiPost } from './api'
import type { InvestigationResponse, InvestigationRun } from './investigationTypes'

interface State {
  response: InvestigationResponse | null
  loading: boolean
  error: string | null
}

type Action = { type: 'success'; response: InvestigationResponse } | { type: 'error'; error: string }

export function useInvestigations() {
  const [generation, setGeneration] = useState(0)
  const [state, dispatch] = useReducer((_state: State, action: Action): State =>
    action.type === 'success'
      ? { response: action.response, loading: false, error: null }
      : { response: null, loading: false, error: action.error },
    { response: null, loading: true, error: null })
  const refresh = useCallback(() => setGeneration(value => value + 1), [])
  useEffect(() => {
    let disposed = false
    apiFetch<InvestigationResponse>('/api/investigations')
      .then(response => { if (!disposed) dispatch({ type: 'success', response }) })
      .catch((error: unknown) => {
        if (!disposed) dispatch({ type: 'error', error: error instanceof Error ? error.message : 'Investigation request failed' })
      })
    return () => { disposed = true }
  }, [generation])
  return { ...state, refresh }
}

export async function startInvestigation(command: {
  trigger: { kind: 'event' | 'watch_event'; id: string; activeOnly: boolean }
  boundary: { perspective: 'system_observation' | 'public_information'; asOf: number }
  budgets: { steps: number; elapsedMs: number }
}) {
  const created = await apiPost<{ run: InvestigationRun }>('/api/investigations', command)
  return apiPost<{ run: InvestigationRun }>(`/api/investigations/${encodeURIComponent(created.run.id)}/execute`)
}

export function useInvestigationEvents(asOf: number, perspective: 'system_observation' | 'public_information') {
  const [events, setEvents] = useState<Array<{ id: string; status: string }>>([])
  useEffect(() => {
    if (!Number.isFinite(asOf)) return
    let disposed = false
    apiFetch<{ events: Array<{ id: string; status: string }> }>(`/api/events?perspective=${perspective}&asOf=${asOf}`)
      .then(response => { if (!disposed) setEvents(response.events.filter(event => event.status === 'event')) })
      .catch(() => { if (!disposed) setEvents([]) })
    return () => { disposed = true }
  }, [asOf, perspective])
  return events
}

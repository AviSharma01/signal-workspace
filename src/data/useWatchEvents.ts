import { useEffect, useReducer } from 'react'
import { apiFetch } from './api'

export interface WatchAssessment {
  policyVersion: string
  evaluatedAt: number
  evidenceStanding: { status: 'supported' | 'withdrawn' | 'unresolved'; evidenceIds: string[] }
  admissionCriteria: { satisfied: boolean; reasons: string[] }
  recency: { status: 'within_window' | 'expired' | 'publication_age_unknown' | 'expiry_uncertain' }
  expirySupport: {
    status: 'exact' | 'interval' | 'unsupported'
    expiresAt?: number
    earliestExpiryAt?: number
    latestExpiryAt?: number
    reason?: string
    policyTimezone: string
  }
  activeEligibility: { eligible: boolean; reasons: string[] }
  lifecycleReasons: string[]
  publicationSupport: {
    assessment: {
      status: string
      interval: { start: number; endExclusive: number; precision: string } | null
    }
    selectedEvidence: { rawValue: string; timezone: string | null } | null
  }
  transactionDate: string | null
}

export interface WatchEventDetail {
  watchEvent: {
    id: string
    eventId: string
    discoveredAt: number
    officialEvidenceFirstObservedAt: number
    verifiedAt: number
    admittedAt: number
  }
  currentEvaluation: WatchAssessment
  lastPersistedAssessment: WatchAssessment
  lastPersistedAssessmentIsStale: boolean
  currentDiffersFromLastPersisted: boolean
  lifecycleHistory: Array<{
    id: string
    evaluatedAt: number
    persistedAt: number
    trigger: string
    transitionReasons: string[]
    assessment: WatchAssessment
    recordType: 'recorded_historical_state'
  }>
  currentEvent: {
    fields: { transactionDirection?: string; ticker?: string }
    provenance: {
      rows: Array<{
        occurrenceId: string
        sourceUrl: string
        sourceAuthority: string
        artifactVersionId: string
      }>
    }
  }
}

interface Response {
  evaluatedAt: number
  policyVersion: string
  state: 'empty' | 'complete'
  watchEvents: WatchEventDetail[]
}

interface State {
  response: Response | null
  loading: boolean
  error: string | null
}

type Action = { type: 'success'; response: Response } | { type: 'error'; error: string }

function reducer(state: State, action: Action): State {
  return action.type === 'success'
    ? { response: action.response, loading: false, error: null }
    : { ...state, loading: false, error: action.error }
}

export function useWatchEvents(): State {
  const [state, dispatch] = useReducer(reducer, { response: null, loading: true, error: null })
  useEffect(() => {
    let disposed = false
    const refresh = () => {
      apiFetch<Response>('/api/watch-events')
        .then(response => {
          if (!disposed) dispatch({ type: 'success', response })
        })
        .catch((error: unknown) => {
          if (!disposed)
            dispatch({
              type: 'error',
              error: error instanceof Error ? error.message : 'Unable to load Watch Events',
            })
        })
    }
    refresh()
    const interval = window.setInterval(refresh, 30_000)
    return () => {
      disposed = true
      window.clearInterval(interval)
    }
  }, [])
  return state
}

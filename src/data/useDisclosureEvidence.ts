import { useEffect, useReducer } from 'react'
import { apiFetch } from './api'
import type { CapabilityState, ResultStatus } from '../capabilities/types'

export interface DisclosureNormalization {
  id: string
  extractionId: string
  method: string
  methodVersion: string
  normalizedAt: number
  status: 'succeeded' | 'partial' | 'failed'
  normalizedFields: Record<string, unknown>
  issues: string[]
}

export interface DisclosureRowOccurrence {
  id: string
  ordinal: number
  rawFields: unknown
  parseStatus: string
  normalizations: DisclosureNormalization[]
}

export interface DisclosureArtifactVersion {
  id: string
  contentSha256: string
  contentLength: number
  mediaType: string
  firstObservedAt: number
  extractions: Array<{
    id: string
    method: string
    methodVersion: string
    extractedAt: number
    status: string
    error: string | null
  }>
  rowOccurrences: DisclosureRowOccurrence[]
}

export interface DisclosureArtifact {
  id: string
  sourceName: string
  sourceAuthority: 'official' | 'supporting'
  artifactKind: string
  sourceUrl: string
  mediaType: string
  versions: DisclosureArtifactVersion[]
  retrievalObservations: Array<{
    id: string
    artifactVersionId: string | null
    observedAt: number
    purpose: string
    availabilityStatus: string
    freshnessStatus: string
    coverageStatus: string
    httpStatus: number | null
  }>
}

interface DisclosureEvidenceResponse {
  capability: CapabilityState
  result: ResultStatus
  population: 'real'
  sourceFilings: Array<{
    id: string
    sourceName: string
    sourceFilingId: string
    chamber: string
    sourceUrl: string | null
    discoveredAt: number
  }>
  artifacts: DisclosureArtifact[]
}

interface ChamberReadiness {
  id: string
  name: string
  chamber: string
  availability: 'available' | 'conditional' | 'unavailable'
  reasonCode: string
  reasonCodes: string[]
  detail: string
  evaluatedAt: number
  governingVersion: string
  unmetPrerequisites: Array<{ code: string; detail: string; supported: boolean }>
}

interface DisclosureReadinessResponse {
  house: ChamberReadiness
  senate: ChamberReadiness
  result: ResultStatus
}

interface State {
  evidence: DisclosureEvidenceResponse | null
  readiness: DisclosureReadinessResponse | null
  loading: boolean
  error: string | null
}

type Action =
  | { type: 'success'; evidence: DisclosureEvidenceResponse; readiness: DisclosureReadinessResponse }
  | { type: 'error'; error: string }

const initialState: State = { evidence: null, readiness: null, loading: true, error: null }

function reducer(_state: State, action: Action): State {
  if (action.type === 'success') {
    return { evidence: action.evidence, readiness: action.readiness, loading: false, error: null }
  }
  return { evidence: null, readiness: null, loading: false, error: action.error }
}

export function useDisclosureEvidence(): State {
  const [state, dispatch] = useReducer(reducer, initialState)

  useEffect(() => {
    Promise.all([
      apiFetch<DisclosureEvidenceResponse>('/api/disclosures/evidence'),
      apiFetch<DisclosureReadinessResponse>('/api/disclosures/readiness'),
    ])
      .then(([evidence, readiness]) => dispatch({ type: 'success', evidence, readiness }))
      .catch((error: unknown) =>
        dispatch({
          type: 'error',
          error: error instanceof Error ? error.message : 'Unable to load disclosure evidence',
        }),
      )
  }, [])

  return state
}

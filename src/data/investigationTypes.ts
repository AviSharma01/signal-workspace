import type { CapabilityState, ResultStatus } from '../capabilities/types'

export interface Boundary {
  perspective: 'public_information' | 'system_observation'
  asOf: number
}

export interface EvidenceReference {
  kind: string
  citations: Array<{
    artifactVersionId: string
    artifactId: string
    locator: string
    sourceAuthority: string
    sourceUrl: string
    contentSha256: string
    observedAt: number
    publicAvailableBy: number
    publicTimeBasis: string
    publicationEvidenceIds: string[]
    observationIds: string[]
  }>
  observedAt: number
  publicAvailableBy: number | null
  derivedAt: number
  methodVersion: string
  eligibility: Boundary & { eligible: boolean; availableBy: number; reasons: string[] }
}

interface Claim {
  text: string
  citations: Array<{ evidenceId: string; reference: EvidenceReference }>
}

export interface InvestigationTrigger {
  kind: 'event' | 'watch_event'
  id: string
  eventId: string
  activeOnly: boolean
  version: string
  eventMethodVersion: string
}

export interface Finding {
  runId: string
  trigger: InvestigationTrigger
  boundary: Boundary
  outcome: 'unexplained' | 'insufficient_eligible_evidence' | 'capability_unavailable' | 'budget_exhausted'
  summary: string
  hypothesesConsidered: string[]
  claims: Claim[]
  counterevidence: Claim[]
  unresolvedQuestions: string[]
  confidence: 'low' | 'medium' | 'high'
  confidenceBasis: string
  limitations: string[]
  missingness: string[]
  capabilityLimitations: CapabilityState[]
  methodVersion: string
  modelVersion: string | null
  reviewStatus: 'needs_human_review'
  noAdviceStatus: 'validated'
  advice: null
  createdAt: number
}

export interface InvestigationRun {
  id: string
  population: 'real' | 'test' | 'demo' | 'evaluation'
  createdAt: number
  status: 'ready' | 'completed' | 'incomplete' | 'unavailable' | 'review_required'
  manifest: {
    trigger: InvestigationTrigger
    boundary: Boundary
    evidence: Array<EvidenceReference & { id: string; content: unknown }>
    capabilitySnapshot: { contractVersion: string; capabilities: CapabilityState[]; evaluatedAt: number }
    budgets: { steps: number; elapsedMs: number; modelSpendUsd: number | null }
    mode: 'deterministic' | 'optional_model'
    methodVersion: string
    validatorVersion: string
    digest: string
  }
  execution: {
    outcome: Finding['outcome']
    reasons: string[]
    inspectedEvidenceIds: string[]
    usage: { steps: number; elapsedMs: number; modelSpendUsd: number }
    finishedAt: number
  } | null
  finding: Finding | null
}

export interface InvestigationResponse {
  capability: CapabilityState
  result: ResultStatus
  runs: InvestigationRun[]
}

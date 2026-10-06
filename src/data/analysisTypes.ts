import type { CapabilityState, ResultStatus } from '../capabilities/types'

export interface OutcomeMetric {
  value: number | null
  availability: 'available' | 'unavailable'
  reasons: string[]
}

export interface EventOutcome {
  eventId: string
  horizonSessions: number
  primaryHorizon: boolean
  direction: string
  eventBoundary: number | null
  outcomeBoundary: number | null
  sessionDates: string[]
  reasons: string[]
  metrics: {
    securityTotalReturn: OutcomeMetric
    benchmarkTotalReturn: OutcomeMetric
    benchmarkRelativeLog: OutcomeMetric
    compoundedRelative: OutcomeMetric
    directionAlignedLog: OutcomeMetric
  }
  securitySnapshots: { id: string; revision: string; source: string }[]
  benchmarkSnapshots: { id: string; revision: string; source: string }[]
}

export interface AnalysisRun {
  id: string
  methodVersion: string
  calculatedAt: number
  asOf: number
  eventViewId: string
  marketInputId: string
  readinessScope: string
  productionReady: boolean
  outcomes: EventOutcome[]
  result: ResultStatus
}

export interface AnalysisResponse {
  capability: CapabilityState
  result: ResultStatus
  runs: AnalysisRun[]
}

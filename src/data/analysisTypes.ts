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

export interface CohortEstimate {
  value: number | null
  availability: 'available' | 'unavailable'
  interval: [number, number] | null
  intervalReasons: string[]
}

export interface CohortResult {
  cohort: string
  horizonSessions: number
  primary: boolean
  eventWeighted: CohortEstimate
  memberBalanced: CohortEstimate
  episode: CohortEstimate
  signDisagreement: boolean
  interpretation: string
  sample: {
    events: number
    outcomeAvailable: number
    retainedOutcomeAvailable: number
    readinessBlocked: number
    missing: number
    members: number
    securities: number
    sourceFilings: number
    anchorSessions: number
    episodes: number
    anchorMonths: number
    chambers: Record<string, number>
    coveredTimeRange: { start: string | null; end: string | null }
  }
  distribution: { median: number | null; q1: number | null; q3: number | null; iqr: number | null }
  missingness: { reasonCounts: Record<string, number>; reasonsNonExclusive: boolean; finalDenominator: number }
  provenance: Record<string, unknown>
}

export interface CohortRun {
  id: string
  sourceRunId: string
  methodVersion: string
  calculatedAt: number
  productionReady: boolean
  readinessScope: string
  result: ResultStatus
  report: {
    primaryEstimand: string
    results: CohortResult[]
    coverage: {
      chamberLabel: string
      exploratory: boolean
      periodStatus: string
      panelComplete: boolean
      observedTimeRange: { start: string | null; end: string | null }
    }
    flow: {
      counts: Record<string, number>
      reasonCounts: Record<string, number>
      windows: { horizonSessions: number; events: number; completedWindows: number; marketMissing: number; readinessBlocked: number; missing: number; finalDenominator: number }[]
    }
    consensus: { availability: 'unavailable'; reasons: string[] }
  }
}

export interface CohortResponse {
  capability: CapabilityState
  result: ResultStatus
  runs: CohortRun[]
}

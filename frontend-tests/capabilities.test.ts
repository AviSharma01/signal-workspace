import InvestigationResults from '../src/detail/InvestigationResults.js'
import { strict as assert } from 'node:assert'
import { test } from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

import CapabilityActionButton from '../src/capabilities/CapabilityActionButton.js'
import CapabilityNotice from '../src/capabilities/CapabilityNotice.js'
import CapabilityStateLabel from '../src/capabilities/CapabilityStateLabel.js'
import AnalysisResults from '../src/detail/AnalysisResults.js'
import CohortResults from '../src/detail/CohortResults.js'
import type { AnalysisResponse, CohortResponse } from '../src/data/analysisTypes.js'
import {
  capabilityActionDisabled,
  capabilityPresentation,
  relationshipPresentation,
} from '../src/capabilities/presentation.js'

test('Analysis shows blocked readiness and error without claiming empty success', () => {
  const response: AnalysisResponse = {
    capability: {
      id: 'market.data_readiness',
      name: 'Production market-data readiness',
      availability: 'unavailable',
      reasonCodes: ['provider_not_approved'],
      detail: 'No approved provider.',
      evaluatedAt: 1,
      governingVersion: 'contract@1',
      unmetPrerequisites: [{ code: 'approval', detail: 'Explicit approval required.' }],
    },
    result: { state: 'error', detail: 'Market readiness unavailable.', evaluatedAt: 1 },
    runs: [],
  }
  const markup = renderToStaticMarkup(createElement(AnalysisResults, { response }))
  assert.match(markup, /Unavailable/)
  assert.match(markup, /Result: error/)
  assert.match(markup, /No approved provider/)
  assert.doesNotMatch(markup, /No retained Analysis runs/)
})

test('cohort Analysis shows blocked readiness without claiming empty success', () => {
  const response: CohortResponse = {
    capability: {
      id: 'market',
      name: 'Market readiness',
      availability: 'unavailable',
      reasonCodes: ['provider_not_approved'],
      detail: 'No approved provider.',
      evaluatedAt: 1,
      governingVersion: 'contract@1',
      unmetPrerequisites: [],
    },
    result: { state: 'error', detail: 'Unavailable.', evaluatedAt: 1 },
    runs: [],
  }
  const markup = renderToStaticMarkup(createElement(CohortResults, { response }))
  assert.match(markup, /Result: error/)
  assert.match(markup, /No approved provider/)
  assert.doesNotMatch(markup, /No retained cohort runs/)
})

test('cohort tables retain nulls, descriptive estimates, disagreement, dimensions and provenance', () => {
  const point = {
    value: 0,
    availability: 'available' as const,
    interval: null,
    intervalReasons: ['fewer_than_30_reporting_members'],
  }
  const unavailable = { ...point, value: null, availability: 'unavailable' as const }
  const result = {
    state: 'partial' as const,
    detail: 'Supported results remain valid.',
    evaluatedAt: 1,
  }
  const run = {
    id: 'cohort:production',
    sourceRunId: 'retained-32',
    methodVersion: 'cohort-analysis@1',
    calculatedAt: 1,
    productionReady: true,
    readinessScope: 'production',
    result,
    report: {
      primaryEstimand: '20_session_event_weighted_direction_aligned_log_mean',
      coverage: {
        chamberLabel: 'House-only readiness',
        exploratory: true,
        periodStatus: 'coverage_unvalidated',
        panelComplete: false,
        observedTimeRange: { start: '2025-01-06', end: '2025-07-03' },
      },
      consensus: {
        availability: 'unavailable' as const,
        reasons: ['historical_consensus_deferred'],
      },
      flow: {
        counts: { events: 3 },
        reasonCounts: {},
        windows: [
          {
            horizonSessions: 20,
            events: 3,
            completedWindows: 2,
            marketMissing: 1,
            readinessBlocked: 0,
            missing: 1,
            finalDenominator: 2,
          },
        ],
      },
      results: [
        {
          cohort: 'combined',
          horizonSessions: 20,
          primary: true,
          eventWeighted: point,
          memberBalanced: { ...point, value: -0.01 },
          episode: unavailable,
          signDisagreement: true,
          interpretation: 'Valid null/inconclusive result; descriptive small sample.',
          sample: {
            events: 3,
            outcomeAvailable: 2,
            retainedOutcomeAvailable: 2,
            readinessBlocked: 0,
            missing: 1,
            members: 2,
            securities: 1,
            sourceFilings: 3,
            anchorSessions: 2,
            episodes: 2,
            anchorMonths: 2,
            chambers: { house: 2 },
            coveredTimeRange: { start: '2025-01-06', end: '2025-07-03' },
          },
          distribution: { median: 0, q1: -0.01, q3: 0.01, iqr: 0.02 },
          missingness: {
            reasonCounts: { missing_bar: 1 },
            reasonsNonExclusive: true,
            finalDenominator: 2,
          },
          provenance: {
            snapshotIds: ['retained-snapshot'],
            asOf: 1,
            methodVersion: 'cohort-analysis@1',
          },
        },
      ],
    },
  }
  const response: CohortResponse = {
    capability: {
      id: 'market',
      name: 'Market readiness',
      availability: 'available',
      reasonCodes: [],
      detail: 'Ready.',
      evaluatedAt: 1,
      governingVersion: 'contract@1',
      unmetPrerequisites: [],
    },
    result,
    runs: [run, { ...run, id: 'cohort:synthetic', productionReady: false, readinessScope: 'toy' }],
  }
  const markup = renderToStaticMarkup(createElement(CohortResults, { response }))
  for (const expected of [
    /sole primary estimand/,
    /House-only readiness/,
    /Exploratory/,
    /Historical Consensus: Unavailable/,
    /Strict sign disagreement/,
    /null\/inconclusive/,
    /95%|Interval unavailable/,
    /2 members/,
    /1 securities/,
    /3 source filings/,
    /2 anchor sessions/,
    /2 episodes/,
    /2 months/,
    /retained-snapshot/,
    /missing_bar/,
    /retained-32/,
  ]) {
    assert.match(markup, expected)
  }
  assert.match(markup, /0\.0000000/)
  assert.doesNotMatch(markup, /cohort:synthetic/)
})

test('Analysis displays per-metric missingness and run provenance and withholds synthetic runs', () => {
  const unavailable = {
    value: null,
    availability: 'unavailable' as const,
    reasons: ['missing_bar:2025-07-07'],
  }
  const available = { value: 0, availability: 'available' as const, reasons: [] }
  const result = {
    state: 'partial' as const,
    detail: 'Dependent window unavailable.',
    evaluatedAt: 1,
  }
  const run = {
    id: 'production-run',
    methodVersion: 'event-outcomes@1',
    calculatedAt: 1,
    asOf: 1,
    eventViewId: 'retained-event-view',
    marketInputId: 'retained-market-revision',
    readinessScope: 'production',
    productionReady: true,
    result,
    outcomes: [
      {
        eventId: 'event:one',
        horizonSessions: 20,
        primaryHorizon: true,
        direction: 'purchase',
        eventBoundary: 1,
        outcomeBoundary: 2,
        sessionDates: ['2025-07-03'],
        reasons: unavailable.reasons,
        metrics: {
          securityTotalReturn: unavailable,
          benchmarkTotalReturn: available,
          benchmarkRelativeLog: unavailable,
          compoundedRelative: unavailable,
          directionAlignedLog: unavailable,
        },
        securitySnapshots: [],
        benchmarkSnapshots: [],
      },
    ],
  }
  const response: AnalysisResponse = {
    capability: {
      id: 'market.outcomes',
      name: 'Market outcomes',
      availability: 'available',
      reasonCodes: [],
      detail: 'Ready.',
      evaluatedAt: 1,
      governingVersion: 'contract@1',
      unmetPrerequisites: [],
    },
    result,
    runs: [run, { ...run, id: 'synthetic-run', productionReady: false, readinessScope: 'test' }],
  }
  const markup = renderToStaticMarkup(createElement(AnalysisResults, { response }))
  assert.match(markup, /20.*primary/)
  assert.match(markup, /Unavailable: missing_bar/)
  assert.match(markup, /retained-event-view/)
  assert.match(markup, /retained-market-revision/)
  assert.match(markup, /0\.0000%/)
  assert.doesNotMatch(markup, /synthetic-run/)
})

test('renders available, conditional, and unavailable capability states with blocking detail', () => {
  assert.deepEqual(
    capabilityPresentation({ availability: 'available', reasonCodes: [], detail: 'Ready.' }),
    { label: 'Available', blockingDetail: null, disabled: false }
  )
  assert.deepEqual(
    capabilityPresentation({
      availability: 'conditional',
      reasonCodes: ['chamber_readiness_incomplete'],
      detail: 'Evidence gates remain.',
    }),
    { label: 'Conditional', blockingDetail: 'Evidence gates remain.', disabled: true }
  )
  assert.deepEqual(
    capabilityPresentation({
      availability: 'unavailable',
      reasonCodes: ['market_data_contract_unsatisfied'],
      detail: 'No provider is approved.',
    }),
    { label: 'Unavailable', blockingDetail: 'No provider is approved.', disabled: true }
  )
})

test('keeps candidate, verified, and legacy graph relationships distinct', () => {
  assert.deepEqual(relationshipPresentation('candidate'), {
    label: 'Candidate relationship',
    verified: false,
  })
  assert.deepEqual(relationshipPresentation('verified'), {
    label: 'Verified relationship',
    verified: true,
  })
  assert.deepEqual(relationshipPresentation('legacy_context'), {
    label: 'Legacy V1 context',
    verified: false,
  })
})

test('disables unsupported and pending actions without treating conditional as available', () => {
  assert.equal(capabilityActionDisabled({ availability: 'available' }), false)
  assert.equal(capabilityActionDisabled({ availability: 'available' }, true), true)
  assert.equal(capabilityActionDisabled({ availability: 'conditional' }), true)
  assert.equal(capabilityActionDisabled({ availability: 'unavailable' }), true)
  assert.equal(capabilityActionDisabled(null), true)
})

test('renders actual capability labels and disables the actual unsupported action control', () => {
  const conditional = {
    availability: 'conditional' as const,
    reasonCodes: ['gate_incomplete'],
    detail: 'A prerequisite is incomplete.',
  }
  const label = renderToStaticMarkup(
    createElement(CapabilityStateLabel, { capability: conditional })
  )
  assert.match(label, /data-availability="conditional"/)
  assert.match(label, /aria-disabled="true"/)
  assert.match(label, />Conditional</)

  const button = renderToStaticMarkup(
    createElement(CapabilityActionButton, { capability: conditional }, 'Scan now')
  )
  assert.match(button, /disabled=""/)
  assert.match(button, /title="A prerequisite is incomplete."/)
  assert.match(button, />Scan now</)
})

test('renders capability availability and result state as separate UI facts', () => {
  const notice = renderToStaticMarkup(
    createElement(CapabilityNotice, {
      capability: {
        id: 'fixture.capability',
        name: 'Fixture capability',
        availability: 'conditional',
        reasonCodes: ['gate_incomplete'],
        detail: 'A prerequisite is incomplete.',
        evaluatedAt: 1,
        governingVersion: 'fixture@1',
        unmetPrerequisites: [{ code: 'gate', detail: 'Complete the gate.' }],
      },
      result: {
        state: 'partial',
        detail: 'Some records loaded.',
        evaluatedAt: 2,
      },
    })
  )

  assert.match(notice, />Conditional</)
  assert.match(notice, /Result: partial/)
  assert.match(notice, /Some records loaded/)
  assert.match(notice, /gate_incomplete/)
  assert.match(notice, /Complete the gate/)
})

test('investigation navigation exposes frozen provenance, incomplete outcomes and validated citations', () => {
  const capability = {
    id: 'investigation.runtime',
    name: 'Investigation',
    availability: 'available' as const,
    reasonCodes: [],
    detail: 'Deterministic runtime.',
    evaluatedAt: 1000,
    governingVersion: 'bounded-investigation@1',
    unmetPrerequisites: [],
  }
  const boundary = { perspective: 'system_observation' as const, asOf: 1000 }
  const trigger = {
    kind: 'event' as const,
    id: 'event:one',
    eventId: 'event:one',
    activeOnly: false,
    version: 'trigger-version',
    eventMethodVersion: 'event-pit@1',
  }
  const reference = {
    kind: 'reported_row',
    observedAt: 900,
    publicAvailableBy: 800,
    derivedAt: 900,
    methodVersion: 'house-ptr@1',
    eligibility: { ...boundary, eligible: true, availableBy: 900, reasons: [] },
    citations: [
      {
        artifactVersionId: 'artifact-version',
        artifactId: 'artifact',
        locator: 'row:0',
        sourceAuthority: 'official',
        sourceUrl: 'https://fixture.example/artifact',
        contentSha256: 'retained-sha',
        observedAt: 900,
        publicAvailableBy: 800,
        publicTimeBasis: 'supported_publication_evidence',
        publicationEvidenceIds: ['publication-proof'],
        observationIds: ['retrieval-observation'],
      },
    ],
  }
  const unavailable = {
    ...capability,
    id: 'investigation.selection_evaluation',
    name: 'Selection evaluation',
    availability: 'unavailable' as const,
    reasonCodes: ['independent_evaluation_target_unavailable'],
    detail: 'No independent target and baseline.',
  }
  const finding = {
    runId: 'run-one',
    trigger,
    boundary,
    outcome: 'budget_exhausted' as const,
    summary: 'Investigation incomplete.',
    hypothesesConsidered: [],
    claims: [
      {
        text: 'Eligible disclosure row retained.',
        citations: [{ evidenceId: 'row:one', reference }],
      },
    ],
    counterevidence: [],
    unresolvedQuestions: ['What explains this Event?'],
    confidence: 'low' as const,
    confidenceBasis: 'Confidence is not evidence.',
    limitations: ['Explanation unresolved.'],
    missingness: ['step_budget_exhausted'],
    capabilityLimitations: [unavailable],
    methodVersion: 'bounded-investigation@1',
    modelVersion: null,
    reviewStatus: 'needs_human_review' as const,
    noAdviceStatus: 'validated' as const,
    advice: null,
    createdAt: 1000,
  }
  const run = {
    id: 'run-one',
    population: 'real' as const,
    createdAt: 1000,
    status: 'incomplete' as const,
    manifest: {
      trigger,
      boundary,
      evidence: [{ id: 'row:one', content: {}, ...reference }],
      capabilitySnapshot: {
        contractVersion: 'signal-capabilities@1',
        capabilities: [capability, unavailable],
        evaluatedAt: 1000,
      },
      budgets: { steps: 3, elapsedMs: 10000, modelSpendUsd: null },
      mode: 'deterministic' as const,
      methodVersion: 'bounded-investigation@1',
      validatorVersion: 'finding-validation@1',
      digest: 'manifest-sha',
    },
    execution: {
      outcome: finding.outcome,
      reasons: finding.missingness,
      inspectedEvidenceIds: ['row:one'],
      usage: { steps: 3, elapsedMs: 10, modelSpendUsd: 0 },
      finishedAt: 1000,
    },
    finding,
  }
  const markup = renderToStaticMarkup(
    createElement(InvestigationResults, {
      response: {
        capability,
        result: { state: 'partial', detail: 'Investigation incomplete.', evaluatedAt: 1000 },
        runs: [run, { ...run, id: 'test-run', population: 'test' }],
      },
    })
  )
  for (const pattern of [
    /Available/,
    /Result: partial/,
    /budget exhausted/,
    /needs human review/,
    /trigger-version/,
    /manifest-sha/,
    /row:one/,
    /artifact-version/,
    /retained-sha/,
    /row:0/,
    /Confidence is not evidence/,
    /No-advice:.*validated/,
    /independent_evaluation_target_unavailable/,
    /step_budget_exhausted/,
    /Model:.*none/,
    /system observation/,
    /Declared budgets/,
  ])
    assert.match(markup, pattern)
  assert.doesNotMatch(markup, /test-run/)
  assert.doesNotMatch(markup, /Scan now/)
})

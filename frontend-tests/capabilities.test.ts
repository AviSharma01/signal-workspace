import { strict as assert } from 'node:assert'
import { test } from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

import CapabilityActionButton from '../src/capabilities/CapabilityActionButton.js'
import CapabilityNotice from '../src/capabilities/CapabilityNotice.js'
import CapabilityStateLabel from '../src/capabilities/CapabilityStateLabel.js'
import AnalysisResults from '../src/detail/AnalysisResults.js'
import type { AnalysisResponse } from '../src/data/analysisTypes.js'
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

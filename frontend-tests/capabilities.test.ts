import { strict as assert } from 'node:assert'
import { test } from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

import CapabilityActionButton from '../src/capabilities/CapabilityActionButton.js'
import CapabilityNotice from '../src/capabilities/CapabilityNotice.js'
import CapabilityStateLabel from '../src/capabilities/CapabilityStateLabel.js'
import {
  capabilityActionDisabled,
  capabilityPresentation,
  relationshipPresentation,
} from '../src/capabilities/presentation.js'

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

import type { CapabilityState } from './types'

type CapabilityPresentationInput = Pick<CapabilityState, 'availability' | 'reasonCodes' | 'detail'>

export function capabilityPresentation(capability: CapabilityPresentationInput): {
  label: string
  blockingDetail: string | null
  disabled: boolean
} {
  if (capability.availability === 'available') {
    return { label: 'Available', blockingDetail: null, disabled: false }
  }
  if (capability.availability === 'conditional') {
    return { label: 'Conditional', blockingDetail: capability.detail, disabled: true }
  }
  return { label: 'Unavailable', blockingDetail: capability.detail, disabled: true }
}

export function relationshipPresentation(standing: 'candidate' | 'verified' | 'legacy_context'): {
  label: string
  verified: boolean
} {
  if (standing === 'verified') return { label: 'Verified relationship', verified: true }
  if (standing === 'candidate') return { label: 'Candidate relationship', verified: false }
  return { label: 'Legacy V1 context', verified: false }
}

export function capabilityActionDisabled(
  capability: Pick<CapabilityState, 'availability'> | null,
  pending = false
): boolean {
  return pending || !capability || capability.availability !== 'available'
}

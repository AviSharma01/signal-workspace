import { createElement } from 'react'
import type { CapabilityState } from './types'
import { capabilityPresentation } from './presentation.js'

interface CapabilityStateLabelProps {
  capability: Pick<CapabilityState, 'availability' | 'reasonCodes' | 'detail'>
}

export default function CapabilityStateLabel({ capability }: CapabilityStateLabelProps) {
  const presentation = capabilityPresentation(capability)
  return createElement(
    'span',
    {
      'data-availability': capability.availability,
      'aria-disabled': presentation.disabled ? 'true' : undefined,
    },
    presentation.label
  )
}

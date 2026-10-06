import { createElement, type ComponentPropsWithoutRef } from 'react'
import type { CapabilityState } from './types'
import { capabilityActionDisabled } from './presentation.js'

interface CapabilityActionButtonProps extends Omit<ComponentPropsWithoutRef<'button'>, 'disabled'> {
  capability: Pick<CapabilityState, 'availability' | 'detail'> | null
  pending?: boolean
}

export default function CapabilityActionButton({
  capability,
  pending = false,
  title,
  ...props
}: CapabilityActionButtonProps) {
  return createElement('button', {
    ...props,
    disabled: capabilityActionDisabled(capability, pending),
    title: title ?? capability?.detail,
  })
}

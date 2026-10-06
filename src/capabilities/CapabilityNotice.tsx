import { capabilityPresentation } from './presentation.js'
import type { CapabilityState, ResultStatus } from './types'
import CapabilityStateLabel from './CapabilityStateLabel.js'

interface CapabilityNoticeProps {
  capability: CapabilityState
  result?: ResultStatus | null
  compact?: boolean
}

export default function CapabilityNotice({
  capability,
  result,
  compact = false,
}: CapabilityNoticeProps) {
  const presentation = capabilityPresentation(capability)
  const stateColor =
    capability.availability === 'available'
      ? '#6f9f7f'
      : capability.availability === 'conditional'
        ? '#c99745'
        : '#c96a62'

  return (
    <div
      className={
        compact ? 'text-[11px]' : 'rounded-md border border-[#2a2a2e] bg-[#17171a] p-3 text-xs'
      }
    >
      <div className="flex items-center gap-2">
        <span className="text-[#f0f0f0]">{capability.name}</span>
        <span style={{ color: stateColor }}>
          <CapabilityStateLabel capability={capability} />
        </span>
        {result && <span className="text-[#6b6b7b]">Result: {result.state}</span>}
      </div>
      {presentation.blockingDetail && (
        <div className="mt-1 text-[#8b8b98]">{presentation.blockingDetail}</div>
      )}
      {result && <div className="mt-1 text-[#8b8b98]">{result.detail}</div>}
      {capability.reasonCodes.length > 0 && (
        <div className="mt-1 font-mono text-[10px] text-[#6b6b7b]">
          {capability.reasonCodes.join(' · ')}
        </div>
      )}
      {!compact && capability.unmetPrerequisites.length > 0 && (
        <div className="mt-2 text-[#6b6b7b]">
          Unmet: {capability.unmetPrerequisites.map(item => item.detail).join('; ')}
        </div>
      )}
      {!compact && (
        <div className="mt-2 text-[10px] text-[#555560]">
          {capability.governingVersion} · evaluated{' '}
          {new Date(capability.evaluatedAt).toLocaleString()}
        </div>
      )}
    </div>
  )
}

import type { InvestigationResponse } from '../data/investigationTypes'
import CapabilityNotice from '../capabilities/CapabilityNotice.js'
import FindingCard from './FindingCard.js'

export default function InvestigationResults({ response }: { response: InvestigationResponse }) {
  return (
    <div className="space-y-3 text-xs text-[#8b8b98]">
      <CapabilityNotice capability={response.capability} result={response.result} />
      {response.result.state === 'empty' && <p>No retained investigation runs.</p>}
      {response.runs
        .filter(run => run.population === 'real')
        .map(run => (
          <details key={run.id} className="border-t border-[#2a2a2e] pt-3">
            <summary className="cursor-pointer">
              {run.manifest.trigger.id} · {run.status} ·{' '}
              {run.finding?.outcome.replaceAll('_', ' ') ?? 'not executed'}
            </summary>
            <div className="my-2 space-y-1">
              <div>
                Run: <code>{run.id}</code> · Created: {new Date(run.createdAt).toISOString()}
              </div>
              <div>
                As-Of: {run.manifest.boundary.perspective.replaceAll('_', ' ')} ·{' '}
                {new Date(run.manifest.boundary.asOf).toISOString()}
              </div>
              <div>
                Trigger version: <code className="break-all">{run.manifest.trigger.version}</code>
              </div>
              <div>
                Method: {run.manifest.methodVersion} · Validator: {run.manifest.validatorVersion}
              </div>
              <div>
                Manifest SHA-256: <code className="break-all">{run.manifest.digest}</code>
              </div>
              <div>
                Declared budgets: {run.manifest.budgets.steps} steps ·{' '}
                {run.manifest.budgets.elapsedMs} ms · model spend{' '}
                {run.manifest.budgets.modelSpendUsd === null
                  ? 'not applicable'
                  : `$${run.manifest.budgets.modelSpendUsd}`}
              </div>
              {run.execution && (
                <div>
                  Used: {run.execution.usage.steps} steps · {run.execution.usage.elapsedMs} ms · $
                  {run.execution.usage.modelSpendUsd} model spend ·{' '}
                  {run.execution.reasons.join(', ') || 'no exhaustion recorded'}
                </div>
              )}
              <details>
                <summary className="cursor-pointer">
                  Frozen eligible evidence ({run.manifest.evidence.length})
                </summary>
                {run.manifest.evidence.map(item => (
                  <div key={item.id}>
                    <code>{item.id}</code> · {item.kind} · eligible by{' '}
                    {new Date(item.eligibility.availableBy).toISOString()} · {item.methodVersion}
                  </div>
                ))}
              </details>
              <details>
                <summary className="cursor-pointer">
                  Capability snapshot at{' '}
                  {new Date(run.manifest.capabilitySnapshot.evaluatedAt).toISOString()}
                </summary>
                {run.manifest.capabilitySnapshot.capabilities.map(capability => (
                  <CapabilityNotice key={capability.id} capability={capability} compact />
                ))}
              </details>
            </div>
            {run.finding && <FindingCard finding={run.finding} />}
          </details>
        ))}
    </div>
  )
}

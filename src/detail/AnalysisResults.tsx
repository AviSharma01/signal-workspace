import CapabilityNotice from '../capabilities/CapabilityNotice.js'
import type { AnalysisResponse, OutcomeMetric } from '../data/analysisTypes'

function metricText(metric: OutcomeMetric, percent = false) {
  if (metric.availability !== 'available' || metric.value === null) {
    return `Unavailable: ${metric.reasons.join('; ')}`
  }
  return percent ? `${(metric.value * 100).toFixed(4)}%` : metric.value.toPrecision(8)
}

export default function AnalysisResults({ response }: { response: AnalysisResponse }) {
  return (
    <>
      <CapabilityNotice capability={response.capability} result={response.result} />
      {response.capability.availability === 'available' && response.runs.length === 0 && (
        <p>No retained Analysis runs.</p>
      )}
      {response.runs
        .filter(run => run.productionReady && run.readinessScope === 'production')
        .map(run => (
          <section
            key={run.id}
            className="mt-4 rounded-md border border-[#2a2a2e] bg-[#17171a] p-4 text-xs"
          >
            <h2 className="text-sm">Run {run.id}</h2>
            <p className="text-[#8b8b98]">
              {run.methodVersion} · {run.readinessScope} · As-Of {new Date(run.asOf).toISOString()}{' '}
              · calculated {new Date(run.calculatedAt).toISOString()}
            </p>
            <p className="break-all text-[#8b8b98]">
              Event view: {run.eventViewId} · Market inputs: {run.marketInputId} · Result:{' '}
              {run.result.state}
            </p>
            <p>
              Per-Event outcomes. 20 sessions is primary. No cohort estimate or statistical
              inference.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left">
                <thead>
                  <tr>
                    {[
                      'Event / direction',
                      'Sessions',
                      'Security total',
                      'SPY total',
                      'Relative log',
                      'Compounded relative',
                      'Aligned log',
                      'Outcome boundary',
                    ].map(label => (
                      <th key={label} className="border-b border-[#2a2a2e] p-2">
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {run.outcomes.map(outcome => (
                    <tr key={`${outcome.eventId}:${outcome.horizonSessions}`}>
                      <td className="p-2">
                        {outcome.eventId}
                        <br />
                        {outcome.direction}
                      </td>
                      <td className="p-2">
                        {outcome.horizonSessions}
                        {outcome.primaryHorizon ? ' (primary)' : ''}
                      </td>
                      <td className="p-2">
                        {metricText(outcome.metrics.securityTotalReturn, true)}
                      </td>
                      <td className="p-2">
                        {metricText(outcome.metrics.benchmarkTotalReturn, true)}
                      </td>
                      <td className="p-2">{metricText(outcome.metrics.benchmarkRelativeLog)}</td>
                      <td className="p-2">
                        {metricText(outcome.metrics.compoundedRelative, true)}
                      </td>
                      <td className="p-2">{metricText(outcome.metrics.directionAlignedLog)}</td>
                      <td className="p-2">
                        {outcome.outcomeBoundary === null
                          ? 'Unavailable'
                          : new Date(outcome.outcomeBoundary).toISOString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <details className="mt-3 text-[#8b8b98]">
              <summary>Input provenance, sessions and unavailability reasons</summary>
              <pre className="overflow-x-auto text-[10px]">{JSON.stringify(run, null, 2)}</pre>
            </details>
          </section>
        ))}
    </>
  )
}

import CapabilityNotice from '../capabilities/CapabilityNotice.js'
import type { CohortEstimate, CohortResponse } from '../data/analysisTypes'

function numberText(value: number | null) {
  return value === null ? 'Unavailable' : value.toPrecision(8)
}

function Estimate({ estimate }: { estimate: CohortEstimate }) {
  return (
    <>
      <span>{numberText(estimate.value)}</span>
      <br />
      <span className="text-[#8b8b98]">
        {estimate.interval
          ? `95% interval [${estimate.interval.map(numberText).join(', ')}]`
          : `Interval unavailable: ${estimate.intervalReasons.join('; ')}`}
      </span>
    </>
  )
}

export default function CohortResults({ response }: { response: CohortResponse }) {
  return (
    <>
      <h2 className="mt-6 text-sm">Cohort Analysis</h2>
      <CapabilityNotice capability={response.capability} result={response.result} />
      {response.capability.availability === 'available' && response.runs.length === 0 && (
        <p>No retained cohort runs.</p>
      )}
      {response.runs
        .filter(run => run.productionReady && run.readinessScope === 'production')
        .map(run => (
          <section
            key={run.id}
            className="mt-4 rounded-md border border-[#2a2a2e] bg-[#17171a] p-4 text-xs"
          >
            <h3 className="text-sm">Cohort run {run.id}</h3>
            <p className="break-all text-[#8b8b98]">
              {run.methodVersion} · source outcome run {run.sourceRunId} · calculated{' '}
              {new Date(run.calculatedAt).toISOString()} · Result: {run.result.state}
            </p>
            <p>
              20-session event-weighted direction-aligned log mean is the sole primary estimand.
            </p>
            <p>1/5/60 sessions, direction/chamber/year strata and distributions are supporting.</p>
            <p>
              Member-balanced and episode means are mandatory sensitivities. Supporting intervals
              are descriptive and unadjusted for multiple comparisons.
            </p>
            <p>
              {run.report.coverage.chamberLabel} ·{' '}
              {run.report.coverage.exploratory ? 'Exploratory' : 'Historical study'} · panel
              completeness: {String(run.report.coverage.panelComplete)}
            </p>
            <p className="text-[#8b8b98]">
              Observed anchors: {run.report.coverage.observedTimeRange.start ?? 'Unavailable'} to{' '}
              {run.report.coverage.observedTimeRange.end ?? 'Unavailable'} ·{' '}
              {run.report.coverage.periodStatus}
            </p>
            <p>
              Filing size is a sensitivity only: fewer than 15 / at least 15 distinct literal source
              ticker strings / indeterminate. No size exclusion or behavioral classification.
            </p>
            <p>Historical Consensus: Unavailable · {run.report.consensus.reasons.join('; ')}</p>
            <details className="mt-3">
              <summary>Flow and non-exclusive disclosure failure reasons</summary>
              <table className="w-full text-left">
                <tbody>
                  {Object.entries(run.report.flow.counts).map(([name, count]) => (
                    <tr key={name}>
                      <td className="p-1">{name}</td>
                      <td>{count}</td>
                    </tr>
                  ))}
                  {Object.entries(run.report.flow.reasonCounts).map(([name, count]) => (
                    <tr key={name}>
                      <td className="p-1">{name}</td>
                      <td>{count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {run.report.flow.windows.map(window => (
                <p key={window.horizonSessions}>
                  {window.horizonSessions} sessions: {window.events} Events;{' '}
                  {window.completedWindows} retained completed windows; {window.marketMissing}{' '}
                  market-missing; {window.readinessBlocked} blocked by chamber readiness;{' '}
                  {window.missing} unavailable for Analysis; final denominator{' '}
                  {window.finalDenominator}
                </p>
              ))}
            </details>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full border-collapse text-left">
                <thead>
                  <tr>
                    {[
                      'Cohort / sessions',
                      'Event-weighted',
                      'Member-balanced',
                      'Episode',
                      'Distribution',
                      'Sample / missingness',
                    ].map(label => (
                      <th key={label} className="border-b border-[#2a2a2e] p-2">
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {run.report.results.map(result => (
                    <tr
                      key={`${result.cohort}:${result.horizonSessions}`}
                      className="border-b border-[#2a2a2e] align-top"
                    >
                      <td className="p-2">
                        {result.cohort} · {result.horizonSessions} sessions{' '}
                        {result.primary ? '(primary)' : '(supporting)'}
                        <p className="text-[#8b8b98]">{result.interpretation}</p>
                        {result.signDisagreement && (
                          <p>Strict sign disagreement across supported estimates.</p>
                        )}
                      </td>
                      <td className="p-2">
                        <Estimate estimate={result.eventWeighted} />
                      </td>
                      <td className="p-2">
                        <Estimate estimate={result.memberBalanced} />
                      </td>
                      <td className="p-2">
                        <Estimate estimate={result.episode} />
                      </td>
                      <td className="p-2">
                        Median {numberText(result.distribution.median)}
                        <br />
                        Q1 {numberText(result.distribution.q1)}
                        <br />
                        Q3 {numberText(result.distribution.q3)}
                        <br />
                        IQR {numberText(result.distribution.iqr)}
                      </td>
                      <td className="min-w-56 p-2">
                        {result.sample.events} Events · {result.sample.outcomeAvailable} available ·{' '}
                        {result.sample.missing} missing
                        <br />
                        {result.sample.retainedOutcomeAvailable} retained completed outcomes ·{' '}
                        {result.sample.readinessBlocked} blocked by chamber readiness
                        <br />
                        {result.sample.members} members · {result.sample.securities} securities ·{' '}
                        {result.sample.sourceFilings} source filings
                        <br />
                        {result.sample.anchorSessions} anchor sessions · {result.sample.episodes}{' '}
                        episodes · {result.sample.anchorMonths} months
                        <br />
                        {result.sample.coveredTimeRange.start ?? 'Unavailable'} to{' '}
                        {result.sample.coveredTimeRange.end ?? 'Unavailable'}
                        <br />
                        Chambers: {JSON.stringify(result.sample.chambers)}
                        <details>
                          <summary>Coverage, reasons, seeds and provenance</summary>
                          <pre className="max-w-lg overflow-x-auto text-[10px]">
                            {JSON.stringify(result, null, 2)}
                          </pre>
                        </details>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <details className="mt-3 text-[#8b8b98]">
              <summary>Immutable manifest, filing counts and retained inputs</summary>
              <pre className="overflow-x-auto text-[10px]">{JSON.stringify(run, null, 2)}</pre>
            </details>
          </section>
        ))}
    </>
  )
}

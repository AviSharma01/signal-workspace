import { useWatchEvents } from '../data/useWatchEvents'
import type { WatchAssessment } from '../data/useWatchEvents'
import CapabilityNotice from '../capabilities/CapabilityNotice'

function instant(value: number): string {
  return new Date(value).toLocaleString('en-US', {
    timeZone: 'America/New_York',
    timeZoneName: 'short',
  })
}

function expiry(assessment: WatchAssessment): string {
  const support = assessment.expirySupport
  if (support.status === 'exact' && support.expiresAt !== undefined)
    return instant(support.expiresAt)
  if (
    support.status === 'interval' &&
    support.earliestExpiryAt !== undefined &&
    support.latestExpiryAt !== undefined
  ) {
    return `Supported range: ${instant(support.earliestExpiryAt)} – ${instant(support.latestExpiryAt)}`
  }
  return support.reason?.replaceAll('_', ' ') ?? 'Unsupported expiry'
}

export default function WatchEventsPanel() {
  const { response, loading, error } = useWatchEvents()
  return (
    <section className="mb-5 rounded-md border border-[#2a2a2e] bg-[#17171a] p-4">
      <h2 className="mb-1 mt-0 text-sm">Watch Events</h2>
      <p className="mb-3 mt-0 text-xs text-[#6b6b7b]">
        Admission and active eligibility under the 30-calendar-date America/New_York policy. Active
        eligibility does not establish available capabilities or successful checks.
      </p>
      {loading && <p className="text-xs text-[#6b6b7b]">Loading Watch Events…</p>}
      {error && <p className="text-xs text-[#e5534b]">{error} · Displayed data may be stale.</p>}
      {response && <CapabilityNotice capability={response.capability} result={response.result} />}
      {response?.state === 'empty' && (
        <p className="text-xs text-[#6b6b7b]">No Watch Events have been admitted.</p>
      )}
      {response?.watchEvents.map(detail => {
        const watch = detail.watchEvent
        const current = detail.currentEvaluation
        const publication = current.publicationSupport
        return (
          <details key={watch.id} className="mt-3 border-t border-[#2a2a2e] pt-3">
            <summary className="cursor-pointer text-xs">
              {detail.currentEvent.fields.ticker ?? watch.eventId} ·{' '}
              {detail.currentEvent.fields.transactionDirection ?? 'direction unresolved'} ·{' '}
              {current.activeEligibility.eligible
                ? 'Eligible at evaluation'
                : 'Active eligibility withheld'}{' '}
              · {current.recency.status.replaceAll('_', ' ')}
            </summary>
            <div className="mt-2 space-y-1 text-xs text-[#6b6b7b]">
              <CapabilityNotice capability={detail.capability} result={detail.result} compact />
              <div>
                Current evaluation: {instant(current.evaluatedAt)} · {current.policyVersion}
              </div>
              <div>
                Standing: {current.evidenceStanding.status} · Admission criteria:{' '}
                {current.admissionCriteria.satisfied
                  ? 'satisfied'
                  : current.admissionCriteria.reasons.join(', ')}
              </div>
              <div>Reasons: {current.lifecycleReasons.join(', ') || 'none'}</div>
              <div>
                Market check outcome: {detail.checkOutcomes.market.state} ·{' '}
                {detail.checkOutcomes.market.capability.availability} ·{' '}
                {detail.checkOutcomes.market.capability.reasonCodes.join(', ')}
              </div>
              <div>Transaction date: {current.transactionDate ?? 'unknown'}</div>
              <div>
                Publication:{' '}
                {publication.selectedEvidence?.rawValue ?? publication.assessment.status} ·{' '}
                {publication.selectedEvidence?.timezone ?? 'source offset or unsupported timezone'}
              </div>
              {publication.assessment.interval?.precision === 'date' && (
                <div>
                  Supported publication interval: {instant(publication.assessment.interval.start)}{' '}
                  to {instant(publication.assessment.interval.endExclusive)} (end excluded)
                </div>
              )}
              <div>Expiry: {expiry(current)}</div>
              <div>
                Discovery: {instant(watch.discoveredAt)} · Official evidence observed:{' '}
                {instant(watch.officialEvidenceFirstObservedAt)}
              </div>
              <div>
                Verified: {instant(watch.verifiedAt)} · Admitted: {instant(watch.admittedAt)}
              </div>
              <div>
                Last persisted assessment: {instant(detail.lastPersistedAssessment.evaluatedAt)} ·{' '}
                {detail.lastPersistedAssessment.activeEligibility.eligible
                  ? 'active eligible'
                  : 'active withheld'}
                {detail.lastPersistedAssessmentIsStale && ' · earlier stored assessment'}
                {detail.currentDiffersFromLastPersisted && ' · differs from current evaluation'}
              </div>
              <div className="pt-2 text-[#f0f0f0]">Recorded lifecycle history</div>
              {detail.lifecycleHistory.map(item => (
                <div key={item.id}>
                  {instant(item.evaluatedAt)} · {item.trigger.replaceAll('_', ' ')} ·{' '}
                  {item.transitionReasons.join(', ')} · {item.assessment.evidenceStanding.status} /{' '}
                  {item.assessment.recency.status.replaceAll('_', ' ')} · persisted{' '}
                  {instant(item.persistedAt)}
                </div>
              ))}
              <div className="pt-2 text-[#f0f0f0]">Evidence</div>
              {detail.currentEvent.provenance.rows.map(row => (
                <div key={row.occurrenceId}>
                  {row.sourceAuthority} · <a href={row.sourceUrl}>Source artifact</a> ·{' '}
                  {row.artifactVersionId}
                </div>
              ))}
            </div>
          </details>
        )
      })}
    </section>
  )
}

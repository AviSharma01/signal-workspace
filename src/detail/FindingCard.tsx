import type { Finding } from '../data/investigationTypes'

export default function FindingCard({ finding }: { finding: Finding }) {
  if (finding.noAdviceStatus !== 'validated') return null
  return (
    <article className="space-y-2 rounded-md border border-[#2a2a2e] p-3 text-xs text-[#8b8b98]">
      <div className="text-[#f0f0f0]">
        {finding.outcome.replaceAll('_', ' ')} · {finding.reviewStatus.replaceAll('_', ' ')}
      </div>
      <p>{finding.summary}</p>
      <div>
        Run: <code>{finding.runId}</code> · Trigger: <code>{finding.trigger.id}</code>
      </div>
      <div>
        Trigger version: <code className="break-all">{finding.trigger.version}</code>
      </div>
      <div>
        As-Of: {finding.boundary.perspective.replaceAll('_', ' ')} ·{' '}
        {new Date(finding.boundary.asOf).toISOString()}
      </div>
      <div>
        {finding.confidence} confidence · {finding.confidenceBasis}
      </div>
      {(['claims', 'counterevidence'] as const).map(group => (
        <div key={group}>
          <div className="text-[#f0f0f0]">
            {group === 'claims' ? 'Supported claims' : 'Counterevidence'}
          </div>
          {finding[group].length === 0 && <div>None established.</div>}
          {finding[group].map((claim, index) => (
            <div key={index} className="mt-1">
              <div>{claim.text}</div>
              {claim.citations.map(citation => (
                <div key={citation.evidenceId} className="ml-2 break-words">
                  <code>{citation.evidenceId}</code> · eligible by{' '}
                  {new Date(citation.reference.eligibility.availableBy).toISOString()}
                  <div>
                    Observed: {new Date(citation.reference.observedAt).toISOString()} · Public
                    availability by:{' '}
                    {citation.reference.publicAvailableBy === null
                      ? 'unsupported'
                      : new Date(citation.reference.publicAvailableBy).toISOString()}
                  </div>
                  {citation.reference.citations.map(source => (
                    <div key={`${source.artifactVersionId}:${source.locator}`}>
                      {source.sourceAuthority} · <a href={source.sourceUrl}>Source artifact</a> ·{' '}
                      <code>{source.artifactVersionId}</code> · {source.locator}
                      <div>
                        SHA-256: <code className="break-all">{source.contentSha256}</code> ·{' '}
                        {source.publicTimeBasis.replaceAll('_', ' ')}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ))}
        </div>
      ))}
      <div>
        Hypotheses considered: {finding.hypothesesConsidered.join('; ') || 'None supported.'}
      </div>
      <div>Unresolved questions: {finding.unresolvedQuestions.join('; ')}</div>
      <div>Limitations: {finding.limitations.join(' ')}</div>
      <div>
        Missingness: {finding.missingness.join(', ') || 'No additional missingness recorded.'}
      </div>
      <details>
        <summary className="cursor-pointer">Retained capability limitations</summary>
        {finding.capabilityLimitations.map(capability => (
          <div key={capability.id}>
            {capability.name}: {capability.availability} · {capability.reasonCodes.join(', ')} ·{' '}
            {capability.detail}
          </div>
        ))}
      </details>
      <div>
        Method: {finding.methodVersion} · Model: {finding.modelVersion ?? 'none'} · No-advice:{' '}
        {finding.noAdviceStatus}
      </div>
      <div>Created: {new Date(finding.createdAt).toISOString()}</div>
    </article>
  )
}

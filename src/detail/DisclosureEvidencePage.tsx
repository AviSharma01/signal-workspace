import { useNavigate } from 'react-router-dom'
import { useDisclosureEvidence } from '../data/useDisclosureEvidence'
import CapabilityNotice from '../capabilities/CapabilityNotice'
import { useCapabilities } from '../data/useCapabilities'
import WatchEventsPanel from './WatchEventsPanel'

const sectionClass = 'mt-3.5 rounded-md border border-[#2a2a2e] bg-[#17171a] p-4'
const labelClass = 'text-[11px] uppercase tracking-[0.06em] text-[#6b6b7b]'

export default function DisclosureEvidencePage() {
  const navigate = useNavigate()
  const { evidence, readiness, loading, error } = useDisclosureEvidence()
  const { response: capabilityResponse, error: capabilityError } = useCapabilities()
  const surfacedCapabilities = capabilityResponse?.capabilities.filter(capability =>
    [
      'monitoring.disclosure_discovery',
      'monitoring.market_checks',
      'analysis.market_event_study',
      'analysis.consensus.raw',
      'analysis.consensus.expected',
      'analysis.consensus.excess',
      'investigation.runtime',
      'investigation.selection_evaluation',
    ].includes(capability.id)
  )

  return (
    <main className="h-screen w-full overflow-y-auto bg-[#0e0e10] p-6 text-[#f0f0f0]">
      <div className="mx-auto max-w-6xl">
        <button
          onClick={() => navigate(-1)}
          className="cursor-pointer border-0 bg-transparent p-0 text-[#6b6b7b]"
        >
          ← Back
        </button>
        <h1 className="mb-1.5 mt-4.5 text-xl">Disclosure evidence</h1>
        <p className="mb-5 mt-0 text-[13px] text-[#6b6b7b]">
          Retained source material, retrieval history, extraction status, and normalized
          interpretations.
        </p>

        {loading && <p className="text-[#6b6b7b]">Loading retained evidence…</p>}
        {error && <p className="text-[#e5534b]">{error}</p>}
        {capabilityError && <p className="text-[#e5534b]">{capabilityError}</p>}

        {surfacedCapabilities && (
          <section className={`${sectionClass} mb-5`}>
            <h2 className="mb-3 mt-0 text-sm">V2 capability status</h2>
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              {surfacedCapabilities.map(capability => (
                <CapabilityNotice key={capability.id} capability={capability} />
              ))}
            </div>
          </section>
        )}

        <WatchEventsPanel />

        {readiness && (
          <section className="grid grid-cols-2 gap-3">
            {[readiness.house, readiness.senate].map(chamber => (
              <CapabilityNotice key={chamber.chamber} capability={chamber} />
            ))}
          </section>
        )}

        {evidence && (
          <div className="mt-3">
            <CapabilityNotice capability={evidence.capability} result={evidence.result} />
          </div>
        )}

        {evidence && evidence.artifacts.length === 0 && (
          <p className="mt-6 text-[#6b6b7b]">No real disclosure evidence has been retained.</p>
        )}

        {evidence?.artifacts.map(artifact => (
          <section key={artifact.id} className={sectionClass}>
            <div className="flex justify-between gap-4">
              <div>
                <div className={labelClass}>
                  {artifact.sourceAuthority} · {artifact.artifactKind}
                </div>
                <div className="mt-1 text-sm">{artifact.sourceName}</div>
              </div>
              <a href={artifact.sourceUrl} className="text-xs text-[#6b6b7b]">
                Source
              </a>
            </div>

            <div className="mt-3.5">
              <div className={labelClass}>Retrieval observations</div>
              {artifact.retrievalObservations.map(observation => (
                <div key={observation.id} className="mt-1 text-xs text-[#6b6b7b]">
                  {new Date(observation.observedAt).toLocaleString()} · {observation.purpose} ·
                  availability {observation.availabilityStatus} · freshness{' '}
                  {observation.freshnessStatus} · coverage {observation.coverageStatus}
                </div>
              ))}
            </div>

            {artifact.versions.map(version => (
              <div key={version.id} className="mt-3.5 border-t border-[#2a2a2e] pt-3">
                <div className="text-xs">
                  Version <code>{version.contentSha256.slice(0, 12)}</code> ·{' '}
                  {version.contentLength.toLocaleString()} bytes
                </div>
                <div className="mt-1 text-xs text-[#6b6b7b]">
                  Extraction{' '}
                  {version.extractions
                    .map(item => `${item.method}@${item.methodVersion}: ${item.status}`)
                    .join(', ') || 'not attempted'}
                </div>
                {version.rowOccurrences.map(row => (
                  <details key={row.id} className="mt-2.5">
                    <summary className="cursor-pointer text-xs">
                      Reported row occurrence {row.ordinal + 1} · {row.parseStatus}
                    </summary>
                    <pre className="whitespace-pre-wrap break-words text-[11px] text-[#6b6b7b]">
                      {JSON.stringify(row.rawFields, null, 2)}
                    </pre>
                    {row.normalizations.map(normalization => (
                      <pre
                        key={normalization.id}
                        className="whitespace-pre-wrap text-[11px] text-[#6b6b7b]"
                      >
                        {normalization.method}@{normalization.methodVersion} ({normalization.status}
                        ){`\n`}
                        {JSON.stringify(normalization.normalizedFields, null, 2)}
                      </pre>
                    ))}
                  </details>
                ))}
              </div>
            ))}
          </section>
        ))}
      </div>
    </main>
  )
}

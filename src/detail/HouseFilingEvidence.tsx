import type { OfflineHouseSample } from '../data/houseFiling'

interface Props {
  sample: OfflineHouseSample | null
  pending: boolean
  error: string | null
  onInspect: () => void
  contentUrl: (artifactId: string, versionId: string) => string
}

export default function HouseFilingEvidence({
  sample,
  pending,
  error,
  onInspect,
  contentUrl,
}: Props) {
  return (
    <section className="mb-5 space-y-3 rounded-md border border-[#2a2a2e] bg-[#17171a] p-4 text-xs text-[#8b8b98]">
      <h2 className="m-0 text-sm text-[#f0f0f0]">One House filing · offline retained sample</h2>
      <p>
        House 2021 / 20018021 · test population. Live acquisition is blocked while access and
        retained-copy permissions remain unresolved. No House request is made by this action.
      </p>
      <p>
        This official-source sample is isolated from real V2 evidence, Events, Watches and Findings.
        Local observation time is neither original retrieval time nor publication time.
      </p>
      <button
        type="button"
        disabled={pending || !sample}
        onClick={onInspect}
        className="cursor-pointer rounded border border-[#2a2a2e] px-3 py-1.5 text-[#f0f0f0] disabled:cursor-not-allowed disabled:opacity-50"
      >
        {pending
          ? 'Loading sample…'
          : sample?.evidence.artifacts.length
            ? 'Read retained sample again'
            : 'Inspect retained sample'}
      </button>
      {error && (
        <p role="alert" className="text-[#e5534b]">
          {error}
        </p>
      )}
      {sample && <p>{sample.detail}</p>}
      {sample?.evidence.artifacts.map(artifact => (
        <div key={artifact.id} className="space-y-2 border-t border-[#2a2a2e] pt-3">
          <p>
            Source authority: {artifact.sourceAuthority} · {artifact.sourceName}
          </p>
          <p className="break-all">Original locator: {artifact.sourceUrl}</p>
          {artifact.versions.map(version => (
            <div key={version.id} className="space-y-2">
              <p className="break-all">
                Retained SHA-256: <code>{version.contentSha256}</code>
              </p>
              <p>
                {version.contentLength.toLocaleString()} bytes · {version.mediaType}
              </p>
              <a href={contentUrl(artifact.id, version.id)} className="underline">
                Download exact retained PDF
              </a>
              <p>Publication time: unknown · Original retrieval instant: unknown</p>
              <p>
                {version.extractions
                  .map(item => `${item.method}@${item.methodVersion}: ${item.status}`)
                  .join('; ')}
              </p>
              <p>
                {version.rowOccurrences.length} extracted row occurrence(s). Identity and Event
                eligibility remain unresolved.
              </p>
              {version.rowOccurrences.map(row => (
                <details key={row.id}>
                  <summary className="cursor-pointer">
                    Row {row.ordinal + 1} · {row.parseStatus}
                  </summary>
                  <p>Literal extracted fields and page/table/band position:</p>
                  <pre className="whitespace-pre-wrap break-words">
                    {JSON.stringify(row.rawFields, null, 2)}
                  </pre>
                  {row.normalizations.map(normalization => (
                    <div key={normalization.id}>
                      <p>
                        {normalization.method}@{normalization.methodVersion} ·{' '}
                        {normalization.status}
                      </p>
                      <pre className="whitespace-pre-wrap break-words">
                        {JSON.stringify(normalization.normalizedFields, null, 2)}
                      </pre>
                      <p>
                        Normalization issues: {normalization.issues.join(', ') || 'none recorded'}
                      </p>
                    </div>
                  ))}
                </details>
              ))}
            </div>
          ))}
          <details>
            <summary className="cursor-pointer">
              Local sample observations ({artifact.retrievalObservations.length})
            </summary>
            {artifact.retrievalObservations.map(observation => (
              <div key={observation.id} className="my-2">
                <p>
                  Local sample read: {new Date(observation.observedAt).toISOString()} · HTTP status:
                  none (offline)
                </p>
                <p>
                  Local copy: {observation.availabilityStatus} · Live source availability: unknown ·
                  Freshness: {observation.freshnessStatus} · Coverage: {observation.coverageStatus}
                </p>
                <pre className="whitespace-pre-wrap break-words">
                  {JSON.stringify(observation.sourceMetadata, null, 2)}
                </pre>
              </div>
            ))}
          </details>
        </div>
      ))}
    </section>
  )
}

import { useEffect, useState } from 'react'
import {
  processOfflineHouseEntry,
  offlineCorpusContentUrl,
  readOfflineHouseCorpus,
} from '../data/houseFiling'
import type { OfflineHouseCorpus } from '../data/houseFiling'
import HouseFilingEvidence from './HouseFilingEvidence'

export default function HouseFilingIntake() {
  const [corpus, setCorpus] = useState<OfflineHouseCorpus | null>(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let disposed = false
    readOfflineHouseCorpus()
      .then(response => {
        if (!disposed) setCorpus(response)
      })
      .catch(() => {
        if (!disposed) setError('Unable to load the offline corpus. Reload to retry.')
      })
    return () => {
      disposed = true
    }
  }, [])

  async function process(key: string, action: 'observations' | 'resume') {
    if (pending) return
    setPending(true)
    setError(null)
    try {
      await processOfflineHouseEntry(key, action)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Offline processing failed.')
    } finally {
      // A failed request may have committed raw evidence or an extraction.
      // Refresh even on failure so the next action can resume that exact state.
      try {
        setCorpus(await readOfflineHouseCorpus())
      } catch {
        setError(previous => previous ?? 'Unable to refresh status. Reload to retry.')
      }
      setPending(false)
    }
  }

  return (
    <div>
      <h2 className="mb-2 text-sm text-[#f0f0f0]">Bounded House corpus · offline test evidence</h2>
      <p className="mb-3 text-xs text-[#8b8b98]">
        {corpus
          ? `${corpus.importedCount} imported of ${corpus.entries.length} declared samples.`
          : 'Loading corpus…'}{' '}
        Available entries are declarations; only explicit inspection imports evidence. No annual
        indexes are retained.
      </p>
      {error && (
        <p role="alert" className="mb-3 text-xs text-[#e5534b]">
          {error}
        </p>
      )}
      {corpus?.entries.map(entry => (
        <HouseFilingEvidence
          key={entry.key}
          entry={entry}
          sample={{
            mode: 'offline_retained_sample',
            population: 'test',
            filing: {
              reportYear: entry.reportYear,
              documentId: entry.documentId,
              sourceUrl: entry.sourceUrl,
            },
            expectedSha256: entry.expectedSha256,
            liveAcquisitionPermitted: false,
            reasonCode: corpus.reasonCode,
            detail: corpus.detail,
            evidence: { population: 'test', artifacts: entry.artifact ? [entry.artifact] : [] },
          }}
          pending={pending}
          error={null}
          onInspect={() => {
            void process(entry.key, 'observations')
          }}
          onResume={() => {
            void process(entry.key, 'resume')
          }}
          contentUrl={offlineCorpusContentUrl}
        />
      ))}
    </div>
  )
}

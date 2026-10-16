import { apiFetch, apiPost, apiUrl } from './api'
import type { DisclosureArtifact } from './useDisclosureEvidence'

export interface OfflineHouseSample {
  mode: 'offline_retained_sample'
  population: 'test'
  filing: { reportYear: number; documentId: string; sourceUrl: string }
  expectedSha256: string
  liveAcquisitionPermitted: false
  reasonCode: string
  detail: string
  evidence: { population: 'test'; artifacts: DisclosureArtifact[] }
}

export interface OfflineHouseEntry {
  key: string
  reportYear: number
  documentId: string
  sourceUrl: string
  expectedSha256: string
  expectedBytes: number
  expectedPages: number
  characteristics: string
  locatorProvenance: string
  retentionScope: 'isolated_offline_test_only'
  localCopyStatus: string
  imported: boolean
  processingStatus: string
  extractionStatus: string
  artifact: DisclosureArtifact | null
  receipt: {
    manifestVersion: string
    expectedRowStarts: number | null
    extractedRowStarts: number | null
    independentCountMatches: boolean | null
    storedRows: number
    normalizedRows: number
    partialRows: number
    unresolvedFragmentCount: number
    completeness: string
    engine: string | null
    integrity: string
    reconciliationSha256: string
  }
}

export interface OfflineHouseCorpus {
  mode: 'offline_retained_corpus'
  population: 'test'
  manifestVersion: string
  liveAcquisitionPermitted: false
  reasonCode: string
  detail: string
  entries: OfflineHouseEntry[]
  importedCount: number
}

export function readOfflineHouseCorpus(): Promise<OfflineHouseCorpus> {
  return apiFetch('/api/disclosures/offline-corpus')
}

export async function processOfflineHouseEntry(key: string, action: 'observations' | 'resume') {
  // Preserve the bounded route's actionable reason/retryability; generic API
  // wrappers intentionally expose only an HTTP status on failure.
  const response = await fetch(apiUrl(`/api/disclosures/offline-corpus/${encodeURIComponent(key)}/${action}`), {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}',
  })
  if (!response.ok) {
    const body = await response.json() as { detail?: { message?: string; retryable?: boolean } }
    throw new Error(`${body.detail?.message ?? 'Offline processing failed.'}${body.detail?.retryable ? ' Retry is available.' : ''}`)
  }
}

export function offlineCorpusContentUrl(artifactId: string, versionId: string): string {
  return apiUrl(`/api/disclosures/offline-corpus/artifacts/${encodeURIComponent(artifactId)}/versions/${encodeURIComponent(versionId)}/content`)
}

export function readOfflineHouseSample(): Promise<OfflineHouseSample> {
  return apiFetch<OfflineHouseSample>('/api/disclosures/offline-sample')
}

export function inspectOfflineHouseSample() {
  return apiPost('/api/disclosures/offline-sample/observations', {})
}

export function offlineSampleContentUrl(artifactId: string, versionId: string): string {
  return apiUrl(
    `/api/disclosures/offline-sample/artifacts/${encodeURIComponent(artifactId)}/versions/${encodeURIComponent(versionId)}/content`,
  )
}

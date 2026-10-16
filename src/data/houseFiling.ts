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

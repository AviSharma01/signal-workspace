import type { ResultStatus } from '../capabilities/types'
import type { DiscussionItem, NewsItem } from '../shared/types'
import { apiFetch } from './api'

export interface SignalsResponse {
  classification: 'legacy_v1_context'
  v2Capability: false
  detail: string
  result: ResultStatus
  news: NewsItem[]
  discussion: DiscussionItem[]
}

export function fetchSignals(companyId: string): Promise<SignalsResponse> {
  return apiFetch<SignalsResponse>(`/api/signals/${companyId}`)
}

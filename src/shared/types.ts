export interface Company {
  id: string
  name: string
  sector: string
}

export interface PricePoint {
  companyId: string
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface NewsItem {
  id: string
  companyId: string
  headline: string
  summary: string
  source: string
  url: string
  publishedAt: number
}

export interface DiscussionItem {
  id: string
  companyId: string
  title: string
  summary: string
  source: string
  url: string
  publishedAt: number
}

export type SignalNode = NewsItem | DiscussionItem

export type NodeType = 'company' | 'news' | 'discussion' | 'relatedCompany'

export interface EvidenceEntry {
  type: string
  ref: string
  why: string
}

export interface FindingTrigger {
  z_score: number
  volume_ratio: number
  direction: string
  latest_return_pct: number
}

export interface Finding {
  id: string
  companyId: string
  createdAt: number
  trigger: FindingTrigger
  primaryDriver: string
  hypothesis: string
  evidence: EvidenceEntry[]
  confidence: string
  needsHumanReview: boolean
  iterations: number
  costUsd: number
}

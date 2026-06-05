import type { Node, Edge } from 'reactflow'
import type { NewsItem, DiscussionItem } from '../shared/types'

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export interface HubNodeData {}

export interface CompanyNodeData {
  label: string
  sector: string
}

export interface RelatedCompanyNodeData {
  label: string
  sector: string
  ticker: string    // the actual company id for navigation
  parentId: string  // which primary company this was expanded from
  animationDelay: number
}

export interface NewsNodeData {
  item: NewsItem
  animationDelay: number
  parentId: string
}

export interface DiscussionNodeData {
  item: DiscussionItem
  animationDelay: number
  parentId: string
}

export type HubFlowNode = Node<HubNodeData, 'hub'>
export type CompanyFlowNode = Node<CompanyNodeData, 'company'>
export type RelatedCompanyFlowNode = Node<RelatedCompanyNodeData, 'relatedCompany'>
export type NewsFlowNode = Node<NewsNodeData, 'news'>
export type DiscussionFlowNode = Node<DiscussionNodeData, 'discussion'>

export type AppNode = HubFlowNode | CompanyFlowNode | RelatedCompanyFlowNode | NewsFlowNode | DiscussionFlowNode
export type AppEdge = Edge<Record<string, never>>

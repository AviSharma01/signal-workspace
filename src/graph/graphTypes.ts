import type { Node, Edge } from 'reactflow'
import type { NewsItem, DiscussionItem } from '../shared/types'

export interface CompanyNodeData {
  label: string
  sector: string
  expanded: boolean
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

export type CompanyFlowNode = Node<CompanyNodeData, 'company'>
export type NewsFlowNode = Node<NewsNodeData, 'news'>
export type DiscussionFlowNode = Node<DiscussionNodeData, 'discussion'>

export type AppNode = CompanyFlowNode | NewsFlowNode | DiscussionFlowNode
export type AppEdge = Edge<Record<string, never>>

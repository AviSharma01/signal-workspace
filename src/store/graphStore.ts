import { create } from 'zustand'
import { SEED_COMPANIES, ANIMATION } from '../shared/constants'
import { apiFetch } from '../data/api'
import type { NewsItem, DiscussionItem } from '../shared/types'
import type { AppNode, AppEdge, CompanyFlowNode, NewsFlowNode, DiscussionFlowNode } from '../graph/graphTypes'

interface SignalsResponse {
  news: NewsItem[]
  discussion: DiscussionItem[]
}

interface GraphState {
  nodes: AppNode[]
  edges: AppEdge[]
  initGraph: () => void
  toggleExpand: (companyId: string) => void
}

function makeCompanyNode(company: (typeof SEED_COMPANIES)[number]): CompanyFlowNode {
  return {
    id: company.id,
    type: 'company',
    position: { x: 0, y: 0 },
    data: {
      label: company.name,
      sector: company.sector,
      expanded: false,
    },
  }
}

export const useGraphStore = create<GraphState>((set, get) => ({
  nodes: [],
  edges: [],

  initGraph() {
    if (get().nodes.length > 0) return
    set({ nodes: SEED_COMPANIES.map(makeCompanyNode), edges: [] })
  },

  toggleExpand(companyId) {
    const { nodes, edges } = get()

    const companyNode = nodes.find((n) => n.id === companyId)
    if (!companyNode || companyNode.type !== 'company') return

    const isExpanded = companyNode.data.expanded

    if (isExpanded) {
      // Collapse: remove all signal nodes and edges that belong to this company
      const nextNodes = nodes
        .filter((n) => n.type === 'company' || (n.data as { parentId: string }).parentId !== companyId)
        .map((n) => {
          if (n.id === companyId && n.type === 'company') {
            return { ...n, data: { ...n.data, expanded: false } }
          }
          return n
        })
      const nextEdges = edges.filter((e) => e.source !== companyId)
      set({ nodes: nextNodes, edges: nextEdges })
      return
    }

    // Expand: fetch signals from API then build nodes (fire-and-forget)
    void apiFetch<SignalsResponse>(`/api/signals/${companyId}`).then(
      ({ news: newsItems, discussion: discussionItems }) => {
        const { nodes: currentNodes, edges: currentEdges } = get()

        // Guard: node may have been removed while the request was in-flight
        const node = currentNodes.find((n) => n.id === companyId)
        if (!node || node.type !== 'company') return

        const newNewsNodes: NewsFlowNode[] = newsItems.map((item, i) => ({
          id: `${companyId}-news-${item.id}`,
          type: 'news',
          position: { x: 0, y: 0 },
          data: {
            item,
            animationDelay: i * ANIMATION.stagger,
            parentId: companyId,
          },
        }))

        const newDiscussionNodes: DiscussionFlowNode[] = discussionItems.map((item, i) => ({
          id: `${companyId}-discussion-${item.id}`,
          type: 'discussion',
          position: { x: 0, y: 0 },
          data: {
            item,
            animationDelay: (newsItems.length + i) * ANIMATION.stagger,
            parentId: companyId,
          },
        }))

        const newEdges: AppEdge[] = [
          ...newNewsNodes.map((n) => ({
            id: `edge-${companyId}-${n.id}`,
            source: companyId,
            target: n.id,
            data: {} as Record<string, never>,
          })),
          ...newDiscussionNodes.map((n) => ({
            id: `edge-${companyId}-${n.id}`,
            source: companyId,
            target: n.id,
            data: {} as Record<string, never>,
          })),
        ]

        const nextNodes: AppNode[] = [
          ...currentNodes.map((n) => {
            if (n.id === companyId && n.type === 'company') {
              return { ...n, data: { ...n.data, expanded: true } }
            }
            return n
          }),
          ...newNewsNodes,
          ...newDiscussionNodes,
        ]

        set({ nodes: nextNodes, edges: [...currentEdges, ...newEdges] })
      },
    )
  },
}))

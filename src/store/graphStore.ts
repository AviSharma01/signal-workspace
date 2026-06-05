import { create } from 'zustand'
import { ANIMATION } from '../shared/constants'
import { apiFetch } from '../data/api'
import type { Company, NewsItem, DiscussionItem } from '../shared/types'
import type { AppNode, AppEdge, CompanyFlowNode, NewsFlowNode, DiscussionFlowNode, RelatedCompanyFlowNode } from '../graph/graphTypes'

interface SignalsResponse {
  news: NewsItem[]
  discussion: DiscussionItem[]
}

interface GraphState {
  nodes: AppNode[]
  edges: AppEdge[]
  loading: boolean
  selectedCompanyId: string | null
  initGraph: () => void
  selectCompany: (companyId: string | null) => void
}

function makeCompanyNode(company: Company): CompanyFlowNode {
  return {
    id: company.id,
    type: 'company',
    position: { x: 0, y: 0 },
    data: {
      label: company.name,
      sector: company.sector,
    },
  }
}

export const useGraphStore = create<GraphState>((set, get) => ({
  nodes: [],
  edges: [],
  loading: false,
  selectedCompanyId: null,

  async initGraph() {
    // Already initialized — skip fetch, preserves full state across navigation
    if (get().nodes.length > 0) return

    set({ loading: true })

    const companies = await apiFetch<Company[]>('/api/companies').catch(() => [] as Company[])

    // Fetch all signals in parallel; individual failures return empty arrays
    const results = await Promise.all(
      companies.map((c) =>
        apiFetch<SignalsResponse>(`/api/signals/${c.id}`)
          .then((data) => ({ companyId: c.id, news: data.news, discussion: data.discussion }))
          .catch(() => ({ companyId: c.id, news: [] as NewsItem[], discussion: [] as DiscussionItem[] })),
      ),
    )

    const companyNodes: CompanyFlowNode[] = companies.map(makeCompanyNode)
    const signalNodes: AppNode[] = []
    const edges: AppEdge[] = []

    for (const { companyId, news: newsItems, discussion: discussionItems } of results) {
      const companyInfo = companies.find((c) => c.id === companyId)!

      const newNewsNodes: NewsFlowNode[] = newsItems.map((item, i) => ({
        id: `${companyId}-news-${item.id}`,
        type: 'news',
        position: { x: 0, y: 0 },
        data: { item, animationDelay: i * ANIMATION.stagger, parentId: companyId },
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

      const signalCount = newsItems.length + discussionItems.length
      const newRelatedNodes: RelatedCompanyFlowNode[] = companies
        .filter((c) => c.sector === companyInfo.sector && c.id !== companyId)
        .map((c, i) => ({
          id: `${companyId}-related-${c.id}`,
          type: 'relatedCompany' as const,
          position: { x: 0, y: 0 },
          data: {
            label: c.name,
            sector: c.sector,
            ticker: c.id,
            parentId: companyId,
            animationDelay: (signalCount + i) * ANIMATION.stagger,
          },
        }))

      const allSignalNodes = [...newNewsNodes, ...newDiscussionNodes, ...newRelatedNodes]
      signalNodes.push(...allSignalNodes)

      edges.push(
        ...allSignalNodes.map((n) => ({
          id: `edge-${companyId}-${n.id}`,
          source: companyId,
          target: n.id,
          data: {} as Record<string, never>,
        })),
      )
    }

    set({ nodes: [...companyNodes, ...signalNodes], edges, loading: false })
  },

  selectCompany(companyId) {
    set((s) => ({ selectedCompanyId: s.selectedCompanyId === companyId ? null : companyId }))
  },
}))

import { create } from 'zustand'
import { ANIMATION } from '../shared/constants'
import type { Company, NewsItem, DiscussionItem } from '../shared/types'
import type {
  AppNode,
  AppEdge,
  CompanyFlowNode,
  NewsFlowNode,
  DiscussionFlowNode,
  RelatedCompanyFlowNode,
} from '../graph/graphTypes'
import type { ResultStatus } from '../capabilities/types'
import { fetchCompanies } from '../data/companies'
import { fetchSignals } from '../data/signals'

interface GraphState {
  nodes: AppNode[]
  edges: AppEdge[]
  loading: boolean
  result: ResultStatus | null
  error: string | null
  selectedCompanyId: string | null
  savedPositions: Map<string, { x: number; y: number }>
  savedViewport: { x: number; y: number; zoom: number } | null
  initGraph: () => void
  selectCompany: (companyId: string | null) => void
  savePositions: (positions: ReadonlyMap<string, { x: number; y: number }>) => void
  saveViewport: (viewport: { x: number; y: number; zoom: number }) => void
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
  result: null,
  error: null,
  selectedCompanyId: null,
  savedPositions: new Map(),
  savedViewport: null,

  async initGraph() {
    // Already initialized — skip fetch, preserves full state across navigation
    if (get().nodes.length > 0) return

    set({ loading: true, error: null })

    let companies: Company[]
    try {
      companies = await fetchCompanies()
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Unable to load graph companies'
      set({
        loading: false,
        error: detail,
        result: { state: 'error', detail, evaluatedAt: Date.now() },
      })
      return
    }

    // Retain individual request failures separately from valid empty legacy context.
    const results = await Promise.all(
      companies.map(c =>
        fetchSignals(c.id)
          .then(data => ({
            companyId: c.id,
            news: data.news,
            discussion: data.discussion,
            result: data.result,
            requestError: null,
          }))
          .catch((error: unknown) => ({
            companyId: c.id,
            news: [] as NewsItem[],
            discussion: [] as DiscussionItem[],
            result: null,
            requestError: error instanceof Error ? error.message : 'Unable to load legacy context',
          }))
      )
    )

    const companyNodes: CompanyFlowNode[] = companies.map(makeCompanyNode)
    const signalNodes: AppNode[] = []
    const edges: AppEdge[] = []

    for (const { companyId, news: newsItems, discussion: discussionItems } of results) {
      const companyInfo = companies.find(c => c.id === companyId)!

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
        .filter(c => c.sector === companyInfo.sector && c.id !== companyId)
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
        ...allSignalNodes.map(n => ({
          id: `edge-${companyId}-${n.id}`,
          source: companyId,
          target: n.id,
          data: {
            relationshipType:
              n.type === 'news'
                ? ('news_context' as const)
                : n.type === 'discussion'
                  ? ('discussion_context' as const)
                  : ('sector_context' as const),
            standing: 'legacy_context' as const,
            evidenceBasis:
              n.type === 'relatedCompany'
                ? ('shared_seed_sector' as const)
                : ('legacy_v1_signal_feed' as const),
          },
        }))
      )
    }

    const failures = results.filter(item => item.requestError !== null)
    const resultState: ResultStatus['state'] =
      failures.length === results.length && results.length > 0
        ? 'error'
        : failures.length > 0
          ? 'partial'
          : signalNodes.length === 0
            ? 'empty'
            : 'successful'
    const detail =
      failures.length > 0
        ? `${failures.length} legacy context request${failures.length === 1 ? '' : 's'} failed.`
        : signalNodes.length === 0
          ? 'No legacy V1 context records were returned.'
          : 'Legacy V1 graph context loaded.'
    set({
      nodes: [...companyNodes, ...signalNodes],
      edges,
      loading: false,
      error:
        failures
          .map(item => item.requestError)
          .filter(Boolean)
          .join('; ') || null,
      result: { state: resultState, detail, evaluatedAt: Date.now() },
    })
  },

  selectCompany(companyId) {
    set(s => ({ selectedCompanyId: s.selectedCompanyId === companyId ? null : companyId }))
  },

  savePositions(positions) {
    set({ savedPositions: new Map(positions) })
  },

  saveViewport(viewport) {
    set({ savedViewport: viewport })
  },
}))

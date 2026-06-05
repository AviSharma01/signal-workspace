import { useEffect, useState, useMemo, useCallback, useRef } from 'react'
import ReactFlow, {
  ReactFlowProvider,
  useReactFlow,
  type NodeMouseHandler,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useGraphStore } from '../store/graphStore'
import { useForceLayout } from './useForceLayout'
import CompanyNode from './CompanyNode'
import NewsNode from './NewsNode'
import DiscussionNode from './DiscussionNode'
import HubNode from './HubNode'
import RelatedCompanyNode from './RelatedCompanyNode'
import GraphLegend from './GraphLegend'
import type { AppEdge } from './graphTypes'
import { BORDER, BG_PRIMARY, TEXT_MUTED } from '../shared/constants'
import './graph.css'

const nodeTypes = {
  company: CompanyNode,
  news: NewsNode,
  discussion: DiscussionNode,
  hub: HubNode,
  relatedCompany: RelatedCompanyNode,
}

const defaultEdgeOptions = {
  style: { stroke: BORDER, strokeWidth: 1.5 },
}

function GraphViewInner() {
  const rawNodes = useGraphStore((s) => s.nodes)
  const rawEdges = useGraphStore((s) => s.edges)
  const loading = useGraphStore((s) => s.loading)
  const initGraph = useGraphStore((s) => s.initGraph)

  const simulatedNodes = useForceLayout(rawNodes, rawEdges)

  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null)
  const { fitView } = useReactFlow()
  const initialFitDoneRef = useRef(false)

  useEffect(() => {
    void initGraph()
  }, [initGraph])

  // Fit view once after company nodes have positions — anchors viewport on
  // the company layer at a comfortable zoom, blobs settle around them.
  const companyNodes = useMemo(
    () => simulatedNodes.filter((n) => n.type === 'company').map((n) => ({ id: n.id })),
    [simulatedNodes],
  )
  useEffect(() => {
    if (companyNodes.length > 0 && !initialFitDoneRef.current) {
      initialFitDoneRef.current = true
      const timer = setTimeout(
        () => fitView({ nodes: companyNodes, duration: 700, padding: 0.5 }),
        120,
      )
      return () => clearTimeout(timer)
    }
  }, [companyNodes, fitView])

  const onNodeMouseEnter: NodeMouseHandler = useCallback((_, node) => {
    if (node.type !== 'company') setHoveredNodeId(node.id)
  }, [])

  const onNodeMouseLeave: NodeMouseHandler = useCallback(() => {
    setHoveredNodeId(null)
  }, [])

  const highlightedEdges = useMemo((): AppEdge[] => {
    if (!hoveredNodeId) return rawEdges
    return rawEdges.map((e) => ({
      ...e,
      className: e.target === hoveredNodeId ? 'highlighted' : '',
    }))
  }, [rawEdges, hoveredNodeId])

  return (
    <div className="graph-canvas">
      <GraphLegend />
      <ReactFlow
        nodes={simulatedNodes}
        edges={highlightedEdges}
        onNodeMouseEnter={onNodeMouseEnter}
        onNodeMouseLeave={onNodeMouseLeave}
        nodeTypes={nodeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        nodesDraggable={false}
        nodesConnectable={false}
        proOptions={{ hideAttribution: true }}
        selectionOnDrag={false}
        elevateEdgesOnSelect={false}
      />
      {loading && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: BG_PRIMARY,
            fontSize: 13,
            color: TEXT_MUTED,
            letterSpacing: '0.04em',
            zIndex: 20,
          }}
        >
          Loading signals…
        </div>
      )}
    </div>
  )
}

export default function GraphView() {
  return (
    <ReactFlowProvider>
      <GraphViewInner />
    </ReactFlowProvider>
  )
}

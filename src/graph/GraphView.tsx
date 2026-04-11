import { useEffect, useState, useMemo, useCallback, useRef } from 'react'
import ReactFlow, {
  ReactFlowProvider,
  applyNodeChanges,
  useReactFlow,
  type Node,
  type OnNodesChange,
  type NodeMouseHandler,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useGraphStore } from '../store/graphStore'
import { useGraphLayout } from './useGraphLayout'
import CompanyNode from './CompanyNode'
import NewsNode from './NewsNode'
import DiscussionNode from './DiscussionNode'
import type { AppEdge } from './graphTypes'
import { BORDER } from '../shared/constants'
import './graph.css'

// Defined outside component so React Flow never sees a new reference
const nodeTypes = {
  company: CompanyNode,
  news: NewsNode,
  discussion: DiscussionNode,
}

const defaultEdgeOptions = {
  style: { stroke: BORDER, strokeWidth: 1.5 },
}

function GraphViewInner() {
  const rawNodes = useGraphStore((s) => s.nodes)
  const rawEdges = useGraphStore((s) => s.edges)
  const initGraph = useGraphStore((s) => s.initGraph)

  const layoutedNodes = useGraphLayout(rawNodes, rawEdges)

  // Local display state — decoupled from store so drag moves don't trigger re-layout
  const [displayNodes, setDisplayNodes] = useState<Node[]>([])
  const [displayEdges, setDisplayEdges] = useState<AppEdge[]>([])
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null)

  const { fitView } = useReactFlow()
  const initialFitDoneRef = useRef(false)

  useEffect(() => {
    initGraph()
  }, [initGraph])

  // Push new layout into display state whenever the node structure changes.
  // This intentionally resets any drag positions on expand/collapse.
  useEffect(() => {
    setDisplayNodes(layoutedNodes)
  }, [layoutedNodes])

  useEffect(() => {
    setDisplayEdges(rawEdges)
  }, [rawEdges])

  // Fit view once after the first batch of nodes lands
  useEffect(() => {
    if (displayNodes.length > 0 && !initialFitDoneRef.current) {
      initialFitDoneRef.current = true
      const timer = setTimeout(() => fitView({ duration: 400, padding: 0.15 }), 50)
      return () => clearTimeout(timer)
    }
  }, [displayNodes.length, fitView])

  const onNodesChange: OnNodesChange = useCallback(
    (changes) => setDisplayNodes((nds) => applyNodeChanges(changes, nds)),
    [],
  )

  const onNodeMouseEnter: NodeMouseHandler = useCallback((_, node) => {
    if (node.type !== 'company') setHoveredNodeId(node.id)
  }, [])

  const onNodeMouseLeave: NodeMouseHandler = useCallback(() => {
    setHoveredNodeId(null)
  }, [])

  // Derive highlighted edges without touching store state
  const highlightedEdges = useMemo(() => {
    if (!hoveredNodeId) return displayEdges
    return displayEdges.map((e) => ({
      ...e,
      className: e.target === hoveredNodeId ? 'highlighted' : '',
    }))
  }, [displayEdges, hoveredNodeId])

  return (
    <div className="graph-canvas">
      <ReactFlow
        nodes={displayNodes}
        edges={highlightedEdges}
        onNodesChange={onNodesChange}
        onNodeMouseEnter={onNodeMouseEnter}
        onNodeMouseLeave={onNodeMouseLeave}
        nodeTypes={nodeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        proOptions={{ hideAttribution: true }}
        selectionOnDrag={false}
        elevateEdgesOnSelect={false}
      />
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

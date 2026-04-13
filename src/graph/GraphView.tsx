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
import type { AppEdge } from './graphTypes'
import { BORDER } from '../shared/constants'
import './graph.css'

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

  // Force simulation drives positions — updates on every tick via internal setTick
  const simulatedNodes = useForceLayout(rawNodes, rawEdges)

  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null)
  const { fitView } = useReactFlow()
  const initialFitDoneRef = useRef(false)

  useEffect(() => {
    initGraph()
  }, [initGraph])

  // Fit view once — very zoomed out so the whole graph breathes.
  // Obsidian-style: you see everything at a glance, zoom in to inspect.
  // After expansion the view stays put; new nodes animate into frame.
  useEffect(() => {
    if (simulatedNodes.length > 0 && !initialFitDoneRef.current) {
      initialFitDoneRef.current = true
      // Delay slightly so the first simulation tick has positioned nodes
      const timer = setTimeout(() => fitView({ duration: 700, padding: 0.45 }), 120)
      return () => clearTimeout(timer)
    }
  }, [simulatedNodes.length, fitView])

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
      <ReactFlow
        nodes={simulatedNodes}
        edges={highlightedEdges}
        onNodeMouseEnter={onNodeMouseEnter}
        onNodeMouseLeave={onNodeMouseLeave}
        nodeTypes={nodeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        // Layout is owned by the force simulation — disable drag so nodes
        // settle naturally rather than fighting user position overrides
        nodesDraggable={false}
        nodesConnectable={false}
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

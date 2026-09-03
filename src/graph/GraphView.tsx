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
  const { fitView, setViewport } = useReactFlow()
  const cameraReadyRef = useRef(false)

  useEffect(() => {
    void initGraph()
  }, [initGraph])

  // Reset cameraReadyRef on cleanup so Strict Mode's second run and any
  // real remount re-apply the saved viewport rather than skipping.
  useEffect(() => {
    return () => {
      console.log('[cam] unmount — savedViewport at cleanup:', useGraphStore.getState().savedViewport)
      cameraReadyRef.current = false
    }
  }, [])

  // Camera setup: gate on simulatedNodes so nodes have positions before applying.
  // Restored mount → setViewport immediately (no DOM measurement needed, unlike fitView).
  // Fresh load → fitView after 120ms (needs settled node bounds).
  useEffect(() => {
    if (simulatedNodes.length > 0 && !cameraReadyRef.current) {
      cameraReadyRef.current = true
      const saved = useGraphStore.getState().savedViewport
      console.log('[cam] camera effect fired — savedViewport:', saved)
      if (saved) {
        console.log('[cam] restore branch — calling setViewport with:', saved)
        setViewport(saved)
      } else {
        console.log('[cam] fitView branch — no savedViewport, calling fitView')
        const timer = setTimeout(() => fitView({ duration: 700, padding: 0.4 }), 120)
        return () => clearTimeout(timer)
      }
    }
  }, [simulatedNodes, fitView, setViewport])

  // Persist viewport on every pan/zoom end so savedViewport is always the
  // live camera. This replaces the unmount-cleanup save, which was unreliable:
  // the cleanup fired during Strict Mode's fake unmount before setViewport had
  // rendered, causing getViewport() to return the default {0,0,1}.
  const handleMoveEnd = useCallback(
    (_: MouseEvent | TouchEvent, vp: { x: number; y: number; zoom: number }) => {
      console.log('[cam] handleMoveEnd saving:', vp)
      useGraphStore.getState().saveViewport(vp)
    },
    [],
  )

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
        onMoveEnd={handleMoveEnd}
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

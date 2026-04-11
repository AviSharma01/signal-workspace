import { useMemo } from 'react'
import dagre from 'dagre'
import type { AppNode, AppEdge } from './graphTypes'

// Dimensions are exported so node components can match their visual size to the layout
export const NODE_DIMENSIONS = {
  company: { width: 160, height: 36 },
  news: { width: 210, height: 32 },
  discussion: { width: 210, height: 32 },
} as const satisfies Record<string, { width: number; height: number }>

const FALLBACK_DIMS = { width: 210, height: 32 }

export function useGraphLayout(nodes: AppNode[], edges: AppEdge[]): AppNode[] {
  return useMemo(() => {
    if (nodes.length === 0) return nodes

    const g = new dagre.graphlib.Graph()
    g.setDefaultEdgeLabel(() => ({}))
    g.setGraph({ rankdir: 'LR', nodesep: 60, ranksep: 120, marginx: 48, marginy: 48 })

    nodes.forEach((node) => {
      const dims = NODE_DIMENSIONS[node.type as keyof typeof NODE_DIMENSIONS] ?? FALLBACK_DIMS
      g.setNode(node.id, { width: dims.width, height: dims.height })
    })

    edges.forEach((edge) => {
      g.setEdge(edge.source, edge.target)
    })

    dagre.layout(g)

    // dagre positions by center; React Flow positions by top-left corner
    return nodes.map((node) => {
      const { x, y } = g.node(node.id)
      const dims = NODE_DIMENSIONS[node.type as keyof typeof NODE_DIMENSIONS] ?? FALLBACK_DIMS
      return {
        ...node,
        position: { x: x - dims.width / 2, y: y - dims.height / 2 },
      }
    })
  }, [nodes, edges])
}

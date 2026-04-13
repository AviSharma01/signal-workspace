import { useEffect, useRef, useState, useMemo } from 'react'
import {
  forceSimulation,
  forceManyBody,
  forceLink,
  forceCenter,
  forceCollide,
  type Simulation,
  type SimulationNodeDatum,
  type SimulationLinkDatum,
} from 'd3-force'
import type { AppNode, AppEdge } from './graphTypes'
import { NODE_DIMENSIONS } from '../shared/constants'

// Collision radius = half-width + padding so nodes don't visually overlap
const COLLISION_RADIUS: Record<string, number> = {
  company: NODE_DIMENSIONS.company.width / 2 + 20,
  news: NODE_DIMENSIONS.news.width / 2 + 25,
  discussion: NODE_DIMENSIONS.discussion.width / 2 + 25,
}
const FALLBACK_COLLISION = 130
const LINK_DISTANCE = 220

interface SimNode extends SimulationNodeDatum {
  id: string
  nodeType: string
}
type SimLink = SimulationLinkDatum<SimNode>

type PositionMap = ReadonlyMap<string, { x: number; y: number }>

export function useForceLayout(nodes: AppNode[], edges: AppEdge[]): AppNode[] {
  // All refs are only accessed inside effects and RAF callbacks — never during render
  const simRef = useRef<Simulation<SimNode, SimLink> | null>(null)
  const simNodesMapRef = useRef<Map<string, SimNode>>(new Map())
  const simNodesArrayRef = useRef<SimNode[]>([])
  const rafRef = useRef<number | null>(null)

  // Positions live in state: tick callbacks (RAF) write here, render reads here.
  // No ref is ever read during the render path.
  const [positions, setPositions] = useState<PositionMap>(new Map())

  // ── Create simulation once on mount ────────────────────────────────────────
  useEffect(() => {
    const sim = forceSimulation<SimNode>()
      .force('charge', forceManyBody<SimNode>().strength(-420))
      .force(
        'collision',
        forceCollide<SimNode>()
          .radius((n) => COLLISION_RADIUS[n.nodeType] ?? FALLBACK_COLLISION)
          .strength(0.85),
      )
      .force('center', forceCenter(0, 0).strength(0.04))
      .force(
        'link',
        forceLink<SimNode, SimLink>()
          .id((n) => n.id)
          .distance(LINK_DISTANCE)
          .strength(0.55),
      )
      // Slow alpha decay → ~4 s to settle. Nodes visibly drift into position.
      .alphaDecay(0.025)
      .on('tick', () => {
        // Throttle renders to display refresh rate
        if (rafRef.current !== null) return
        rafRef.current = requestAnimationFrame(() => {
          rafRef.current = null
          // Reading refs in a RAF callback is outside the render path — allowed
          const newPos = new Map<string, { x: number; y: number }>()
          for (const [id, sn] of simNodesMapRef.current) {
            if (sn.x !== undefined && sn.y !== undefined) {
              newPos.set(id, { x: sn.x, y: sn.y })
            }
          }
          setPositions(newPos)
        })
      })

    simRef.current = sim

    return () => {
      sim.stop()
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current)
      simRef.current = null
    }
  }, [])

  // ── Sync store nodes into simulation when structure changes ─────────────────
  // All ref access here is inside a useEffect — allowed
  useEffect(() => {
    const sim = simRef.current
    if (!sim) return

    const existingMap = simNodesMapRef.current
    const existingArray = simNodesArrayRef.current
    const storeIds = new Set(nodes.map((n) => n.id))

    // Remove nodes no longer in the store
    for (let i = existingArray.length - 1; i >= 0; i--) {
      if (!storeIds.has(existingArray[i].id)) {
        existingMap.delete(existingArray[i].id)
        existingArray.splice(i, 1)
      }
    }

    // Add nodes new to the store — signal nodes spawn at their parent's position
    for (const node of nodes) {
      if (!existingMap.has(node.id)) {
        let spawnX = (Math.random() - 0.5) * 80
        let spawnY = (Math.random() - 0.5) * 80

        const parentId = (node.data as { parentId?: string }).parentId
        if (parentId) {
          const parent = existingMap.get(parentId)
          if (parent?.x !== undefined && parent?.y !== undefined) {
            spawnX = parent.x + (Math.random() - 0.5) * 16
            spawnY = parent.y + (Math.random() - 0.5) * 16
          }
        }

        const simNode: SimNode = {
          id: node.id,
          nodeType: node.type ?? 'news',
          x: spawnX,
          y: spawnY,
          vx: 0,
          vy: 0,
        }
        existingMap.set(node.id, simNode)
        existingArray.push(simNode)
      }
    }

    const links = edges
      .filter((e) => existingMap.has(e.source) && existingMap.has(e.target))
      .map((e) => ({ source: e.source, target: e.target }))

    // Existing SimNode objects retain x/y/vx/vy — d3 only randomises nodes
    // where x or y is NaN/undefined, so settled nodes stay put
    sim.nodes(existingArray)
    ;(sim.force('link') as ReturnType<typeof forceLink<SimNode, SimLink>>).links(links)

    const isInitialLoad = existingArray.length <= 5
    sim.alpha(isInitialLoad ? 1.0 : 0.5).restart()
  }, [nodes, edges])

  // ── Apply positions to nodes — only state and props, no ref reads ───────────
  return useMemo(
    () =>
      nodes.map((node) => {
        const pos = positions.get(node.id)
        if (!pos) return node
        const dims = NODE_DIMENSIONS[node.type as keyof typeof NODE_DIMENSIONS] ?? NODE_DIMENSIONS.news
        const { width: w, height: h } = dims
        return {
          ...node,
          position: { x: pos.x - w / 2, y: pos.y - h / 2 },
        }
      }),
    [nodes, positions],
  )
}

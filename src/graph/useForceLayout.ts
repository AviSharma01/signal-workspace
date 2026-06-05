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

const COLLISION_RADIUS: Record<string, number> = {
  company: NODE_DIMENSIONS.company.width / 2 + 20,
  relatedCompany: NODE_DIMENSIONS.relatedCompany.width / 2 + 20,
  news: NODE_DIMENSIONS.news.width / 2 + 25,
  discussion: NODE_DIMENSIONS.discussion.width / 2 + 25,
}
const FALLBACK_COLLISION = 50
const LINK_DISTANCE = 220

// Company nodes are pinned once alpha drops below this threshold.
const SETTLE_THRESHOLD = 0.05

interface SimNode extends SimulationNodeDatum {
  id: string
  nodeType: string
}
type SimLink = SimulationLinkDatum<SimNode>

type PositionMap = ReadonlyMap<string, { x: number; y: number }>

export function useForceLayout(nodes: AppNode[], edges: AppEdge[]): AppNode[] {
  const simRef = useRef<Simulation<SimNode, SimLink> | null>(null)
  const simNodesMapRef = useRef<Map<string, SimNode>>(new Map())
  const simNodesArrayRef = useRef<SimNode[]>([])
  const rafRef = useRef<number | null>(null)

  // Latches true on first non-empty node sync — gates initial alpha(1.0)
  const hasInitializedRef = useRef(false)
  // Latches true once the initial layout settles — triggers company node pinning
  const settledRef = useRef(false)

  const [positions, setPositions] = useState<PositionMap>(new Map())
  // Mirror of positions used for change-threshold check — avoids re-renders when
  // alphaTarget keeps the sim ticking but nothing has moved visibly (>0.5px)
  const prevPositionsRef = useRef<Map<string, { x: number; y: number }>>(new Map())

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
      .alphaDecay(0.025)
      // Keep sim warm — enables smooth expansion without a high-alpha restart.
      // At 0.003 forces are sub-pixel; the threshold check below prevents
      // unnecessary React re-renders when nothing has visibly moved.
      .alphaTarget(0.003)
      .on('tick', () => {
        // Once the initial layout settles, pin every company node in place.
        if (!settledRef.current && sim.alpha() < SETTLE_THRESHOLD) {
          settledRef.current = true
          for (const sn of simNodesArrayRef.current) {
            if (sn.nodeType === 'company') {
              sn.fx = sn.x
              sn.fy = sn.y
            }
          }
        }

        // Throttle to display refresh rate, and skip the state update when
        // nothing has moved more than 0.5px (avoids render spam from alphaTarget)
        if (rafRef.current !== null) return
        rafRef.current = requestAnimationFrame(() => {
          rafRef.current = null
          const prev = prevPositionsRef.current
          const newPos = new Map<string, { x: number; y: number }>()
          let changed = false

          for (const [id, sn] of simNodesMapRef.current) {
            if (sn.x === undefined || sn.y === undefined) continue
            newPos.set(id, { x: sn.x, y: sn.y })
            if (!changed) {
              const p = prev.get(id)
              if (!p || Math.abs(p.x - sn.x) > 0.5 || Math.abs(p.y - sn.y) > 0.5) {
                changed = true
              }
            }
          }

          if (changed) {
            prevPositionsRef.current = newPos
            setPositions(newPos)
          }
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
    const newSimNodes: SimNode[] = []
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
        newSimNodes.push(simNode)
      }
    }

    const links = edges
      .filter((e) => existingMap.has(e.source) && existingMap.has(e.target))
      .map((e) => ({ source: e.source, target: e.target }))

    sim.nodes(existingArray)
    ;(sim.force('link') as ReturnType<typeof forceLink<SimNode, SimLink>>).links(links)

    if (existingArray.length === 0) return

    // Seed spawn positions into React state so new nodes are visible at their
    // parent's location before the first sim tick fires. Deferred via
    // queueMicrotask to satisfy the no-setState-in-effect lint rule while
    // still beating the RAF-based first tick (~16ms later).
    if (newSimNodes.length > 0) {
      const snapshot = newSimNodes.map((sn) => ({ id: sn.id, x: sn.x ?? 0, y: sn.y ?? 0 }))
      queueMicrotask(() => {
        setPositions((prev) => {
          const next = new Map(prev)
          for (const { id, x, y } of snapshot) next.set(id, { x, y })
          return next
        })
      })
    }

    if (!hasInitializedRef.current) {
      // First load — full energy, company nodes drift into their natural positions
      hasInitializedRef.current = true
      sim.alpha(1.0).restart()
    } else if (newSimNodes.length > 0) {
      // Expand: give new nodes a small random velocity kick so they drift away
      // from the spawn point. Don't spike alpha — the warm sim carries them.
      // Company nodes are pinned via fx/fy and are completely unaffected.
      for (const sn of newSimNodes) {
        sn.vx = (Math.random() - 0.5) * 3
        sn.vy = (Math.random() - 0.5) * 3
      }
      sim.alpha(Math.max(sim.alpha(), 0.15)).restart()
    }
    // Collapse (nodes removed, none added): no restart at all.
    // Pinned company nodes stay exactly where they are.
  }, [nodes, edges])

  // ── Apply positions — map directly, no hiding ────────────────────────────────
  return useMemo(
    () =>
      nodes.flatMap((node) => {
        const pos = positions.get(node.id)
        if (!pos) return []
        const dims = NODE_DIMENSIONS[node.type as keyof typeof NODE_DIMENSIONS] ?? NODE_DIMENSIONS.news
        const { width: w, height: h } = dims
        return [{ ...node, position: { x: pos.x - w / 2, y: pos.y - h / 2 } }]
      }),
    [nodes, positions],
  )
}

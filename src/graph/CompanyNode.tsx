import { memo } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import { motion } from 'framer-motion'
import { useGraphStore } from '../store/graphStore'
import type { CompanyNodeData } from './graphTypes'
import { NODE_DIMENSIONS } from '../shared/constants'
import { ACCENT, BG_SURFACE, BORDER, TEXT_PRIMARY, TEXT_MUTED, ANIMATION } from '../shared/constants'

const { width, height } = NODE_DIMENSIONS.company

function CompanyNode({ id, data }: NodeProps<CompanyNodeData>) {
  const toggleExpand = useGraphStore((s) => s.toggleExpand)

  return (
    <>
      <Handle type="source" position={Position.Right} isConnectable={false} />
      <motion.div
        onClick={() => toggleExpand(id)}
        whileHover={{ scale: 1.03 }}
        transition={ANIMATION.hover}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          width,
          height,
          padding: '0 14px',
          borderRadius: 999,
          backgroundColor: BG_SURFACE,
          border: `1.5px solid ${data.expanded ? ACCENT : BORDER}`,
          cursor: 'pointer',
          userSelect: 'none',
          whiteSpace: 'nowrap',
          boxSizing: 'border-box',
        }}
      >
        <span
          style={{
            fontSize: 10,
            color: data.expanded ? ACCENT : TEXT_MUTED,
            fontWeight: 600,
            letterSpacing: '0.06em',
            fontFamily: 'monospace',
          }}
        >
          {id}
        </span>
        <span style={{ fontSize: 13, color: TEXT_PRIMARY, fontWeight: 500 }}>{data.label}</span>
      </motion.div>
    </>
  )
}

export default memo(CompanyNode)

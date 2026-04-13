import { memo, useState } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import { motion } from 'framer-motion'
import { useUiStore } from '../store/uiStore'
import type { NewsNodeData } from './graphTypes'
import { NODE_DIMENSIONS } from '../shared/constants'
import { ANIMATION, BG_SURFACE, BORDER, TEXT_PRIMARY, TEXT_MUTED } from '../shared/constants'
import NodeTooltip from './NodeTooltip'

const { width, height } = NODE_DIMENSIONS.news

const NewsIcon = () => (
  <svg width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true" style={{ flexShrink: 0 }}>
    <rect x="1" y="1" width="10" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
    <line x1="3.5" y1="4" x2="8.5" y2="4" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
    <line x1="3.5" y1="6" x2="8.5" y2="6" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
    <line x1="3.5" y1="8" x2="6.5" y2="8" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
  </svg>
)

function NewsNode({ id, data }: NodeProps<NewsNodeData>) {
  const openPanel = useUiStore((s) => s.openPanel)
  const [hovered, setHovered] = useState(false)

  return (
    <>
      <NodeTooltip
        visible={hovered}
        headline={data.item.headline}
        source={data.item.source}
        publishedAt={data.item.publishedAt}
      />
      <Handle type="target" position={Position.Left} isConnectable={false} />
      <motion.div
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ ...ANIMATION.reveal, delay: data.animationDelay }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        onClick={() => openPanel(id)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 7,
          width,
          height,
          padding: '0 12px',
          borderRadius: 999,
          backgroundColor: BG_SURFACE,
          border: `1px solid ${BORDER}`,
          cursor: 'pointer',
          userSelect: 'none',
          whiteSpace: 'nowrap',
          boxSizing: 'border-box',
          color: TEXT_MUTED,
          overflow: 'hidden',
        }}
      >
        <NewsIcon />
        <span
          style={{
            fontSize: 12,
            color: TEXT_PRIMARY,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            flex: 1,
          }}
        >
          {data.item.headline}
        </span>
      </motion.div>
    </>
  )
}

export default memo(NewsNode)

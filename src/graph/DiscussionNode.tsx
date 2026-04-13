import { memo, useState } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import { motion } from 'framer-motion'
import { useUiStore } from '../store/uiStore'
import type { DiscussionNodeData } from './graphTypes'
import { NODE_DIMENSIONS } from '../shared/constants'
import { ANIMATION, BG_SURFACE, BORDER, TEXT_PRIMARY, TEXT_MUTED } from '../shared/constants'
import NodeTooltip from './NodeTooltip'

const { width, height } = NODE_DIMENSIONS.discussion

const DiscussionIcon = () => (
  <svg width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true" style={{ flexShrink: 0 }}>
    <path
      d="M10 1H2C1.44772 1 1 1.44772 1 2V7.5C1 8.05228 1.44772 8.5 2 8.5H4L6 10.5L8 8.5H10C10.5523 8.5 11 8.05228 11 7.5V2C11 1.44772 10.5523 1 10 1Z"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinejoin="round"
    />
  </svg>
)

function DiscussionNode({ id, data }: NodeProps<DiscussionNodeData>) {
  const openPanel = useUiStore((s) => s.openPanel)
  const [hovered, setHovered] = useState(false)

  return (
    <>
      <NodeTooltip
        visible={hovered}
        headline={data.item.title}
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
        <DiscussionIcon />
        <span
          style={{
            fontSize: 12,
            color: TEXT_PRIMARY,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            flex: 1,
          }}
        >
          {data.item.title}
        </span>
      </motion.div>
    </>
  )
}

export default memo(DiscussionNode)

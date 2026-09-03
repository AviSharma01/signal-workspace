import { memo, useState } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import { motion } from 'framer-motion'
import { useUiStore } from '../store/uiStore'
import { useGraphStore } from '../store/graphStore'
import type { DiscussionNodeData } from './graphTypes'
import { ANIMATION, BLOB_DISCUSSION } from '../shared/constants'
import NodeTooltip from './NodeTooltip'

function blobSize(publishedAt: number): number {
  const ageHours = (Date.now() - publishedAt) / 3_600_000
  const size = 20 - ageHours * (12 / 72)
  return Math.round(Math.max(8, Math.min(20, size)))
}

function DiscussionNode({ id, data }: NodeProps<DiscussionNodeData>) {
  const openPanel = useUiStore((s) => s.openPanel)
  const selectCompany = useGraphStore((s) => s.selectCompany)
  const selectedCompanyId = useGraphStore((s) => s.selectedCompanyId)
  const [hovered, setHovered] = useState(false)

  const isDimmed = selectedCompanyId !== null && selectedCompanyId !== data.parentId
  const diameter = blobSize(data.item.publishedAt)

  return (
    <div
      style={{ width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <NodeTooltip
        visible={hovered}
        headline={data.item.title}
        source={data.item.source}
        publishedAt={data.item.publishedAt}
      />
      <Handle type="target" position={Position.Left} isConnectable={false} />
      <motion.div
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{
          opacity: isDimmed ? 0.15 : (hovered ? 1 : 0.85),
          scale: hovered ? 1.15 : 1,
        }}
        transition={{ ...ANIMATION.reveal, delay: data.animationDelay }}
        onClick={() => {
          selectCompany(data.parentId)
          openPanel(id)
        }}
        style={{
          width: diameter,
          height: diameter,
          borderRadius: '50%',
          backgroundColor: BLOB_DISCUSSION,
          cursor: 'pointer',
          flexShrink: 0,
        }}
      />
    </div>
  )
}

export default memo(DiscussionNode)

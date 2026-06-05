import { memo, useState } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useGraphStore } from '../store/graphStore'
import type { RelatedCompanyNodeData } from './graphTypes'
import { ANIMATION, BLOB_RELATED } from '../shared/constants'
import NodeTooltip from './NodeTooltip'

const DIAMETER = 14

function RelatedCompanyNode({ data }: NodeProps<RelatedCompanyNodeData>) {
  const navigate = useNavigate()
  const selectedCompanyId = useGraphStore((s) => s.selectedCompanyId)
  const [hovered, setHovered] = useState(false)

  const isDimmed = selectedCompanyId !== null && selectedCompanyId !== data.parentId

  return (
    <div style={{ width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <NodeTooltip
        visible={hovered}
        headline={data.label}
        source={data.ticker}
        publishedAt={0}
      />
      <Handle type="target" position={Position.Left} isConnectable={false} />
      <motion.div
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{
          opacity: isDimmed ? 0.15 : (hovered ? 1 : 0.7),
          scale: hovered ? 1.15 : 1,
        }}
        transition={{ ...ANIMATION.reveal, delay: data.animationDelay }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        onClick={() => navigate(`/company/${data.ticker}`)}
        style={{
          width: DIAMETER,
          height: DIAMETER,
          borderRadius: '50%',
          backgroundColor: BLOB_RELATED,
          cursor: 'pointer',
          flexShrink: 0,
        }}
      />
    </div>
  )
}

export default memo(RelatedCompanyNode)

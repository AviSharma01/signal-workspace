import { memo } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import { motion } from 'framer-motion'
import { useGraphStore } from '../store/graphStore'
import { useUiStore } from '../store/uiStore'
import type { CompanyNodeData } from './graphTypes'
import { NODE_DIMENSIONS } from '../shared/constants'
import { ACCENT, BG_SURFACE, BORDER, TEXT_PRIMARY, TEXT_MUTED, ANIMATION } from '../shared/constants'

const { width, height } = NODE_DIMENSIONS.company

function CompanyNode({ id, data }: NodeProps<CompanyNodeData>) {
  const selectCompany = useGraphStore((s) => s.selectCompany)
  const selectedCompanyId = useGraphStore((s) => s.selectedCompanyId)
  const openPanel = useUiStore((s) => s.openPanel)
  const closePanel = useUiStore((s) => s.closePanel)

  const isSelected = selectedCompanyId === id
  const isDimmed = selectedCompanyId !== null && !isSelected

  function handleClick() {
    if (isSelected) {
      selectCompany(null)
      closePanel()
    } else {
      selectCompany(id)
      openPanel(id)
    }
  }

  return (
    <>
      <Handle type="source" position={Position.Right} isConnectable={false} />
      <motion.div
        onClick={handleClick}
        animate={{ opacity: isDimmed ? 0.25 : 1, scale: 1 }}
        whileHover={{ scale: 1.03, opacity: 1 }}
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
          border: `1.5px solid ${isSelected ? ACCENT : BORDER}`,
          cursor: 'pointer',
          userSelect: 'none',
          whiteSpace: 'nowrap',
          boxSizing: 'border-box',
        }}
      >
        <span
          style={{
            fontSize: 10,
            color: isSelected ? ACCENT : TEXT_MUTED,
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

import { NodeToolbar, Position } from 'reactflow'
import { motion, AnimatePresence } from 'framer-motion'
import { ANIMATION, BG_SURFACE, BORDER, TEXT_PRIMARY, TEXT_MUTED, formatRelativeTime } from '../shared/constants'

interface NodeTooltipProps {
  visible: boolean
  headline: string
  source: string
  publishedAt: number
}

export default function NodeTooltip({ visible, headline, source, publishedAt }: NodeTooltipProps) {
  return (
    <NodeToolbar isVisible={visible} position={Position.Top} offset={8}>
      <AnimatePresence>
        {visible && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            transition={ANIMATION.reveal}
            style={{
              backgroundColor: BG_SURFACE,
              border: `1px solid ${BORDER}`,
              borderRadius: 6,
              padding: '8px 10px',
              maxWidth: 260,
              pointerEvents: 'none',
            }}
          >
            <p
              style={{
                color: TEXT_PRIMARY,
                fontSize: 12,
                lineHeight: 1.4,
                margin: 0,
                marginBottom: 4,
              }}
            >
              {headline}
            </p>
            <p style={{ color: TEXT_MUTED, fontSize: 11, margin: 0 }}>
              {source}{publishedAt > 0 ? ` · ${formatRelativeTime(publishedAt)}` : ''}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </NodeToolbar>
  )
}

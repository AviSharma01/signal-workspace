import { useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import type { NewsItem, DiscussionItem } from '../shared/types'
import { ACCENT, ANIMATION, BG_SURFACE, BORDER, TEXT_MUTED, TEXT_PRIMARY } from '../shared/constants'

type SignalItemData = NewsItem | DiscussionItem

function isNews(item: SignalItemData): item is NewsItem {
  return 'headline' in item
}

function formatRelativeTime(timestamp: number): string {
  const diff = Date.now() - timestamp
  const minutes = Math.floor(diff / 60000)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

interface SignalItemProps {
  item: SignalItemData
  isActive: boolean
  animationDelay: number
  onClick: () => void
}

export default function SignalItem({ item, isActive, animationDelay, onClick }: SignalItemProps) {
  const ref = useRef<HTMLDivElement>(null)
  const headline = isNews(item) ? item.headline : item.title

  // Scroll into view when this item becomes active (panel → chart direction)
  useEffect(() => {
    if (isActive) {
      ref.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [isActive])

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...ANIMATION.reveal, delay: animationDelay }}
      onClick={onClick}
      style={{
        padding: '10px 16px',
        cursor: 'pointer',
        borderLeft: `2px solid ${isActive ? ACCENT : 'transparent'}`,
        backgroundColor: isActive ? `${BG_SURFACE}cc` : 'transparent',
        borderBottom: `1px solid ${BORDER}`,
        userSelect: 'none',
      }}
      whileHover={{ backgroundColor: `${BG_SURFACE}99` }}
    >
      <p
        style={{
          fontSize: 11,
          color: TEXT_MUTED,
          margin: '0 0 4px',
          lineHeight: 1.4,
        }}
      >
        {item.source} · {formatRelativeTime(item.publishedAt)}
      </p>
      <p
        style={{
          fontSize: 13,
          color: isActive ? TEXT_PRIMARY : `${TEXT_PRIMARY}cc`,
          fontWeight: isActive ? 600 : 500,
          lineHeight: 1.45,
          margin: 0,
          overflow: 'hidden',
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
        }}
      >
        {headline}
      </p>
    </motion.div>
  )
}

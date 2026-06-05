import { useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import type { NewsItem, DiscussionItem } from '../shared/types'
import { ACCENT, ANIMATION, BG_SURFACE, BORDER, TEXT_MUTED, TEXT_PRIMARY, formatRelativeTime } from '../shared/constants'

type SignalItemData = NewsItem | DiscussionItem

function isNews(item: SignalItemData): item is NewsItem {
  return 'headline' in item
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
        {item.url && (
          <a
            href={item.url}
            target="_blank"
            rel="noreferrer"
            onClick={(e) => e.stopPropagation()}
            style={{ color: TEXT_MUTED, marginLeft: 6, textDecoration: 'none', opacity: 0.7 }}
          >
            ↗
          </a>
        )}
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

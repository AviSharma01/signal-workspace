import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import type { NewsItem, DiscussionItem } from '../shared/types'
import type { Company } from '../shared/types'
import { ANIMATION, BG_SURFACE, BLOB_RELATED, BORDER, TEXT_MUTED, TEXT_PRIMARY } from '../shared/constants'
import SignalItem from './SignalItem'

interface SignalPanelProps {
  news: NewsItem[]
  discussion: DiscussionItem[]
  activeSignalId: string | null
  onSignalSelect: (signalId: string) => void
  loading: boolean
  relatedCompanies: Company[]
}

function SectionLabel({ label }: { label: string }) {
  return (
    <div
      style={{
        padding: '10px 16px 6px',
        fontSize: 11,
        color: TEXT_MUTED,
        fontWeight: 500,
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
        flexShrink: 0,
      }}
    >
      {label}
    </div>
  )
}

function SkeletonRow() {
  return (
    <div
      style={{
        padding: '10px 16px',
        borderBottom: `1px solid ${BORDER}`,
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
      }}
    >
      <div
        style={{
          height: 10,
          width: '40%',
          borderRadius: 3,
          backgroundColor: `${TEXT_MUTED}22`,
        }}
      />
      <div
        style={{
          height: 13,
          width: '85%',
          borderRadius: 3,
          backgroundColor: `${TEXT_MUTED}18`,
        }}
      />
      <div
        style={{
          height: 13,
          width: '60%',
          borderRadius: 3,
          backgroundColor: `${TEXT_MUTED}18`,
        }}
      />
    </div>
  )
}

export default function SignalPanel({
  news,
  discussion,
  activeSignalId,
  onSignalSelect,
  loading,
  relatedCompanies,
}: SignalPanelProps) {
  const navigate = useNavigate()
  return (
    <motion.aside
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={ANIMATION.reveal}
      style={{
        width: 300,
        flexShrink: 0,
        height: '100%',
        backgroundColor: BG_SURFACE,
        borderLeft: `1px solid ${BORDER}`,
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
      }}
    >
      {loading ? (
        <>
          <SectionLabel label="News" />
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
          <SectionLabel label="Discussion" />
          <SkeletonRow />
          <SkeletonRow />
        </>
      ) : (
        <>
          {news.length > 0 && (
            <>
              <SectionLabel label="News" />
              {news.map((item, i) => (
                <SignalItem
                  key={item.id}
                  item={item}
                  isActive={item.id === activeSignalId}
                  animationDelay={i * ANIMATION.stagger}
                  onClick={() => onSignalSelect(item.id)}
                />
              ))}
            </>
          )}
          {discussion.length > 0 && (
            <>
              <SectionLabel label="Discussion" />
              {discussion.map((item, i) => (
                <SignalItem
                  key={item.id}
                  item={item}
                  isActive={item.id === activeSignalId}
                  animationDelay={(news.length + i) * ANIMATION.stagger}
                  onClick={() => onSignalSelect(item.id)}
                />
              ))}
            </>
          )}
          {relatedCompanies.length > 0 && (
            <>
              <SectionLabel label="Related" />
              <div style={{ padding: '4px 16px 16px', display: 'flex', flexDirection: 'column', gap: 2 }}>
                {relatedCompanies.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => navigate(`/company/${c.id}`)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      padding: '7px 0',
                      background: 'none',
                      border: 'none',
                      borderBottom: `1px solid ${BORDER}`,
                      cursor: 'pointer',
                      textAlign: 'left',
                      width: '100%',
                    }}
                  >
                    <div style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      backgroundColor: BLOB_RELATED,
                      opacity: 0.8,
                      flexShrink: 0,
                    }} />
                    <span style={{ fontSize: 11, color: TEXT_MUTED, fontFamily: 'monospace', letterSpacing: '0.06em', flexShrink: 0 }}>
                      {c.id}
                    </span>
                    <span style={{ fontSize: 13, color: TEXT_PRIMARY, fontWeight: 500 }}>
                      {c.name}
                    </span>
                    <span style={{ marginLeft: 'auto', fontSize: 12, color: TEXT_MUTED }}>→</span>
                  </button>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </motion.aside>
  )
}

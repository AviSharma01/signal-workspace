import { motion } from 'framer-motion'
import type { Finding } from '../shared/types'
import { BORDER, TEXT_MUTED, TEXT_PRIMARY, ANIMATION } from '../shared/constants'
import { formatRelativeTime } from '../shared/constants'

// Muted driver colors — accent blue reserved for news per aesthetic spec
const DRIVER_COLORS: Record<string, string> = {
  news:        '#4d7fff',
  discussion:  '#2a6b4a',
  sector:      '#6b4bb5',
  unexplained: '#8a6a2a',
}

const CONFIDENCE_COLORS: Record<string, string> = {
  high:   '#2da44e',
  medium: '#9a9aaa',
  low:    '#c97a1a',
}

interface FindingCardProps {
  finding: Finding
  animationDelay?: number
}

export default function FindingCard({ finding, animationDelay = 0 }: FindingCardProps) {
  const driverColor = DRIVER_COLORS[finding.primaryDriver] ?? '#6b6b7b'
  const confidenceColor = CONFIDENCE_COLORS[finding.confidence] ?? '#9a9aaa'

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: ANIMATION.reveal.duration, ease: ANIMATION.reveal.ease, delay: animationDelay }}
      style={{
        padding: '14px 16px',
        borderRadius: 6,
        border: `1px solid ${BORDER}`,
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
      }}
    >
      {/* Top row: driver badge + confidence + time */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <span
          style={{
            fontSize: 10,
            fontWeight: 600,
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
            padding: '2px 8px',
            borderRadius: 99,
            backgroundColor: `${driverColor}22`,
            color: driverColor,
            border: `1px solid ${driverColor}44`,
            flexShrink: 0,
          }}
        >
          {finding.primaryDriver}
        </span>

        <span style={{ fontSize: 12, color: confidenceColor, fontWeight: 500, flexShrink: 0 }}>
          {finding.confidence} confidence
        </span>

        <span style={{ fontSize: 11, color: TEXT_MUTED, marginLeft: 'auto', flexShrink: 0 }}>
          {formatRelativeTime(finding.createdAt)}
        </span>

        {finding.needsHumanReview && (
          <span
            style={{
              fontSize: 10,
              fontWeight: 600,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
              padding: '2px 8px',
              borderRadius: 99,
              backgroundColor: '#c97a1a22',
              color: '#c97a1a',
              border: '1px solid #c97a1a44',
              flexShrink: 0,
            }}
          >
            Needs human review
          </span>
        )}
      </div>

      {/* Trigger details */}
      <div
        style={{
          fontSize: 11,
          color: TEXT_MUTED,
          fontFamily: 'monospace',
          display: 'flex',
          gap: 12,
          flexWrap: 'wrap',
        }}
      >
        <span>z {finding.trigger.z_score > 0 ? '+' : ''}{finding.trigger.z_score.toFixed(2)}</span>
        <span>vol ×{finding.trigger.volume_ratio.toFixed(1)}</span>
        <span>
          {finding.trigger.direction === 'up' ? '▲' : '▼'}{' '}
          {Math.abs(finding.trigger.latest_return_pct).toFixed(2)}%
        </span>
      </div>

      {/* Hypothesis */}
      <p style={{ fontSize: 13, color: TEXT_PRIMARY, lineHeight: 1.6, margin: 0 }}>
        {finding.hypothesis}
      </p>

      {/* Evidence */}
      {finding.evidence.length > 0 && (
        <div>
          <span
            style={{
              fontSize: 10,
              fontWeight: 600,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: TEXT_MUTED,
              display: 'block',
              marginBottom: 6,
            }}
          >
            Evidence
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {finding.evidence.map((entry, i) => (
              <div key={i} style={{ fontSize: 12, color: TEXT_MUTED, lineHeight: 1.5 }}>
                <span style={{ color: TEXT_PRIMARY, fontWeight: 500 }}>{entry.type}</span>
                {' · '}
                <span style={{ fontFamily: 'monospace', fontSize: 11 }}>{entry.ref}</span>
                {' · '}
                <span>{entry.why}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )
}

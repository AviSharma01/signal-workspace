import { BLOB_NEWS, BLOB_DISCUSSION, BLOB_RELATED, TEXT_MUTED, BG_SURFACE, BORDER } from '../shared/constants'

const ITEMS = [
  { color: BLOB_NEWS, label: 'News' },
  { color: BLOB_DISCUSSION, label: 'Discussion' },
  { color: BLOB_RELATED, label: 'Related co.' },
] as const

export default function GraphLegend() {
  return (
    <div
      style={{
        position: 'absolute',
        bottom: 24,
        left: 20,
        zIndex: 10,
        backgroundColor: BG_SURFACE,
        border: `1px solid ${BORDER}`,
        borderRadius: 6,
        padding: '8px 12px',
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        pointerEvents: 'none',
      }}
    >
      <span
        style={{
          fontSize: 10,
          color: TEXT_MUTED,
          fontWeight: 600,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          marginBottom: 2,
        }}
      >
        Signals
      </span>
      {ITEMS.map(({ color, label }) => (
        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: color,
              opacity: 0.85,
              flexShrink: 0,
            }}
          />
          <span style={{ fontSize: 11, color: TEXT_MUTED }}>{label}</span>
        </div>
      ))}
      <div
        style={{
          marginTop: 4,
          paddingTop: 6,
          borderTop: `1px solid ${BORDER}`,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div style={{ width: 5, height: 5, borderRadius: '50%', backgroundColor: TEXT_MUTED, opacity: 0.4 }} />
          <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: TEXT_MUTED, opacity: 0.4 }} />
        </div>
        <span style={{ fontSize: 11, color: TEXT_MUTED }}>size = recency</span>
      </div>
    </div>
  )
}

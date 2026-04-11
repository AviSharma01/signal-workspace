import { useParams, Link } from 'react-router-dom'
import { SEED_COMPANIES, BG_PRIMARY, TEXT_MUTED, TEXT_PRIMARY, ACCENT } from '../shared/constants'

export default function DetailPage() {
  const { companyId } = useParams<{ companyId: string }>()
  const company = SEED_COMPANIES.find((c) => c.id === companyId)

  return (
    <div
      style={{
        width: '100%',
        height: '100vh',
        backgroundColor: BG_PRIMARY,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
      }}
    >
      <span
        style={{
          fontSize: 11,
          color: TEXT_MUTED,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          fontFamily: 'monospace',
        }}
      >
        {companyId}
      </span>
      <h1 style={{ fontSize: 24, color: TEXT_PRIMARY, fontWeight: 600, margin: 0 }}>
        {company?.name ?? companyId}
      </h1>
      <p style={{ fontSize: 13, color: TEXT_MUTED, margin: '0 0 24px' }}>Detail view — coming in Phase 4</p>
      <Link
        to="/"
        style={{ fontSize: 13, color: ACCENT, textDecoration: 'none', fontWeight: 500 }}
      >
        ← Back to graph
      </Link>
    </div>
  )
}

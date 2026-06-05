import { Link } from 'react-router-dom'
import { usePrices } from '../data/usePrices'
import { useCompanies } from '../data/useCompanies'
import { ACCENT, BORDER, TEXT_MUTED, TEXT_PRIMARY } from '../shared/constants'

interface CompanyPanelContentProps {
  companyId: string
}

function formatPrice(price: number): string {
  return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function computeDayChange(prices: { close: number }[]): { text: string; positive: boolean } | null {
  if (prices.length < 2) return null
  const open = prices[0].close
  const close = prices[prices.length - 1].close
  if (open === 0) return null
  const pct = ((close - open) / open) * 100
  return { text: `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`, positive: pct >= 0 }
}

export default function CompanyPanelContent({ companyId }: CompanyPanelContentProps) {
  const { companies } = useCompanies()
  const company = companies.find((c) => c.id === companyId)
  const { prices, loading } = usePrices(companyId, '1D')

  const currentPrice = prices[prices.length - 1]?.close
  const dayChange = computeDayChange(prices)

  return (
    <>
      {/* Body */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px 16px' }}>
        {/* Ticker + name */}
        <div style={{ marginBottom: 20 }}>
          <span
            style={{
              fontSize: 11,
              color: TEXT_MUTED,
              fontFamily: 'monospace',
              fontWeight: 600,
              letterSpacing: '0.06em',
              display: 'block',
              marginBottom: 4,
            }}
          >
            {companyId}
          </span>
          <span style={{ fontSize: 18, color: TEXT_PRIMARY, fontWeight: 600 }}>
            {company?.name ?? companyId}
          </span>
        </div>

        {/* Sector */}
        <div style={{ marginBottom: 20 }}>
          <span style={{ fontSize: 11, color: TEXT_MUTED, display: 'block', marginBottom: 2 }}>
            Sector
          </span>
          <span style={{ fontSize: 13, color: TEXT_PRIMARY }}>{company?.sector ?? '—'}</span>
        </div>

        {/* Price */}
        <div
          style={{
            padding: '12px 14px',
            borderRadius: 6,
            border: `1px solid ${BORDER}`,
          }}
        >
          {loading ? (
            <div style={{ height: 36, display: 'flex', alignItems: 'center' }}>
              <span style={{ fontSize: 12, color: TEXT_MUTED }}>Loading…</span>
            </div>
          ) : currentPrice !== undefined ? (
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <span
                style={{
                  fontSize: 20,
                  color: TEXT_PRIMARY,
                  fontWeight: 600,
                  fontVariantNumeric: 'tabular-nums',
                }}
              >
                ${formatPrice(currentPrice)}
              </span>
              {dayChange && (
                <span
                  style={{
                    fontSize: 12,
                    fontWeight: 500,
                    color: dayChange.positive ? '#2da44e' : '#e5534b',
                    fontVariantNumeric: 'tabular-nums',
                  }}
                >
                  {dayChange.text} today
                </span>
              )}
            </div>
          ) : (
            <span style={{ fontSize: 12, color: TEXT_MUTED }}>No price data</span>
          )}
        </div>
      </div>

      {/* Footer */}
      <div
        style={{
          padding: '14px 16px',
          borderTop: `1px solid ${BORDER}`,
          flexShrink: 0,
        }}
      >
        <Link
          to={`/company/${companyId}`}
          style={{
            fontSize: 13,
            color: ACCENT,
            textDecoration: 'none',
            fontWeight: 500,
          }}
        >
          View details →
        </Link>
      </div>
    </>
  )
}

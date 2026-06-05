import { useState, useMemo, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useSignals } from '../data/useSignals'
import { usePrices } from '../data/usePrices'
import { useCompanies } from '../data/useCompanies'
import type { PriceRange } from '../data/usePrices'
import { buildMarkers } from './EventMarker'
import PriceChart from './PriceChart'
import SignalPanel from './SignalPanel'
import FindingsPanel from './FindingsPanel'
import { ACCENT, ANIMATION, BG_PRIMARY, BG_SURFACE, BORDER, TEXT_MUTED, TEXT_PRIMARY } from '../shared/constants'
import './detail.css'

type ChartType = 'candlestick' | 'line'

const RANGES: PriceRange[] = ['1D', '1W', '1M', '3M']

function formatPrice(price: number): string {
  return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatDayChange(prices1D: { close: number }[]): { text: string; positive: boolean } | null {
  if (prices1D.length < 2) return null
  const open = prices1D[0].close
  const close = prices1D[prices1D.length - 1].close
  if (open === 0) return null
  const pct = ((close - open) / open) * 100
  const sign = pct >= 0 ? '+' : ''
  return { text: `${sign}${pct.toFixed(2)}%`, positive: pct >= 0 }
}

export default function DetailPage() {
  const { companyId } = useParams<{ companyId: string }>()
  const navigate = useNavigate()
  const { companies } = useCompanies()
  const company = companies.find((c) => c.id === companyId)

  const [chartType, setChartType] = useState<ChartType>('candlestick')
  const [range, setRange] = useState<PriceRange>('1M')

  // activeSignalId is the single source of truth for bidirectional marker↔item selection.
  // Both PriceChart and SignalPanel receive it as a prop and write back through callbacks
  // that converge here. No circular updates — each user gesture calls setActiveSignalId once.
  const [activeSignalId, setActiveSignalId] = useState<string | null>(null)

  const { prices, loading: pricesLoading } = usePrices(companyId ?? '', range)
  const { prices: prices1D, loading: prices1DLoading } = usePrices(companyId ?? '', '1D')
  const { news, discussion, loading: signalsLoading } = useSignals(companyId ?? null)

  const relatedCompanies = useMemo(
    () => company ? companies.filter((c) => c.sector === company.sector && c.id !== companyId) : [],
    [company, companyId, companies],
  )

  const priceRange = useMemo(
    () => ({
      from: prices[0]?.timestamp ?? 0,
      to: prices[prices.length - 1]?.timestamp ?? 0,
    }),
    [prices],
  )

  // Markers filtered to current chart range — rebuilds when prices or signals change.
  // activeSignalId is NOT a dependency: styling is applied inside PriceChart based on the prop.
  const markers = useMemo(
    () => buildMarkers(news, discussion, priceRange),
    [news, discussion, priceRange],
  )

  const currentPrice = prices1D[prices1D.length - 1]?.close
  const dayChange = formatDayChange(prices1D)

  const handleMarkerClick = useCallback((signalId: string) => {
    setActiveSignalId((prev) => (prev === signalId ? null : signalId))
  }, [])

  const handleSignalSelect = useCallback((signalId: string) => {
    setActiveSignalId((prev) => (prev === signalId ? null : signalId))
  }, [])

  if (!companyId) return null

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={ANIMATION.pageTransition}
      style={{
        width: '100%',
        height: '100vh',
        backgroundColor: BG_PRIMARY,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* ── Header ── */}
      <header
        style={{
          height: 52,
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          padding: '0 20px',
          borderBottom: `1px solid ${BORDER}`,
          backgroundColor: BG_SURFACE,
        }}
      >
        {/* Back */}
        <button
          onClick={() => navigate(-1)}
          style={{
            background: 'none',
            border: 'none',
            color: TEXT_MUTED,
            fontSize: 13,
            cursor: 'pointer',
            padding: '4px 8px 4px 0',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            flexShrink: 0,
          }}
        >
          ← Back
        </button>

        <div style={{ width: 1, height: 16, backgroundColor: BORDER, flexShrink: 0 }} />

        {/* Company name + ticker */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexShrink: 0 }}>
          <span style={{ fontSize: 15, color: TEXT_PRIMARY, fontWeight: 600 }}>
            {company?.name ?? companyId}
          </span>
          <span
            style={{
              fontSize: 11,
              color: TEXT_MUTED,
              fontFamily: 'monospace',
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
            }}
          >
            {companyId}
          </span>
        </div>

        {/* Price + day change */}
        {!prices1DLoading && currentPrice !== undefined && (
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontSize: 15, color: TEXT_PRIMARY, fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>
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
        )}

        {/* Spacer */}
        <div style={{ flex: 1 }} />

        {/* Chart type toggle */}
        <div style={{ display: 'flex', gap: 2 }}>
          {(['candlestick', 'line'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setChartType(type)}
              style={{
                fontSize: 11,
                padding: '3px 10px',
                borderRadius: 4,
                border: `1px solid ${chartType === type ? ACCENT : BORDER}`,
                backgroundColor: chartType === type ? `${ACCENT}22` : 'transparent',
                color: chartType === type ? ACCENT : TEXT_MUTED,
                cursor: 'pointer',
                fontWeight: 500,
                textTransform: 'capitalize',
              }}
            >
              {type === 'candlestick' ? 'Candles' : 'Line'}
            </button>
          ))}
        </div>

        {/* Range selector */}
        <div style={{ display: 'flex', gap: 2 }}>
          {RANGES.map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              style={{
                fontSize: 11,
                padding: '3px 10px',
                borderRadius: 4,
                border: `1px solid ${range === r ? ACCENT : BORDER}`,
                backgroundColor: range === r ? `${ACCENT}22` : 'transparent',
                color: range === r ? ACCENT : TEXT_MUTED,
                cursor: 'pointer',
                fontWeight: 500,
              }}
            >
              {r}
            </button>
          ))}
        </div>
      </header>

      {/* ── Body: chart + findings + signal panel ── */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <PriceChart
            prices={prices}
            markers={markers}
            activeSignalId={activeSignalId}
            onMarkerClick={handleMarkerClick}
            chartType={chartType}
            loading={pricesLoading}
          />
        </div>

        {/* Findings panel — investigation agent output */}
        <div
          style={{
            width: 280,
            flexShrink: 0,
            borderLeft: `1px solid ${BORDER}`,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <FindingsPanel companyId={companyId ?? ''} />
        </div>

        <SignalPanel
          news={news}
          discussion={discussion}
          activeSignalId={activeSignalId}
          onSignalSelect={handleSignalSelect}
          loading={signalsLoading}
          relatedCompanies={relatedCompanies}
        />
      </div>
    </motion.div>
  )
}

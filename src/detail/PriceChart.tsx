import { useEffect, useRef, useState } from 'react'
import {
  createChart,
  CandlestickSeries,
  LineSeries,
  createSeriesMarkers,
} from 'lightweight-charts'
import type {
  IChartApi,
  ISeriesMarkersPluginApi,
  MouseEventParams,
  Time,
  SeriesMarker,
} from 'lightweight-charts'
import type { PricePoint } from '../shared/types'
import type { ChartMarker } from './EventMarker'
import { ACCENT, BG_PRIMARY, BG_SURFACE, BORDER, TEXT_MUTED, TEXT_PRIMARY } from '../shared/constants'

// Colours for markers — inactive versions are dimmed so the chart stays readable
const MARKER_NEWS_ACTIVE = ACCENT
const MARKER_NEWS_INACTIVE = '#2a3a5e'
const MARKER_DISC_ACTIVE = '#2da44e'
const MARKER_DISC_INACTIVE = '#1a3024'

const CHART_OPTIONS = {
  layout: {
    background: { color: BG_PRIMARY },
    textColor: TEXT_MUTED,
    fontSize: 11,
    fontFamily: 'Inter, -apple-system, sans-serif',
  },
  grid: {
    vertLines: { color: 'transparent' },
    horzLines: { color: `${BORDER}88` },
  },
  crosshair: {
    vertLine: { color: `${ACCENT}55`, width: 1 as const },
    horzLine: { color: `${ACCENT}55`, width: 1 as const },
  },
  timeScale: {
    borderColor: BORDER,
    timeVisible: true,
    secondsVisible: false,
  },
  rightPriceScale: {
    borderColor: BORDER,
  },
  handleScroll: true,
  handleScale: true,
} as const

const CANDLESTICK_OPTIONS = {
  upColor: '#2da44e',
  downColor: '#e5534b',
  borderUpColor: '#2da44e',
  borderDownColor: '#e5534b',
  wickUpColor: '#2da44e',
  wickDownColor: '#e5534b',
} as const

const LINE_OPTIONS = {
  color: ACCENT,
  lineWidth: 2 as const,
  crosshairMarkerVisible: true,
  crosshairMarkerRadius: 4,
} as const

interface OhlcTooltip {
  time: number
  open?: number
  high?: number
  low?: number
  close: number
}

interface PriceChartProps {
  prices: PricePoint[]
  markers: ChartMarker[]
  activeSignalId: string | null
  onMarkerClick: (signalId: string) => void
  chartType: 'candlestick' | 'line'
  loading: boolean
}

function fmt(n: number) {
  return n.toFixed(2)
}

function formatTooltipTime(unixSeconds: number): string {
  return new Date(unixSeconds * 1000).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function PriceChart({
  prices,
  markers,
  activeSignalId,
  onMarkerClick,
  chartType,
  loading,
}: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  // Stable refs — never trigger re-renders
  const chartRef = useRef<IChartApi | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const seriesRef = useRef<any>(null)
  const markersPluginRef = useRef<ISeriesMarkersPluginApi<Time> | null>(null)
  const prevChartTypeRef = useRef<'candlestick' | 'line' | null>(null)

  // Refs for the click handler so it always reads current values without re-subscribing
  const markersRef = useRef<ChartMarker[]>(markers)
  const onMarkerClickRef = useRef(onMarkerClick)
  useEffect(() => { markersRef.current = markers }, [markers])
  useEffect(() => { onMarkerClickRef.current = onMarkerClick }, [onMarkerClick])

  const [tooltip, setTooltip] = useState<OhlcTooltip | null>(null)

  // ── Effect 1: create chart, subscribe to click and crosshair, ResizeObserver ─
  useEffect(() => {
    if (!containerRef.current) return

    const chart = createChart(containerRef.current, {
      ...CHART_OPTIONS,
      width: containerRef.current.clientWidth,
      height: containerRef.current.clientHeight,
    })
    chartRef.current = chart

    // Click handler: find the nearest ChartMarker by time and fire onMarkerClick.
    // Tolerance: 2 days (172800s) — loose but safe threshold across all ranges.
    const clickHandler = (param: MouseEventParams<Time>) => {
      if (!param.time) return
      const clickTime = param.time as number

      let nearest: ChartMarker | null = null
      let minDiff = Infinity
      for (const m of markersRef.current) {
        const diff = Math.abs(m.time - clickTime)
        if (diff < minDiff) {
          minDiff = diff
          nearest = m
        }
      }

      if (nearest && minDiff < 172800) {
        onMarkerClickRef.current(nearest.signalId)
      }
    }
    chart.subscribeClick(clickHandler)

    // Crosshair handler: populate the OHLC tooltip while hovering.
    // Reads seriesRef at call time so it always targets the current series.
    const crosshairHandler = (param: MouseEventParams<Time>) => {
      if (!param.time || !seriesRef.current) {
        setTooltip(null)
        return
      }
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const raw = param.seriesData.get(seriesRef.current) as any
      if (!raw) { setTooltip(null); return }

      if ('open' in raw) {
        setTooltip({ time: param.time as number, open: raw.open, high: raw.high, low: raw.low, close: raw.close })
      } else {
        setTooltip({ time: param.time as number, close: raw.value })
      }
    }
    chart.subscribeCrosshairMove(crosshairHandler)

    const resizeObserver = new ResizeObserver(() => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        })
      }
    })
    resizeObserver.observe(containerRef.current)

    return () => {
      resizeObserver.disconnect()
      chart.unsubscribeClick(clickHandler)
      chart.unsubscribeCrosshairMove(crosshairHandler)
      chart.remove()
      chartRef.current = null
      seriesRef.current = null
      markersPluginRef.current = null
      prevChartTypeRef.current = null
    }
  }, [])

  // ── Effect 2: create or swap series when chartType changes ──────────────────
  useEffect(() => {
    const chart = chartRef.current
    if (!chart) return
    if (prevChartTypeRef.current === chartType) return

    // Tear down old series (markers plugin is implicitly detached when series removed)
    if (seriesRef.current) {
      markersPluginRef.current = null
      chart.removeSeries(seriesRef.current)
      seriesRef.current = null
    }

    if (chartType === 'candlestick') {
      seriesRef.current = chart.addSeries(CandlestickSeries, CANDLESTICK_OPTIONS)
    } else {
      seriesRef.current = chart.addSeries(LineSeries, LINE_OPTIONS)
    }

    // Initialise an empty markers plugin so Effect 4 can always call setMarkers
    markersPluginRef.current = createSeriesMarkers(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      seriesRef.current as any,
      [],
    ) as ISeriesMarkersPluginApi<Time>

    prevChartTypeRef.current = chartType
  }, [chartType])

  // ── Effect 3: load price data ────────────────────────────────────────────────
  useEffect(() => {
    if (!seriesRef.current || prices.length === 0) return

    if (chartType === 'candlestick') {
      seriesRef.current.setData(
        prices.map((p) => ({
          time: Math.floor(p.timestamp / 1000) as Time,
          open: p.open,
          high: p.high,
          low: p.low,
          close: p.close,
        })),
      )
    } else {
      seriesRef.current.setData(
        prices.map((p) => ({
          time: Math.floor(p.timestamp / 1000) as Time,
          value: p.close,
        })),
      )
    }
  }, [prices, chartType])

  // ── Effect 4: update markers ─────────────────────────────────────────────────
  useEffect(() => {
    if (!markersPluginRef.current) return

    const seriesMarkers: SeriesMarker<Time>[] = markers.map((m) => {
      const isActive = m.signalId === activeSignalId
      const isNews = m.type === 'news'
      return {
        time: m.time as Time,
        position: isNews ? ('aboveBar' as const) : ('belowBar' as const),
        shape: 'circle' as const,
        color: isActive
          ? (isNews ? MARKER_NEWS_ACTIVE : MARKER_DISC_ACTIVE)
          : (isNews ? MARKER_NEWS_INACTIVE : MARKER_DISC_INACTIVE),
        size: isActive ? 2 : 1,
        id: m.signalId,
      }
    })

    markersPluginRef.current.setMarkers(seriesMarkers)
  }, [markers, activeSignalId, chartType])

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={containerRef} className="chart-container" style={{ width: '100%', height: '100%' }} />

      {/* OHLC tooltip — top-left, updates on crosshair move */}
      {tooltip && (
        <div
          style={{
            position: 'absolute',
            top: 12,
            left: 12,
            pointerEvents: 'none',
            backgroundColor: `${BG_SURFACE}f0`,
            border: `1px solid ${BORDER}`,
            borderRadius: 4,
            padding: '6px 10px',
            fontSize: 11,
            lineHeight: 1.7,
            zIndex: 1,
          }}
        >
          <div style={{ color: TEXT_MUTED, marginBottom: 2 }}>
            {formatTooltipTime(tooltip.time)}
          </div>
          {tooltip.open !== undefined ? (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', columnGap: 14 }}>
              <span style={{ color: TEXT_MUTED }}>O <span style={{ color: TEXT_PRIMARY, fontVariantNumeric: 'tabular-nums' }}>{fmt(tooltip.open)}</span></span>
              <span style={{ color: TEXT_MUTED }}>H <span style={{ color: '#2da44e', fontVariantNumeric: 'tabular-nums' }}>{fmt(tooltip.high!)}</span></span>
              <span style={{ color: TEXT_MUTED }}>C <span style={{ color: TEXT_PRIMARY, fontVariantNumeric: 'tabular-nums' }}>{fmt(tooltip.close)}</span></span>
              <span style={{ color: TEXT_MUTED }}>L <span style={{ color: '#e5534b', fontVariantNumeric: 'tabular-nums' }}>{fmt(tooltip.low!)}</span></span>
            </div>
          ) : (
            <span style={{ color: TEXT_PRIMARY, fontVariantNumeric: 'tabular-nums' }}>
              {fmt(tooltip.close)}
            </span>
          )}
        </div>
      )}

      {loading && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: `${BG_PRIMARY}cc`,
            fontSize: 12,
            color: TEXT_MUTED,
            pointerEvents: 'none',
          }}
        >
          Loading chart…
        </div>
      )}
    </div>
  )
}

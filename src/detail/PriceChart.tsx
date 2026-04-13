import { useEffect, useRef } from 'react'
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
import { ACCENT, BG_PRIMARY, BORDER, TEXT_MUTED } from '../shared/constants'

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
    fontFamily: "Inter, -apple-system, sans-serif",
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

interface PriceChartProps {
  prices: PricePoint[]
  markers: ChartMarker[]
  activeSignalId: string | null
  onMarkerClick: (signalId: string) => void
  chartType: 'candlestick' | 'line'
  loading: boolean
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

  // ── Effect 1: create chart, subscribe to click, hook up ResizeObserver ──────
  useEffect(() => {
    if (!containerRef.current) return

    const chart = createChart(containerRef.current, {
      ...CHART_OPTIONS,
      width: containerRef.current.clientWidth,
      height: containerRef.current.clientHeight,
    })
    chartRef.current = chart

    // Click handler: find the nearest ChartMarker by time and fire onMarkerClick.
    // Tolerance: 1 bar-width. For daily data that's 86400s; for intraday less.
    // Using 2 days (172800s) as a loose but safe threshold across all ranges.
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
      chart.remove()
      chartRef.current = null
      seriesRef.current = null
      markersPluginRef.current = null
      prevChartTypeRef.current = null
    }
  }, [])

  // ── Effect 2: create or swap series when chartType changes ──────────────────
  // Runs on mount (creates initial series) and when chartType prop changes.
  // Effect 1 is declared first so chartRef is guaranteed set before this runs.
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

    // Create new series
    if (chartType === 'candlestick') {
      seriesRef.current = chart.addSeries(CandlestickSeries, CANDLESTICK_OPTIONS)
    } else {
      seriesRef.current = chart.addSeries(LineSeries, LINE_OPTIONS)
    }

    // Initialise an empty markers plugin so Effect 4 can always call setMarkers
    markersPluginRef.current = createSeriesMarkers(
      seriesRef.current as Parameters<typeof createSeriesMarkers>[0],
      [],
    )

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
  // Depends on chartType so it re-runs after Effect 2 swaps the series,
  // ensuring the new plugin is populated with the current marker set.
  useEffect(() => {
    if (!markersPluginRef.current) return

    const seriesMarkers: SeriesMarker<Time>[] = markers.map((m) => {
      const isActive = m.signalId === activeSignalId
      const isNews = m.type === 'news'
      return {
        time: m.time as Time,
        position: (isNews ? 'aboveBar' : 'belowBar') as const,
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

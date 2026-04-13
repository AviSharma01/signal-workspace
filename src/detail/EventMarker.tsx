import type { NewsItem, DiscussionItem } from '../shared/types'

// App-level marker descriptor — no Lightweight Charts types here.
// PriceChart converts these to SeriesMarker<Time> internally,
// applying active/inactive colour based on activeSignalId.
export interface ChartMarker {
  time: number // Unix seconds (Lightweight Charts expects seconds, not ms)
  signalId: string
  type: 'news' | 'discussion'
}

export function buildMarkers(
  news: NewsItem[],
  discussion: DiscussionItem[],
  priceRange: { from: number; to: number }, // Unix milliseconds — matches PricePoint.timestamp
): ChartMarker[] {
  if (priceRange.from === 0 && priceRange.to === 0) return []

  const markers: ChartMarker[] = []

  for (const item of news) {
    if (item.publishedAt < priceRange.from || item.publishedAt > priceRange.to) continue
    markers.push({
      time: Math.floor(item.publishedAt / 1000),
      signalId: item.id,
      type: 'news',
    })
  }

  for (const item of discussion) {
    if (item.publishedAt < priceRange.from || item.publishedAt > priceRange.to) continue
    markers.push({
      time: Math.floor(item.publishedAt / 1000),
      signalId: item.id,
      type: 'discussion',
    })
  }

  // Lightweight Charts requires markers sorted ascending by time
  return markers.sort((a, b) => a.time - b.time)
}

import { useState, useEffect } from 'react'
import type { NewsItem, DiscussionItem } from '../shared/types'
import { apiFetch } from './api'

interface SignalsResult {
  news: NewsItem[]
  discussion: DiscussionItem[]
  loading: boolean
  error: string | null
}

interface SignalsResponse {
  news: NewsItem[]
  discussion: DiscussionItem[]
}

export function useSignals(companyId: string | null): SignalsResult {
  const [news, setNews] = useState<NewsItem[]>([])
  const [discussion, setDiscussion] = useState<DiscussionItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!companyId) return

    let cancelled = false
    setLoading(true)
    setError(null)

    apiFetch<SignalsResponse>(`/api/signals/${companyId}`)
      .then((data) => {
        if (!cancelled) {
          setNews(data.news)
          setDiscussion(data.discussion)
          setLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unknown error')
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [companyId])

  return { news, discussion, loading, error }
}

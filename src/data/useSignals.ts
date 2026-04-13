import { useReducer, useEffect, useRef } from 'react'
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

type State = SignalsResult

type Action =
  | { type: 'start' }
  | { type: 'success'; news: NewsItem[]; discussion: DiscussionItem[] }
  | { type: 'error'; error: string }

function reducer(_state: State, action: Action): State {
  switch (action.type) {
    case 'start':
      return { news: [], discussion: [], loading: true, error: null }
    case 'success':
      return { news: action.news, discussion: action.discussion, loading: false, error: null }
    case 'error':
      return { news: [], discussion: [], loading: false, error: action.error }
  }
}

const initialState: State = { news: [], discussion: [], loading: false, error: null }

export function useSignals(companyId: string | null): SignalsResult {
  const [state, dispatch] = useReducer(reducer, initialState)

  // Track fetch generation so stale responses from a previous companyId are dropped
  const generationRef = useRef(0)

  useEffect(() => {
    if (!companyId) return

    const generation = ++generationRef.current
    dispatch({ type: 'start' })

    apiFetch<SignalsResponse>(`/api/signals/${companyId}`)
      .then((data) => {
        if (generation !== generationRef.current) return
        dispatch({ type: 'success', news: data.news, discussion: data.discussion })
      })
      .catch((err: unknown) => {
        if (generation !== generationRef.current) return
        dispatch({
          type: 'error',
          error: err instanceof Error ? err.message : 'Unknown error',
        })
      })
  }, [companyId])

  return state
}

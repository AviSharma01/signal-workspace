import { useReducer, useEffect, useRef } from 'react'
import type { NewsItem, DiscussionItem } from '../shared/types'
import type { ResultStatus } from '../capabilities/types'
import { fetchSignals, type SignalsResponse } from './signals'

interface SignalsResult {
  news: NewsItem[]
  discussion: DiscussionItem[]
  classification: 'legacy_v1_context' | null
  detail: string | null
  result: ResultStatus | null
  loading: boolean
  error: string | null
}

type State = SignalsResult

type Action =
  | { type: 'start' }
  | { type: 'success'; response: SignalsResponse }
  | { type: 'error'; error: string }

function reducer(_state: State, action: Action): State {
  switch (action.type) {
    case 'start':
      return {
        news: [],
        discussion: [],
        classification: null,
        detail: null,
        result: null,
        loading: true,
        error: null,
      }
    case 'success':
      return {
        news: action.response.news,
        discussion: action.response.discussion,
        classification: action.response.classification,
        detail: action.response.detail,
        result: action.response.result,
        loading: false,
        error: null,
      }
    case 'error':
      return {
        news: [],
        discussion: [],
        classification: null,
        detail: null,
        result: null,
        loading: false,
        error: action.error,
      }
  }
}

const initialState: State = {
  news: [],
  discussion: [],
  classification: null,
  detail: null,
  result: null,
  loading: false,
  error: null,
}

export function useSignals(companyId: string | null): SignalsResult {
  const [state, dispatch] = useReducer(reducer, initialState)

  // Track fetch generation so stale responses from a previous companyId are dropped
  const generationRef = useRef(0)

  useEffect(() => {
    if (!companyId) return

    const generation = ++generationRef.current
    dispatch({ type: 'start' })

    fetchSignals(companyId)
      .then((data) => {
        if (generation !== generationRef.current) return
        dispatch({ type: 'success', response: data })
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

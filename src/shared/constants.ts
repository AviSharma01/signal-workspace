export const ACCENT = '#4d7fff'
export const BG_PRIMARY = '#0e0e10'
export const BG_SURFACE = '#17171a'
export const BORDER = '#2a2a2e'
export const TEXT_PRIMARY = '#f0f0f0'
export const TEXT_MUTED = '#6b6b7b'

// Signal blob colors
export const BLOB_NEWS = '#4d7fff'
export const BLOB_DISCUSSION = '#2da44e'
export const BLOB_RELATED = '#9f7aea'

export const ANIMATION = {
  reveal: { duration: 0.3, ease: 'easeOut' },
  hover: { duration: 0.2, ease: 'easeOut' },
  stagger: 0.05,
  pageTransition: { duration: 0.25, ease: 'easeOut' },
} as const


export function formatRelativeTime(timestamp: number): string {
  const diff = Date.now() - timestamp
  const minutes = Math.floor(diff / 60000)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

// Node dimensions — single source of truth used by node components and the force layout
export const NODE_DIMENSIONS = {
  hub: { width: 10, height: 10 },
  company: { width: 160, height: 36 },
  relatedCompany: { width: 148, height: 32 },
  news: { width: 28, height: 28 },
  discussion: { width: 28, height: 28 },
} as const satisfies Record<string, { width: number; height: number }>

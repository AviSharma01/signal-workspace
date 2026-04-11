export const ACCENT = '#4d7fff'
export const BG_PRIMARY = '#0e0e10'
export const BG_SURFACE = '#17171a'
export const BORDER = '#2a2a2e'
export const TEXT_PRIMARY = '#f0f0f0'
export const TEXT_MUTED = '#6b6b7b'

export const ANIMATION = {
  reveal: { duration: 0.3, ease: 'easeOut' },
  hover: { duration: 0.2, ease: 'easeOut' },
  stagger: 0.05,
  pageTransition: { duration: 0.25, ease: 'easeOut' },
} as const

export const SEED_COMPANIES = [
  { id: 'AAPL', name: 'Apple', sector: 'Technology' },
  { id: 'MSFT', name: 'Microsoft', sector: 'Technology' },
  { id: 'GOOGL', name: 'Alphabet', sector: 'Technology' },
  { id: 'AMZN', name: 'Amazon', sector: 'Consumer' },
  { id: 'NVDA', name: 'Nvidia', sector: 'Semiconductors' },
]

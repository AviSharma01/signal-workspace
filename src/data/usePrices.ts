import type { PricePoint } from '../shared/types'

type Range = '1D' | '1W' | '1M' | '3M'

// Stub — implemented in Phase 4 (DetailPage chart)
export function usePrices(_companyId: string, _range: Range): { prices: PricePoint[]; loading: boolean } {
  return { prices: [], loading: false }
}

import type { Company } from '../shared/types'
import { apiFetch } from './api'

export function fetchCompanies(): Promise<Company[]> {
  return apiFetch<Company[]>('/api/companies')
}

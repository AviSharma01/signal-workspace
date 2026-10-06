export type CapabilityAvailability = 'available' | 'conditional' | 'unavailable'
export type ResultState = 'empty' | 'stale' | 'partial' | 'error' | 'successful'

export interface CapabilityPrerequisite {
  code: string
  detail: string
  supported?: boolean
}

export interface CapabilityState {
  id: string
  name: string
  availability: CapabilityAvailability
  reasonCodes: string[]
  detail: string
  evaluatedAt: number
  governingVersion: string
  unmetPrerequisites: CapabilityPrerequisite[]
}

export interface ResultStatus {
  state: ResultState
  detail: string
  evaluatedAt: number
}

export interface CapabilityResponse {
  contractVersion: string
  evaluatedAt: number
  result: ResultStatus
  capabilities: CapabilityState[]
}

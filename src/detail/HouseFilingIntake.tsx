import { useEffect, useState } from 'react'
import {
  inspectOfflineHouseSample,
  offlineSampleContentUrl,
  readOfflineHouseSample,
} from '../data/houseFiling'
import type { OfflineHouseSample } from '../data/houseFiling'
import HouseFilingEvidence from './HouseFilingEvidence'

export default function HouseFilingIntake() {
  const [sample, setSample] = useState<OfflineHouseSample | null>(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let disposed = false
    readOfflineHouseSample()
      .then(response => {
        if (!disposed) setSample(response)
      })
      .catch(() => {
        if (!disposed) setError('Unable to load the offline sample status. Reload to retry.')
      })
    return () => {
      disposed = true
    }
  }, [])

  async function inspect() {
    if (pending) return
    setPending(true)
    setError(null)
    try {
      await inspectOfflineHouseSample()
      setSample(await readOfflineHouseSample())
    } catch {
      setError(
        'Sample inspection failed. No live acquisition was attempted; retry or check local sample integrity.'
      )
    } finally {
      setPending(false)
    }
  }

  return (
    <HouseFilingEvidence
      sample={sample}
      pending={pending}
      error={error}
      onInspect={inspect}
      contentUrl={offlineSampleContentUrl}
    />
  )
}

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { Finding } from '../shared/types'
import { useFindings } from '../data/useFindings'
import { apiPost } from '../data/api'
import { BORDER, TEXT_MUTED, TEXT_PRIMARY, ANIMATION } from '../shared/constants'
import FindingCard from './FindingCard'

interface ScanResult {
  scanned: number
  flagged: number
  findings: string[]
}

function deduplicateFindings(findings: Finding[]): Finding[] {
  const seen = new Set<string>()
  const result: Finding[] = []
  for (const f of findings) {
    const key = `${f.primaryDriver}||${f.hypothesis}`
    if (!seen.has(key)) {
      seen.add(key)
      result.push(f)
    }
  }
  return result
}

interface FindingsPanelProps {
  companyId: string
}

export default function FindingsPanel({ companyId }: FindingsPanelProps) {
  const { findings, loading, refetch } = useFindings(companyId)
  const [scanning, setScanning] = useState(false)
  const [scanError, setScanError] = useState<string | null>(null)
  const [priorExpanded, setPriorExpanded] = useState(false)

  const deduped = deduplicateFindings(findings)
  const latest = deduped[0] ?? null
  const prior = deduped.slice(1)

  async function handleScanNow() {
    setScanning(true)
    setScanError(null)
    try {
      await apiPost<ScanResult>('/api/scan/run')
      refetch()
    } catch (err) {
      setScanError(err instanceof Error ? err.message : 'Scan failed')
    } finally {
      setScanning(false)
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 0,
        height: '100%',
        overflowY: 'auto',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 16px',
          borderBottom: `1px solid ${BORDER}`,
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: TEXT_MUTED,
          }}
        >
          Investigation
        </span>

        {/* Scan Now — debug action */}
        <button
          onClick={handleScanNow}
          disabled={scanning}
          style={{
            fontSize: 11,
            padding: '3px 10px',
            borderRadius: 4,
            border: `1px solid ${BORDER}`,
            backgroundColor: 'transparent',
            color: scanning ? TEXT_MUTED : TEXT_PRIMARY,
            cursor: scanning ? 'default' : 'pointer',
            fontWeight: 500,
            opacity: scanning ? 0.5 : 1,
            transition: 'opacity 150ms',
          }}
        >
          {scanning ? 'Scanning…' : 'Scan now'}
        </button>
      </div>

      {/* Body */}
      <div style={{ flex: 1, padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 12, overflowY: 'auto' }}>
        {scanError && (
          <p style={{ fontSize: 12, color: '#c97a1a', margin: 0 }}>{scanError}</p>
        )}

        {loading ? (
          <p style={{ fontSize: 12, color: TEXT_MUTED, margin: 0 }}>Loading…</p>
        ) : latest ? (
          <>
            <FindingCard finding={latest} animationDelay={0} />

            {prior.length > 0 && (
              <div>
                <button
                  onClick={() => setPriorExpanded((x) => !x)}
                  style={{
                    background: 'none',
                    border: 'none',
                    padding: 0,
                    fontSize: 11,
                    color: TEXT_MUTED,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                    marginBottom: 8,
                  }}
                >
                  <span style={{ fontSize: 9 }}>{priorExpanded ? '▼' : '▶'}</span>
                  {prior.length} prior {prior.length === 1 ? 'finding' : 'findings'}
                </button>

                <AnimatePresence>
                  {priorExpanded && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={ANIMATION.reveal}
                      style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column', gap: 8 }}
                    >
                      {prior.map((f, i) => (
                        <FindingCard
                          key={f.id}
                          finding={f}
                          animationDelay={(i + 1) * 0.05}
                        />
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}
          </>
        ) : (
          <p style={{ fontSize: 12, color: TEXT_MUTED, margin: 0 }}>No findings yet.</p>
        )}
      </div>
    </div>
  )
}

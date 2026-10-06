import { Link } from 'react-router-dom'
import { useFindings } from '../data/useFindings'
import CapabilityNotice from '../capabilities/CapabilityNotice'
import FindingCard from './FindingCard'

export default function FindingsPanel({ companyId }: { companyId: string }) {
  const { findings, capability, result, loading, error } = useFindings(companyId)
  return (
    <section className="space-y-3 overflow-y-auto p-4 text-xs text-[#6b6b7b]">
      <div className="text-[#f0f0f0]">Investigation Findings</div>
      <Link to="/disclosures">Event/Watch investigations →</Link>
      <div>Literal source ticker filter; this does not establish security identity.</div>
      {capability && <CapabilityNotice capability={capability} result={result} />}
      {loading && <p>Loading Findings…</p>}
      {error && <p className="text-[#e5534b]">{error}</p>}
      {!loading && !error && capability && findings.length === 0 && (
        <p>No validated Findings for this source ticker.</p>
      )}
      {findings.map(finding => (
        <FindingCard key={finding.runId} finding={finding} />
      ))}
    </section>
  )
}

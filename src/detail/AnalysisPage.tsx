import { Link } from 'react-router-dom'
import { useAnalysis } from '../data/useAnalysis'
import AnalysisResults from './AnalysisResults'
import CohortResults from './CohortResults'

export default function AnalysisPage() {
  const { response, loading, error, cohortResponse, cohortLoading, cohortError } = useAnalysis()
  return (
    <main className="h-screen overflow-y-auto bg-[#0e0e10] p-6 text-[#f0f0f0]">
      <div className="mx-auto max-w-6xl">
        <Link to="/disclosures" className="text-xs text-[#8b8b98]">
          ← Events & evidence
        </Link>
        <h1 className="text-xl">Analysis outcomes</h1>
        {loading && <p>Loading Analysis…</p>}
        {error && <p className="text-[#e5534b]">{error}</p>}
        {response && <AnalysisResults response={response} />}
        {cohortLoading && <p>Loading cohort Analysis…</p>}
        {cohortError && <p className="text-[#e5534b]">{cohortError}</p>}
        {cohortResponse && <CohortResults response={cohortResponse} />}
      </div>
    </main>
  )
}

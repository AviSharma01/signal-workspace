import { BrowserRouter, Routes, Route, useLocation, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import GraphView from './graph/GraphView'
import SidePanel from './panel/SidePanel'
import DetailPage from './detail/DetailPage'
import DisclosureEvidencePage from './detail/DisclosureEvidencePage'
import AnalysisPage from './detail/AnalysisPage'
import { ANIMATION, BG_PRIMARY } from './shared/constants'

const pageFade = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: ANIMATION.pageTransition,
}

function GraphLayout() {
  const navigate = useNavigate()

  return (
    <motion.div {...pageFade} style={{ position: 'relative', width: '100%', height: '100vh' }}>
      <GraphView />
      <SidePanel />
      <button
        onClick={() => navigate('/disclosures')}
        className="absolute bottom-4 left-4 cursor-pointer rounded-sm border border-[#2a2a2e] bg-[#17171a] px-2.5 py-1.5 text-[11px] text-[#6b6b7b]"
      >
        Watch Events & evidence
      </button>
    </motion.div>
  )
}

function AnimatedRoutes() {
  const location = useLocation()

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<GraphLayout />} />
        <Route
          path="/company/:companyId"
          element={
            <motion.div {...pageFade} style={{ width: '100%', height: '100vh' }}>
              <DetailPage />
            </motion.div>
          }
        />
        <Route path="/disclosures" element={<DisclosureEvidencePage />} />
        <Route path="/analysis" element={<AnalysisPage />} />
      </Routes>
    </AnimatePresence>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div
        style={{
          width: '100%',
          height: '100vh',
          backgroundColor: BG_PRIMARY,
          fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
          overflow: 'hidden',
        }}
      >
        <AnimatedRoutes />
      </div>
    </BrowserRouter>
  )
}

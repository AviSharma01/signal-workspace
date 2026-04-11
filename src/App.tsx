import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import GraphView from './graph/GraphView'
import SidePanel from './panel/SidePanel'
import DetailPage from './detail/DetailPage'
import { BG_PRIMARY, ANIMATION } from './shared/constants'

const pageFade = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: ANIMATION.pageTransition,
}

function GraphLayout() {
  return (
    <motion.div
      {...pageFade}
      style={{ position: 'relative', width: '100%', height: '100vh' }}
    >
      <GraphView />
      <SidePanel />
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

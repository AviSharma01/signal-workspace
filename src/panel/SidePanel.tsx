import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useUiStore } from '../store/uiStore'
import { useGraphStore } from '../store/graphStore'
import { ACCENT, ANIMATION, BG_SURFACE, BORDER, TEXT_MUTED, TEXT_PRIMARY, formatRelativeTime } from '../shared/constants'
import CompanyPanelContent from './CompanyPanelContent'

export default function SidePanel() {
  const sidePanelOpen = useUiStore((s) => s.sidePanelOpen)
  const selectedNodeId = useUiStore((s) => s.selectedNodeId)
  const closePanel = useUiStore((s) => s.closePanel)
  const nodes = useGraphStore((s) => s.nodes)

  const selectedNode = nodes.find((n) => n.id === selectedNodeId)

  // If the selected node was removed (e.g. company collapsed), close the panel
  useEffect(() => {
    if (selectedNodeId && !selectedNode) {
      closePanel()
    }
  }, [selectedNodeId, selectedNode, closePanel])

  // Normalise news and discussion into one display shape
  const signalContent = (() => {
    if (!selectedNode) return null
    if (selectedNode.type === 'news') {
      const { item } = selectedNode.data
      return {
        type: 'News' as const,
        headline: item.headline,
        summary: item.summary,
        source: item.source,
        publishedAt: item.publishedAt,
        companyId: item.companyId,
        url: item.url,
      }
    }
    if (selectedNode.type === 'discussion') {
      const { item } = selectedNode.data
      return {
        type: 'Discussion' as const,
        headline: item.title,
        summary: item.summary,
        source: item.source,
        publishedAt: item.publishedAt,
        companyId: item.companyId,
        url: item.url,
      }
    }
    return null
  })()

  const isCompany = selectedNode?.type === 'company'
  const panelVisible = sidePanelOpen && (isCompany || signalContent !== null)

  const panelShell = (children: React.ReactNode, label: string) => (
    <motion.aside
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      transition={ANIMATION.reveal}
      style={{
        position: 'absolute',
        top: 0,
        right: 0,
        width: 340,
        height: '100%',
        backgroundColor: BG_SURFACE,
        borderLeft: `1px solid ${BORDER}`,
        display: 'flex',
        flexDirection: 'column',
        zIndex: 10,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 16px',
          borderBottom: `1px solid ${BORDER}`,
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontSize: 11,
            color: TEXT_MUTED,
            fontWeight: 500,
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
          }}
        >
          {label}
        </span>
        <button
          onClick={closePanel}
          aria-label="Close panel"
          style={{
            background: 'none',
            border: 'none',
            color: TEXT_MUTED,
            fontSize: 18,
            lineHeight: 1,
            cursor: 'pointer',
            padding: '2px 4px',
          }}
        >
          ×
        </button>
      </div>
      {children}
    </motion.aside>
  )

  return (
    <AnimatePresence>
      {panelVisible && (
        isCompany && selectedNodeId ? (
          panelShell(<CompanyPanelContent companyId={selectedNodeId} />, 'Company')
        ) : signalContent ? (
          panelShell(
            <>
              {/* Body */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '20px 16px' }}>
                <p style={{ fontSize: 11, color: TEXT_MUTED, margin: '0 0 10px' }}>
                  {signalContent.source} · {formatRelativeTime(signalContent.publishedAt)}
                  {signalContent.url && (
                    <a
                      href={signalContent.url}
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: TEXT_MUTED, marginLeft: 6, textDecoration: 'none', opacity: 0.7 }}
                    >
                      ↗
                    </a>
                  )}
                </p>
                <h2
                  style={{
                    fontSize: 15,
                    color: TEXT_PRIMARY,
                    fontWeight: 600,
                    lineHeight: 1.45,
                    margin: '0 0 12px',
                  }}
                >
                  {signalContent.headline}
                </h2>
                <p
                  style={{
                    fontSize: 13,
                    color: TEXT_MUTED,
                    lineHeight: 1.65,
                    margin: 0,
                  }}
                >
                  {signalContent.summary}
                </p>
              </div>
              {/* Footer */}
              <div
                style={{
                  padding: '14px 16px',
                  borderTop: `1px solid ${BORDER}`,
                  flexShrink: 0,
                }}
              >
                <Link
                  to={`/company/${signalContent.companyId}`}
                  style={{
                    fontSize: 13,
                    color: ACCENT,
                    textDecoration: 'none',
                    fontWeight: 500,
                  }}
                >
                  View details →
                </Link>
              </div>
            </>,
            signalContent.type,
          )
        ) : null
      )}
    </AnimatePresence>
  )
}

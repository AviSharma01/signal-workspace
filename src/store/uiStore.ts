import { create } from 'zustand'

interface UiState {
  sidePanelOpen: boolean
  selectedNodeId: string | null
  openPanel: (nodeId: string) => void
  closePanel: () => void
}

export const useUiStore = create<UiState>((set) => ({
  sidePanelOpen: false,
  selectedNodeId: null,

  openPanel(nodeId) {
    set({ sidePanelOpen: true, selectedNodeId: nodeId })
  },

  closePanel() {
    set({ sidePanelOpen: false, selectedNodeId: null })
  },
}))

import { useState, useCallback, useEffect } from 'react'

export interface ChatLayoutState {
  // Sidebar states
  sidebarCollapsed: boolean
  chatHistoryCollapsed: boolean
  queryDetailsCollapsed: boolean
  
  // Layout preferences
  chatHistoryWidth: number
  queryDetailsWidth: number
  
  // UI states
  showDatasetSelector: boolean
  compactMode: boolean
}

const DEFAULT_CHAT_HISTORY_WIDTH = 320
const DEFAULT_QUERY_DETAILS_WIDTH = 384
const COLLAPSED_WIDTH = 48

const LAYOUT_STORAGE_KEY = 'chat-layout-preferences'

export function useChatLayout() {
  const [state, setState] = useState<ChatLayoutState>(() => {
    // Load from localStorage
    const saved = localStorage.getItem(LAYOUT_STORAGE_KEY)
    if (saved) {
      try {
        return { ...getDefaultState(), ...JSON.parse(saved) }
      } catch {
        return getDefaultState()
      }
    }
    return getDefaultState()
  })

  // Save to localStorage when state changes
  useEffect(() => {
    localStorage.setItem(LAYOUT_STORAGE_KEY, JSON.stringify(state))
  }, [state])

  const toggleSidebar = useCallback(() => {
    setState(prev => ({
      ...prev,
      sidebarCollapsed: !prev.sidebarCollapsed
    }))
  }, [])

  const toggleChatHistory = useCallback(() => {
    setState(prev => ({
      ...prev,
      chatHistoryCollapsed: !prev.chatHistoryCollapsed
    }))
  }, [])

  const toggleQueryDetails = useCallback(() => {
    setState(prev => ({
      ...prev,
      queryDetailsCollapsed: !prev.queryDetailsCollapsed
    }))
  }, [])

  const toggleDatasetSelector = useCallback(() => {
    setState(prev => ({
      ...prev,
      showDatasetSelector: !prev.showDatasetSelector
    }))
  }, [])

  const enterCompactMode = useCallback(() => {
    setState(prev => ({
      ...prev,
      compactMode: true,
      chatHistoryCollapsed: true,
      queryDetailsCollapsed: true,
      showDatasetSelector: false
    }))
  }, [])

  const exitCompactMode = useCallback(() => {
    setState(prev => ({
      ...prev,
      compactMode: false,
      chatHistoryCollapsed: false,
      queryDetailsCollapsed: false,
      showDatasetSelector: true
    }))
  }, [])

  const resetLayout = useCallback(() => {
    setState(getDefaultState())
  }, [])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + Shift + shortcuts
      if ((e.ctrlKey || e.metaKey) && e.shiftKey) {
        switch (e.key) {
          case 'H':
            e.preventDefault()
            toggleChatHistory()
            break
          case 'D':
            e.preventDefault()
            toggleQueryDetails()
            break
          case 'B':
            e.preventDefault()
            toggleSidebar()
            break
          case 'F':
            e.preventDefault()
            if (state.compactMode) {
              exitCompactMode()
            } else {
              enterCompactMode()
            }
            break
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [toggleChatHistory, toggleQueryDetails, toggleSidebar, enterCompactMode, exitCompactMode, state.compactMode])

  // Calculate actual widths
  const getActualWidths = useCallback(() => {
    return {
      chatHistoryWidth: state.chatHistoryCollapsed ? COLLAPSED_WIDTH : state.chatHistoryWidth,
      queryDetailsWidth: state.queryDetailsCollapsed ? COLLAPSED_WIDTH : state.queryDetailsWidth,
      sidebarWidth: state.sidebarCollapsed ? 64 : 256
    }
  }, [state])

  return {
    state,
    toggleSidebar,
    toggleChatHistory,
    toggleQueryDetails,
    toggleDatasetSelector,
    enterCompactMode,
    exitCompactMode,
    resetLayout,
    getActualWidths
  }
}

function getDefaultState(): ChatLayoutState {
  return {
    sidebarCollapsed: false,
    chatHistoryCollapsed: false,
    queryDetailsCollapsed: false,
    chatHistoryWidth: DEFAULT_CHAT_HISTORY_WIDTH,
    queryDetailsWidth: DEFAULT_QUERY_DETAILS_WIDTH,
    showDatasetSelector: true,
    compactMode: false
  }
}
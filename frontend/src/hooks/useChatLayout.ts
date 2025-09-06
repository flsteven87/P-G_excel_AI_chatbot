import { useState, useCallback, useEffect } from 'react'

export interface ChatLayoutState {
  // Sidebar states
  sidebarCollapsed: boolean
  chatHistoryCollapsed: boolean
  queryDetailsCollapsed: boolean
  
  // Layout preferences (in percentages for ResizablePanel)
  chatHistorySize: number
  queryDetailsSize: number
  centerPanelSize: number
  
  // Legacy pixel-based widths (for backwards compatibility)
  chatHistoryWidth: number
  queryDetailsWidth: number
  
  // UI states
  showDatasetSelector: boolean
  compactMode: boolean
  
  // Responsive design
  isMobile: boolean
}

const DEFAULT_CHAT_HISTORY_WIDTH = 320
const DEFAULT_QUERY_DETAILS_WIDTH = 384
const COLLAPSED_WIDTH = 48
const MIN_PANEL_WIDTH = 200
const MAX_PANEL_WIDTH = 600

// Panel size percentages (for ResizablePanel)
const DEFAULT_CHAT_HISTORY_SIZE = 25
const DEFAULT_QUERY_DETAILS_SIZE = 25
const DEFAULT_CENTER_PANEL_SIZE = 50

const LAYOUT_STORAGE_KEY = 'chat-layout-preferences'

// Responsive breakpoints
const MOBILE_BREAKPOINT = 768

export function useChatLayout() {
  const [state, setState] = useState<ChatLayoutState>(() => {
    // Load from localStorage
    const saved = localStorage.getItem(LAYOUT_STORAGE_KEY)
    const defaultState = getDefaultState()
    if (saved) {
      try {
        return { ...defaultState, ...JSON.parse(saved) }
      } catch {
        return defaultState
      }
    }
    return defaultState
  })

  // Handle responsive design
  useEffect(() => {
    const handleResize = () => {
      const isMobile = window.innerWidth < MOBILE_BREAKPOINT
      const shouldEnterCompactMode = isMobile && !state.compactMode
      
      setState(prev => ({
        ...prev,
        isMobile,
        // Auto-enter compact mode on mobile
        ...(shouldEnterCompactMode && {
          compactMode: true,
          chatHistoryCollapsed: true,
          queryDetailsCollapsed: true,
          showDatasetSelector: false
        })
      }))
    }

    // Initial check
    handleResize()
    
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [state.compactMode])

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

  // Resize panel functions (legacy pixel-based)
  const resizeChatHistory = useCallback((delta: number) => {
    setState(prev => ({
      ...prev,
      chatHistoryWidth: Math.max(
        MIN_PANEL_WIDTH,
        Math.min(MAX_PANEL_WIDTH, prev.chatHistoryWidth + delta)
      )
    }))
  }, [])

  const resizeQueryDetails = useCallback((delta: number) => {
    setState(prev => ({
      ...prev,
      queryDetailsWidth: Math.max(
        MIN_PANEL_WIDTH,
        Math.min(MAX_PANEL_WIDTH, prev.queryDetailsWidth - delta) // Reverse delta for right panel
      )
    }))
  }, [])

  // Panel size functions (percentage-based for ResizablePanel)
  const updatePanelSizes = useCallback((leftSize: number, centerSize: number, rightSize: number) => {
    setState(prev => ({
      ...prev,
      chatHistorySize: Math.max(10, Math.min(50, leftSize)),
      centerPanelSize: Math.max(30, Math.min(80, centerSize)),
      queryDetailsSize: Math.max(10, Math.min(50, rightSize))
    }))
  }, [])

  const resetPanelSizes = useCallback(() => {
    setState(prev => ({
      ...prev,
      chatHistorySize: DEFAULT_CHAT_HISTORY_SIZE,
      centerPanelSize: DEFAULT_CENTER_PANEL_SIZE,
      queryDetailsSize: DEFAULT_QUERY_DETAILS_SIZE
    }))
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
    resizeChatHistory,
    resizeQueryDetails,
    updatePanelSizes,
    resetPanelSizes,
    getActualWidths
  }
}

function getDefaultState(): ChatLayoutState {
  const isMobile = typeof window !== 'undefined' && window.innerWidth < MOBILE_BREAKPOINT
  
  return {
    sidebarCollapsed: false,
    chatHistoryCollapsed: isMobile,
    queryDetailsCollapsed: isMobile,
    chatHistorySize: DEFAULT_CHAT_HISTORY_SIZE,
    queryDetailsSize: DEFAULT_QUERY_DETAILS_SIZE,
    centerPanelSize: DEFAULT_CENTER_PANEL_SIZE,
    chatHistoryWidth: DEFAULT_CHAT_HISTORY_WIDTH,
    queryDetailsWidth: DEFAULT_QUERY_DETAILS_WIDTH,
    showDatasetSelector: !isMobile,
    compactMode: isMobile,
    isMobile
  }
}
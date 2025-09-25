import { useState, useCallback, useRef } from 'react'
import { ChatSession, ChatMessage, Dataset } from '@/types/chat'

export interface ChatState {
  sessions: ChatSession[]
  currentSession: string | null
  messages: Record<string, ChatMessage[]>
  availableDatasets: Dataset[]
  selectedDataset: string | null
  isProcessing: boolean
  error: string | null
}

// Real-time sessions and messages loaded from API
const INITIAL_SESSIONS: ChatSession[] = []
const INITIAL_MESSAGES: Record<string, ChatMessage[]> = {}

const SUGGESTED_QUESTIONS = [
  '顯示庫存量前10的產品',
  '哪些產品的庫存低於安全庫存？',
  '按品牌統計總庫存量',
  '最近一週庫存變化趨勢如何？',
  '哪些倉庫的使用率最高？',
  '即將過期的產品有哪些？',
  '銷售額最高的產品類別是什麼？',
  '庫存周轉率最低的產品',
  '各地區的庫存分布情況',
  '缺貨風險最高的 SKU'
]

export function useChat() {
  const [state, setState] = useState<ChatState>({
    sessions: INITIAL_SESSIONS,
    currentSession: null,
    messages: INITIAL_MESSAGES,
    availableDatasets: [],
    selectedDataset: null,
    isProcessing: false,
    error: null
  })

  const messageIdRef = useRef(0)

  const generateMessageId = () => `msg-${++messageIdRef.current}-${Date.now()}`

  const createNewSession = useCallback(() => {
    const newSession: ChatSession = {
      id: `session-${Date.now()}`,
      title: '新的對話',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      message_count: 0,
      is_active: true
    }

    setState(prev => ({
      ...prev,
      sessions: [newSession, ...prev.sessions],
      currentSession: newSession.id,
      messages: { ...prev.messages, [newSession.id]: [] }
    }))

    return newSession.id
  }, [])

  const selectSession = useCallback((sessionId: string) => {
    setState(prev => ({
      ...prev,
      currentSession: sessionId
    }))
  }, [])

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return

    const sessionId = state.currentSession || createNewSession()
    
    // 創建用戶訊息
    const userMessage: ChatMessage = {
      id: generateMessageId(),
      session_id: sessionId,
      type: 'user',
      content: content.trim(),
      timestamp: new Date()
    }

    // 添加用戶訊息到狀態
    setState(prev => ({
      ...prev,
      currentSession: sessionId,
      messages: {
        ...prev.messages,
        [sessionId]: [...(prev.messages[sessionId] || []), userMessage]
      },
      isProcessing: true,
      error: null
    }))

    try {
      // 調用後端 API
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8001'
      const response = await fetch(`${apiUrl}/api/v1/chat/vanna/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: content.trim() })
      })

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`)
      }

      const result = await response.json()
      
      // 創建 AI 回應訊息
      const aiResponse: ChatMessage = {
        id: generateMessageId(),
        session_id: sessionId,
        type: 'assistant',
        content: `我為您查詢了相關資料，找到了 ${result.row_count} 筆結果。`,
        timestamp: new Date(),
        sql: result.sql,
        results: {
          data: result.results,
          columns: result.columns,
          row_count: result.row_count,
          execution_time_ms: result.processing_time_ms,
          chart_type: result.row_count > 1 ? 'table' : 'bar'
        },
        status: 'completed',
        metadata: {
          processing_time: result.processing_time_ms,
          row_count: result.row_count,
          chart_suggestion: `建議使用${result.row_count > 5 ? '表格' : '圖表'}顯示`,
          suggested_visualizations: result.row_count > 0 ? [
            '數據已成功查詢',
            '可以進行進一步的篩選和分析'
          ] : ['查詢無結果，請嘗試調整查詢條件']
        }
      }
      
      setState(prev => ({
        ...prev,
        messages: {
          ...prev.messages,
          [sessionId]: [...prev.messages[sessionId], aiResponse]
        },
        isProcessing: false,
        sessions: prev.sessions.map(s => 
          s.id === sessionId 
            ? { ...s, message_count: s.message_count + 2, updated_at: new Date().toISOString() }
            : s
        )
      }))

    } catch (error) {
      console.error('Failed to send message:', error)
      
      // 創建錯誤訊息
      const errorResponse: ChatMessage = {
        id: generateMessageId(),
        session_id: sessionId,
        type: 'error',
        content: '抱歉，處理您的問題時發生錯誤。這可能是網路連線問題或伺服器暫時無法回應。請稍後再試。',
        timestamp: new Date(),
        status: 'failed'
      }
      
      setState(prev => ({
        ...prev,
        messages: {
          ...prev.messages,
          [sessionId]: [...prev.messages[sessionId], errorResponse]
        },
        isProcessing: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      }))
    }

  }, [state.currentSession, createNewSession])

  const retryMessage = useCallback(async (messageId: string) => {
    // 找到失敗的訊息並重新生成回應
    const sessionId = state.currentSession
    if (!sessionId) return

    const messages = state.messages[sessionId] || []
    const messageIndex = messages.findIndex(m => m.id === messageId)
    const message = messages[messageIndex]
    
    if (message && message.type === 'assistant' && message.status === 'failed') {
      // 重新生成回應
      setState(prev => ({
        ...prev,
        isProcessing: true
      }))

      setTimeout(() => {
        // TODO: Implement real retry logic by calling API again
        setState(prev => ({
          ...prev,
          isProcessing: false
        }))
      }, 1500)
    }
  }, [state.currentSession, state.messages])

  const deleteSession = useCallback((sessionId: string) => {
    setState(prev => ({
      ...prev,
      sessions: prev.sessions.filter(s => s.id !== sessionId),
      messages: Object.fromEntries(
        Object.entries(prev.messages).filter(([id]) => id !== sessionId)
      ),
      currentSession: prev.currentSession === sessionId ? null : prev.currentSession
    }))
  }, [])

  const exportSession = useCallback(async (sessionId: string) => {
    const session = state.sessions.find(s => s.id === sessionId)
    const messages = state.messages[sessionId] || []
    
    const exportData = {
      session,
      messages,
      exported_at: new Date().toISOString()
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })
    
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chat_session_${sessionId}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [state.sessions, state.messages])

  const getSuggestedQuestions = useCallback(() => {
    return SUGGESTED_QUESTIONS
  }, [])

  const getCurrentMessages = useCallback(() => {
    return state.currentSession ? (state.messages[state.currentSession] || []) : []
  }, [state.currentSession, state.messages])

  return {
    state,
    currentMessages: getCurrentMessages(),
    suggestedQuestions: getSuggestedQuestions(),
    createNewSession,
    selectSession,
    sendMessage,
    retryMessage,
    deleteSession,
    exportSession
  }
}
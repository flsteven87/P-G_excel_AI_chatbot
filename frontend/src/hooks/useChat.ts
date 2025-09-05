import { useState, useCallback, useRef } from 'react'
import { ChatSession, ChatMessage, QueryResult, Dataset } from '@/types/chat'

export interface ChatState {
  sessions: ChatSession[]
  currentSession: string | null
  messages: Record<string, ChatMessage[]>
  availableDatasets: Dataset[]
  selectedDataset: string | null
  isProcessing: boolean
  error: string | null
}

// Mock data for demonstration
const MOCK_SESSIONS: ChatSession[] = [
  {
    id: 'session-1',
    title: '庫存分析對話',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    message_count: 8,
    is_active: true
  },
  {
    id: 'session-2', 
    title: '銷售趨勢查詢',
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
    message_count: 12,
    is_active: true
  },
  {
    id: 'session-3',
    title: '品牌績效分析', 
    created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    message_count: 6,
    is_active: true
  }
]

const MOCK_MESSAGES: Record<string, ChatMessage[]> = {
  'session-1': [
    {
      id: 'msg-1',
      session_id: 'session-1',
      type: 'user',
      content: '顯示庫存量前10的產品',
      timestamp: new Date(Date.now() - 60 * 60 * 1000)
    },
    {
      id: 'msg-2',
      session_id: 'session-1', 
      type: 'assistant',
      content: '我為您查詢了庫存量前10的產品，以下是結果：',
      timestamp: new Date(Date.now() - 59 * 60 * 1000),
      sql: `SELECT 
  dp.sku, 
  dp.descr, 
  dp.brand_name, 
  SUM(f.qty) as total_qty
FROM vw_inventory_latest f
JOIN dim_product dp ON dp.product_id = f.product_id
GROUP BY dp.sku, dp.descr, dp.brand_name
ORDER BY total_qty DESC
LIMIT 10;`,
      results: {
        data: [
          { sku: 'TW001', descr: '產品 A', brand_name: 'Brand A', total_qty: 15420 },
          { sku: 'TW002', descr: '產品 B', brand_name: 'Brand B', total_qty: 12850 },
          { sku: 'TW003', descr: '產品 C', brand_name: 'Brand A', total_qty: 9760 },
          { sku: 'TW004', descr: '產品 D', brand_name: 'Brand C', total_qty: 8340 },
          { sku: 'TW005', descr: '產品 E', brand_name: 'Brand B', total_qty: 7220 }
        ],
        columns: ['sku', 'descr', 'brand_name', 'total_qty'],
        row_count: 10,
        execution_time_ms: 245,
        chart_type: 'bar'
      },
      status: 'completed',
      metadata: {
        processing_time: 1240,
        row_count: 10,
        chart_suggestion: '建議使用柱狀圖顯示數量比較',
        suggested_visualizations: ['柱狀圖適合比較不同產品的庫存量', '可以按品牌分組顯示']
      }
    }
  ]
}

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
    sessions: MOCK_SESSIONS,
    currentSession: null,
    messages: MOCK_MESSAGES,
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

    // 模擬 AI 處理時間 (1-3秒)
    const processingTime = Math.random() * 2000 + 1000
    
    setTimeout(async () => {
      // 生成模擬的 AI 回應
      const aiResponse = generateMockAIResponse(content, sessionId)
      
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
    }, processingTime)

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
        const newResponse = generateMockAIResponse(
          messages[messageIndex - 1]?.content || '重試查詢', 
          sessionId
        )

        setState(prev => ({
          ...prev,
          messages: {
            ...prev.messages,
            [sessionId]: prev.messages[sessionId].map((m, idx) =>
              idx === messageIndex ? newResponse : m
            )
          },
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

function generateMockAIResponse(userQuestion: string, sessionId: string): ChatMessage {
  const question = userQuestion.toLowerCase()
  const responseId = `msg-ai-${Date.now()}`
  
  // 根據問題類型生成不同的模擬回應
  let content = ''
  let sql = ''
  let results: QueryResult | undefined
  let status: 'completed' | 'failed' = 'completed'

  if (question.includes('前') && (question.includes('10') || question.includes('十'))) {
    content = '我為您查詢了庫存量前10的產品，以下是結果：'
    sql = `SELECT 
  dp.sku, 
  dp.descr, 
  dp.brand_name, 
  SUM(f.qty) as total_qty
FROM vw_inventory_latest f
JOIN dim_product dp ON dp.product_id = f.product_id
GROUP BY dp.sku, dp.descr, dp.brand_name
ORDER BY total_qty DESC
LIMIT 10;`
    
    results = {
      data: [
        { sku: 'TW001', descr: '高級筆記本電腦', brand_name: 'TechBrand', total_qty: 15420 },
        { sku: 'TW002', descr: '無線藍牙耳機', brand_name: 'AudioMax', total_qty: 12850 },
        { sku: 'TW003', descr: '智慧手機保護殼', brand_name: 'TechBrand', total_qty: 9760 },
        { sku: 'TW004', descr: '行動電源', brand_name: 'PowerTech', total_qty: 8340 },
        { sku: 'TW005', descr: '藍牙滑鼠', brand_name: 'CompuGear', total_qty: 7220 }
      ],
      columns: ['sku', 'descr', 'brand_name', 'total_qty'],
      row_count: 10,
      execution_time_ms: 245,
      chart_type: 'bar'
    }
  } else if (question.includes('品牌') && question.includes('統計')) {
    content = '以下是按品牌統計的總庫存量：'
    sql = `SELECT 
  dp.brand_name,
  COUNT(DISTINCT dp.sku) as product_count,
  SUM(f.qty) as total_qty
FROM vw_inventory_latest f
JOIN dim_product dp ON dp.product_id = f.product_id
GROUP BY dp.brand_name
ORDER BY total_qty DESC;`
    
    results = {
      data: [
        { brand_name: 'TechBrand', product_count: 45, total_qty: 89420 },
        { brand_name: 'AudioMax', product_count: 23, total_qty: 67340 },
        { brand_name: 'PowerTech', product_count: 18, total_qty: 43220 },
        { brand_name: 'CompuGear', product_count: 31, total_qty: 38940 }
      ],
      columns: ['brand_name', 'product_count', 'total_qty'],
      row_count: 4,
      execution_time_ms: 189,
      chart_type: 'pie'
    }
  } else if (question.includes('低於') || question.includes('不足')) {
    content = '找到了庫存不足的產品清單：'
    sql = `SELECT 
  dp.sku,
  dp.descr,
  dp.brand_name,
  SUM(f.qty) as current_qty
FROM vw_inventory_latest f
JOIN dim_product dp ON dp.product_id = f.product_id
GROUP BY dp.sku, dp.descr, dp.brand_name
HAVING SUM(f.qty) < 100
ORDER BY current_qty ASC;`
    
    results = {
      data: [
        { sku: 'TW099', descr: '限量版鍵盤', brand_name: 'CompuGear', current_qty: 23 },
        { sku: 'TW087', descr: '專業攝影腳架', brand_name: 'PhotoPro', current_qty: 45 },
        { sku: 'TW156', descr: '無線充電板', brand_name: 'PowerTech', current_qty: 67 },
        { sku: 'TW203', descr: 'USB-C 集線器', brand_name: 'TechBrand', current_qty: 89 }
      ],
      columns: ['sku', 'descr', 'brand_name', 'current_qty'],
      row_count: 4,
      execution_time_ms: 178,
      chart_type: 'bar'
    }
  } else {
    content = '我理解您的問題。讓我查詢相關數據：'
    sql = `SELECT COUNT(*) as total_records 
FROM vw_inventory_latest 
LIMIT 1000;`
    
    results = {
      data: [{ total_records: 45678 }],
      columns: ['total_records'],
      row_count: 1,
      execution_time_ms: 89,
      chart_type: 'table'
    }
  }

  // 隨機決定是否失敗 (10% 機率)
  if (Math.random() < 0.1) {
    status = 'failed'
    content = '抱歉，查詢過程中遇到了問題。這可能是因為資料庫連線問題或查詢語法需要調整。'
    results = undefined
  }

  return {
    id: responseId,
    session_id: sessionId,
    type: 'assistant' as const,
    content,
    timestamp: new Date(),
    sql,
    results,
    status,
    metadata: {
      processing_time: Math.floor(Math.random() * 2000) + 500,
      row_count: results?.row_count || 0,
      chart_suggestion: results?.chart_type ? `建議使用${getChartTypeLabel(results.chart_type)}` : undefined,
      suggested_visualizations: results?.data && results.data.length > 0 ? [
        '數據量適中，適合製作視覺化圖表',
        '建議關注數值差異較大的項目'
      ] : undefined
    }
  }
}

function getChartTypeLabel(chartType: string): string {
  switch (chartType) {
    case 'bar': return '柱狀圖'
    case 'line': return '折線圖' 
    case 'pie': return '圓餅圖'
    case 'table': return '數據表格'
    default: return '圖表'
  }
}
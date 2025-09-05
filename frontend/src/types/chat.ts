export interface ChatSession {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  is_active: boolean
}

export interface ChatMessage {
  id: string
  session_id: string
  type: 'user' | 'assistant' | 'system' | 'error'
  content: string
  timestamp: Date
  sql?: string
  results?: QueryResult
  status?: 'processing' | 'completed' | 'failed'
  metadata?: QueryMetadata
}

export interface QueryResult {
  data: Record<string, unknown>[]
  columns: string[]
  row_count: number
  execution_time_ms: number
  chart_type?: 'table' | 'bar' | 'line' | 'pie'
}

export interface QueryMetadata {
  processing_time: number
  row_count: number
  chart_suggestion?: string
  complexity_score?: number
  suggested_visualizations?: string[]
}

export interface SmartSuggestions {
  dataStructureSuggestions: string[]
  historicalSuggestions: string[]
  contextualSuggestions: string[]
}

export interface ConversationContext {
  previousQueries: Array<{
    question: string
    sql: string
    results: QueryResult
  }>
  followUpQuestions: string[]
  contextPrompt: string
}

export interface Dataset {
  id: string
  name: string
  description: string
  table_count: number
  last_updated: string
  status: 'ready' | 'loading' | 'error'
}
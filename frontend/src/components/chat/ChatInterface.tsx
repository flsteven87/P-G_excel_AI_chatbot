import React, { useState, useRef, useEffect } from 'react'
import { 
  Send, 
  RotateCcw, 
  Copy, 
  TrendingUp, 
  Loader2,
  Maximize2,
  Minimize2,
  Keyboard
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { ChatMessage, QueryResult, QueryMetadata } from '@/types/chat'
import { cn } from '@/lib/utils'

interface ChatInterfaceProps {
  messages: ChatMessage[]
  onSendMessage: (content: string) => Promise<void>
  onRetry: (messageId: string) => void
  suggestedQuestions: string[]
  isProcessing?: boolean
  isFullscreen?: boolean
  onToggleFullscreen?: () => void
  className?: string
}

export function ChatInterface({
  messages,
  onSendMessage,
  onRetry,
  suggestedQuestions,
  isProcessing = false,
  isFullscreen = false,
  onToggleFullscreen,
  className
}: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || isProcessing) return

    const question = inputValue.trim()
    setInputValue('')
    setShowSuggestions(false)
    
    await onSendMessage(question)
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion)
    setShowSuggestions(false)
    textareaRef.current?.focus()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
    
    // Escape to hide suggestions
    if (e.key === 'Escape') {
      setShowSuggestions(false)
      setShowKeyboardHelp(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className={cn('flex flex-col h-full relative', className)}>
      {/* Header Controls */}
      {!isFullscreen && (
        <div className="flex items-center justify-between p-4 border-b border-border bg-background/95 backdrop-blur">
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-semibold">AI 對話助手</h2>
            {messages.length > 0 && (
              <Badge variant="outline" className="text-xs">
                {messages.length} 則訊息
              </Badge>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowKeyboardHelp(!showKeyboardHelp)}
              className="h-8 w-8 p-0"
              title="鍵盤快捷鍵"
            >
              <Keyboard className="h-4 w-4" />
            </Button>
            
            {onToggleFullscreen && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onToggleFullscreen}
                className="h-8 w-8 p-0"
                title={isFullscreen ? '退出全螢幕' : '全螢幕模式'}
              >
                {isFullscreen ? (
                  <Minimize2 className="h-4 w-4" />
                ) : (
                  <Maximize2 className="h-4 w-4" />
                )}
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Keyboard Help */}
      {showKeyboardHelp && (
        <div className="absolute top-16 right-4 z-10 bg-popover border border-border rounded-lg shadow-lg p-4 w-64">
          <h3 className="font-medium mb-3">鍵盤快捷鍵</h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span>發送訊息</span>
              <Badge variant="outline">Enter</Badge>
            </div>
            <div className="flex justify-between">
              <span>換行</span>
              <Badge variant="outline">Shift+Enter</Badge>
            </div>
            <div className="flex justify-between">
              <span>收合歷史</span>
              <Badge variant="outline">⌘+Shift+H</Badge>
            </div>
            <div className="flex justify-between">
              <span>收合結果</span>
              <Badge variant="outline">⌘+Shift+D</Badge>
            </div>
            <div className="flex justify-between">
              <span>專注模式</span>
              <Badge variant="outline">⌘+Shift+F</Badge>
            </div>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className={cn(
        'flex-1 overflow-y-auto space-y-4',
        isFullscreen ? 'p-8' : 'p-4'
      )}>
        {messages.length === 0 ? (
          <EmptyState 
            suggestedQuestions={suggestedQuestions} 
            onSuggestionClick={handleSuggestionClick}
            isFullscreen={isFullscreen}
          />
        ) : (
          messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onRetry={onRetry}
              onCopy={copyToClipboard}
              isFullscreen={isFullscreen}
            />
          ))
        )}
        
        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg px-4 py-3 max-w-xs">
              <div className="flex items-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm text-muted-foreground">AI 正在分析您的問題...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className={cn(
        'border-t border-border bg-background',
        isFullscreen ? 'p-8' : 'p-4'
      )}>
        {/* Suggested Questions */}
        {showSuggestions && suggestedQuestions.length > 0 && (
          <div className="mb-4">
            <div className="text-xs text-muted-foreground mb-2">建議問題：</div>
            <div className={cn(
              'flex flex-wrap gap-2',
              isFullscreen && 'max-w-4xl'
            )}>
              {suggestedQuestions.slice(0, isFullscreen ? 6 : 3).map((suggestion, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="text-xs whitespace-nowrap"
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="flex items-end space-x-3">
            <div className={cn('flex-1', isFullscreen && 'max-w-4xl')}>
              <Textarea
                ref={textareaRef}
                placeholder="詢問關於您的庫存數據，例如：「顯示銷售額前10的產品」或「哪些產品庫存不足？」"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setShowSuggestions(true)}
                disabled={isProcessing}
                className={cn(
                  'min-h-[60px] max-h-32 resize-none',
                  isFullscreen && 'min-h-[80px] text-base'
                )}
                rows={isFullscreen ? 3 : 2}
              />
            </div>
            
            <div className="flex flex-col space-y-1">
              <Button
                type="submit"
                disabled={!inputValue.trim() || isProcessing}
                className={cn(
                  'px-4',
                  isFullscreen ? 'h-[80px]' : 'h-[60px]'
                )}
              >
                {isProcessing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
              
              {!showSuggestions && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowSuggestions(true)}
                  className="text-xs"
                  title="顯示建議問題"
                >
                  💡
                </Button>
              )}
            </div>
          </div>
          
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>按 Enter 發送，Shift+Enter 換行</span>
            {isFullscreen && (
              <span>專注模式已啟用 - 更大的對話空間</span>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}

interface MessageBubbleProps {
  message: ChatMessage
  onRetry: (messageId: string) => void
  onCopy: (text: string) => void
  isFullscreen?: boolean
}

function MessageBubble({ message, onRetry, onCopy, isFullscreen }: MessageBubbleProps) {
  const isUser = message.type === 'user'
  const isError = message.type === 'error'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={cn(
        'rounded-lg p-4 space-y-3',
        isFullscreen ? 'max-w-[85%]' : 'max-w-[80%]',
        isUser 
          ? 'bg-primary text-primary-foreground' 
          : isError 
            ? 'bg-destructive/10 border-destructive/20' 
            : 'bg-muted'
      )}>
        {/* Message Content */}
        <div className="prose prose-sm max-w-none">
          <p className={cn(
            'leading-relaxed',
            isFullscreen ? 'text-base' : 'text-sm'
          )}>
            {message.content}
          </p>
        </div>

        {/* SQL Query Display */}
        {message.sql && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">生成的 SQL：</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onCopy(message.sql!)}
                className="h-6 w-6 p-0"
              >
                <Copy className="h-3 w-3" />
              </Button>
            </div>
            <pre className={cn(
              'bg-background/50 rounded p-3 overflow-x-auto font-mono',
              isFullscreen ? 'text-sm' : 'text-xs'
            )}>
              <code>{message.sql}</code>
            </pre>
          </div>
        )}

        {/* Query Results Preview */}
        {message.results && (
          <QueryResultsPreview 
            results={message.results}
            metadata={message.metadata}
            isFullscreen={isFullscreen}
          />
        )}

        {/* Message Footer */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{new Date(message.timestamp).toLocaleTimeString('zh-TW')}</span>
          
          <div className="flex items-center space-x-2">
            {message.status && (
              <Badge 
                variant={message.status === 'completed' ? 'default' : message.status === 'failed' ? 'destructive' : 'secondary'}
                className="text-xs"
              >
                {message.status === 'processing' ? '處理中' : 
                 message.status === 'completed' ? '已完成' : '失敗'}
              </Badge>
            )}
            
            {(message.status === 'failed' || isError) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onRetry(message.id)}
                className="h-6 px-2 text-xs"
              >
                <RotateCcw className="h-3 w-3 mr-1" />
                重試
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

interface QueryResultsPreviewProps {
  results: QueryResult
  metadata?: QueryMetadata
  isFullscreen?: boolean
}

function QueryResultsPreview({ results, metadata, isFullscreen }: QueryResultsPreviewProps) {
  const [showFullResults, setShowFullResults] = useState(false)
  const maxPreviewRows = isFullscreen ? 8 : 3
  const maxDisplayRows = isFullscreen ? 15 : 5

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">
          查詢結果 ({results.row_count} 筆記錄)
        </span>
        <div className="flex items-center space-x-1">
          {metadata?.processing_time && (
            <Badge variant="outline" className="text-xs">
              {metadata.processing_time}ms
            </Badge>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowFullResults(!showFullResults)}
            className="h-6 px-2 text-xs"
          >
            {showFullResults ? '收合' : '展開'}
          </Button>
        </div>
      </div>

      {/* Results Table */}
      <div className="bg-background/50 rounded border">
        {results.data && results.data.length > 0 ? (
          <div className="overflow-x-auto">
            <table className={cn('w-full', isFullscreen ? 'text-sm' : 'text-xs')}>
              <thead>
                <tr className="border-b">
                  {results.columns.map((col) => (
                    <th key={col} className="px-3 py-2 text-left font-medium">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.data
                  .slice(0, showFullResults ? maxDisplayRows : maxPreviewRows)
                  .map((row, index) => (
                    <tr key={index} className="border-b last:border-b-0">
                      {results.columns.map((col) => (
                        <td key={col} className="px-3 py-2">
                          {String(row[col] ?? '')}
                        </td>
                      ))}
                    </tr>
                  ))}
              </tbody>
            </table>
            
            {!showFullResults && results.data.length > maxPreviewRows && (
              <div className="text-center py-2 text-xs text-muted-foreground border-t">
                還有 {results.data.length - maxPreviewRows} 筆記錄...
              </div>
            )}
          </div>
        ) : (
          <div className="p-4 text-center text-xs text-muted-foreground">
            查詢無結果
          </div>
        )}
      </div>

      {/* Chart Suggestion */}
      {results.chart_type && (
        <div className="flex items-center space-x-2">
          <TrendingUp className="h-3 w-3 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">
            建議圖表: {getChartTypeLabel(results.chart_type)}
          </span>
        </div>
      )}
    </div>
  )
}

interface EmptyStateProps {
  suggestedQuestions: string[]
  onSuggestionClick: (suggestion: string) => void
  isFullscreen?: boolean
}

function EmptyState({ suggestedQuestions, onSuggestionClick, isFullscreen }: EmptyStateProps) {
  return (
    <div className={cn(
      'flex flex-col items-center justify-center h-full space-y-6',
      isFullscreen ? 'p-12' : 'p-8'
    )}>
      <div className="text-center space-y-3">
        <div className={cn(
          'bg-primary/10 rounded-full flex items-center justify-center mx-auto',
          isFullscreen ? 'h-20 w-20' : 'h-16 w-16'
        )}>
          <TrendingUp className={cn(
            'text-primary',
            isFullscreen ? 'h-10 w-10' : 'h-8 w-8'
          )} />
        </div>
        <h3 className={cn(
          'font-semibold',
          isFullscreen ? 'text-2xl' : 'text-xl'
        )}>
          歡迎使用 AI 數據助手
        </h3>
        <p className={cn(
          'text-muted-foreground',
          isFullscreen ? 'max-w-xl text-lg' : 'max-w-md'
        )}>
          用自然語言詢問您的庫存數據問題，我會幫您生成 SQL 查詢並展示結果
        </p>
      </div>

      {/* Example Questions */}
      <div className={cn(
        'space-y-3 w-full',
        isFullscreen ? 'max-w-2xl' : 'max-w-md'
      )}>
        <div className="text-sm font-medium text-center">試試這些問題：</div>
        <div className={cn(
          'space-y-2',
          isFullscreen && 'grid grid-cols-2 gap-3'
        )}>
          {suggestedQuestions
            .slice(0, isFullscreen ? 8 : 4)
            .map((question, index) => (
              <Button
                key={index}
                variant="outline"
                onClick={() => onSuggestionClick(question)}
                className="w-full justify-start text-left text-wrap h-auto p-3"
              >
                <span className="text-sm">{question}</span>
              </Button>
            ))}
        </div>
      </div>

      {/* Quick Tips */}
      <div className={cn(
        'p-3 bg-muted/50 rounded-lg',
        isFullscreen ? 'max-w-xl' : 'max-w-md'
      )}>
        <p className="text-xs text-center">
          💡 <strong>提示：</strong> 您可以詢問數量統計、排序比較、趨勢分析等各種商業問題
        </p>
      </div>
    </div>
  )
}

function getChartTypeLabel(chartType: string): string {
  switch (chartType) {
    case 'bar': return '柱狀圖'
    case 'line': return '折線圖'
    case 'pie': return '圓餅圖'
    case 'table': return '數據表格'
    default: return '數據視覺化'
  }
}
import { useEffect } from 'react'
import { CollapsibleSidebar } from '@/components/layout/CollapsibleSidebar'
import { CollapsibleChatHistory } from '@/components/chat/CollapsibleChatHistory'
import { ChatInterface } from '@/components/chat/ChatInterface'
import { CollapsibleQueryDetails } from '@/components/chat/CollapsibleQueryDetails'
import { DatasetSelector } from '@/components/chat/DatasetSelector'
import { ChatToolbar } from '@/components/chat/ChatToolbar'
import { useChat } from '@/hooks/useChat'
import { useChatLayout } from '@/hooks/useChatLayout'
import { Button } from '@/components/ui/button'

export function ChatbotPage() {
  const {
    state: chatState,
    currentMessages,
    suggestedQuestions,
    createNewSession,
    selectSession,
    sendMessage,
    retryMessage,
    deleteSession,
    exportSession
  } = useChat()

  const {
    state: layoutState,
    toggleSidebar,
    toggleChatHistory,
    toggleQueryDetails,
    enterCompactMode,
    exitCompactMode,
    getActualWidths
  } = useChatLayout()

  const { chatHistoryWidth, queryDetailsWidth, sidebarWidth } = getActualWidths()
  
  // 當前查詢詳情 (最後一個 assistant 訊息)
  const currentQuery = currentMessages
    .filter(m => m.type === 'assistant' && m.sql && m.results)
    .slice(-1)[0]

  const handleExportResults = (format: 'csv' | 'excel' | 'json') => {
    console.log(`Export results as ${format}`)
    // TODO: 實作匯出邏輯
  }

  const handleCreateChart = (chartType: string) => {
    console.log(`Create chart: ${chartType}`)
    // TODO: 實作圖表創建邏輯
  }

  const handleCopySQL = async (sql: string) => {
    await navigator.clipboard.writeText(sql)
  }

  const handleSelectDataset = (datasetId: string) => {
    console.log(`Selected dataset: ${datasetId}`)
    // TODO: 實作數據集選擇邏輯
  }

  const handleToggleFullscreen = () => {
    if (layoutState.compactMode) {
      exitCompactMode()
    } else {
      enterCompactMode()
    }
  }

  // 鍵盤快捷鍵提示
  useEffect(() => {
    const showKeyboardShortcuts = () => {
      console.log('Keyboard shortcuts:', {
        'Ctrl+Shift+H': 'Toggle chat history',
        'Ctrl+Shift+D': 'Toggle query details', 
        'Ctrl+Shift+B': 'Toggle sidebar',
        'Ctrl+Shift+F': 'Toggle fullscreen mode'
      })
    }

    // 只在開發模式顯示
    if (process.env.NODE_ENV === 'development') {
      setTimeout(showKeyboardShortcuts, 1000)
    }
  }, [])

  return (
    <div className="h-screen flex bg-background overflow-hidden">
      {/* Main Sidebar */}
      <div 
        className="flex-shrink-0 transition-all duration-300"
        style={{ width: sidebarWidth }}
      >
        <CollapsibleSidebar
          isCollapsed={layoutState.sidebarCollapsed}
          onToggleCollapse={toggleSidebar}
        />
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Chat History */}
        {!layoutState.compactMode && (
          <div 
            className="flex-shrink-0 transition-all duration-300"
            style={{ width: chatHistoryWidth }}
          >
            <div className="h-full flex flex-col">
              {/* Dataset Selector */}
              {layoutState.showDatasetSelector && (
                <DatasetSelector
                  datasets={[]}
                  selectedDataset={chatState.selectedDataset}
                  onSelectDataset={handleSelectDataset}
                />
              )}
              
              {/* Chat History */}
              <div className="flex-1 overflow-hidden">
                <CollapsibleChatHistory
                  sessions={chatState.sessions}
                  currentSession={chatState.currentSession}
                  isCollapsed={layoutState.chatHistoryCollapsed}
                  onToggleCollapse={toggleChatHistory}
                  onSessionSelect={selectSession}
                  onNewChat={createNewSession}
                  onDeleteSession={deleteSession}
                  onExportSession={exportSession}
                />
              </div>
            </div>
          </div>
        )}

        {/* Center Panel - Chat Interface */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <ChatInterface
            messages={currentMessages}
            onSendMessage={sendMessage}
            onRetry={retryMessage}
            suggestedQuestions={suggestedQuestions}
            isProcessing={chatState.isProcessing}
            isFullscreen={layoutState.compactMode}
            onToggleFullscreen={handleToggleFullscreen}
          />
        </div>

        {/* Right Panel - Query Details */}
        {!layoutState.compactMode && (
          <div 
            className="flex-shrink-0 transition-all duration-300"
            style={{ width: queryDetailsWidth }}
          >
            <CollapsibleQueryDetails
              currentQuery={currentQuery ? {
                sql: currentQuery.sql!,
                results: currentQuery.results!,
                metadata: currentQuery.metadata!
              } : undefined}
              isCollapsed={layoutState.queryDetailsCollapsed}
              onToggleCollapse={toggleQueryDetails}
              onExportResults={handleExportResults}
              onCreateChart={handleCreateChart}
              onCopySQL={handleCopySQL}
            />
          </div>
        )}
      </div>

      {/* Floating Toolbar for All Modes */}
      <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50">
        <ChatToolbar
          chatHistoryCollapsed={layoutState.chatHistoryCollapsed}
          queryDetailsCollapsed={layoutState.queryDetailsCollapsed}
          compactMode={layoutState.compactMode}
          onToggleChatHistory={toggleChatHistory}
          onToggleQueryDetails={toggleQueryDetails}
          onToggleCompactMode={handleToggleFullscreen}
        />
      </div>

      {/* Floating Quick Actions for Compact Mode */}
      {layoutState.compactMode && currentQuery && (
        <div className="absolute bottom-6 right-6 z-50">
          <div className="bg-background/95 backdrop-blur border border-border rounded-lg shadow-lg p-2 flex space-x-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleCopySQL(currentQuery.sql!)}
              className="text-xs"
            >
              複製 SQL
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleExportResults('csv')}
              className="text-xs"
            >
              匯出 CSV
            </Button>
          </div>
        </div>
      )}

      {/* Status Bar */}
      {!layoutState.compactMode && (
        <div className="absolute bottom-0 left-0 right-0 h-6 bg-muted/30 border-t border-border flex items-center justify-center">
          <div className="flex items-center space-x-4 text-xs text-muted-foreground">
            <span>{chatState.sessions.length} 個會話</span>
            <span>{currentMessages.length} 則訊息</span>
            {chatState.isProcessing && (
              <span className="text-primary">AI 處理中...</span>
            )}
            <span>按 ? 查看快捷鍵</span>
          </div>
        </div>
      )}
    </div>
  )
}
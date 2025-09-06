import { useEffect, useRef } from 'react'
import { CollapsibleSidebar } from '@/components/layout/CollapsibleSidebar'
import { CollapsibleChatHistory } from '@/components/chat/CollapsibleChatHistory'
import { ChatInterface } from '@/components/chat/ChatInterface'
import { CollapsibleQueryDetails } from '@/components/chat/CollapsibleQueryDetails'
import { DatasetSelector } from '@/components/chat/DatasetSelector'
import { ChatToolbar } from '@/components/chat/ChatToolbar'
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable'
import type { ImperativePanelHandle } from 'react-resizable-panels'
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
    updatePanelSizes,
    getActualWidths
  } = useChatLayout()

  const { sidebarWidth } = getActualWidths()
  
  // Panel refs for programmatic control
  const leftPanelRef = useRef<ImperativePanelHandle>(null)
  const rightPanelRef = useRef<ImperativePanelHandle>(null)
  
  // 當前查詢詳情 (最後一個 assistant 訊息)
  const currentQuery = currentMessages
    .filter(m => m.type === 'assistant' && m.sql && m.results)
    .slice(-1)[0]

  const handleExportResults = () => {
    // TODO: 實作匯出邏輯
  }

  const handleCreateChart = () => {
    // TODO: 實作圖表創建邏輯
  }

  const handleCopySQL = async (sql: string) => {
    await navigator.clipboard.writeText(sql)
  }

  const handleSelectDataset = () => {
    // TODO: 實作數據集選擇邏輯  
  }

  const handleToggleFullscreen = () => {
    if (layoutState.compactMode) {
      exitCompactMode()
    } else {
      enterCompactMode()
    }
  }

  // Sync panel collapse/expand with ResizablePanel state
  const handleToggleChatHistory = () => {
    if (layoutState.chatHistoryCollapsed) {
      // Expand panel programmatically
      leftPanelRef.current?.expand()
    } else {
      // Collapse panel programmatically
      leftPanelRef.current?.collapse()
    }
    toggleChatHistory()
  }

  const handleToggleQueryDetails = () => {
    if (layoutState.queryDetailsCollapsed) {
      // Expand panel programmatically
      rightPanelRef.current?.expand()
    } else {
      // Collapse panel programmatically  
      rightPanelRef.current?.collapse()
    }
    toggleQueryDetails()
  }

  // 鍵盤快捷鍵提示
  useEffect(() => {
    const showKeyboardShortcuts = () => {
      // Keyboard shortcuts for future implementation
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
      <div className="flex-1 overflow-hidden">
        {layoutState.compactMode ? (
          /* Compact Mode - Single Panel */
          <div className="h-full">
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
        ) : (
          /* Normal Mode - Resizable Panels */
          <ResizablePanelGroup 
            direction="horizontal" 
            className="h-full"
            onLayout={(sizes) => {
              // Debounce and persist layout changes
              const [leftSize, centerSize, rightSize] = sizes
              if (leftSize > 5 && rightSize > 5) { // Only update if panels are not collapsed
                updatePanelSizes(leftSize, centerSize, rightSize)
              }
            }}
          >
            {/* Left Panel - Chat History */}
            <ResizablePanel 
              ref={leftPanelRef}
              defaultSize={layoutState.chatHistorySize}
              minSize={layoutState.isMobile ? 0 : 10}
              maxSize={layoutState.isMobile ? 100 : 45}
              collapsible={true}
              collapsedSize={4} // 4% when collapsed (enough for toggle button)
              onCollapse={() => {
                // Sync with our state when panel collapses via drag
                if (!layoutState.chatHistoryCollapsed) {
                  toggleChatHistory()
                }
              }}
              onExpand={() => {
                // Sync with our state when panel expands via drag
                if (layoutState.chatHistoryCollapsed) {
                  toggleChatHistory()
                }
              }}
              onResize={(size) => {
                // Only update sizes when not collapsed
                if (size > 10) {
                  const remainingSize = 100 - size
                  const centerRatio = layoutState.centerPanelSize / (layoutState.centerPanelSize + layoutState.queryDetailsSize)
                  const newCenterSize = remainingSize * centerRatio
                  const newRightSize = remainingSize * (1 - centerRatio)
                  updatePanelSizes(size, newCenterSize, newRightSize)
                }
              }}
            >
              <div className="h-full flex flex-col">
                {/* Dataset Selector */}
                {layoutState.showDatasetSelector && !layoutState.chatHistoryCollapsed && (
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
                    onToggleCollapse={handleToggleChatHistory}
                    onSessionSelect={selectSession}
                    onNewChat={createNewSession}
                    onDeleteSession={deleteSession}
                    onExportSession={exportSession}
                  />
                </div>
              </div>
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* Center Panel - Chat Interface */}
            <ResizablePanel 
              defaultSize={layoutState.centerPanelSize} 
              minSize={30}
            >
              <ChatInterface
                messages={currentMessages}
                onSendMessage={sendMessage}
                onRetry={retryMessage}
                suggestedQuestions={suggestedQuestions}
                isProcessing={chatState.isProcessing}
                isFullscreen={layoutState.compactMode}
                onToggleFullscreen={handleToggleFullscreen}
              />
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* Right Panel - Query Details */}
            <ResizablePanel 
              ref={rightPanelRef}
              defaultSize={layoutState.queryDetailsSize}
              minSize={layoutState.isMobile ? 0 : 10}
              maxSize={layoutState.isMobile ? 100 : 45}
              collapsible={true}
              collapsedSize={4} // 4% when collapsed (enough for toggle button)
              onCollapse={() => {
                // Sync with our state when panel collapses via drag
                if (!layoutState.queryDetailsCollapsed) {
                  toggleQueryDetails()
                }
              }}
              onExpand={() => {
                // Sync with our state when panel expands via drag
                if (layoutState.queryDetailsCollapsed) {
                  toggleQueryDetails()
                }
              }}
              onResize={(size) => {
                // Only update sizes when not collapsed
                if (size > 10) {
                  const remainingSize = 100 - size
                  const leftRatio = layoutState.chatHistorySize / (layoutState.chatHistorySize + layoutState.centerPanelSize)
                  const newLeftSize = remainingSize * leftRatio
                  const newCenterSize = remainingSize * (1 - leftRatio)
                  updatePanelSizes(newLeftSize, newCenterSize, size)
                }
              }}
            >
              <CollapsibleQueryDetails
                currentQuery={currentQuery ? {
                  sql: currentQuery.sql!,
                  results: currentQuery.results!,
                  metadata: currentQuery.metadata!
                } : undefined}
                isCollapsed={layoutState.queryDetailsCollapsed}
                onToggleCollapse={handleToggleQueryDetails}
                onExportResults={handleExportResults}
                onCreateChart={handleCreateChart}
                onCopySQL={handleCopySQL}
              />
            </ResizablePanel>
          </ResizablePanelGroup>
        )}
      </div>

      {/* Floating Toolbar for All Modes */}
      <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50">
        <ChatToolbar
          chatHistoryCollapsed={layoutState.chatHistoryCollapsed}
          queryDetailsCollapsed={layoutState.queryDetailsCollapsed}
          compactMode={layoutState.compactMode}
          onToggleChatHistory={handleToggleChatHistory}
          onToggleQueryDetails={handleToggleQueryDetails}
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
              onClick={() => handleExportResults()}
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
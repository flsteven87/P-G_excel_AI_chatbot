import { useState } from 'react'
import { 
  Maximize2, 
  Minimize2, 
  PanelLeftClose, 
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Keyboard
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface ChatToolbarProps {
  chatHistoryCollapsed: boolean
  queryDetailsCollapsed: boolean
  compactMode: boolean
  onToggleChatHistory: () => void
  onToggleQueryDetails: () => void
  onToggleCompactMode: () => void
  className?: string
}

export function ChatToolbar({
  chatHistoryCollapsed,
  queryDetailsCollapsed, 
  compactMode,
  onToggleChatHistory,
  onToggleQueryDetails,
  onToggleCompactMode,
  className
}: ChatToolbarProps) {
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false)

  const keyboardShortcuts = [
    { key: '⌘+Shift+H', action: '切換聊天歷史' },
    { key: '⌘+Shift+D', action: '切換查詢結果' },
    { key: '⌘+Shift+F', action: '專注模式' },
    { key: 'Enter', action: '發送訊息' },
    { key: 'Shift+Enter', action: '換行' },
    { key: 'Esc', action: '關閉選單' }
  ]

  return (
    <div className={cn('relative', className)}>
      {/* Main Toolbar */}
      <div className="flex items-center justify-center space-x-1 bg-background/95 backdrop-blur border border-border rounded-lg shadow-lg p-2">
        {/* Layout Controls */}
        <div className="flex items-center space-x-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleChatHistory}
            className={cn(
              'h-8 w-8 p-0',
              !chatHistoryCollapsed && 'bg-primary/10 text-primary'
            )}
            title={`${chatHistoryCollapsed ? '顯示' : '隱藏'}聊天歷史 (⌘+Shift+H)`}
          >
            {chatHistoryCollapsed ? (
              <PanelLeftOpen className="h-4 w-4" />
            ) : (
              <PanelLeftClose className="h-4 w-4" />
            )}
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleQueryDetails}
            className={cn(
              'h-8 w-8 p-0',
              !queryDetailsCollapsed && 'bg-primary/10 text-primary'
            )}
            title={`${queryDetailsCollapsed ? '顯示' : '隱藏'}查詢結果 (⌘+Shift+D)`}
          >
            {queryDetailsCollapsed ? (
              <PanelRightOpen className="h-4 w-4" />
            ) : (
              <PanelRightClose className="h-4 w-4" />
            )}
          </Button>

          <div className="w-px h-4 bg-border mx-1" />

          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleCompactMode}
            className={cn(
              'h-8 w-8 p-0',
              compactMode && 'bg-primary/10 text-primary'
            )}
            title={`${compactMode ? '退出' : '進入'}專注模式 (⌘+Shift+F)`}
          >
            {compactMode ? (
              <Minimize2 className="h-4 w-4" />
            ) : (
              <Maximize2 className="h-4 w-4" />
            )}
          </Button>
        </div>

        <div className="w-px h-4 bg-border mx-1" />

        {/* Info Controls */}
        <div className="flex items-center space-x-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowKeyboardHelp(!showKeyboardHelp)}
            className="h-8 w-8 p-0"
            title="鍵盤快捷鍵說明"
          >
            <Keyboard className="h-4 w-4" />
          </Button>

          <Badge variant="outline" className="text-xs">
            {compactMode ? '專注模式' : '標準模式'}
          </Badge>
        </div>
      </div>

      {/* Keyboard Help Popup */}
      {showKeyboardHelp && (
        <Card className="absolute top-full mt-2 right-0 w-72 shadow-lg border z-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-medium text-sm">鍵盤快捷鍵</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowKeyboardHelp(false)}
                className="h-6 w-6 p-0"
              >
                ×
              </Button>
            </div>
            
            <div className="space-y-2">
              {keyboardShortcuts.map((shortcut, index) => (
                <div key={index} className="flex justify-between items-center text-xs">
                  <span className="text-muted-foreground">{shortcut.action}</span>
                  <Badge variant="outline" className="text-xs font-mono">
                    {shortcut.key}
                  </Badge>
                </div>
              ))}
            </div>

            <div className="mt-3 pt-3 border-t border-border">
              <p className="text-xs text-muted-foreground">
                💡 所有快捷鍵都可以在聊天過程中使用
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
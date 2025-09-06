import { useState } from 'react'
import { 
  Plus, 
  Search, 
  MessageCircle, 
  Trash2, 
  Pin, 
  PinOff, 
  Download,
  ChevronLeft,
  ChevronRight,
  History
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ChatSession } from '@/types/chat'
import { cn, formatRelativeTime } from '@/lib/utils'

interface CollapsibleChatHistoryProps {
  sessions: ChatSession[]
  currentSession: string | null
  isCollapsed: boolean
  onToggleCollapse: () => void
  onSessionSelect: (sessionId: string) => void
  onNewChat: () => void
  onDeleteSession: (sessionId: string) => void
  onExportSession: (sessionId: string) => void
  className?: string
}

export function CollapsibleChatHistory({
  sessions,
  currentSession,
  isCollapsed,
  onToggleCollapse,
  onSessionSelect,
  onNewChat,
  onDeleteSession,
  onExportSession,
  className
}: CollapsibleChatHistoryProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [pinnedSessions, setPinnedSessions] = useState<Set<string>>(new Set())

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const togglePin = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    const newPinned = new Set(pinnedSessions)
    if (newPinned.has(sessionId)) {
      newPinned.delete(sessionId)
    } else {
      newPinned.add(sessionId)
    }
    setPinnedSessions(newPinned)
  }


  const pinnedSessionsList = filteredSessions.filter(s => pinnedSessions.has(s.id))
  const regularSessionsList = filteredSessions.filter(s => !pinnedSessions.has(s.id))

  if (isCollapsed) {
    return (
      <div className={cn('flex flex-col h-full bg-background border-r border-border w-12', className)}>
        {/* Collapsed Header */}
        <div className="p-2 border-b border-border">
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleCollapse}
            className="w-full h-8 p-0"
            title="展開聊天歷史"
          >
            <History className="h-4 w-4" />
          </Button>
        </div>

        {/* Collapsed Sessions (show dots for first few) */}
        <div className="flex-1 p-2 space-y-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={onNewChat}
            className="w-full h-8 p-0"
            title="新對話"
          >
            <Plus className="h-4 w-4" />
          </Button>
          
          {sessions.slice(0, 5).map((session) => (
            <Button
              key={session.id}
              variant={currentSession === session.id ? "default" : "ghost"}
              size="sm"
              onClick={() => onSessionSelect(session.id)}
              className="w-full h-8 p-0"
              title={session.title}
            >
              <div className={cn(
                'w-2 h-2 rounded-full',
                currentSession === session.id 
                  ? 'bg-primary-foreground' 
                  : 'bg-muted-foreground',
                pinnedSessions.has(session.id) && 'ring-2 ring-primary/50'
              )} />
            </Button>
          ))}
          
          {sessions.length > 5 && (
            <div className="text-center">
              <div className="text-xs text-muted-foreground">+{sessions.length - 5}</div>
            </div>
          )}
        </div>

        {/* Expand Button */}
        <div className="border-t border-border p-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleCollapse}
            className="w-full h-8 p-0"
            title="展開面板"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className={cn('flex flex-col h-full bg-background border-r border-border w-full min-w-0', className)}>
      {/* Header */}
      <div className="p-3 sm:p-4 border-b border-border space-y-3 sm:space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base sm:text-lg font-semibold truncate">聊天記錄</h2>
          <div className="flex items-center space-x-1 flex-shrink-0">
            <Button onClick={onNewChat} size="sm" variant="ghost" className="h-8 w-8 p-0">
              <Plus className="h-4 w-4" />
            </Button>
            <Button 
              onClick={onToggleCollapse} 
              size="sm" 
              variant="ghost"
              className="h-8 w-8 p-0"
              title="收合面板 (Ctrl+Shift+H)"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </div>
        </div>
        
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜尋..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-sm"
          />
        </div>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto p-2">
        {/* Pinned Sessions */}
        {pinnedSessionsList.length > 0 && (
          <div className="mb-4">
            <div className="px-2 py-1 text-xs font-medium text-muted-foreground flex items-center">
              <Pin className="h-3 w-3 mr-1" />
              已釘選
            </div>
            <div className="space-y-1">
              {pinnedSessionsList.map((session) => (
                <SessionCard
                  key={session.id}
                  session={session}
                  isActive={currentSession === session.id}
                  isPinned={true}
                  onSelect={() => onSessionSelect(session.id)}
                  onTogglePin={(e) => togglePin(session.id, e)}
                  onDelete={(e) => {
                    e.stopPropagation()
                    onDeleteSession(session.id)
                  }}
                  onExport={(e) => {
                    e.stopPropagation()
                    onExportSession(session.id)
                  }}
                  formatDate={formatRelativeTime}
                />
              ))}
            </div>
          </div>
        )}

        {/* Regular Sessions */}
        <div className="space-y-1">
          {regularSessionsList.length > 0 ? (
            regularSessionsList.map((session) => (
              <SessionCard
                key={session.id}
                session={session}
                isActive={currentSession === session.id}
                isPinned={false}
                onSelect={() => onSessionSelect(session.id)}
                onTogglePin={(e) => togglePin(session.id, e)}
                onDelete={(e) => {
                  e.stopPropagation()
                  onDeleteSession(session.id)
                }}
                onExport={(e) => {
                  e.stopPropagation()
                  onExportSession(session.id)
                }}
                formatDate={formatRelativeTime}
              />
            ))
          ) : (
            <div className="text-center py-8">
              <MessageCircle className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">
                {searchQuery ? '沒有找到相符的聊天記錄' : '尚無聊天記錄'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Footer Stats & Controls */}
      <div className="border-t border-border p-4 space-y-3">
        <div className="text-xs text-muted-foreground text-center">
          共 {sessions.length} 個對話會話
        </div>
        
        {/* Quick Actions */}
        <div className="flex items-center justify-center space-x-1">
          <Button
            variant="ghost"
            size="sm"
            className="text-xs"
            title="鍵盤快捷鍵"
          >
            ⌘+N 新對話
          </Button>
        </div>
      </div>
    </div>
  )
}

interface SessionCardProps {
  session: ChatSession
  isActive: boolean
  isPinned: boolean
  onSelect: () => void
  onTogglePin: (e: React.MouseEvent) => void
  onDelete: (e: React.MouseEvent) => void
  onExport: (e: React.MouseEvent) => void
  formatDate: (dateString: string) => string
}

function SessionCard({
  session,
  isActive,
  isPinned,
  onSelect,
  onTogglePin,
  onDelete,
  onExport,
  formatDate,
}: SessionCardProps) {
  const [showActions, setShowActions] = useState(false)

  return (
    <Card
      className={cn(
        'p-3 cursor-pointer transition-all hover:bg-accent/50',
        isActive && 'bg-accent border-primary/50',
        'relative group'
      )}
      onClick={onSelect}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className="space-y-2">
        <div className="flex items-start justify-between">
          <h3 className={cn(
            'text-sm font-medium truncate flex-1 pr-2',
            isActive ? 'text-foreground' : 'text-foreground/80'
          )}>
            {session.title}
          </h3>
          {isPinned && <Pin className="h-3 w-3 text-muted-foreground flex-shrink-0" />}
        </div>
        
        <div className="flex items-center justify-between text-xs gap-2">
          <span className="text-muted-foreground truncate flex-1">
            {formatDate(session.updated_at)}
          </span>
          <Badge variant="outline" className="text-xs flex-shrink-0">
            <span className="hidden sm:inline">{session.message_count} 則</span>
            <span className="sm:hidden">{session.message_count}</span>
          </Badge>
        </div>

        {/* Action Buttons - Adaptive based on container width */}
        {showActions && (
          <div className="absolute top-1 right-1 sm:top-2 sm:right-2 flex items-center space-x-1 bg-background/90 backdrop-blur rounded p-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={onTogglePin}
              className="h-6 w-6 p-0"
              title={isPinned ? '取消釘選' : '釘選'}
            >
              {isPinned ? (
                <PinOff className="h-3 w-3" />
              ) : (
                <Pin className="h-3 w-3" />
              )}
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={onExport}
              className="h-6 w-6 p-0"
              title="匯出對話"
            >
              <Download className="h-3 w-3" />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={onDelete}
              className="h-6 w-6 p-0 text-destructive hover:text-destructive"
              title="刪除會話"
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        )}
      </div>
    </Card>
  )
}
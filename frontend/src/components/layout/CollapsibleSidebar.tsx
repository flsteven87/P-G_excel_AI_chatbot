import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { 
  Bot, 
  BarChart3, 
  FileSpreadsheet, 
  User, 
  ChevronDown,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import { Button } from '@/components/ui/button'

interface CollapsibleSidebarProps {
  isCollapsed: boolean
  onToggleCollapse: () => void
  className?: string
}

const navigation = [
  {
    name: 'AI Chatbot',
    href: '/',
    icon: Bot,
  },
  {
    name: 'Analytics', 
    href: '/analytics',
    icon: BarChart3,
  },
  {
    name: 'Excel',
    href: '/excel',
    icon: FileSpreadsheet,
  },
]

export function CollapsibleSidebar({ 
  isCollapsed, 
  onToggleCollapse, 
  className 
}: CollapsibleSidebarProps) {
  const location = useLocation()

  return (
    <div className={cn(
      'flex h-full flex-col bg-background border-r border-border transition-all duration-300',
      isCollapsed ? 'w-16' : 'w-64',
      className
    )}>
      {/* Logo */}
      <div className="flex h-16 items-center border-b border-border relative">
        {!isCollapsed ? (
          <Link to="/" className="flex items-center space-x-3 px-6">
            <Bot className="w-8 h-8 text-primary" />
            <div className="flex flex-col">
              <span className="font-semibold text-lg text-foreground">Excel AI</span>
              <span className="text-xs text-muted-foreground">智慧分析平台</span>
            </div>
          </Link>
        ) : (
          <div className="flex items-center justify-center w-full">
            <Bot className="w-8 h-8 text-primary" />
          </div>
        )}
        
        {/* Collapse Toggle Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleCollapse}
          className={cn(
            'absolute top-1/2 -translate-y-1/2 h-6 w-6 p-0 border border-border bg-background hover:bg-accent',
            isCollapsed ? 'right-[-12px]' : 'right-[-12px]'
          )}
        >
          {isCollapsed ? (
            <ChevronRight className="h-3 w-3" />
          ) : (
            <ChevronLeft className="h-3 w-3" />
          )}
        </Button>
      </div>

      {/* Navigation */}
      <nav className={cn('flex-1 space-y-2 py-6', isCollapsed ? 'px-2' : 'px-4')}>
        <div className="space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            const Icon = item.icon
            
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  'group flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isCollapsed ? 'justify-center' : 'space-x-3',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
                title={isCollapsed ? item.name : undefined}
              >
                <Icon className="h-5 w-5" />
                {!isCollapsed && <span>{item.name}</span>}
              </Link>
            )
          })}
        </div>
      </nav>

      {/* User Section */}
      <div className="border-t border-border p-4">
        {!isCollapsed ? (
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">
                Demo User
              </p>
              <p className="text-xs text-muted-foreground truncate">
                demo@example.com
              </p>
            </div>
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </div>
        ) : (
          <div className="flex justify-center">
            <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-muted-foreground" />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
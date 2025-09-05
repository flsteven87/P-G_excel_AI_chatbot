import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Bot, BarChart3, FileSpreadsheet, User, ChevronDown } from 'lucide-react'

interface SidebarProps {
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

export function Sidebar({ className }: SidebarProps) {
  const location = useLocation()

  return (
    <div className={cn('flex h-full w-64 flex-col bg-background border-r border-border', className)}>
      {/* Logo */}
      <div className="flex h-16 items-center px-6 border-b border-border">
        <Link to="/" className="flex items-center space-x-3">
          <Bot className="w-8 h-8 text-primary" />
          <div className="flex flex-col">
            <span className="font-semibold text-lg text-foreground">Excel AI</span>
            <span className="text-xs text-muted-foreground">智慧分析平台</span>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-2 px-4 py-6">
        <div className="space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            const Icon = item.icon
            
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  'group flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <Icon className="h-5 w-5" />
                <span>{item.name}</span>
              </Link>
            )
          })}
        </div>
      </nav>

      {/* User Section */}
      <div className="border-t border-border p-4">
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
      </div>
    </div>
  )
}
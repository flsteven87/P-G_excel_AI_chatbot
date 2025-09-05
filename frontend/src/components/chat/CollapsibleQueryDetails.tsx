import { useState } from 'react'
import { 
  Code2, 
  Download, 
  BarChart3, 
  Table, 
  LineChart, 
  PieChart,
  Clock,
  Database,
  Eye,
  EyeOff,
  Copy,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Minimize2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { QueryResult, QueryMetadata } from '@/types/chat'
import { cn } from '@/lib/utils'

interface CollapsibleQueryDetailsProps {
  currentQuery?: {
    sql: string
    results: QueryResult
    metadata: QueryMetadata
  }
  isCollapsed: boolean
  onToggleCollapse: () => void
  onExportResults: (format: 'csv' | 'excel' | 'json') => void
  onCreateChart: (chartType: string) => void
  onCopySQL: (sql: string) => void
  className?: string
}

export function CollapsibleQueryDetails({
  currentQuery,
  isCollapsed,
  onToggleCollapse,
  onExportResults,
  onCreateChart,
  onCopySQL,
  className
}: CollapsibleQueryDetailsProps) {
  const [activeTab, setActiveTab] = useState('results')
  const [showAllRows, setShowAllRows] = useState(false)
  const [sqlCopied, setSqlCopied] = useState(false)
  const [isMaximized, setIsMaximized] = useState(false)

  const handleCopySQL = async () => {
    if (currentQuery?.sql) {
      await onCopySQL(currentQuery.sql)
      setSqlCopied(true)
      setTimeout(() => setSqlCopied(false), 2000)
    }
  }

  // Collapsed view - minimal panel
  if (isCollapsed) {
    return (
      <div className={cn('flex flex-col h-full bg-background border-l border-border w-12', className)}>
        {/* Collapsed Header */}
        <div className="p-2 border-b border-border">
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleCollapse}
            className="w-full h-8 p-0"
            title="展開查詢結果"
          >
            <Database className="h-4 w-4" />
          </Button>
        </div>

        {/* Status Indicator */}
        <div className="flex-1 flex flex-col items-center justify-center p-2">
          {currentQuery ? (
            <div className="space-y-3">
              {/* SQL indicator */}
              <Button
                variant="ghost"
                size="sm"
                className="w-full h-8 p-0"
                title="有 SQL 查詢結果"
              >
                <Code2 className="h-4 w-4 text-green-600" />
              </Button>
              
              {/* Results indicator */}
              <Button
                variant="ghost"
                size="sm" 
                className="w-full h-8 p-0"
                title={`${currentQuery.results.row_count} 筆記錄`}
              >
                <Table className="h-4 w-4 text-blue-600" />
              </Button>
              
              {/* Chart indicator */}
              <Button
                variant="ghost"
                size="sm"
                className="w-full h-8 p-0"
                title="圖表建議"
              >
                <BarChart3 className="h-4 w-4 text-purple-600" />
              </Button>
            </div>
          ) : (
            <div className="text-muted-foreground">
              <Database className="h-6 w-6 mx-auto" />
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
            title="展開面板 (Ctrl+Shift+D)"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        </div>
      </div>
    )
  }

  // No query state
  if (!currentQuery) {
    return (
      <div className={cn('flex flex-col h-full bg-background border-l border-border w-96', className)}>
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 className="text-lg font-semibold">查詢結果</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleCollapse}
            className="h-8 w-8 p-0"
            title="收合面板 (Ctrl+Shift+D)"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
        
        <div className="flex-1 flex flex-col items-center justify-center p-8">
          <Database className="h-16 w-16 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">查詢結果面板</h3>
          <p className="text-center text-muted-foreground max-w-sm text-sm">
            開始對話後，您的 SQL 查詢和結果將在此處顯示
          </p>
        </div>
      </div>
    )
  }

  const { sql, results, metadata } = currentQuery

  return (
    <div className={cn(
      'flex flex-col h-full bg-background border-l border-border transition-all duration-300',
      isMaximized ? 'w-[600px]' : 'w-96',
      className
    )}>
      {/* Header */}
      <div className="border-b border-border p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">查詢詳情</h2>
          
          <div className="flex items-center space-x-2">
            {/* Metrics */}
            <Badge variant="outline" className="text-xs">
              <Clock className="h-3 w-3 mr-1" />
              {metadata.processing_time}ms
            </Badge>
            <Badge variant="outline" className="text-xs">
              {results.row_count} 筆
            </Badge>
            
            {/* Controls */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMaximized(!isMaximized)}
              className="h-8 w-8 p-0"
              title={isMaximized ? '還原大小' : '最大化面板'}
            >
              {isMaximized ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggleCollapse}
              className="h-8 w-8 p-0"
              title="收合面板 (Ctrl+Shift+D)"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <TabsList className="mx-4 mt-4 grid w-full grid-cols-3">
            <TabsTrigger value="results" className="text-xs">
              <Table className="h-4 w-4 mr-2" />
              結果 ({results.row_count})
            </TabsTrigger>
            <TabsTrigger value="sql" className="text-xs">
              <Code2 className="h-4 w-4 mr-2" />
              SQL
            </TabsTrigger>
            <TabsTrigger value="charts" className="text-xs">
              <BarChart3 className="h-4 w-4 mr-2" />
              圖表
            </TabsTrigger>
          </TabsList>

          {/* Results Tab */}
          <TabsContent value="results" className="flex-1 overflow-hidden mx-4 mb-4">
            <Card className="h-full">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">數據表格</CardTitle>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowAllRows(!showAllRows)}
                      className="text-xs"
                    >
                      {showAllRows ? (
                        <>
                          <EyeOff className="h-3 w-3 mr-1" />
                          顯示前10筆
                        </>
                      ) : (
                        <>
                          <Eye className="h-3 w-3 mr-1" />
                          顯示全部
                        </>
                      )}
                    </Button>
                    <ExportDropdown onExport={onExportResults} />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className={cn(
                  'overflow-auto',
                  isMaximized ? 'max-h-[600px]' : 'max-h-96'
                )}>
                  {results.data && results.data.length > 0 ? (
                    <DataTable 
                      data={results.data}
                      columns={results.columns}
                      showAllRows={showAllRows}
                      isMaximized={isMaximized}
                    />
                  ) : (
                    <div className="p-8 text-center text-muted-foreground">
                      查詢無結果
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* SQL Tab */}
          <TabsContent value="sql" className="flex-1 overflow-hidden mx-4 mb-4">
            <Card className="h-full">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">生成的 SQL 查詢</CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopySQL}
                    className="text-xs"
                  >
                    {sqlCopied ? (
                      <>
                        <CheckCircle2 className="h-3 w-3 mr-1 text-green-600" />
                        已複製
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3 mr-1" />
                        複製 SQL
                      </>
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <pre className={cn(
                  'bg-muted rounded p-4 text-xs overflow-auto font-mono',
                  isMaximized ? 'max-h-[500px]' : 'max-h-80'
                )}>
                  <code>{sql}</code>
                </pre>
                
                {/* SQL Metrics */}
                <div className="mt-4 grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-muted-foreground">執行時間：</span>
                    <span className="font-medium ml-1">{results.execution_time_ms}ms</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">返回行數：</span>
                    <span className="font-medium ml-1">{results.row_count}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Charts Tab */}
          <TabsContent value="charts" className="flex-1 overflow-hidden mx-4 mb-4">
            <Card className="h-full">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">數據視覺化</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-sm text-muted-foreground">
                  建議的圖表類型：
                </div>
                
                <div className={cn(
                  'grid gap-3',
                  isMaximized ? 'grid-cols-3' : 'grid-cols-2'
                )}>
                  <ChartOption
                    label="柱狀圖"
                    description="適合比較類別數據"
                    icon={<BarChart3 className="h-6 w-6" />}
                    isRecommended={results.chart_type === 'bar'}
                    onClick={() => onCreateChart('bar')}
                    isCompact={!isMaximized}
                  />
                  
                  <ChartOption
                    label="折線圖"
                    description="適合時間序列數據"
                    icon={<LineChart className="h-6 w-6" />}
                    isRecommended={results.chart_type === 'line'}
                    onClick={() => onCreateChart('line')}
                    isCompact={!isMaximized}
                  />
                  
                  <ChartOption
                    label="圓餅圖"
                    description="適合比例分析"
                    icon={<PieChart className="h-6 w-6" />}
                    isRecommended={results.chart_type === 'pie'}
                    onClick={() => onCreateChart('pie')}
                    isCompact={!isMaximized}
                  />
                  
                  {isMaximized && (
                    <ChartOption
                      label="數據表格"
                      description="詳細數據檢視"
                      icon={<Table className="h-6 w-6" />}
                      isRecommended={results.chart_type === 'table'}
                      onClick={() => onCreateChart('table')}
                      isCompact={false}
                    />
                  )}
                </div>

                {/* AI Suggestions */}
                {metadata.suggested_visualizations && (
                  <div className="space-y-2">
                    <div className="text-sm font-medium">AI 建議：</div>
                    <div className="space-y-1">
                      {metadata.suggested_visualizations.map((suggestion, index) => (
                        <div key={index} className="text-xs text-muted-foreground bg-muted/50 rounded p-2">
                          💡 {suggestion}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

interface ChartOptionProps {
  label: string
  description: string
  icon: React.ReactNode
  isRecommended?: boolean
  isCompact?: boolean
  onClick: () => void
}

function ChartOption({ label, description, icon, isRecommended, isCompact, onClick }: ChartOptionProps) {
  return (
    <Button
      variant="outline"
      onClick={onClick}
      className={cn(
        'h-auto flex flex-col items-center space-y-2 relative',
        isCompact ? 'p-2' : 'p-3',
        isRecommended && 'border-primary bg-primary/5'
      )}
    >
      {isRecommended && (
        <Badge className="absolute -top-2 -right-2 bg-primary text-xs">推薦</Badge>
      )}
      
      <div className={cn(
        'rounded-lg flex items-center justify-center',
        isCompact ? 'h-6 w-6' : 'h-8 w-8',
        isRecommended ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'
      )}>
        {icon}
      </div>
      
      <div className="text-center">
        <div className={cn('font-medium', isCompact ? 'text-xs' : 'text-xs')}>
          {label}
        </div>
        {!isCompact && (
          <div className="text-xs text-muted-foreground">{description}</div>
        )}
      </div>
    </Button>
  )
}

interface DataTableProps {
  data: Record<string, unknown>[]
  columns: string[]
  showAllRows: boolean
  isMaximized: boolean
}

function DataTable({ data, columns, showAllRows, isMaximized }: DataTableProps) {
  const displayData = showAllRows ? data : data.slice(0, isMaximized ? 20 : 10)

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b bg-muted/30">
            {columns.map((col) => (
              <th key={col} className="px-3 py-2 text-left font-medium">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayData.map((row, index) => (
            <tr key={index} className="border-b last:border-b-0 hover:bg-muted/20">
              {columns.map((col) => (
                <td key={col} className="px-3 py-2">
                  {formatCellValue(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      
      {!showAllRows && data.length > (isMaximized ? 20 : 10) && (
        <div className="text-center py-3 text-xs text-muted-foreground border-t bg-muted/10">
          還有 {data.length - (isMaximized ? 20 : 10)} 筆記錄...
        </div>
      )}
    </div>
  )
}

interface ExportDropdownProps {
  onExport: (format: 'csv' | 'excel' | 'json') => void
}

function ExportDropdown({ onExport }: ExportDropdownProps) {
  return (
    <div className="flex items-center space-x-1">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onExport('csv')}
        className="text-xs"
      >
        <Download className="h-3 w-3 mr-1" />
        CSV
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => onExport('excel')}
        className="text-xs"
      >
        <Download className="h-3 w-3 mr-1" />
        Excel
      </Button>
    </div>
  )
}

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '-'
  }
  
  if (typeof value === 'number') {
    return new Intl.NumberFormat('zh-TW').format(value)
  }
  
  if (typeof value === 'boolean') {
    return value ? '是' : '否'
  }
  
  return String(value)
}
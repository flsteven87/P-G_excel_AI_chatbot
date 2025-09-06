import { useState, useEffect, useRef } from 'react'
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
  ChevronRight
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
  const [containerWidth, setContainerWidth] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)

  // Track container width for responsive behavior
  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth)
      }
    }

    updateWidth()
    
    const resizeObserver = new ResizeObserver(updateWidth)
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current)
    }

    return () => resizeObserver.disconnect()
  }, [])

  // Dynamic responsive breakpoints based on actual container width
  const isNarrow = containerWidth < 300
  const isWide = containerWidth > 400

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

  // Empty state component
  const EmptyState = () => (
    <>
      <div className="flex items-center justify-between p-3 sm:p-4 border-b border-border">
        <h2 className={cn(
          "font-semibold truncate", 
          isNarrow ? "text-base" : "text-lg"
        )}>
          {isNarrow ? "查詢" : "查詢結果"}
        </h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleCollapse}
          className="h-8 w-8 p-0 flex-shrink-0"
          title="收合面板 (Ctrl+Shift+D)"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
      
      <div className="flex-1 flex flex-col items-center justify-center p-4 sm:p-8">
        <Database className={cn(
          "text-muted-foreground mb-4",
          isNarrow ? "h-12 w-12" : isWide ? "h-20 w-20" : "h-16 w-16"
        )} />
        <h3 className={cn(
          "font-semibold mb-2 text-center",
          isNarrow ? "text-base" : "text-lg"
        )}>
          {isNarrow ? "查詢面板" : "查詢結果面板"}
        </h3>
        <p className={cn(
          "text-center text-muted-foreground leading-relaxed",
          isNarrow ? "text-xs px-2" : isWide ? "text-sm max-w-sm" : "text-sm max-w-xs"
        )}>
          {isNarrow 
            ? "開始對話後顯示 SQL 查詢結果"
            : "開始對話後，您的 SQL 查詢和結果將在此處顯示"
          }
        </p>
        
        {/* Suggestion hints when wide enough */}
        {isWide && (
          <div className="mt-6 p-4 bg-muted/30 rounded-lg text-center">
            <p className="text-xs text-muted-foreground">
              💡 嘗試詢問：「顯示庫存量最高的產品」或「各品牌的總庫存統計」
            </p>
          </div>
        )}
      </div>
    </>
  )

  // Render empty state if no query
  if (!currentQuery) {
    return (
      <div 
        ref={containerRef}
        className={cn('flex flex-col h-full bg-background border-l border-border w-full min-w-0', className)}
      >
        <EmptyState />
      </div>
    )
  }

  // Main content with query results
  const { sql, results, metadata } = currentQuery

  return (
    <div 
      ref={containerRef}
      className={cn(
        'flex flex-col h-full bg-background border-l border-border w-full min-w-0',
        className
      )}
    >
      {/* Header */}
      <div className="border-b border-border p-3 sm:p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base sm:text-lg font-semibold truncate">查詢詳情</h2>
          
          <div className="flex items-center space-x-1 sm:space-x-2 flex-shrink-0">
            {/* Metrics */}
            {!isNarrow && (
              <Badge variant="outline" className="text-xs px-1 sm:px-2">
                <Clock className="h-3 w-3 mr-1" />
                {isWide ? `${metadata.processing_time}ms` : metadata.processing_time}
              </Badge>
            )}
            <Badge variant="outline" className="text-xs px-1 sm:px-2">
              {isWide ? `${results.row_count} 筆` : results.row_count}
            </Badge>
            
            {/* Controls */}
            
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
            <TabsTrigger value="results" className={cn("text-xs", isNarrow ? "px-1" : "px-2 sm:px-3")}>
              <Table className="h-4 w-4" />
              {!isNarrow && <span className="ml-1 sm:ml-2">結果 ({results.row_count})</span>}
              {isNarrow && <span className="ml-1">{results.row_count}</span>}
            </TabsTrigger>
            <TabsTrigger value="sql" className={cn("text-xs", isNarrow ? "px-1" : "px-2 sm:px-3")}>
              <Code2 className="h-4 w-4" />
              {!isNarrow && <span className="ml-1 sm:ml-2">SQL</span>}
            </TabsTrigger>
            <TabsTrigger value="charts" className={cn("text-xs", isNarrow ? "px-1" : "px-2 sm:px-3")}>
              <BarChart3 className="h-4 w-4" />
              {!isNarrow && <span className="ml-1 sm:ml-2">{isNarrow ? '圖' : '圖表'}</span>}
            </TabsTrigger>
          </TabsList>

          {/* Results Tab */}
          <TabsContent value="results" className="flex-1 overflow-hidden mx-4 mb-4">
            <Card className="h-full flex flex-col">
              <CardHeader className="pb-3 flex-shrink-0">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base truncate">數據表格</CardTitle>
                  <div className="flex items-center space-x-1 sm:space-x-2 flex-shrink-0">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowAllRows(!showAllRows)}
                      className={cn("text-xs", isNarrow ? "px-1" : "px-2 sm:px-3")}
                    >
                      {showAllRows ? (
                        <>
                          <EyeOff className="h-3 w-3 mr-1" />
                          {isWide ? "顯示前10筆" : isNarrow ? "10筆" : "前10"}
                        </>
                      ) : (
                        <>
                          <Eye className="h-3 w-3 mr-1" />
                          {isWide ? "顯示全部" : "全部"}
                        </>
                      )}
                    </Button>
                    <ExportDropdown onExport={onExportResults} isNarrow={isNarrow} isWide={isWide} />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0 flex-1 overflow-hidden">
                <div className="h-full overflow-auto">
                  {results.data && results.data.length > 0 ? (
                    <DataTable 
                      data={results.data}
                      columns={results.columns}
                      showAllRows={showAllRows}
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
            <Card className="h-full flex flex-col">
              <CardHeader className="pb-3 flex-shrink-0">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base truncate">SQL 查詢</CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopySQL}
                    className="text-xs flex-shrink-0"
                  >
                    {sqlCopied ? (
                      <>
                        <CheckCircle2 className="h-3 w-3 mr-1 text-green-600" />
                        {isWide ? "已複製" : "✓"}
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3 mr-1" />
                        {isWide ? "複製 SQL" : "複製"}
                      </>
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-hidden flex flex-col">
                <pre className="bg-muted rounded p-3 sm:p-4 text-xs overflow-auto font-mono flex-1 min-h-0">
                  <code>{sql}</code>
                </pre>
                
                {/* SQL Metrics */}
                <div className="mt-3 sm:mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-4 text-xs flex-shrink-0">
                  <div className="truncate">
                    <span className="text-muted-foreground">執行時間：</span>
                    <span className="font-medium ml-1">{results.execution_time_ms}ms</span>
                  </div>
                  <div className="truncate">
                    <span className="text-muted-foreground">返回行數：</span>
                    <span className="font-medium ml-1">{results.row_count}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Charts Tab */}
          <TabsContent value="charts" className="flex-1 overflow-hidden mx-4 mb-4">
            <Card className="h-full flex flex-col">
              <CardHeader className="pb-3 flex-shrink-0">
                <CardTitle className="text-base">數據視覺化</CardTitle>
              </CardHeader>
              <CardContent className="flex-1 overflow-auto space-y-4">
                <div className="text-sm text-muted-foreground">
                  建議的圖表類型：
                </div>
                
                <div className={cn(
                  "grid gap-2",
                  isNarrow ? "grid-cols-1" : isWide ? "grid-cols-3" : "grid-cols-2"
                )}>
                  <ChartOption
                    label="柱狀圖"
                    description="適合比較類別數據"
                    icon={<BarChart3 className="h-6 w-6" />}
                    isRecommended={results.chart_type === 'bar'}
                    onClick={() => onCreateChart('bar')}
                  />
                  
                  <ChartOption
                    label="折線圖"
                    description="適合時間序列數據"
                    icon={<LineChart className="h-6 w-6" />}
                    isRecommended={results.chart_type === 'line'}
                    onClick={() => onCreateChart('line')}
                  />
                  
                  <ChartOption
                    label="圓餅圖"
                    description="適合比例分析"
                    icon={<PieChart className="h-6 w-6" />}
                    isRecommended={results.chart_type === 'pie'}
                    onClick={() => onCreateChart('pie')}
                  />
                  
                  <ChartOption
                    label="數據表格"
                    description="詳細數據檢視"
                    icon={<Table className="h-6 w-6" />}
                    isRecommended={results.chart_type === 'table'}
                    onClick={() => onCreateChart('table')}
                  />
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
  onClick: () => void
}

function ChartOption({ label, description, icon, isRecommended, onClick }: ChartOptionProps) {
  return (
    <Button
      variant="outline"
      onClick={onClick}
      className={cn(
        'h-auto flex flex-col items-center space-y-2 relative p-3',
        isRecommended && 'border-primary bg-primary/5'
      )}
    >
      {isRecommended && (
        <Badge className="absolute -top-2 -right-2 bg-primary text-xs">推薦</Badge>
      )}
      
      <div className={cn(
        'rounded-lg flex items-center justify-center h-8 w-8',
        isRecommended ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'
      )}>
        {icon}
      </div>
      
      <div className="text-center">
        <div className="font-medium text-xs">
          {label}
        </div>
        <div className="text-xs text-muted-foreground">{description}</div>
      </div>
    </Button>
  )
}

interface DataTableProps {
  data: Record<string, unknown>[]
  columns: string[]
  showAllRows: boolean
}

function DataTable({ data, columns, showAllRows }: DataTableProps) {
  const displayData = showAllRows ? data : data.slice(0, 10)

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b bg-muted/30">
            {columns.map((col) => (
              <th key={col} className="px-2 sm:px-3 py-2 text-left font-medium text-xs">
                <span className="truncate block">{col}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayData.map((row, index) => (
            <tr key={index} className="border-b last:border-b-0 hover:bg-muted/20">
              {columns.map((col) => (
                <td key={col} className="px-2 sm:px-3 py-2 min-w-0">
                  <div className="truncate text-xs">
                    {formatCellValue(row[col])}
                  </div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      
      {!showAllRows && data.length > 10 && (
        <div className="text-center py-2 sm:py-3 text-xs text-muted-foreground border-t bg-muted/10">
          還有 {data.length - 10} 筆記錄...
        </div>
      )}
    </div>
  )
}

interface ExportDropdownProps {
  onExport: (format: 'csv' | 'excel' | 'json') => void
  isNarrow: boolean
  isWide: boolean
}

function ExportDropdown({ onExport, isNarrow, isWide }: ExportDropdownProps) {
  if (isNarrow) {
    // Very compact mode - single button with dropdown behavior
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => onExport('csv')}
        className="text-xs px-1"
        title="匯出 CSV"
      >
        <Download className="h-3 w-3" />
      </Button>
    )
  }

  return (
    <div className="flex items-center space-x-1">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onExport('csv')}
        className="text-xs px-2"
      >
        <Download className="h-3 w-3 mr-1" />
        {isWide ? "CSV" : "CSV"}
      </Button>
      {!isNarrow && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => onExport('excel')}
          className="text-xs px-2"
        >
          <Download className="h-3 w-3 mr-1" />
          {isWide ? "Excel" : "XLS"}
        </Button>
      )}
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
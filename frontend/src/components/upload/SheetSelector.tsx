// React import removed
import { FileSpreadsheet, Table, CheckSquare, Square } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { SheetInfo } from '@/lib/api'

interface SheetSelectorProps {
  sheets: SheetInfo[]
  selectedSheets: string[]
  onToggleSheet: (sheetName: string) => void
  onAnalyzeSheets: () => Promise<boolean>
  isAnalyzing: boolean
}

export function SheetSelector({ 
  sheets, 
  selectedSheets, 
  onToggleSheet, 
  onAnalyzeSheets,
  isAnalyzing 
}: SheetSelectorProps) {
  
  const formatNumber = (num: number) => {
    return num.toLocaleString('zh-TW')
  }
  const handleSelectAll = () => {
    if (selectedSheets.length === sheets.length) {
      // Deselect all
      sheets.forEach(sheet => {
        if (selectedSheets.includes(sheet.sheet_name)) {
          onToggleSheet(sheet.sheet_name)
        }
      })
    } else {
      // Select all
      sheets.forEach(sheet => {
        if (!selectedSheets.includes(sheet.sheet_name)) {
          onToggleSheet(sheet.sheet_name)
        }
      })
    }
  }

  const allSelected = sheets.length > 0 && selectedSheets.length === sheets.length
  const someSelected = selectedSheets.length > 0 && selectedSheets.length < sheets.length

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <Table className="h-12 w-12 mx-auto text-purple-600" />
        <h2 className="text-2xl font-bold">選擇要處理的工作表</h2>
        <p className="text-muted-foreground">
          檔案已上傳完成，請選擇要進行 ETL 處理的工作表
        </p>
      </div>

      {/* Analyze Button */}
      {sheets.length === 0 && (
        <div className="text-center">
          <Button 
            onClick={onAnalyzeSheets}
            disabled={isAnalyzing}
            size="lg"
          >
            {isAnalyzing ? (
              <>
                <div className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-current border-t-transparent" />
                分析檔案中...
              </>
            ) : (
              <>
                <FileSpreadsheet className="h-4 w-4 mr-2" />
                分析檔案 Sheets
              </>
            )}
          </Button>
        </div>
      )}

      {/* Sheets List */}
      {sheets.length > 0 && (
        <>
          {/* Select All Controls */}
          <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSelectAll}
                className="h-auto p-1"
              >
                {allSelected ? (
                  <CheckSquare className="h-5 w-5 text-primary" />
                ) : someSelected ? (
                  <div className="h-5 w-5 border-2 border-primary rounded bg-primary/50" />
                ) : (
                  <Square className="h-5 w-5" />
                )}
              </Button>
              <span className="font-medium">
                {allSelected ? '取消全選' : someSelected ? '選擇全部' : '選擇全部'}
              </span>
            </div>
            <Badge variant="secondary">
              {sheets.length} 個工作表
            </Badge>
          </div>

          {/* Sheets Grid */}
          <div className="grid gap-4">
            {sheets.map((sheet) => {
              const isSelected = selectedSheets.includes(sheet.sheet_name)
              
              return (
                <Card 
                  key={sheet.sheet_name}
                  className={`cursor-pointer transition-all hover:shadow-sm ${
                    isSelected 
                      ? 'ring-2 ring-primary border-primary bg-primary/5' 
                      : 'hover:border-primary/50'
                  }`}
                  onClick={() => onToggleSheet(sheet.sheet_name)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start space-x-4">
                      {/* Selection Checkbox */}
                      <div className="mt-1">
                        {isSelected ? (
                          <CheckSquare className="h-5 w-5 text-primary" />
                        ) : (
                          <Square className="h-5 w-5 text-muted-foreground hover:text-foreground" />
                        )}
                      </div>

                      {/* Sheet Info */}
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center justify-between">
                          <h3 className="font-medium text-lg">{sheet.sheet_name}</h3>
                          <FileSpreadsheet className="h-5 w-5 text-blue-600" />
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-muted-foreground">記錄數：</span>
                            <span className="font-medium ml-1">
                              {formatNumber(sheet.row_count)}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">欄位數：</span>
                            <span className="font-medium ml-1">
                              {sheet.column_count}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">狀態：</span>
                            <Badge variant="secondary" className="ml-1">
                              {sheet.validation_status === 'pending' ? '待驗證' : 
                               sheet.validation_status === 'validated' ? '已驗證' : 
                               '錯誤'}
                            </Badge>
                          </div>
                        </div>

                        {/* Column Preview */}
                        {sheet.columns && sheet.columns.length > 0 && (
                          <div className="space-y-1">
                            <div className="text-sm text-muted-foreground">主要欄位：</div>
                            <div className="flex flex-wrap gap-1">
                              {sheet.columns.slice(0, 8).map((col, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  {col}
                                </Badge>
                              ))}
                              {sheet.columns.length > 8 && (
                                <Badge variant="outline" className="text-xs">
                                  +{sheet.columns.length - 8}
                                </Badge>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>

          {/* Selection Summary */}
          <Alert>
            <AlertDescription>
              已選擇 <span className="font-medium">{selectedSheets.length}</span> 個工作表：
              {selectedSheets.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {selectedSheets.map((sheetName) => (
                    <Badge key={sheetName} variant="default" className="text-xs">
                      {sheetName}
                    </Badge>
                  ))}
                </div>
              )}
            </AlertDescription>
          </Alert>
        </>
      )}
    </div>
  )
}
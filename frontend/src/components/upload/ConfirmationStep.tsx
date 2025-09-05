// React import removed
import { CheckCircle, Calendar, FileSpreadsheet, Globe, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { ValidationResult } from '@/lib/api'

interface ConfirmationStepProps {
  filename: string
  selectedCountry: string
  selectedSheets: string[]
  validationResults: Record<string, ValidationResult>
  targetDate: string
  onTargetDateChange: (date: string) => void
}

export function ConfirmationStep({ 
  filename,
  selectedCountry,
  selectedSheets,
  validationResults,
  targetDate,
  onTargetDateChange,
}: ConfirmationStepProps) {
  // Note: totalRecords calculation available if needed
  // const totalRecords = Object.values(validationResults).reduce(
  //   (sum, result) => sum + result.total_records, 0
  // )
  
  // Note: totalIssues calculation available if needed
  // const totalIssues = Object.values(validationResults).reduce(
  //   (sum, result) => sum + (result.issues?.length || 0), 0
  // )
  
  const hasErrors = Object.values(validationResults).some(
    result => !result.is_valid
  )

  const formatNumber = (num: number) => {
    return num.toLocaleString('zh-TW')
  }
  
  // 調試：檢查驗證結果數據

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <CheckCircle className="h-12 w-12 mx-auto text-green-600" />
        <h2 className="text-2xl font-bold">確認上傳資訊</h2>
        <p className="text-muted-foreground">
          請檢查以下資訊，確認後將完成檔案上傳
        </p>
      </div>

      {/* Upload Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileSpreadsheet className="h-5 w-5" />
            <span>上傳摘要</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <Globe className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium">目標系統</span>
              </div>
              <Badge variant="default">{selectedCountry} 系統</Badge>
            </div>
            
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <FileSpreadsheet className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium">檔案名稱</span>
              </div>
              <div className="text-sm bg-muted p-2 rounded">
                <div className="font-medium">{filename}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  上傳時將自動添加時間戳和 ID 前綴
                </div>
              </div>
            </div>
          </div>

          <div>
            <div className="flex items-center space-x-2 mb-2">
              <Calendar className="h-4 w-4 text-purple-600" />
              <Label htmlFor="target-date" className="text-sm font-medium">
                目標快照日期
              </Label>
            </div>
            <Input
              id="target-date"
              type="date"
              value={targetDate}
              onChange={(e) => onTargetDateChange(e.target.value)}
              className="max-w-48"
            />
            <p className="text-xs text-muted-foreground mt-1">
              此日期將作為庫存快照的記錄日期
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Selected Sheets Summary */}
      <Card>
        <CardHeader>
          <CardTitle>選中的工作表 ({selectedSheets.length})</CardTitle>
          <CardDescription>
            以下工作表將被上傳到系統，稍後可單獨執行 ETL 載入
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {selectedSheets.map((sheetName) => {
              const result = validationResults[sheetName]
              const status = result?.is_valid ? 'success' : 'warning'
              
              return (
                <div key={sheetName} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <div className="flex items-center space-x-3">
                    {status === 'success' ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-yellow-600" />
                    )}
                    <div>
                      <div className="font-medium">{sheetName}</div>
                      <div className="text-sm text-muted-foreground">
                        {result ? formatNumber(result.total_records) : 0} 筆記錄
                        {result?.issues && result.issues.length > 0 && (
                          <span className="text-yellow-600 ml-2">
                            • {result.issues.length} 個問題
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <Badge variant={status === 'success' ? 'success' : 'warning'}>
                    {status === 'success' ? '準備就緒' : '有問題'}
                  </Badge>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Data Quality Warning */}
      {hasErrors && (
        <Alert variant="warning">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>資料品質警告</AlertTitle>
          <AlertDescription>
            <div className="space-y-2">
              <p>部分工作表存在資料品質問題，但仍可以進行上傳：</p>
              <ul className="space-y-1 text-sm">
                {Object.entries(validationResults)
                  .filter(([, result]) => !result.is_valid)
                  .map(([sheetName, result]) => (
                    <li key={sheetName}>
                      • <span className="font-medium">{sheetName}</span>: {result.issues.length} 個問題
                    </li>
                  ))}
              </ul>
              <p className="text-xs">
                您可以選擇繼續上傳，問題記錄在 ETL 處理時會被跳過或修正。
              </p>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Summary Information - Confirmation is handled by parent component */}
      <div className="text-center">        
        <div className="mt-4 text-sm text-muted-foreground space-y-1">
          <p>確認後，檔案將正式上傳到 {selectedCountry} 系統</p>
          <p>您可以在檔案管理頁面中對各個工作表執行 ETL 載入</p>
        </div>
      </div>
    </div>
  )
}
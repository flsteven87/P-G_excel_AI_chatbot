// React import removed
import { CheckCircle, AlertTriangle, XCircle, Shield, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import { ValidationResult } from '@/lib/api'
import { formatNumber } from '@/lib/utils'

interface ValidationStepProps {
  selectedSheets: string[]
  validationResults: Record<string, ValidationResult>
  onValidate: () => Promise<boolean>
  isValidating: boolean
}

export function ValidationStep({ 
  selectedSheets, 
  validationResults, 
  onValidate, 
  isValidating 
}: ValidationStepProps) {
  const hasValidationResults = Object.keys(validationResults).length > 0
  const allSheetsValid = selectedSheets.every(sheetName => 
    validationResults[sheetName]?.is_valid
  )
  const totalIssues = Object.values(validationResults).reduce(
    (sum, result) => sum + (result.issues?.length || 0), 0
  )

  const getValidationStatus = (sheetName: string) => {
    const result = validationResults[sheetName]
    if (!result) return 'pending'
    return result.is_valid ? 'success' : 'warning'
  }

  const getValidationIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />
      case 'error':
        return <XCircle className="h-5 w-5 text-red-600" />
      default:
        return <Shield className="h-5 w-5 text-gray-400" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <Shield className="h-12 w-12 mx-auto text-blue-600" />
        <h2 className="text-2xl font-bold">驗證資料品質</h2>
        <p className="text-muted-foreground">
          檢查選中工作表的表頭結構和資料完整性
        </p>
      </div>

      {/* Validation Action */}
      <div className="text-center">
        <Button 
          onClick={onValidate}
          disabled={isValidating || selectedSheets.length === 0}
          size="lg"
          className="min-w-48"
        >
          {isValidating ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              驗證中... 
            </>
          ) : (
            <>
              <Shield className="h-4 w-4 mr-2" />
              開始驗證資料
            </>
          )}
        </Button>
        
        {selectedSheets.length === 0 && (
          <p className="text-sm text-muted-foreground mt-2">
            請先選擇要驗證的工作表
          </p>
        )}
      </div>

      {/* Validation Progress */}
      {isValidating && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>驗證進度</span>
            <span>{Math.round((Object.keys(validationResults).length / selectedSheets.length) * 100)}%</span>
          </div>
          <Progress 
            value={(Object.keys(validationResults).length / selectedSheets.length) * 100} 
          />
        </div>
      )}

      {/* Validation Results Summary */}
      {hasValidationResults && (
        <Alert variant={allSheetsValid ? 'success' : 'warning'}>
          <AlertTitle className="flex items-center space-x-2">
            {allSheetsValid ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
            )}
            <span>
              驗證結果 - {allSheetsValid ? '全部通過' : `發現 ${totalIssues} 個問題`}
            </span>
          </AlertTitle>
          <AlertDescription>
            {allSheetsValid ? (
              <p>所有選中的工作表都符合資料品質要求，可以進行下一步。</p>
            ) : (
              <p>部分工作表存在資料品質問題，請檢視詳細報告並決定是否繼續。</p>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Detailed Validation Results */}
      {hasValidationResults && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium">詳細驗證報告</h3>
          
          {selectedSheets.map((sheetName) => {
            const result = validationResults[sheetName]
            const status = getValidationStatus(sheetName)
            
            return (
              <Card key={sheetName}>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getValidationIcon(status)}
                      <span>{sheetName}</span>
                    </div>
                    <Badge variant={status === 'success' ? 'success' : 'warning'}>
                      {result ? (result.is_valid ? '通過' : `${result.issues.length} 個問題`) : '驗證中'}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                
                {result && (
                  <CardContent className="pt-0">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">總記錄數：</span>
                        <span className="font-medium ml-1">
                          {formatNumber(result.total_records)}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">驗證狀態：</span>
                        <span className={`font-medium ml-1 ${
                          result.is_valid ? 'text-green-600' : 'text-yellow-600'
                        }`}>
                          {result.is_valid ? '資料完整' : '需要注意'}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">問題數量：</span>
                        <span className="font-medium ml-1">
                          {result.issues.length}
                        </span>
                      </div>
                    </div>

                    {/* Issues List */}
                    {result.issues && result.issues.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-medium text-sm">發現的問題：</h4>
                        <div className="space-y-1 max-h-32 overflow-y-auto">
                          {result.issues.slice(0, 10).map((issue, index) => (
                            <div key={index} className="text-sm p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded">
                              <div className="flex items-start space-x-2">
                                <AlertTriangle className="h-3 w-3 text-yellow-600 mt-0.5 flex-shrink-0" />
                                <div>
                                  <span>{issue.message}</span>
                                  {issue.column && (
                                    <span className="text-muted-foreground ml-2">
                                      (欄位: {issue.column})
                                    </span>
                                  )}
                                  {issue.row_number && (
                                    <span className="text-muted-foreground ml-2">
                                      (第 {issue.row_number} 列)
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                          {result.issues.length > 10 && (
                            <div className="text-sm text-center text-muted-foreground p-2">
                              ... 還有 {result.issues.length - 10} 個問題
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                )}
              </Card>
            )
          })}
        </div>
      )}

      {/* Validation Instructions */}
      <Alert>
        <AlertDescription>
          <div className="space-y-1">
            <div className="font-medium">驗證項目包括：</div>
            <ul className="text-sm space-y-1 ml-4">
              <li>• 必要欄位檢查（Date, Sku, Facility, Loc, Qty）</li>
              <li>• 資料格式驗證（日期格式、數值範圍）</li>
              <li>• 業務邏輯檢查（庫存分配邏輯、負值檢查）</li>
              <li>• 重複記錄檢測</li>
            </ul>
          </div>
        </AlertDescription>
      </Alert>
    </div>
  )
}
import { formatDate } from '@/lib/utils'
import { 
  Play, 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  Clock, 
  X,
  Database,
  FileText,
  Loader2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { SheetInfo } from '@/lib/api'

interface SheetETLControlProps {
  fileId: string
  sheet: SheetInfo
  targetDate: string
  onProcess: (fileId: string, sheetName: string, targetDate: string) => Promise<void>
  onCancel: (jobId: string) => Promise<void>
  canProcess: boolean
}

export function SheetETLControl({ 
  fileId, 
  sheet, 
  targetDate, 
  onProcess, 
  onCancel,
  canProcess
}: SheetETLControlProps) {
  const handleProcess = async () => {
    if (canProcess) {
      try {
        await onProcess(fileId, sheet.sheet_name, targetDate)
      } catch (error) {
      }
    }
  }

  const handleCancel = async () => {
    if (sheet.etl_job_id) {
      await onCancel(sheet.etl_job_id)
    }
  }

  const getETLStatusBadge = () => {
    switch (sheet.etl_status) {
      case 'loaded':
        return (
          <Badge variant="success" className="flex items-center space-x-1">
            <CheckCircle className="h-3 w-3" />
            <span>已載入</span>
          </Badge>
        )
      case 'loading':
        return (
          <Badge variant="default" className="flex items-center space-x-1">
            <Loader2 className="h-3 w-3 animate-spin" />
            <span>載入中</span>
          </Badge>
        )
      case 'failed':
        return (
          <Badge variant="destructive" className="flex items-center space-x-1">
            <XCircle className="h-3 w-3" />
            <span>載入失敗</span>
          </Badge>
        )
      default:
        return (
          <Badge variant="outline" className="flex items-center space-x-1">
            <Clock className="h-3 w-3" />
            <span>未載入</span>
          </Badge>
        )
    }
  }

  const getActionButton = () => {
    if (sheet.etl_status === 'loaded') {
      return (
        <Button variant="outline" size="sm" disabled>
          <CheckCircle className="h-4 w-4 mr-2" />
          已完成
        </Button>
      )
    }

    if (sheet.etl_status === 'loading') {
      return (
        <Button variant="outline" size="sm" onClick={handleCancel}>
          <X className="h-4 w-4 mr-2" />
          取消
        </Button>
      )
    }

    if (sheet.etl_status === 'failed' || sheet.etl_status === 'not_loaded') {
      return (
        <Button 
          size="sm"
          onClick={handleProcess}
          disabled={!canProcess}
        >
          <Play className="h-4 w-4 mr-2" />
          {sheet.etl_status === 'failed' ? '重新載入' : '載入資料庫'}
        </Button>
      )
    }

    return null
  }

  const formatNumber = (num: number) => {
    return num.toLocaleString('zh-TW')
  }

  return (
    <div className="border rounded-lg p-4 space-y-3">
      {/* Sheet Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 bg-purple-100 dark:bg-purple-900/30 rounded flex items-center justify-center">
            <FileText className="h-4 w-4 text-purple-600" />
          </div>
          <div>
            <h4 className="font-medium">{sheet.sheet_name}</h4>
            <div className="text-sm text-muted-foreground">
              {formatNumber(sheet.row_count)} 筆記錄 • {sheet.column_count} 欄位
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {getETLStatusBadge()}
          {getActionButton()}
        </div>
      </div>

      {/* Loading Progress (if loading) */}
      {sheet.etl_status === 'loading' && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center space-x-1">
              <Database className="h-3 w-3" />
              <span>正在載入到資料庫...</span>
            </span>
            <span className="text-xs text-muted-foreground">
              {sheet.etl_job_id && `Job: ${sheet.etl_job_id.substring(0, 8)}`}
            </span>
          </div>
          <Progress value={undefined} className="h-2" />
          <div className="text-xs text-muted-foreground text-center">
            處理中，請稍候...
          </div>
        </div>
      )}

      {/* Loaded Success Info */}
      {sheet.etl_status === 'loaded' && sheet.loaded_at && (
        <Alert variant="success">
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            <div className="flex items-center justify-between">
              <span>已成功載入到資料庫</span>
              <span className="text-xs text-muted-foreground">
                {formatDate(sheet.loaded_at)}
              </span>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Failed Error Info */}
      {sheet.etl_status === 'failed' && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>
            載入失敗，請檢查資料格式或稍後重試
          </AlertDescription>
        </Alert>
      )}

      {/* Validation Issues Preview */}
      {sheet.validation_result?.issues && sheet.validation_result.issues.length > 0 && (
        <Alert variant="warning">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-1">
              <div>發現 {sheet.validation_result.issues.length} 個資料品質問題</div>
              <div className="text-xs">
                前 3 個問題: {sheet.validation_result.issues.slice(0, 3).map(issue => issue.message).join('; ')}
                {sheet.validation_result.issues.length > 3 && '...'}
              </div>
            </div>
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}
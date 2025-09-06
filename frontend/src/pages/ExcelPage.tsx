import { useState } from 'react'
import { FileSpreadsheet, Upload, RefreshCw, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { PageHeader } from '@/components/navigation/PageHeader'
import { UploadWizard } from '@/components/upload/UploadWizard'
import { FileCard } from '@/components/file-manager/FileCard'
import { useFileManager } from '@/hooks/useFileManager'

export function ExcelPage() {
  const {
    state,
    loadFiles,
    processSheet,
    cancelJob,
    canProcessSheet,
    clearError,
  } = useFileManager()

  const [showWizard, setShowWizard] = useState(false)

  const handleWizardComplete = () => {
    // 不再手動添加檔案，讓 useFileManager 自動重新載入完整列表
    // 這樣避免重複記錄的問題
    loadFiles() // 重新載入檔案列表以獲取最新狀態
    setShowWizard(false)
  }

  const handleProcessSheet = async (fileId: string, sheetName: string, targetDate: string) => {
    await processSheet(fileId, sheetName, targetDate)
  }

  const handleCancelJob = async (jobId: string) => {
    try {
      await cancelJob(jobId)
    } catch {
      // Error handled by hook
    }
  }

  const runningJobs = Object.values(state.etlJobs).filter(job => 
    job.status === 'processing' || job.status === 'pending'
  ).length

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Excel ETL 管理系統"
        subtitle="上傳 Excel 庫存檔案，選擇處理的工作表，驗證資料品質，並執行 ETL 載入到資料庫"
        actions={
          <Button onClick={() => setShowWizard(true)}>
            <Plus className="h-4 w-4 mr-2" />
            上傳新檔案
          </Button>
        }
      />


      {/* Error Display */}
      {state.error && (
        <Alert variant="destructive">
          <AlertTitle>錯誤</AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            {state.error}
            <Button variant="ghost" size="sm" onClick={clearError}>
              關閉
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Action Bar */}
      <div className="flex justify-between items-center">
        <Button 
          variant="outline" 
          onClick={loadFiles} 
          disabled={state.isLoading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${state.isLoading ? 'animate-spin' : ''}`} />
          重新整理
        </Button>
        
        <div className="text-sm text-muted-foreground">
          {runningJobs > 0 && (
            <Badge className="mr-2 bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
              {runningJobs} 個作業進行中
            </Badge>
          )}
          共管理 {state.files.length} 個檔案
        </div>
      </div>

      {/* Files List */}
      <div className="space-y-6">
        {state.isLoading && state.files.length === 0 ? (
          <div className="text-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-muted-foreground" />
            <p className="text-muted-foreground">載入中...</p>
          </div>
        ) : state.files.length === 0 ? (
          <Card>
            <CardContent className="text-center py-16">
              <FileSpreadsheet className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">尚未上傳任何檔案</h3>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                開始上傳您的 Excel 庫存檔案，系統會引導您完成整個 ETL 處理流程
              </p>
              <Button onClick={() => setShowWizard(true)} size="lg">
                <Upload className="h-5 w-5 mr-2" />
                上傳第一個檔案
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">檔案管理</h2>
            {state.files.map((file) => (
              <FileCard
                key={file.file_id}
                file={file}
                onProcessSheet={handleProcessSheet}
                onCancelJob={handleCancelJob}
                onDeleteFile={async () => {
                  await loadFiles()
                }}
                canProcessSheet={canProcessSheet}
              />
            ))}
          </div>
        )}
      </div>

      {/* Upload Wizard Modal */}
      <UploadWizard
        isOpen={showWizard}
        onClose={() => setShowWizard(false)}
        onComplete={handleWizardComplete}
      />
    </div>
  )
}
import { useState } from 'react'
import { FileSpreadsheet, Calendar, Globe, ChevronDown, ChevronUp, Trash2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { SheetETLControl } from './SheetETLControl'
import { DeleteConfirmDialog } from './DeleteConfirmDialog'
import { UploadedFile } from '@/lib/api'
import { formatDate, formatFileSize } from '@/lib/utils'

interface FileCardProps {
  file: UploadedFile
  onProcessSheet: (fileId: string, sheetName: string, targetDate: string) => Promise<void>
  onCancelJob: (jobId: string) => Promise<void>
  onDeleteFile?: (fileId: string) => void
  canProcessSheet: (fileId: string, sheetName: string) => boolean
}

export function FileCard({ 
  file, 
  onProcessSheet, 
  onCancelJob,
  onDeleteFile,
  canProcessSheet
}: FileCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [targetDate, setTargetDate] = useState(new Date().toISOString().split('T')[0])
  const [showDeleteModal, setShowDeleteModal] = useState(false)


  const handleDeleteComplete = () => {
    if (onDeleteFile) {
      onDeleteFile(file.file_id)
    }
    setShowDeleteModal(false)
  }


  const getFileStatusBadge = () => {
    switch (file.status) {
      case 'uploaded':
        return <Badge variant="secondary">已上傳</Badge>
      case 'analyzing':
        return <Badge variant="warning">分析中</Badge>
      case 'ready':
        return <Badge variant="success">準備就緒</Badge>
      case 'error':
        return <Badge variant="destructive">錯誤</Badge>
      default:
        return <Badge variant="outline">未知</Badge>
    }
  }

  const loadedSheets = file.sheets.filter(sheet => sheet.etl_status === 'loaded').length
  const totalSheets = file.sheets.length

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <div className="h-12 w-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
              <FileSpreadsheet className="h-6 w-6 text-blue-600" />
            </div>
            
            <div className="space-y-1">
              <CardTitle className="text-lg">{file.original_filename}</CardTitle>
              <div className="text-xs text-muted-foreground mb-2">
                檔案 ID: {file.file_id} • 儲存為: {file.filename}
              </div>
              <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                <div className="flex items-center space-x-1">
                  <Globe className="h-3 w-3" />
                  <span>{file.country}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Calendar className="h-3 w-3" />
                  <span>{formatDate(file.upload_date)}</span>
                </div>
                <span>{formatFileSize(file.file_size)}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {getFileStatusBadge()}
            {onDeleteFile && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowDeleteModal(true)}
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Progress Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">工作表：</span>
            <span className="font-medium ml-1">{totalSheets} 個</span>
          </div>
          <div>
            <span className="text-muted-foreground">已載入：</span>
            <span className="font-medium ml-1 text-green-600">{loadedSheets} 個</span>
          </div>
          <div>
            <span className="text-muted-foreground">載入進度：</span>
            <span className="font-medium ml-1">
              {totalSheets > 0 ? Math.round((loadedSheets / totalSheets) * 100) : 0}%
            </span>
          </div>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="space-y-6">
          {/* Target Date Setting */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-muted rounded-lg">
            <div className="space-y-2">
              <Label htmlFor={`target-date-${file.file_id}`}>
                ETL 目標日期
              </Label>
              <Input
                id={`target-date-${file.file_id}`}
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>載入進度</Label>
              <div className="flex items-center space-x-2">
                <div className="flex-1 bg-secondary rounded-full h-2">
                  <div 
                    className="bg-primary h-2 rounded-full transition-all"
                    style={{ width: `${totalSheets > 0 ? (loadedSheets / totalSheets) * 100 : 0}%` }}
                  />
                </div>
                <span className="text-xs text-muted-foreground min-w-12">
                  {loadedSheets}/{totalSheets}
                </span>
              </div>
            </div>
          </div>

          {/* Sheets ETL Controls */}
          <div className="space-y-4">
            <h3 className="font-medium flex items-center space-x-2">
              <span>工作表 ETL 控制</span>
              <Badge variant="outline">{file.sheets.length} 個</Badge>
            </h3>
            
            <div className="space-y-3">
              {file.sheets.map((sheet) => (
                <SheetETLControl
                  key={sheet.sheet_name}
                  fileId={file.file_id}
                  sheet={sheet}
                  targetDate={targetDate}
                  onProcess={onProcessSheet}
                  onCancel={onCancelJob}
                  canProcess={canProcessSheet(file.file_id, sheet.sheet_name)}
                />
              ))}
            </div>
          </div>
        </CardContent>
      )}

      {/* 檔案刪除對話框 */}
      <DeleteConfirmDialog
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        file={{
          file_id: file.file_id,
          filename: file.original_filename,
          file_size: file.file_size
        }}
        onDeleteComplete={handleDeleteComplete}
      />
    </Card>
  )
}
/**
 * Simple Delete Confirmation Modal
 * 簡化的刪除確認對話框
 */
import { useState } from 'react'
import { AlertTriangle, Trash2, X } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface Props {
  readonly isOpen: boolean
  readonly onClose: () => void
  readonly file: {
    readonly file_id: string
    readonly filename: string
    readonly file_size: number
  }
  readonly onDeleteComplete: () => void
}

export function DeleteConfirmDialog({ 
  isOpen, 
  onClose, 
  file, 
  onDeleteComplete 
}: Props) {
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDelete = async () => {
    try {
      setIsDeleting(true)
      setError(null)
      
      const response = await fetch(`http://localhost:8001/api/v1/files/${file.file_id}/hard-delete`, {
        method: 'DELETE'
      })
      
      const result = await response.json()
      
      if (!response.ok) {
        throw new Error(result.detail || result.message || '刪除失敗')
      }
      
      if (result.success) {
        onDeleteComplete()
        onClose()
      } else {
        throw new Error(result.message || '刪除失敗')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '刪除失敗')
    } finally {
      setIsDeleting(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  if (!isOpen) return null

  return (
    <Dialog open={isOpen}>
      <DialogContent className="max-w-md">
        <DialogHeader className="flex flex-row items-center justify-between">
          <DialogTitle className="text-lg font-bold text-red-600">刪除檔案確認</DialogTitle>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </DialogHeader>

        <div className="space-y-4">
          {/* 警告提示 */}
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>⚠️ 警告：這是永久刪除操作</strong>
              <br />
              檔案和相關的工作表資料將被完全刪除，無法恢復。
            </AlertDescription>
          </Alert>

          {/* 檔案資訊 */}
          <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
            <h3 className="font-medium mb-2">即將刪除的檔案</h3>
            <div className="space-y-1 text-sm">
              <div>檔名: <span className="font-mono">{file.filename}</span></div>
              <div>大小: {formatFileSize(file.file_size)}</div>
            </div>
          </div>

          {/* 錯誤訊息 */}
          {error && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* 刪除中狀態 */}
          {isDeleting && (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-red-600 mx-auto"></div>
              <p className="mt-2 text-sm text-muted-foreground">正在刪除檔案...</p>
            </div>
          )}
        </div>

        {/* 操作按鈕 */}
        {!isDeleting && (
          <div className="flex justify-between pt-4 border-t">
            <Button variant="outline" onClick={onClose}>
              取消
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDelete}
              disabled={isDeleting}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              永久刪除
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
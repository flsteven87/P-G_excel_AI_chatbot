import React, { useState, useRef } from 'react'
import { Upload, FileSpreadsheet, X, AlertCircle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface FileUploaderProps {
  selectedFile: File | null
  onFileSelect: (file: File | null) => void
  selectedCountry: string
}

export function FileUploader({ 
  selectedFile, 
  onFileSelect, 
  selectedCountry 
}: FileUploaderProps) {
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0])
    }
  }

  const handleFileSelection = (file: File) => {
    // Validate file type
    const allowedTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
      'text/csv'
    ]
    
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls|csv)$/i)) {
      alert('不支援的檔案格式。請選擇 .xlsx, .xls 或 .csv 檔案')
      return
    }

    // Validate file size (50MB limit)
    if (file.size > 50 * 1024 * 1024) {
      alert('檔案大小不能超過 50MB')
      return
    }

    onFileSelect(file)
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFileSelection(file)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <FileSpreadsheet className="h-12 w-12 mx-auto text-green-600" />
        <h2 className="text-2xl font-bold">上傳 Excel 檔案</h2>
        <p className="text-muted-foreground">
          上傳您的庫存資料檔案到 <span className="font-medium text-foreground">{selectedCountry}</span> 系統
        </p>
      </div>

      {/* File Drop Zone */}
      <Card className={`transition-all ${dragActive ? 'ring-2 ring-primary border-primary' : ''}`}>
        <CardContent className="p-8">
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-all ${
              dragActive 
                ? 'border-primary bg-primary/5' 
                : 'border-border hover:border-primary/50 hover:bg-muted/50'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {selectedFile ? (
              <div className="space-y-4">
                <div className="mx-auto h-16 w-16 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                  <FileSpreadsheet className="h-8 w-8 text-green-600" />
                </div>
                
                <div className="space-y-2">
                  <h3 className="text-lg font-medium">{selectedFile.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {formatFileSize(selectedFile.size)} • {selectedFile.type || '未知格式'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    上次修改: {new Date(selectedFile.lastModified).toLocaleString('zh-TW')}
                  </p>
                </div>

                <div className="flex justify-center">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => {
                      onFileSelect(null)
                      if (fileInputRef.current) {
                        fileInputRef.current.value = ''
                      }
                    }}
                  >
                    <X className="h-4 w-4 mr-2" />
                    重新選擇
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="mx-auto h-16 w-16 bg-muted rounded-lg flex items-center justify-center">
                  <Upload className="h-8 w-8 text-muted-foreground" />
                </div>
                
                <div className="space-y-2">
                  <h3 className="text-lg font-medium">拖放檔案到這裡</h3>
                  <p className="text-muted-foreground">
                    或點擊下方按鈕選擇檔案
                  </p>
                </div>

                <Button 
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="h-4 w-4 mr-2" />
                  選擇檔案
                </Button>
                
                <div className="text-xs text-muted-foreground space-y-1">
                  <div>支援格式: .xlsx, .xls, .csv</div>
                  <div>最大檔案大小: 50MB</div>
                </div>
              </div>
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={handleFileInputChange}
              className="hidden"
            />
          </div>
        </CardContent>
      </Card>

      {/* Upload Instructions */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <div className="space-y-1">
            <div className="font-medium">檔案要求：</div>
            <ul className="text-sm space-y-1 ml-4">
              <li>• 檔案必須包含標準的庫存資料欄位</li>
              <li>• 建議使用標準的 Sheet 名稱（如：庫存報表(SG)）</li>
              <li>• 資料日期格式請使用 YYYY/MM/DD</li>
              <li>• 數量欄位請使用數值格式，避免文字內容</li>
            </ul>
          </div>
        </AlertDescription>
      </Alert>
    </div>
  )
}
import React, { useState } from 'react'
import { Database, ChevronDown, CheckCircle2, AlertCircle, Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Dataset } from '@/types/chat'
import { cn, formatRelativeTime } from '@/lib/utils'

interface DatasetSelectorProps {
  datasets: Dataset[]
  selectedDataset: string | null
  onSelectDataset: (datasetId: string) => void
  className?: string
}

// Mock datasets for demonstration
const MOCK_DATASETS: Dataset[] = [
  {
    id: 'inventory-tw',
    name: '台灣庫存數據',
    description: '包含產品庫存、品牌、地點等完整庫存管理數據',
    table_count: 4,
    last_updated: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    status: 'ready'
  },
  {
    id: 'sales-sg', 
    name: '新加坡銷售數據',
    description: '銷售記錄、客戶訂單、產品績效等銷售分析數據',
    table_count: 6,
    last_updated: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
    status: 'ready'
  },
  {
    id: 'analytics-combined',
    name: '綜合分析數據',
    description: '整合多個數據源的分析視圖和預計算指標',
    table_count: 8,
    last_updated: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    status: 'loading'
  }
]

export function DatasetSelector({
  datasets = MOCK_DATASETS,
  selectedDataset,
  onSelectDataset,
  className
}: DatasetSelectorProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  const selectedDatasetInfo = datasets.find(d => d.id === selectedDataset)


  const getStatusIcon = (status: Dataset['status']) => {
    switch (status) {
      case 'ready':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />
      case 'loading':
        return <Clock className="h-4 w-4 text-yellow-600 animate-pulse" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      default:
        return <Database className="h-4 w-4 text-muted-foreground" />
    }
  }

  const getStatusText = (status: Dataset['status']) => {
    switch (status) {
      case 'ready': return '就緒'
      case 'loading': return '載入中'
      case 'error': return '錯誤'
      default: return '未知'
    }
  }

  return (
    <div className={cn('border-b border-border', className)}>
      {/* Current Selection Display */}
      <div className="p-4">
        <Button
          variant="outline"
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full justify-between h-auto p-3"
        >
          <div className="flex items-center space-x-3 text-left">
            <Database className="h-5 w-5 text-muted-foreground" />
            <div className="flex flex-col">
              <span className="font-medium text-sm">
                {selectedDatasetInfo ? selectedDatasetInfo.name : '選擇數據集'}
              </span>
              {selectedDatasetInfo && (
                <span className="text-xs text-muted-foreground">
                  {selectedDatasetInfo.table_count} 張表 • {formatRelativeTime(selectedDatasetInfo.last_updated)}
                </span>
              )}
            </div>
          </div>
          <ChevronDown className={cn(
            'h-4 w-4 transition-transform',
            isExpanded && 'rotate-180'
          )} />
        </Button>
      </div>

      {/* Dataset Options */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-2">
          {datasets.map((dataset) => (
            <DatasetOption
              key={dataset.id}
              dataset={dataset}
              isSelected={selectedDataset === dataset.id}
              onSelect={() => {
                onSelectDataset(dataset.id)
                setIsExpanded(false)
              }}
              getStatusIcon={getStatusIcon}
              getStatusText={getStatusText}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface DatasetOptionProps {
  dataset: Dataset
  isSelected: boolean
  onSelect: () => void
  getStatusIcon: (status: Dataset['status']) => React.ReactNode
  getStatusText: (status: Dataset['status']) => string
}

function DatasetOption({
  dataset,
  isSelected,
  onSelect,
  getStatusIcon,
  getStatusText
}: DatasetOptionProps) {
  return (
    <Card
      className={cn(
        'cursor-pointer transition-all hover:bg-accent/50 border',
        isSelected && 'border-primary bg-primary/5',
        dataset.status !== 'ready' && 'opacity-60'
      )}
      onClick={dataset.status === 'ready' ? onSelect : undefined}
    >
      <CardContent className="p-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 space-y-1">
            <div className="flex items-center space-x-2">
              <span className="font-medium text-sm">{dataset.name}</span>
              {isSelected && (
                <Badge variant="default" className="text-xs">已選擇</Badge>
              )}
            </div>
            
            <p className="text-xs text-muted-foreground leading-relaxed">
              {dataset.description}
            </p>
            
            <div className="flex items-center space-x-3 text-xs text-muted-foreground">
              <span>{dataset.table_count} 張表</span>
              <span>{formatRelativeTime(dataset.last_updated)}</span>
            </div>
          </div>
          
          <div className="flex flex-col items-end space-y-1">
            <div className="flex items-center space-x-1">
              {getStatusIcon(dataset.status)}
              <span className="text-xs">{getStatusText(dataset.status)}</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
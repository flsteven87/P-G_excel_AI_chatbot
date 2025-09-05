import { BarChart3, TrendingUp, PieChart, LineChart } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PageHeader } from '@/components/navigation/PageHeader'

export function AnalyticsPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="數據分析"
        subtitle="深入分析您的 Excel 數據，發現趨勢、模式和商業洞察"
        actions={
          <Button variant="outline">
            <BarChart3 className="h-4 w-4 mr-2" />
            匯出報告
          </Button>
        }
      />

      {/* Analytics Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-card p-6 rounded-lg border border-border shadow-sm">
          <div className="h-12 w-12 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-4">
            <BarChart3 className="h-6 w-6 text-blue-600" />
          </div>
          <h3 className="text-lg font-semibold mb-2">柱狀圖分析</h3>
          <p className="text-muted-foreground text-sm">
            比較不同類別的數值，清楚顯示數據分布和差異
          </p>
        </div>

        <div className="bg-card p-6 rounded-lg border border-border shadow-sm">
          <div className="h-12 w-12 rounded-lg bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center mb-4">
            <LineChart className="h-6 w-6 text-orange-600" />
          </div>
          <h3 className="text-lg font-semibold mb-2">趨勢分析</h3>
          <p className="text-muted-foreground text-sm">
            追蹤時間序列數據的變化趨勢和季節性模式
          </p>
        </div>

        <div className="bg-card p-6 rounded-lg border border-border shadow-sm">
          <div className="h-12 w-12 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mb-4">
            <PieChart className="h-6 w-6 text-purple-600" />
          </div>
          <h3 className="text-lg font-semibold mb-2">組成分析</h3>
          <p className="text-muted-foreground text-sm">
            分析各部分在整體中的佔比和相對重要性
          </p>
        </div>

        <div className="bg-card p-6 rounded-lg border border-border shadow-sm">
          <div className="h-12 w-12 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center mb-4">
            <TrendingUp className="h-6 w-6 text-green-600" />
          </div>
          <h3 className="text-lg font-semibold mb-2">績效指標</h3>
          <p className="text-muted-foreground text-sm">
            關鍵績效指標 (KPI) 儀表板和預警系統
          </p>
        </div>
      </div>

      {/* Sample Analytics Dashboard */}
      <div className="bg-card rounded-lg border border-border p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-foreground">分析儀表板</h2>
        </div>

        {/* Mock Analytics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-950/50 dark:to-blue-900/50 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-600 text-sm font-medium">總銷售額</p>
                <p className="text-2xl font-bold text-blue-900">NT$ 1,234,567</p>
                <p className="text-blue-600 text-xs">本月 +12.5%</p>
              </div>
              <div className="h-12 w-12 bg-blue-200 rounded-lg flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-green-50 to-green-100 dark:from-green-950/50 dark:to-green-900/50 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-600 text-sm font-medium">訂單數量</p>
                <p className="text-2xl font-bold text-green-900">3,456</p>
                <p className="text-green-600 text-xs">本月 +8.3%</p>
              </div>
              <div className="h-12 w-12 bg-green-200 rounded-lg flex items-center justify-center">
                <BarChart3 className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-purple-50 to-purple-100 dark:from-purple-950/50 dark:to-purple-900/50 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-600 text-sm font-medium">平均客單價</p>
                <p className="text-2xl font-bold text-purple-900">NT$ 357</p>
                <p className="text-purple-600 text-xs">本月 +4.1%</p>
              </div>
              <div className="h-12 w-12 bg-purple-200 rounded-lg flex items-center justify-center">
                <PieChart className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Chart Placeholder */}
        <div className="bg-muted/50 rounded-lg p-8 text-center">
          <div className="mx-auto h-16 w-16 bg-muted rounded-lg flex items-center justify-center mb-4">
            <LineChart className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">互動式圖表</h3>
          <p className="text-muted-foreground mb-4">
            上傳數據後，這裡將顯示豐富的互動式圖表和分析結果
          </p>
          <Button>開始分析</Button>
        </div>
      </div>

      {/* Analysis Types */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-card p-6 rounded-lg border border-border">
          <h3 className="text-xl font-bold mb-4">預設分析模板</h3>
          <ul className="space-y-3">
            <li className="flex items-center space-x-3">
              <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
              <span className="text-foreground">銷售業績分析</span>
            </li>
            <li className="flex items-center space-x-3">
              <div className="h-2 w-2 bg-green-500 rounded-full"></div>
              <span className="text-foreground">客戶行為分析</span>
            </li>
            <li className="flex items-center space-x-3">
              <div className="h-2 w-2 bg-purple-500 rounded-full"></div>
              <span className="text-foreground">產品績效分析</span>
            </li>
            <li className="flex items-center space-x-3">
              <div className="h-2 w-2 bg-orange-500 rounded-full"></div>
              <span className="text-foreground">時間序列分析</span>
            </li>
          </ul>
        </div>

        <div className="bg-card p-6 rounded-lg border border-border">
          <h3 className="text-xl font-bold mb-4">自訂分析</h3>
          <p className="text-muted-foreground mb-4">
            根據您的特定需求建立客製化的分析報告和視覺化圖表
          </p>
          <Button variant="outline" className="w-full">
            建立自訂分析
          </Button>
        </div>
      </div>
    </div>
  )
}
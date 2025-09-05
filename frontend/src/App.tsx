import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { ChatbotPage } from '@/pages/ChatbotPage'
import { AnalyticsPage } from '@/pages/AnalyticsPage'
import { ExcelPage } from '@/pages/ExcelPage'

function App() {
  return (
    <Router>
      <Routes>
        {/* Chat page with completely custom layout */}
        <Route path="/" element={<ChatbotPage />} />
        
        {/* Other pages with standard dashboard layout */}
        <Route 
          path="/analytics" 
          element={
            <DashboardLayout>
              <AnalyticsPage />
            </DashboardLayout>
          } 
        />
        <Route 
          path="/excel" 
          element={
            <DashboardLayout>
              <ExcelPage />
            </DashboardLayout>
          } 
        />
      </Routes>
    </Router>
  )
}

export default App

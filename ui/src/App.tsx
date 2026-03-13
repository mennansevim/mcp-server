import { Navigate, Route, Routes } from 'react-router-dom'
import AppShell from './components/AppShell'
import LogsDashboardPage from './routes/LogsDashboardPage'
import LogDetailPage from './routes/LogDetailPage'
import ConfigPage from './routes/ConfigPage'
import AnalyticsPage from './routes/AnalyticsPage'

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/logs" element={<LogsDashboardPage />} />
        <Route path="/logs/:runId" element={<LogDetailPage />} />
        <Route path="/config" element={<ConfigPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="*" element={<Navigate to="/logs" replace />} />
      </Routes>
    </AppShell>
  )
}

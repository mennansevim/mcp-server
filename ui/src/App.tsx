import { Navigate, Route, Routes } from 'react-router-dom'
import LogsDashboardPage from './routes/LogsDashboardPage'
import LogDetailPage from './routes/LogDetailPage'
import ConfigPage from './routes/ConfigPage'

export default function App() {
  return (
    <Routes>
      <Route path="/logs" element={<LogsDashboardPage />} />
      <Route path="/logs/:runId" element={<LogDetailPage />} />
      <Route path="/config" element={<ConfigPage />} />
      <Route path="*" element={<Navigate to="/logs" replace />} />
    </Routes>
  )
}

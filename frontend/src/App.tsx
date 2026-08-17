import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Curves from './pages/Curves'
import DataSources from './pages/DataSources'
import BuildFit from './pages/BuildFit'
import BuildInterpolate from './pages/BuildInterpolate'
import AnalysisTrend from './pages/AnalysisTrend'
import AnalysisSpread from './pages/AnalysisSpread'
import RiskKRD from './pages/RiskKRD'
import RiskScenario from './pages/RiskScenario'
import AppFTP from './pages/AppFTP'
import AppValuation from './pages/AppValuation'
import AppRegulatory from './pages/AppRegulatory'
import Chat from './pages/Chat'
import DictManagement from './pages/DictManagement'

function AuthGuard({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<AuthGuard><MainLayout /></AuthGuard>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="data-sources" element={<DataSources />} />
        <Route path="curves" element={<Curves />} />
        <Route path="build/fit" element={<BuildFit />} />
        <Route path="build/interpolate" element={<BuildInterpolate />} />
        <Route path="analysis/trend" element={<AnalysisTrend />} />
        <Route path="analysis/spread" element={<AnalysisSpread />} />
        <Route path="risk/krd" element={<RiskKRD />} />
        <Route path="risk/scenario" element={<RiskScenario />} />
        <Route path="app/ftp" element={<AppFTP />} />
        <Route path="app/valuation" element={<AppValuation />} />
        <Route path="app/regulatory" element={<AppRegulatory />} />
        <Route path="chat" element={<Chat />} />
        <Route path="dict" element={<DictManagement />} />
      </Route>
    </Routes>
  )
}
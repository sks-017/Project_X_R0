import { useState, useEffect } from 'react'
import { AuthProvider, useAuth } from './auth/AuthContext'
import LoginPage from './auth/LoginPage'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import Dashboard from './pages/Dashboard'
import ShopFloor from './pages/ShopFloor'
import Analytics from './pages/Analytics'
import Machines from './pages/Machines'
import Downtime from './pages/Downtime'
import AiInsights from './pages/AiInsights'
import TechMate from './pages/TechMate'
import Settings from './pages/Settings'
import { api } from './api/client'

const PAGE_TITLES = {
  dashboard: 'Command Center',
  shopfloor: 'Shop Floor',
  analytics: 'Analytics',
  machines: 'Machine Master',
  downtime: 'Downtime Capture',
  ai: 'AI Insights',
  techmate: 'TechMate AI',
  settings: 'Settings',
}

function AppShell() {
  const { isAuthenticated } = useAuth()
  const [page, setPage] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [health, setHealth] = useState({})

  useEffect(() => {
    if (!isAuthenticated) return
    api.getHealth().then(setHealth)
    const id = setInterval(() => api.getHealth().then(setHealth), 15000)
    return () => clearInterval(id)
  }, [isAuthenticated])

  if (!isAuthenticated) return <LoginPage />

  const renderPage = () => {
    switch (page) {
      case 'dashboard': return <Dashboard />
      case 'shopfloor': return <ShopFloor />
      case 'analytics': return <Analytics />
      case 'machines': return <Machines />
      case 'downtime': return <Downtime />
      case 'ai': return <AiInsights />
      case 'techmate': return <TechMate />
      case 'settings': return <Settings />
      default: return <Dashboard />
    }
  }

  return (
    <div className="app-layout">
      <Sidebar activePage={page} onNavigate={setPage} isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="main-content">
        <Topbar title={PAGE_TITLES[page] || 'Acron'} health={health} onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />
        {renderPage()}
      </div>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  )
}

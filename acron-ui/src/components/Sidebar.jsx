import {
  Bot,
  Clock3,
  Factory,
  LayoutDashboard,
  LineChart,
  Settings,
  Sparkles,
  Wrench,
} from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import { BRAND } from '../utils/constants'

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Command Center', icon: LayoutDashboard, roles: ['operator', 'supervisor', 'maintenance', 'manager', 'admin'] },
  { id: 'shopfloor', label: 'Shop Floor', icon: Factory, roles: ['operator', 'supervisor', 'maintenance', 'manager', 'admin'] },
  { id: 'analytics', label: 'Analytics', icon: LineChart, roles: ['supervisor', 'maintenance', 'manager', 'admin'] },
  { id: 'machines', label: 'Factory Setup', icon: Wrench, roles: ['supervisor', 'maintenance', 'manager', 'admin'] },
  { id: 'downtime', label: 'Downtime', icon: Clock3, roles: ['operator', 'supervisor', 'maintenance', 'manager', 'admin'] },
  { id: 'ai', label: 'AI Insights', icon: Sparkles, roles: ['supervisor', 'maintenance', 'manager', 'admin'] },
  { id: 'techmate', label: 'TechMate AI', icon: Bot, roles: ['operator', 'supervisor', 'maintenance', 'manager', 'admin'] },
  { id: 'settings', label: 'Settings', icon: Settings, roles: ['maintenance', 'manager', 'admin'] },
]

function canAccess(role, roles) {
  return roles.includes(role || 'operator')
}

export default function Sidebar({ activePage, onNavigate, isOpen, onClose }) {
  const { user, logout } = useAuth()
  const visibleItems = NAV_ITEMS.filter((item) => canAccess(user?.role, item.roles))

  return (
    <>
      {isOpen && <div style={{ position: 'fixed', inset: 0, background: 'rgba(0, 0, 0, 0.5)', zIndex: 99 }} onClick={onClose} />}
      <aside className={`sidebar${isOpen ? ' open' : ''}`}>
        <div className="sidebar-brand">
          <div className="sidebar-brand-row">
            <div className="sidebar-logo">S7</div>
            <div>
              <div className="sidebar-title">{BRAND.name}</div>
              <div className="sidebar-tagline">{BRAND.owner} / v{BRAND.version}</div>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {visibleItems.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.id}
                className={`nav-item${activePage === item.id ? ' active' : ''}`}
                onClick={() => {
                  onNavigate(item.id)
                  onClose?.()
                }}
              >
                <Icon size={18} strokeWidth={2} />
                {item.label}
              </button>
            )
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-avatar">{(user?.username || 'U')[0].toUpperCase()}</div>
            <div>
              <div className="sidebar-username">{user?.username || 'User'}</div>
              <div className="sidebar-role">{user?.role || 'operator'}</div>
            </div>
          </div>
          <button className="btn-logout" onClick={logout}>Sign Out</button>
        </div>
      </aside>
    </>
  )
}

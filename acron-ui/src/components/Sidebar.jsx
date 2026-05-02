import { useAuth } from '../auth/AuthContext'
import { BRAND } from '../utils/constants'

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Command Center', icon: '◈' },
  { id: 'shopfloor', label: 'Shop Floor', icon: '⬡' },
  { id: 'analytics', label: 'Analytics', icon: '◐' },
  { id: 'machines', label: 'Machines', icon: '⚙' },
  { id: 'downtime', label: 'Downtime', icon: '⏱' },
  { id: 'ai', label: 'AI Insights', icon: '✧' },
  { id: 'settings', label: 'Settings', icon: '☰' },
]

export default function Sidebar({ activePage, onNavigate, isOpen, onClose }) {
  const { user, logout } = useAuth()

  return (
    <>
      {isOpen && <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)', zIndex: 99 }} onClick={onClose} />}
      <aside className={`sidebar${isOpen ? ' open' : ''}`}>
        <div className="sidebar-brand">
          <div className="sidebar-brand-row">
            <div className="sidebar-logo">⚡</div>
            <div>
              <div className="sidebar-title">{BRAND.name}</div>
              <div className="sidebar-tagline">{BRAND.owner}</div>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              className={`nav-item${activePage === item.id ? ' active' : ''}`}
              onClick={() => { onNavigate(item.id); onClose?.() }}
            >
              <span style={{ fontSize: '1.1rem' }}>{item.icon}</span>
              {item.label}
            </button>
          ))}
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

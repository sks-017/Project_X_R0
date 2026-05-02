import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { HealthPill } from '../components/KpiCard'
import { BRAND } from '../utils/constants'

export default function Settings() {
  const { user } = useAuth()
  const [health, setHealth] = useState({})
  const [connectors, setConnectors] = useState([])
  const [msg, setMsg] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.getHealth(), api.getConnectors()]).then(([h, c]) => { setHealth(h); setConnectors(c); setLoading(false) })
  }, [])

  const checks = health.checks || {}
  const canReset = ['admin', 'manager'].includes(user?.role)

  const handleReset = async () => {
    setMsg(null)
    try { await api.resetDemo(); setMsg({ type: 'ok', text: 'Demo data reset successfully' }) }
    catch (err) { setMsg({ type: 'err', text: err.message }) }
  }

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <div className="page animate-in">
      <div className="page-header">
        <h1>Settings</h1>
        <p>Platform health, connector configuration, and demo operations</p>
      </div>

      <div className="grid-2 mb-24">
        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Platform Health</span>
            <span className={`badge ${health.status === 'healthy' ? 'badge-stable' : 'badge-watch'}`}>{health.status || 'unknown'}</span>
          </div>
          <table className="data-table">
            <thead><tr><th>Service</th><th>Status</th></tr></thead>
            <tbody>
              {Object.entries(checks).map(([name, check]) => (
                <tr key={name}>
                  <td style={{ fontWeight: 700, textTransform: 'capitalize' }}>{name}</td>
                  <td>
                    <HealthPill label="" status={check.status || 'unknown'} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Demo Operations</span>
          </div>
          <p className="text-secondary" style={{ fontSize: '.85rem', marginBottom: 16 }}>
            Reset restores sample factory data including machines, shift calendars, alert rules, and demo users.
          </p>
          {canReset ? (
            <button className="btn btn-primary" onClick={handleReset}>Reset Demo Data</button>
          ) : (
            <p className="text-muted" style={{ fontSize: '.84rem' }}>Demo reset is available to Manager and Admin roles.</p>
          )}
          {msg && <p style={{ color: msg.type === 'ok' ? 'var(--green)' : 'var(--red)', fontSize: '.85rem', marginTop: 12 }}>{msg.text}</p>}
          <div style={{ marginTop: 24, padding: 16, background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
            <div style={{ fontWeight: 800, fontSize: '.85rem', marginBottom: 8 }}>About {BRAND.name}</div>
            <p className="text-secondary" style={{ fontSize: '.82rem', lineHeight: 1.5 }}>
              {BRAND.name} v{BRAND.version} by {BRAND.owner}<br/>
              {BRAND.tagline}
            </p>
          </div>
        </div>
      </div>

      <div className="glass-panel">
        <div className="glass-panel-header">
          <span className="glass-panel-title">Connector Configuration</span>
          <span className="glass-panel-note">Edge gateway paths</span>
        </div>
        {connectors.length === 0 ? (
          <p className="text-muted">No connectors configured.</p>
        ) : (
          <table className="data-table">
            <thead><tr><th>Name</th><th>Protocol</th><th>Endpoint</th><th>Tags</th></tr></thead>
            <tbody>
              {connectors.map(c => (
                <tr key={c.name}>
                  <td style={{ fontWeight: 700 }}>{c.name}</td>
                  <td><span className="badge badge-info">{c.protocol}</span></td>
                  <td style={{ fontFamily: 'monospace', fontSize: '.8rem' }}>{c.endpoint}</td>
                  <td style={{ fontSize: '.8rem' }}>{JSON.stringify(c.tag_map)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

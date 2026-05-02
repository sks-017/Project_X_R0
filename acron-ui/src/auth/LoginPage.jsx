import { useState } from 'react'
import { useAuth } from './AuthContext'
import { BRAND, ROLES } from '../utils/constants'

export default function LoginPage() {
  const { login, demoLogin } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try { await login(username, password) }
    catch { setError('Invalid username or password') }
    finally { setLoading(false) }
  }

  const handleDemo = async (role) => {
    setError('')
    setLoading(true)
    try { await demoLogin(role) }
    catch { setError('Demo login unavailable') }
    finally { setLoading(false) }
  }

  return (
    <div className="login-page">
      <div className="login-brand-panel">
        <div className="login-brand-logo">⚡</div>
        <h1 className="login-brand-title">{BRAND.name}</h1>
        <p className="login-brand-tagline">
          {BRAND.tagline} An industrial IoT intelligence platform from {BRAND.owner} for
          real-time OEE, predictive maintenance, and AI-powered manufacturing insights.
        </p>
        <div className="login-stats">
          <div><div className="login-stat-value">30+</div><div className="login-stat-label">Connected Assets</div></div>
          <div><div className="login-stat-value">5</div><div className="login-stat-label">Factory Roles</div></div>
          <div><div className="login-stat-value">4</div><div className="login-stat-label">PLC Protocols</div></div>
          <div><div className="login-stat-value">AI</div><div className="login-stat-label">Anomaly Detection</div></div>
        </div>
      </div>

      <div className="login-form-panel">
        <div className="login-form-container">
          <h2 className="login-form-title">Sign in</h2>
          <p className="login-form-subtitle">Access your factory intelligence dashboard</p>

          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label className="form-label" htmlFor="login-user">Username</label>
              <input id="login-user" className="form-input" value={username} onChange={e => setUsername(e.target.value)} placeholder="admin" autoComplete="username" />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="login-pass">Password</label>
              <input id="login-pass" className="form-input" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••" autoComplete="current-password" />
            </div>
            {error && <p style={{ color: 'var(--red)', fontSize: '.84rem', marginBottom: 12 }}>{error}</p>}
            <button className="btn btn-primary w-full" type="submit" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="login-divider">or launch demo</div>

          <p className="text-secondary" style={{ fontSize: '.84rem', marginBottom: 10 }}>
            Select a role to explore the platform with live simulated data.
          </p>
          <div className="demo-roles">
            {ROLES.map(r => (
              <button key={r} className="demo-role-btn" onClick={() => handleDemo(r)} disabled={loading}>{r}</button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

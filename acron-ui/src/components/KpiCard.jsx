import { formatPercent, getStatusClass } from '../utils/constants'

export default function KpiCard({ label, value, delta, deltaLabel, className = '' }) {
  const deltaClass = delta > 0 ? 'positive' : delta < 0 ? 'negative' : 'neutral'

  return (
    <div className={`kpi-card animate-in ${className}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value ?? '—'}</div>
      {(delta != null || deltaLabel) && (
        <div className={`kpi-delta ${deltaClass}`}>
          {delta != null && (delta > 0 ? '↑ ' : delta < 0 ? '↓ ' : '')}{deltaLabel || ''}
        </div>
      )}
    </div>
  )
}

export function OeeGauge({ value, size = 140, label = 'OEE' }) {
  const radius = 56
  const circumference = 2 * Math.PI * radius
  const pct = Math.min(100, Math.max(0, value || 0))
  const offset = circumference - (pct / 100) * circumference
  const color = pct < 75 ? 'var(--red)' : pct < 85 ? 'var(--amber)' : 'var(--green)'

  return (
    <div className="gauge-container">
      <svg className="gauge-svg" viewBox="0 0 140 140" width={size} height={size}>
        <circle cx="70" cy="70" r={radius} className="gauge-bg" />
        <circle cx="70" cy="70" r={radius} className="gauge-fill"
          stroke={color}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 70 70)"
        />
        <text x="70" y="66" textAnchor="middle" className="gauge-text">{value != null ? `${value.toFixed(1)}` : '—'}</text>
        <text x="70" y="84" textAnchor="middle" className="gauge-label">{label}</text>
      </svg>
    </div>
  )
}

export function AndonTile({ name, oee, machineCount, auxCount, assets, state }) {
  const cls = getStatusClass(oee)
  return (
    <div className={`andon-tile ${cls}`}>
      <div className="andon-header">
        <span className="andon-name">{name}</span>
        <span className={`badge badge-${cls || 'info'}`}>{cls || 'waiting'}</span>
      </div>
      <div className="andon-value">{oee != null ? `${oee.toFixed(1)}% OEE` : 'No data'}</div>
      <div className="andon-meta">
        {machineCount || 0} machines, {auxCount || 0} auxiliaries<br/>
        {assets || ''}
      </div>
    </div>
  )
}

export function HealthPill({ label, status }) {
  const ok = ['up', 'connected', 'running', 'ready', 'healthy'].includes(status)
  return (
    <div className="health-pill">
      <span className={`health-dot ${ok ? 'ok' : status ? 'warn' : 'bad'}`} />
      {label}: {status || 'unknown'}
    </div>
  )
}

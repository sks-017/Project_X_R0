import { useState, useEffect } from 'react'
import { api } from '../api/client'
import KpiCard from '../components/KpiCard'
import { getStatusClass } from '../utils/constants'

export default function AiInsights() {
  const [anomalies, setAnomalies] = useState([])
  const [healthScores, setHealthScores] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.getAiAnomalies(), api.getAiHealthScores()])
      .then(([a, h]) => { setAnomalies(a); setHealthScores(h); setLoading(false) })
  }, [])

  const avgHealth = healthScores.length ? healthScores.reduce((s, h) => s + h.health_score, 0) / healthScores.length : null
  const anomalyCount = anomalies.length
  const criticalEquipment = healthScores.filter(h => h.health_score < 60).length

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <div className="page animate-in">
      <div className="page-header">
        <h1>AI Insights</h1>
        <p>Anomaly detection, health scoring, and predictive analytics powered by machine learning</p>
      </div>

      <div className="kpi-grid mb-24">
        <KpiCard label="Avg Health Score" value={avgHealth != null ? `${avgHealth.toFixed(0)}/100` : '—'} className="animate-in-delay-1" />
        <KpiCard label="Active Anomalies" value={anomalyCount} className="animate-in-delay-2" />
        <KpiCard label="At-Risk Equipment" value={criticalEquipment} className="animate-in-delay-3" />
        <KpiCard label="ML Model" value="Active" deltaLabel="IsolationForest" className="animate-in-delay-4" />
      </div>

      <div className="grid-2 mb-24">
        {/* Health Scores */}
        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Equipment Health Scores</span>
            <span className="glass-panel-note">AI-computed composite score (0-100)</span>
          </div>
          {healthScores.length === 0 ? (
            <p className="text-muted">Health scoring will activate once telemetry history builds up. The AI model requires ~30 minutes of data.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[...healthScores].sort((a,b) => a.health_score - b.health_score).map(h => (
                <div key={h.equipment_id} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ width: 70, fontSize: '.8rem', fontWeight: 700, textAlign: 'right' }}>{h.equipment_id}</span>
                  <div className="progress-bar" style={{ flex: 1 }}>
                    <div className="progress-fill" style={{ width: `${h.health_score}%`, background: h.health_score < 60 ? 'var(--red)' : h.health_score < 80 ? 'var(--amber)' : 'var(--green)' }} />
                  </div>
                  <span style={{ width: 36, fontSize: '.8rem', fontWeight: 700, color: h.health_score < 60 ? 'var(--red)' : h.health_score < 80 ? 'var(--amber)' : 'var(--green)' }}>{h.health_score}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Anomalies */}
        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Detected Anomalies</span>
            <span className="glass-panel-note">IsolationForest detection</span>
          </div>
          {anomalies.length === 0 ? (
            <p className="text-muted">No anomalies detected. The system monitors telemetry patterns and flags deviations from normal operating envelopes.</p>
          ) : (
            <table className="data-table">
              <thead><tr><th>Machine</th><th>Metric</th><th>Value</th><th>Severity</th></tr></thead>
              <tbody>
                {anomalies.map((a, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 700 }}>{a.equipment_id}</td>
                    <td>{a.metric}</td>
                    <td>{typeof a.value === 'number' ? a.value.toFixed(2) : a.value}</td>
                    <td><span className={`badge badge-${a.severity === 'critical' ? 'critical' : 'watch'}`}>{a.severity}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* AI Capabilities */}
      <div className="glass-panel">
        <div className="glass-panel-header">
          <span className="glass-panel-title">Intelligence Capabilities</span>
        </div>
        <div className="grid-3">
          {[
            { icon: '🔍', title: 'Anomaly Detection', desc: 'IsolationForest algorithm identifies outlier telemetry patterns in real-time.' },
            { icon: '💚', title: 'Health Scoring', desc: 'Composite health score (0-100) combining OEE, anomaly frequency, and trend stability.' },
            { icon: '📈', title: 'RUL Prediction', desc: 'Remaining Useful Life estimation based on degradation trend analysis.' },
          ].map(cap => (
            <div key={cap.title} style={{ padding: 16 }}>
              <div style={{ fontSize: '1.5rem', marginBottom: 8 }}>{cap.icon}</div>
              <div style={{ fontWeight: 800, fontSize: '.9rem', marginBottom: 6 }}>{cap.title}</div>
              <p className="text-secondary" style={{ fontSize: '.82rem', lineHeight: 1.5 }}>{cap.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

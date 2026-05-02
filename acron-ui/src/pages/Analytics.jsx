import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { OeeGauge } from '../components/KpiCard'

export default function Analytics() {
  const [oee, setOee] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { api.getOee().then(o => { setOee(o); setLoading(false) }) }, [])

  const avg = (key) => oee.length ? oee.reduce((s, o) => s + o[key], 0) / oee.length : null
  const totalDowntime = oee.reduce((s, o) => s + (o.loss_tree?.downtime_minutes || 0), 0)
  const avgPerfLoss = avg('performance') != null ? (100 - avg('performance')).toFixed(1) : '—'
  const avgQualLoss = avg('quality') != null ? (100 - avg('quality')).toFixed(1) : '—'

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <div className="page animate-in">
      <div className="page-header">
        <h1>Analytics</h1>
        <p>OEE components, loss tree analysis, and performance trends</p>
      </div>

      {/* OEE Component Gauges */}
      <div className="grid-3 mb-24">
        {[{ key: 'availability', label: 'Availability' }, { key: 'performance', label: 'Performance' }, { key: 'quality', label: 'Quality' }].map(({ key, label }) => (
          <div key={key} className="glass-panel" style={{ textAlign: 'center' }}>
            <OeeGauge value={avg(key)} label={label} size={150} />
          </div>
        ))}
      </div>

      {/* Loss Tree */}
      <div className="grid-2 mb-24">
        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Loss Tree</span>
            <span className="glass-panel-note">Where production is lost</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {[
              { label: 'Downtime', value: `${totalDowntime.toFixed(0)} min`, color: 'var(--red)', pct: Math.min(100, totalDowntime / 5) },
              { label: 'Performance Loss', value: `${avgPerfLoss}%`, color: 'var(--amber)', pct: parseFloat(avgPerfLoss) || 0 },
              { label: 'Quality Loss', value: `${avgQualLoss}%`, color: 'var(--blue)', pct: parseFloat(avgQualLoss) || 0 },
            ].map(item => (
              <div key={item.label}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontWeight: 700, fontSize: '.85rem' }}>{item.label}</span>
                  <span style={{ fontWeight: 800, fontSize: '.85rem', color: item.color }}>{item.value}</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${item.pct}%`, background: item.color }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* OEE Composition */}
        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Plant OEE</span>
          </div>
          <div style={{ textAlign: 'center' }}>
            <OeeGauge value={avg('oee')} label="Overall OEE" size={180} />
            <p className="text-secondary" style={{ marginTop: 12, fontSize: '.85rem' }}>
              {oee.length} machines monitored · Target: 85%
            </p>
          </div>
        </div>
      </div>

      {/* Machine OEE Table */}
      <div className="glass-panel">
        <div className="glass-panel-header">
          <span className="glass-panel-title">Machine OEE Breakdown</span>
          <span className="glass-panel-note">Sorted by OEE risk</span>
        </div>
        <table className="data-table">
          <thead><tr><th>Machine</th><th>OEE</th><th>Availability</th><th>Performance</th><th>Quality</th><th>Downtime</th></tr></thead>
          <tbody>
            {[...oee].sort((a,b) => a.oee - b.oee).map(o => (
              <tr key={o.equipment_id}>
                <td style={{ fontWeight: 700 }}>{o.equipment_id}</td>
                <td style={{ fontWeight: 700, color: o.oee < 75 ? 'var(--red)' : o.oee < 85 ? 'var(--amber)' : 'var(--green)' }}>{o.oee.toFixed(1)}%</td>
                <td>{o.availability.toFixed(1)}%</td>
                <td>{o.performance.toFixed(1)}%</td>
                <td>{o.quality.toFixed(1)}%</td>
                <td>{(o.loss_tree?.downtime_minutes || 0).toFixed(0)} min</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

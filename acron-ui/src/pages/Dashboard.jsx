import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import KpiCard, { OeeGauge, AndonTile } from '../components/KpiCard'
import { formatPercent, getStatusClass } from '../utils/constants'

export default function Dashboard() {
  const [machines, setMachines] = useState([])
  const [oee, setOee] = useState([])
  const [telemetry, setTelemetry] = useState({})
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    const [m, o, t] = await Promise.all([api.getMachines(), api.getOee(), api.getTelemetry()])
    setMachines(m); setOee(o); setTelemetry(t)
    setLoading(false)
  }, [])

  useEffect(() => { fetchData(); const id = setInterval(fetchData, 8000); return () => clearInterval(id) }, [fetchData])

  const oeeMap = Object.fromEntries(oee.map(o => [o.equipment_id, o]))
  const avgOee = oee.length ? oee.reduce((s, o) => s + o.oee, 0) / oee.length : null
  const liveCount = Object.keys(telemetry).length
  const stableCount = oee.filter(o => o.oee >= 85).length
  const watchCount = oee.filter(o => o.oee >= 75 && o.oee < 85).length
  const criticalCount = oee.filter(o => o.oee < 75).length

  // Group machines by cell
  const cellMap = {}
  machines.forEach(m => {
    const cell = m.cell || 'Unassigned'
    if (!cellMap[cell]) cellMap[cell] = { machines: [], oees: [] }
    cellMap[cell].machines.push(m)
    const o = oeeMap[m.equipment_id]
    if (o) cellMap[cell].oees.push(o.oee)
  })

  // Priority list — bottom 6 by OEE
  const priority = [...oee].sort((a, b) => a.oee - b.oee).slice(0, 6)

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <div className="page animate-in">
      <div className="page-header">
        <h1>Command Center</h1>
        <p>Real-time factory intelligence overview</p>
      </div>

      <div className="kpi-grid">
        <KpiCard label="Average OEE" value={avgOee != null ? `${avgOee.toFixed(1)}%` : '—'}
          delta={avgOee != null ? avgOee - 85 : null} deltaLabel={avgOee != null ? `${(avgOee - 85).toFixed(1)} vs target` : ''} className="animate-in-delay-1" />
        <KpiCard label="Live Assets" value={`${liveCount} / ${machines.length}`} className="animate-in-delay-2" />
        <KpiCard label="Stable" value={stableCount} className="animate-in-delay-3" />
        <KpiCard label="Watch" value={watchCount} className="animate-in-delay-3" />
        <KpiCard label="Critical" value={criticalCount} className="animate-in-delay-4" />
      </div>

      <div className="grid-60-40 mb-24">
        {/* OEE Bar Chart */}
        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">OEE by Machine</span>
            <span className="glass-panel-note">Lowest first</span>
          </div>
          {oee.length === 0 ? <p className="text-muted">Waiting for telemetry...</p> : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[...oee].sort((a,b) => a.oee - b.oee).slice(0, 12).map(o => (
                <div key={o.equipment_id} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ width: 70, fontSize: '.8rem', fontWeight: 700, textAlign: 'right' }}>{o.equipment_id}</span>
                  <div className="progress-bar" style={{ flex: 1 }}>
                    <div className="progress-fill" style={{ width: `${o.oee}%`, background: o.oee < 75 ? 'var(--red)' : o.oee < 85 ? 'var(--amber)' : 'var(--green)' }} />
                  </div>
                  <span style={{ width: 48, fontSize: '.8rem', fontWeight: 700, color: o.oee < 75 ? 'var(--red)' : o.oee < 85 ? 'var(--amber)' : 'var(--green)' }}>{o.oee.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Priority Board */}
        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Priority Board</span>
            <span className="glass-panel-note">Focus areas</span>
          </div>
          {priority.length === 0 ? <p className="text-muted">No data yet</p> : (
            <table className="data-table">
              <thead><tr><th>Machine</th><th>OEE</th><th>Status</th></tr></thead>
              <tbody>
                {priority.map(p => (
                  <tr key={p.equipment_id}>
                    <td style={{ fontWeight: 700 }}>{p.equipment_id}</td>
                    <td>{p.oee.toFixed(1)}%</td>
                    <td><span className={`badge badge-${getStatusClass(p.oee)}`}>{getStatusClass(p.oee)}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Andon Board */}
      <div className="glass-panel mb-24">
        <div className="glass-panel-header">
          <span className="glass-panel-title">Andon Board</span>
          <span className="glass-panel-note">Grouped by production cell</span>
        </div>
        <div className="andon-grid">
          {Object.entries(cellMap).sort(([a],[b]) => a.localeCompare(b)).map(([cell, data]) => {
            const avg = data.oees.length ? data.oees.reduce((s,v) => s+v, 0) / data.oees.length : null
            const immCount = data.machines.filter(m => m.equipment_type === 'IMM').length
            return (
              <AndonTile key={cell} name={cell} oee={avg} machineCount={immCount}
                auxCount={data.machines.length - immCount}
                assets={data.machines.slice(0,4).map(m=>m.equipment_id).join(', ')}
                state={getStatusClass(avg)} />
            )
          })}
        </div>
      </div>

      {/* OEE Components */}
      <div className="grid-3">
        {avgOee != null && ['Availability', 'Performance', 'Quality'].map(comp => {
          const key = comp.toLowerCase()
          const avg = oee.reduce((s, o) => s + o[key], 0) / oee.length
          return (
            <div key={comp} className="glass-panel" style={{ textAlign: 'center' }}>
              <OeeGauge value={avg} label={comp} size={130} />
            </div>
          )
        })}
      </div>
    </div>
  )
}

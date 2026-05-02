import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import { getStatusClass, formatNumber } from '../utils/constants'

export default function Machines() {
  const [machines, setMachines] = useState([])
  const [oee, setOee] = useState([])
  const [filter, setFilter] = useState({ line: '', type: '', state: '' })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.getMachines(), api.getOee()]).then(([m, o]) => { setMachines(m); setOee(o); setLoading(false) })
  }, [])

  const oeeMap = Object.fromEntries(oee.map(o => [o.equipment_id, o]))

  let rows = machines.map(m => {
    const o = oeeMap[m.equipment_id] || {}
    return { ...m, oee: o.oee, availability: o.availability, performance: o.performance, quality: o.quality, state: getStatusClass(o.oee) || 'waiting' }
  })

  if (filter.line) rows = rows.filter(r => r.line === filter.line)
  if (filter.type) rows = rows.filter(r => r.equipment_type === filter.type)
  if (filter.state) rows = rows.filter(r => r.state === filter.state)

  const lines = [...new Set(machines.map(m => m.line).filter(Boolean))].sort()
  const types = [...new Set(machines.map(m => m.equipment_type).filter(Boolean))].sort()

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <div className="page animate-in">
      <div className="page-header">
        <h1>Machine Master</h1>
        <p>Plant → Line → Cell → Machine configuration and live status</p>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <select className="form-select" style={{ width: 160 }} value={filter.line} onChange={e => setFilter(f => ({...f, line: e.target.value}))}>
          <option value="">All Lines</option>
          {lines.map(l => <option key={l} value={l}>{l}</option>)}
        </select>
        <select className="form-select" style={{ width: 160 }} value={filter.type} onChange={e => setFilter(f => ({...f, type: e.target.value}))}>
          <option value="">All Types</option>
          {types.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <select className="form-select" style={{ width: 160 }} value={filter.state} onChange={e => setFilter(f => ({...f, state: e.target.value}))}>
          <option value="">All States</option>
          <option value="stable">Stable</option>
          <option value="watch">Watch</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      <div className="glass-panel">
        <table className="data-table">
          <thead>
            <tr><th>Machine</th><th>Type</th><th>Line</th><th>Cell</th><th>Process</th><th>Model</th><th>OEE</th><th>Avail.</th><th>Perf.</th><th>Quality</th><th>State</th></tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.equipment_id}>
                <td style={{ fontWeight: 700 }}>{r.equipment_id}</td>
                <td>{r.equipment_type}</td>
                <td>{r.line || '—'}</td>
                <td>{r.cell || '—'}</td>
                <td>{r.process || '—'}</td>
                <td>{r.mold_model || '—'}</td>
                <td style={{ fontWeight: 700, color: r.oee != null ? (r.oee < 75 ? 'var(--red)' : r.oee < 85 ? 'var(--amber)' : 'var(--green)') : 'var(--text-muted)' }}>
                  {r.oee != null ? `${r.oee.toFixed(1)}%` : '—'}
                </td>
                <td>{r.availability != null ? `${r.availability.toFixed(1)}%` : '—'}</td>
                <td>{r.performance != null ? `${r.performance.toFixed(1)}%` : '—'}</td>
                <td>{r.quality != null ? `${r.quality.toFixed(1)}%` : '—'}</td>
                <td><span className={`badge badge-${r.state}`}>{r.state}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && <p className="text-muted" style={{ padding: 20, textAlign: 'center' }}>No machines match filters</p>}
      </div>
    </div>
  )
}

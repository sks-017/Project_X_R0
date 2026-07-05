import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import KpiCard, { OeeGauge } from '../components/KpiCard'
import { formatPercent } from '../utils/constants'

function formatWindow(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

export default function Analytics() {
  const [report, setReport] = useState(null)
  const [shiftCalendars, setShiftCalendars] = useState([])
  const [scope, setScope] = useState('shift')
  const [shiftName, setShiftName] = useState('')
  const [referenceDate, setReferenceDate] = useState(new Date().toISOString().slice(0, 10))
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getShiftCalendars().then((rows) => {
      setShiftCalendars(rows)
      if (!shiftName && rows.length) setShiftName(rows[0].shift_name)
    })
  }, [shiftName])

  const loadReport = useCallback(async () => {
    if (scope === 'shift' && !shiftName) return
    setLoading(true)
    setError('')
    try {
      const data = await api.getOeeReport({
        scope,
        shiftName: scope === 'shift' ? shiftName : undefined,
        referenceDate,
      })
      setReport(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [referenceDate, scope, shiftName])

  useEffect(() => {
    loadReport()
  }, [loadReport])

  const losses = useMemo(() => {
    const totals = {}
    const machines = report?.machines || []
    machines.forEach((item) => {
      Object.entries(item.loss_tree || {}).forEach(([key, value]) => {
        totals[key] = (totals[key] || 0) + Number(value || 0)
      })
    })
    return Object.entries(totals).sort((left, right) => right[1] - left[1])
  }, [report])

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  const summary = report?.summary || {}
  const machines = report?.machines || []
  const availableShifts = Array.from(new Set(shiftCalendars.map((item) => item.shift_name)))

  return (
    <div className="page animate-in">
      <div className="page-header">
        <h1>OEE Reporting</h1>
        <p>Shift, day, and month reporting for the Phase 2 operational rollout.</p>
      </div>

      {error && (
        <div className="glass-panel mb-24" style={{ borderColor: 'rgba(239, 68, 68, 0.35)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
            <p style={{ color: 'var(--red)', fontWeight: 700 }}>Report load failed: {error}</p>
            <button className="btn btn-secondary" onClick={loadReport}>Retry</button>
          </div>
        </div>
      )}

      <div className="glass-panel mb-24">
        <div className="glass-panel-header">
          <span className="glass-panel-title">Report Controls</span>
          <span className="glass-panel-note">Window: {formatWindow(report?.window_start)} to {formatWindow(report?.window_end)}</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12 }}>
          <select className="form-select" value={scope} onChange={(event) => setScope(event.target.value)}>
            <option value="shift">Shift</option>
            <option value="day">Day</option>
            <option value="month">Month</option>
          </select>
          {scope === 'shift' ? (
            <select className="form-select" value={shiftName} onChange={(event) => setShiftName(event.target.value)}>
              {availableShifts.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          ) : (
            <input className="form-input" type="date" value={referenceDate} onChange={(event) => setReferenceDate(event.target.value)} />
          )}
          {scope === 'shift' && <input className="form-input" type="date" value={referenceDate} onChange={(event) => setReferenceDate(event.target.value)} />}
          <button className="btn btn-secondary" onClick={loadReport}>Refresh report</button>
        </div>
      </div>

      <div className="kpi-grid">
        <KpiCard label="Overall OEE" value={summary.oee != null ? formatPercent(summary.oee) : '-'} deltaLabel={`${summary.machines || 0} machines in scope`} />
        <KpiCard label="Attainment" value={summary.attainment != null ? formatPercent(summary.attainment) : '-'} deltaLabel={`${summary.actual_parts || 0} / ${summary.target_parts || 0} parts`} />
        <KpiCard label="Downtime" value={summary.downtime_minutes != null ? `${summary.downtime_minutes.toFixed(0)} min` : '-'} deltaLabel="Captured losses in window" />
        <KpiCard label="Plant" value={report?.plant_code || '-'} deltaLabel={report?.shift_name ? `Shift ${report.shift_name}` : scope} />
      </div>

      <div className="grid-2 mb-24">
        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">OEE Components</span>
            <span className="glass-panel-note">Availability x Performance x Quality</span>
          </div>
          <div className="grid-3">
            <div style={{ textAlign: 'center' }}><OeeGauge value={summary.availability} label="Availability" size={130} /></div>
            <div style={{ textAlign: 'center' }}><OeeGauge value={summary.performance} label="Performance" size={130} /></div>
            <div style={{ textAlign: 'center' }}><OeeGauge value={summary.quality} label="Quality" size={130} /></div>
          </div>
        </div>

        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Loss Tree</span>
            <span className="glass-panel-note">Top recurring losses by minutes</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {losses.slice(0, 5).map(([label, value], index) => (
              <div key={label}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontWeight: 700, textTransform: 'capitalize' }}>{label}</span>
                  <span style={{ color: index === 0 ? 'var(--red)' : 'var(--text-secondary)', fontWeight: 700 }}>{value.toFixed(1)} min</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${Math.min(100, value)}%`, background: index === 0 ? 'var(--red)' : index === 1 ? 'var(--amber)' : 'var(--blue)' }} />
                </div>
              </div>
            ))}
            {losses.length === 0 && <p className="text-secondary">No downtime categories were recorded in the selected window.</p>}
          </div>
        </div>
      </div>

      <div className="glass-panel">
        <div className="glass-panel-header">
          <span className="glass-panel-title">Machine Report</span>
          <span className="glass-panel-note">Sorted by OEE to surface the biggest execution risk first</span>
        </div>
        <table className="data-table">
          <thead><tr><th>Machine</th><th>Line</th><th>Cell</th><th>Process</th><th>OEE</th><th>Avail.</th><th>Perf.</th><th>Quality</th><th>Target</th><th>Actual</th><th>Cycle</th><th>Downtime</th></tr></thead>
          <tbody>
            {machines.map((item) => (
              <tr key={item.equipment_id}>
                <td style={{ fontWeight: 700 }}>{item.equipment_id}</td>
                <td>{item.line || '-'}</td>
                <td>{item.cell || '-'}</td>
                <td>{item.process || '-'}</td>
                <td style={{ color: item.oee < 75 ? 'var(--red)' : item.oee < 85 ? 'var(--amber)' : 'var(--green)', fontWeight: 700 }}>{formatPercent(item.oee)}</td>
                <td>{formatPercent(item.availability)}</td>
                <td>{formatPercent(item.performance)}</td>
                <td>{formatPercent(item.quality)}</td>
                <td>{item.target_parts}</td>
                <td>{item.actual_parts}</td>
                <td>{item.avg_cycle_time}s / {item.standard_cycle_time}s</td>
                <td>{item.downtime_minutes.toFixed(1)} min</td>
              </tr>
            ))}
          </tbody>
        </table>
        {machines.length === 0 && <p className="text-muted" style={{ paddingTop: 16, textAlign: 'center' }}>No machine data is available for this report window.</p>}
      </div>
    </div>
  )
}


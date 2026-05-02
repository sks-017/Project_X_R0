import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import { getStatusClass } from '../utils/constants'

export default function ShopFloor() {
  const [machines, setMachines] = useState([])
  const [telemetry, setTelemetry] = useState({})
  const [oee, setOee] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    const [m, t, o] = await Promise.all([api.getMachines(), api.getTelemetry(), api.getOee()])
    setMachines(m); setTelemetry(t); setOee(o); setLoading(false)
  }, [])

  useEffect(() => { fetchData(); const id = setInterval(fetchData, 6000); return () => clearInterval(id) }, [fetchData])

  const oeeMap = Object.fromEntries(oee.map(o => [o.equipment_id, o]))

  // Group by line
  const lineMap = {}
  machines.forEach(m => {
    const line = m.line || 'Unassigned'
    if (!lineMap[line]) lineMap[line] = []
    lineMap[line].push(m)
  })

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <div className="page animate-in">
      <div className="page-header">
        <h1>Shop Floor</h1>
        <p>Live machine telemetry with real-time status updates</p>
      </div>

      {Object.entries(lineMap).sort().map(([line, items]) => (
        <div key={line} className="mb-24">
          <h3 style={{ marginBottom: 12, fontSize: '1rem' }}>{line}</h3>
          <div className="andon-grid">
            {items.map(m => {
              const live = telemetry[m.equipment_id]
              const metrics = live?.metrics || {}
              const o = oeeMap[m.equipment_id]
              const cls = getStatusClass(o?.oee)
              return (
                <div key={m.equipment_id} className={`andon-tile ${cls}`}>
                  <div className="andon-header">
                    <span className="andon-name">{m.equipment_id}</span>
                    <span className={`badge badge-${cls || 'info'}`}>{m.equipment_type}</span>
                  </div>
                  {o && <div className="andon-value" style={{ color: o.oee < 75 ? 'var(--red)' : o.oee < 85 ? 'var(--amber)' : 'var(--green)' }}>{o.oee.toFixed(1)}% OEE</div>}
                  <div className="andon-meta">
                    {metrics.cycle_time != null && <span>Cycle: {Number(metrics.cycle_time).toFixed(1)}s · </span>}
                    {metrics.mold_temp != null && <span>Temp: {Number(metrics.mold_temp).toFixed(1)}°C · </span>}
                    {m.process && <span>{m.process}</span>}
                    {m.mold_model && <><br/>Model: {m.mold_model}</>}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}

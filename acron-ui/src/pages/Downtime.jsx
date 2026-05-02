import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'

export default function Downtime() {
  const { user } = useAuth()
  const [machines, setMachines] = useState([])
  const [reasons, setReasons] = useState([])
  const [form, setForm] = useState({ equipment_id: '', reason_code: '', category: '', minutes: 10, comment: '' })
  const [msg, setMsg] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.getMachines(), api.getDowntimeReasons()]).then(([m, r]) => {
      setMachines(m); setReasons(r)
      if (m.length) setForm(f => ({ ...f, equipment_id: m[0].equipment_id }))
      if (r.length) setForm(f => ({ ...f, reason_code: r[0].code, category: r[0].category }))
      setLoading(false)
    })
  }, [])

  const submit = async (e) => {
    e.preventDefault()
    setMsg(null)
    try {
      await api.postDowntime(form)
      setMsg({ type: 'ok', text: 'Downtime logged successfully' })
      setForm(f => ({ ...f, minutes: 10, comment: '' }))
    } catch (err) {
      setMsg({ type: 'err', text: err.message })
    }
  }

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <div className="page animate-in">
      <div className="page-header">
        <h1>Downtime Capture</h1>
        <p>Log production stoppages with reason codes and operator notes</p>
      </div>

      <div className="grid-2">
        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Log Downtime Event</span>
          </div>
          <form onSubmit={submit}>
            <div className="form-group">
              <label className="form-label">Machine</label>
              <select className="form-select" value={form.equipment_id} onChange={e => setForm(f => ({...f, equipment_id: e.target.value}))}>
                {machines.map(m => <option key={m.equipment_id} value={m.equipment_id}>{m.equipment_id} — {m.equipment_type}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Reason</label>
              <select className="form-select" value={form.reason_code} onChange={e => {
                const r = reasons.find(r => r.code === e.target.value) || {}
                setForm(f => ({...f, reason_code: r.code || '', category: r.category || ''}))
              }}>
                {reasons.map(r => <option key={r.code} value={r.code}>{r.label}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Duration (minutes)</label>
              <input className="form-input" type="number" min="1" max="480" value={form.minutes} onChange={e => setForm(f => ({...f, minutes: Number(e.target.value)}))} />
            </div>
            <div className="form-group">
              <label className="form-label">Comment</label>
              <textarea className="form-textarea" value={form.comment} onChange={e => setForm(f => ({...f, comment: e.target.value}))} placeholder="Short production note..." />
            </div>
            {msg && <p style={{ color: msg.type === 'ok' ? 'var(--green)' : 'var(--red)', fontSize: '.85rem', marginBottom: 12 }}>{msg.text}</p>}
            <button className="btn btn-primary w-full" type="submit">Log Downtime</button>
          </form>
        </div>

        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Reason Codes</span>
            <span className="glass-panel-note">Standard loss taxonomy</span>
          </div>
          <table className="data-table">
            <thead><tr><th>Code</th><th>Category</th><th>Label</th></tr></thead>
            <tbody>
              {reasons.map(r => (
                <tr key={r.code}>
                  <td style={{ fontWeight: 700, fontFamily: 'monospace', fontSize: '.8rem' }}>{r.code}</td>
                  <td>{r.category}</td>
                  <td>{r.label}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import KpiCard from '../components/KpiCard'
import { formatPercent, getStatusClass } from '../utils/constants'

const MACHINE_TEMPLATE = {
  equipment_id: '',
  equipment_type: 'IMM',
  description: '',
  plant: 'S7-PUNE-01',
  line: 'LINE-A',
  cell: 'CELL-01',
  process: 'Injection Molding',
  mold_model: '',
  plc_protocol: 'mitsubishi_mc',
  plc_address: '',
  cycle_time_standard: 35,
  target_per_hour: 240,
}

const SHIFT_TEMPLATE = {
  plant_code: 'S7-PUNE-01',
  shift_name: 'A',
  starts_at: '06:00',
  ends_at: '14:00',
  planned_downtime_minutes: 30,
  active: true,
}

const TARGET_TEMPLATE = {
  equipment_id: '',
  shift_name: 'A',
  target_parts: 1920,
  standard_cycle_time: 35,
  quality_target: 0.98,
}

function canAccess(role, allowedRoles) {
  return allowedRoles.includes(role || 'operator')
}

export default function Machines() {
  const { user } = useAuth()
  const [machines, setMachines] = useState([])
  const [oee, setOee] = useState([])
  const [shiftCalendars, setShiftCalendars] = useState([])
  const [standards, setStandards] = useState([])
  const [filter, setFilter] = useState({ line: '', type: '', state: '' })
  const [machineForm, setMachineForm] = useState(MACHINE_TEMPLATE)
  const [shiftForm, setShiftForm] = useState(SHIFT_TEMPLATE)
  const [targetForm, setTargetForm] = useState(TARGET_TEMPLATE)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState({ machine: false, shift: false, target: false })
  const [message, setMessage] = useState(null)
  const [error, setError] = useState('')

  const canEditMachine = canAccess(user?.role, ['admin', 'manager'])
  const canEditShift = canAccess(user?.role, ['admin', 'manager'])
  const canEditTarget = canAccess(user?.role, ['admin', 'manager', 'supervisor'])

  const loadData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [machineRows, oeeRows, shiftRows, standardRows] = await Promise.all([
        api.getMachines(),
        api.getOee(),
        api.getShiftCalendars(),
        api.getTargetStandards(),
      ])
      setMachines(machineRows)
      setOee(oeeRows)
      setShiftCalendars(shiftRows)
      setStandards(standardRows)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  useEffect(() => {
    if (machines.length && !targetForm.equipment_id) {
      setTargetForm((current) => ({ ...current, equipment_id: machines[0].equipment_id }))
    }
  }, [machines, targetForm.equipment_id])

  const oeeMap = useMemo(() => Object.fromEntries(oee.map((item) => [item.equipment_id, item])), [oee])

  const rows = useMemo(() => {
    let next = machines.map((machine) => {
      const snapshot = oeeMap[machine.equipment_id] || {}
      return {
        ...machine,
        oee: snapshot.oee ?? null,
        availability: snapshot.availability ?? null,
        performance: snapshot.performance ?? null,
        quality: snapshot.quality ?? null,
        state: getStatusClass(snapshot.oee) || 'waiting',
      }
    })

    if (filter.line) next = next.filter((item) => item.line === filter.line)
    if (filter.type) next = next.filter((item) => item.equipment_type === filter.type)
    if (filter.state) next = next.filter((item) => item.state === filter.state)

    return next.sort((left, right) => (right.oee ?? 0) - (left.oee ?? 0))
  }, [machines, oeeMap, filter])

  const summary = useMemo(() => {
    const validOee = rows.filter((item) => item.oee != null)
    const averageOee = validOee.length ? validOee.reduce((sum, item) => sum + item.oee, 0) / validOee.length : null
    return {
      averageOee,
      machines: machines.length,
      lines: new Set(machines.map((item) => item.line).filter(Boolean)).size,
      activeShifts: shiftCalendars.filter((item) => item.active).length,
      standards: standards.length,
    }
  }, [machines, rows, shiftCalendars, standards])

  const lines = [...new Set(machines.map((item) => item.line).filter(Boolean))].sort()
  const types = [...new Set(machines.map((item) => item.equipment_type).filter(Boolean))].sort()
  const shiftNames = [...new Set(shiftCalendars.map((item) => item.shift_name))]

  const updateMachineForm = (field) => (event) => setMachineForm((current) => ({ ...current, [field]: event.target.value }))
  const updateShiftForm = (field) => (event) => setShiftForm((current) => ({ ...current, [field]: event.target.value }))
  const updateTargetForm = (field) => (event) => setTargetForm((current) => ({ ...current, [field]: event.target.value }))

  const handleMachineSave = async (event) => {
    event.preventDefault()
    setSaving((current) => ({ ...current, machine: true }))
    setMessage(null)
    try {
      await api.saveMachine({
        ...machineForm,
        cycle_time_standard: Number(machineForm.cycle_time_standard),
        target_per_hour: Number(machineForm.target_per_hour),
      })
      setMessage({ type: 'ok', text: `Machine ${machineForm.equipment_id} saved to the factory master.` })
      setMachineForm(MACHINE_TEMPLATE)
      await loadData()
    } catch (err) {
      setMessage({ type: 'err', text: err.message })
    } finally {
      setSaving((current) => ({ ...current, machine: false }))
    }
  }

  const handleShiftSave = async (event) => {
    event.preventDefault()
    setSaving((current) => ({ ...current, shift: true }))
    setMessage(null)
    try {
      await api.saveShiftCalendar({
        ...shiftForm,
        planned_downtime_minutes: Number(shiftForm.planned_downtime_minutes),
        active: shiftForm.active === true || shiftForm.active === 'true',
      })
      setMessage({ type: 'ok', text: `Shift ${shiftForm.shift_name} updated for ${shiftForm.plant_code}.` })
      await loadData()
    } catch (err) {
      setMessage({ type: 'err', text: err.message })
    } finally {
      setSaving((current) => ({ ...current, shift: false }))
    }
  }

  const handleTargetSave = async (event) => {
    event.preventDefault()
    setSaving((current) => ({ ...current, target: true }))
    setMessage(null)
    try {
      await api.saveTargetStandard({
        ...targetForm,
        target_parts: Number(targetForm.target_parts),
        standard_cycle_time: Number(targetForm.standard_cycle_time),
        quality_target: Number(targetForm.quality_target),
      })
      setMessage({ type: 'ok', text: `Target standard saved for ${targetForm.equipment_id} / Shift ${targetForm.shift_name}.` })
      await loadData()
    } catch (err) {
      setMessage({ type: 'err', text: err.message })
    } finally {
      setSaving((current) => ({ ...current, target: false }))
    }
  }

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <div className="page animate-in">
      <div className="page-header">
        <h1>Factory Setup</h1>
        <p>Machine master, shift pattern, and target standards for the Acron Phase 2 rollout.</p>
      </div>

      {message && (
        <div className="glass-panel mb-24" style={{ borderColor: message.type === 'ok' ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)' }}>
          <p style={{ color: message.type === 'ok' ? 'var(--green)' : 'var(--red)', fontWeight: 700 }}>{message.text}</p>
        </div>
      )}

      {error && (
        <div className="glass-panel mb-24" style={{ borderColor: 'rgba(239, 68, 68, 0.35)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
            <p style={{ color: 'var(--red)', fontWeight: 700 }}>Factory setup could not load: {error}</p>
            <button className="btn btn-secondary" onClick={loadData}>Retry</button>
          </div>
        </div>
      )}

      <div className="kpi-grid">
        <KpiCard label="Active Machines" value={summary.machines} deltaLabel={`${summary.lines} lines connected`} />
        <KpiCard label="Average OEE" value={summary.averageOee != null ? formatPercent(summary.averageOee) : '-'} deltaLabel="Current fleet health" />
        <KpiCard label="Shift Calendars" value={summary.activeShifts} deltaLabel="Production windows live" />
        <KpiCard label="Target Standards" value={summary.standards} deltaLabel="Cycle and quality baselines" />
      </div>

      <div className="glass-panel mb-24" style={{ paddingBottom: 16 }}>
        <div className="glass-panel-header">
          <span className="glass-panel-title">Operational Filters</span>
          <span className="glass-panel-note">Live status from the GitHub-backed V2 build</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12 }}>
          <select className="form-select" value={filter.line} onChange={(event) => setFilter((current) => ({ ...current, line: event.target.value }))}>
            <option value="">All lines</option>
            {lines.map((line) => <option key={line} value={line}>{line}</option>)}
          </select>
          <select className="form-select" value={filter.type} onChange={(event) => setFilter((current) => ({ ...current, type: event.target.value }))}>
            <option value="">All equipment</option>
            {types.map((type) => <option key={type} value={type}>{type}</option>)}
          </select>
          <select className="form-select" value={filter.state} onChange={(event) => setFilter((current) => ({ ...current, state: event.target.value }))}>
            <option value="">All states</option>
            <option value="stable">Stable</option>
            <option value="watch">Watch</option>
            <option value="critical">Critical</option>
          </select>
          <button className="btn btn-secondary" onClick={() => setFilter({ line: '', type: '', state: '' })}>Clear filters</button>
        </div>
      </div>

      <div className="grid-2 mb-24">
        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Machine Master</span>
            <span className="glass-panel-note">Plant, line, cell, machine, and process</span>
          </div>
          {canEditMachine ? (
            <form onSubmit={handleMachineSave}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 12 }}>
                <div className="form-group"><label className="form-label">Equipment ID</label><input className="form-input" value={machineForm.equipment_id} onChange={updateMachineForm('equipment_id')} placeholder="IMM-09" required /></div>
                <div className="form-group"><label className="form-label">Type</label><input className="form-input" value={machineForm.equipment_type} onChange={updateMachineForm('equipment_type')} placeholder="IMM" required /></div>
                <div className="form-group"><label className="form-label">Plant</label><input className="form-input" value={machineForm.plant} onChange={updateMachineForm('plant')} required /></div>
                <div className="form-group"><label className="form-label">Line</label><input className="form-input" value={machineForm.line} onChange={updateMachineForm('line')} required /></div>
                <div className="form-group"><label className="form-label">Cell</label><input className="form-input" value={machineForm.cell} onChange={updateMachineForm('cell')} required /></div>
                <div className="form-group"><label className="form-label">Process</label><input className="form-input" value={machineForm.process} onChange={updateMachineForm('process')} required /></div>
                <div className="form-group"><label className="form-label">Mold / Model</label><input className="form-input" value={machineForm.mold_model} onChange={updateMachineForm('mold_model')} placeholder="AB-X200" /></div>
                <div className="form-group"><label className="form-label">PLC Protocol</label><select className="form-select" value={machineForm.plc_protocol} onChange={updateMachineForm('plc_protocol')}><option value="mitsubishi_mc">Mitsubishi MC</option><option value="modbus_tcp">Modbus TCP</option><option value="opc_ua">OPC UA</option><option value="mqtt">MQTT</option><option value="simulator">Simulator</option></select></div>
                <div className="form-group"><label className="form-label">Endpoint</label><input className="form-input" value={machineForm.plc_address} onChange={updateMachineForm('plc_address')} placeholder="192.168.10.40:5007" /></div>
                <div className="form-group"><label className="form-label">Cycle standard (sec)</label><input className="form-input" type="number" min="1" step="0.1" value={machineForm.cycle_time_standard} onChange={updateMachineForm('cycle_time_standard')} /></div>
                <div className="form-group"><label className="form-label">Target / hour</label><input className="form-input" type="number" min="1" step="1" value={machineForm.target_per_hour} onChange={updateMachineForm('target_per_hour')} /></div>
                <div className="form-group" style={{ gridColumn: '1 / -1' }}><label className="form-label">Description</label><input className="form-input" value={machineForm.description} onChange={updateMachineForm('description')} placeholder="220T molding press for bumper clips" /></div>
              </div>
              <button className="btn btn-primary" type="submit" disabled={saving.machine}>{saving.machine ? 'Saving...' : 'Save machine master'}</button>
            </form>
          ) : (
            <p className="text-secondary">Your role can review the rollout structure here. Machine-master changes are available to manager and admin roles.</p>
          )}
        </div>

        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Target Standards</span>
            <span className="glass-panel-note">Shift target, cycle baseline, quality goal</span>
          </div>
          {canEditTarget ? (
            <form onSubmit={handleTargetSave}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 12 }}>
                <div className="form-group"><label className="form-label">Equipment</label><select className="form-select" value={targetForm.equipment_id} onChange={updateTargetForm('equipment_id')} required><option value="">Select machine</option>{machines.map((machine) => <option key={machine.equipment_id} value={machine.equipment_id}>{machine.equipment_id}</option>)}</select></div>
                <div className="form-group"><label className="form-label">Shift</label><select className="form-select" value={targetForm.shift_name} onChange={updateTargetForm('shift_name')} required>{shiftNames.map((shift) => <option key={shift} value={shift}>{shift}</option>)}</select></div>
                <div className="form-group"><label className="form-label">Target parts</label><input className="form-input" type="number" min="1" step="1" value={targetForm.target_parts} onChange={updateTargetForm('target_parts')} /></div>
                <div className="form-group"><label className="form-label">Standard cycle (sec)</label><input className="form-input" type="number" min="1" step="0.1" value={targetForm.standard_cycle_time} onChange={updateTargetForm('standard_cycle_time')} /></div>
                <div className="form-group"><label className="form-label">Quality target</label><input className="form-input" type="number" min="0.5" max="1" step="0.01" value={targetForm.quality_target} onChange={updateTargetForm('quality_target')} /></div>
              </div>
              <button className="btn btn-primary" type="submit" disabled={saving.target}>{saving.target ? 'Saving...' : 'Save target standard'}</button>
            </form>
          ) : (
            <p className="text-secondary">Supervisors, managers, and admins can tune target standards for shift attainment.</p>
          )}

          <table className="data-table" style={{ marginTop: 18 }}>
            <thead><tr><th>Machine</th><th>Shift</th><th>Target</th><th>Cycle</th><th>Quality</th></tr></thead>
            <tbody>
              {standards.slice(0, 6).map((item) => (
                <tr key={`${item.equipment_id}-${item.shift_name}`}>
                  <td style={{ fontWeight: 700 }}>{item.equipment_id}</td>
                  <td>{item.shift_name}</td>
                  <td>{item.target_parts}</td>
                  <td>{item.standard_cycle_time}s</td>
                  <td>{formatPercent(item.quality_target * 100)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="glass-panel mb-24">
        <div className="glass-panel-header">
          <span className="glass-panel-title">Shift Calendar</span>
          <span className="glass-panel-note">Planned downtime and production windows</span>
        </div>
        {canEditShift ? (
          <form onSubmit={handleShiftSave} style={{ marginBottom: 18 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 12 }}>
              <div className="form-group"><label className="form-label">Plant code</label><input className="form-input" value={shiftForm.plant_code} onChange={updateShiftForm('plant_code')} required /></div>
              <div className="form-group"><label className="form-label">Shift</label><input className="form-input" value={shiftForm.shift_name} onChange={updateShiftForm('shift_name')} required /></div>
              <div className="form-group"><label className="form-label">Start</label><input className="form-input" type="time" value={shiftForm.starts_at} onChange={updateShiftForm('starts_at')} required /></div>
              <div className="form-group"><label className="form-label">End</label><input className="form-input" type="time" value={shiftForm.ends_at} onChange={updateShiftForm('ends_at')} required /></div>
              <div className="form-group"><label className="form-label">Planned downtime (min)</label><input className="form-input" type="number" min="0" step="1" value={shiftForm.planned_downtime_minutes} onChange={updateShiftForm('planned_downtime_minutes')} /></div>
              <div className="form-group"><label className="form-label">Active</label><select className="form-select" value={shiftForm.active ? 'true' : 'false'} onChange={(event) => setShiftForm((current) => ({ ...current, active: event.target.value === 'true' }))}><option value="true">Active</option><option value="false">Inactive</option></select></div>
            </div>
            <button className="btn btn-primary" type="submit" disabled={saving.shift}>{saving.shift ? 'Saving...' : 'Save shift calendar'}</button>
          </form>
        ) : (
          <p className="text-secondary" style={{ marginBottom: 16 }}>This rollout keeps shift definitions visible to all roles while edit access stays with manager and admin users.</p>
        )}

        <table className="data-table">
          <thead><tr><th>Plant</th><th>Shift</th><th>Window</th><th>Planned downtime</th><th>Status</th></tr></thead>
          <tbody>
            {shiftCalendars.map((item) => (
              <tr key={`${item.plant_code}-${item.shift_name}`}>
                <td style={{ fontWeight: 700 }}>{item.plant_code}</td>
                <td>{item.shift_name}</td>
                <td>{item.starts_at} - {item.ends_at}</td>
                <td>{item.planned_downtime_minutes} min</td>
                <td><span className={`badge ${item.active ? 'badge-stable' : 'badge-watch'}`}>{item.active ? 'Active' : 'Inactive'}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="glass-panel">
        <div className="glass-panel-header">
          <span className="glass-panel-title">Machine Rollout View</span>
          <span className="glass-panel-note">Role-aware factory context with live OEE overlay</span>
        </div>
        <table className="data-table">
          <thead><tr><th>Machine</th><th>Type</th><th>Plant</th><th>Line</th><th>Cell</th><th>Process</th><th>Protocol</th><th>OEE</th><th>Availability</th><th>Performance</th><th>Quality</th><th>Status</th></tr></thead>
          <tbody>
            {rows.map((item) => (
              <tr key={item.equipment_id}>
                <td style={{ fontWeight: 700 }}>{item.equipment_id}</td>
                <td>{item.equipment_type}</td>
                <td>{item.plant || '-'}</td>
                <td>{item.line || '-'}</td>
                <td>{item.cell || '-'}</td>
                <td>{item.process || '-'}</td>
                <td>{item.plc_protocol || '-'}</td>
                <td style={{ color: item.oee != null ? (item.oee < 75 ? 'var(--red)' : item.oee < 85 ? 'var(--amber)' : 'var(--green)') : 'var(--text-muted)', fontWeight: 700 }}>{item.oee != null ? formatPercent(item.oee) : '-'}</td>
                <td>{item.availability != null ? formatPercent(item.availability) : '-'}</td>
                <td>{item.performance != null ? formatPercent(item.performance) : '-'}</td>
                <td>{item.quality != null ? formatPercent(item.quality) : '-'}</td>
                <td><span className={`badge badge-${item.state}`}>{item.state}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && <p className="text-muted" style={{ paddingTop: 16, textAlign: 'center' }}>No machines match the current filters.</p>}
      </div>
    </div>
  )
}

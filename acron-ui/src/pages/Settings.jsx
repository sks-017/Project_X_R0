import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import KpiCard, { HealthPill } from '../components/KpiCard'
import { BRAND } from '../utils/constants'

const CONNECTOR_TEMPLATE = {
  name: '',
  protocol: 'mitsubishi_mc',
  endpoint: '',
  tagMapText: '{\n  "cycle_time": "D100",\n  "status": "D101"\n}',
}

function parseTagMap(tagMapText) {
  try {
    return JSON.parse(tagMapText || '{}')
  } catch {
    throw new Error('Tag map must be valid JSON.')
  }
}

function canAccess(role, allowedRoles) {
  return allowedRoles.includes(role || 'operator')
}

export default function Settings() {
  const { user } = useAuth()
  const [health, setHealth] = useState({})
  const [connectors, setConnectors] = useState([])
  const [connectorForm, setConnectorForm] = useState(CONNECTOR_TEMPLATE)
  const [testResult, setTestResult] = useState(null)
  const [message, setMessage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const checks = health.checks || {}
  const canReset = canAccess(user?.role, ['admin', 'manager'])
  const canManageConnectors = canAccess(user?.role, ['admin', 'manager', 'maintenance'])

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [healthData, connectorRows] = await Promise.all([api.getHealth(), api.getConnectors()])
      setHealth(healthData)
      setConnectors(connectorRows)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const statusSummary = useMemo(() => ({
    services: Object.keys(checks).length,
    simulator: checks.simulator?.latest_devices || 0,
    database: checks.database?.status || 'unknown',
  }), [checks])

  const handleReset = async () => {
    setMessage(null)
    try {
      await api.resetDemo()
      setMessage({ type: 'ok', text: 'Demo factory data reset completed.' })
      await loadData()
    } catch (err) {
      setMessage({ type: 'err', text: err.message })
    }
  }

  const handleSaveConnector = async (event) => {
    event.preventDefault()
    setSaving(true)
    setMessage(null)
    try {
      const payload = {
        name: connectorForm.name,
        protocol: connectorForm.protocol,
        endpoint: connectorForm.endpoint,
        tag_map: parseTagMap(connectorForm.tagMapText),
      }
      await api.saveConnector(payload)
      setMessage({ type: 'ok', text: `Connector ${connectorForm.name} saved.` })
      setConnectorForm(CONNECTOR_TEMPLATE)
      await loadData()
    } catch (err) {
      setMessage({ type: 'err', text: err.message })
    } finally {
      setSaving(false)
    }
  }

  const handleTestConnector = async () => {
    setSaving(true)
    setMessage(null)
    try {
      const payload = {
        name: connectorForm.name || 'connector-probe',
        protocol: connectorForm.protocol,
        endpoint: connectorForm.endpoint,
        tag_map: parseTagMap(connectorForm.tagMapText),
      }
      const response = await api.testConnector(payload)
      setTestResult(response)
      setMessage({ type: response.ok ? 'ok' : 'err', text: response.message })
    } catch (err) {
      setMessage({ type: 'err', text: err.message })
      setTestResult(null)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <div className="page animate-in">
      <div className="page-header">
        <h1>Settings</h1>
        <p>Platform readiness, connector commissioning, and demo operations for Acron v{BRAND.version}.</p>
      </div>

      {message && (
        <div className="glass-panel mb-24" style={{ borderColor: message.type === 'ok' ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)' }}>
          <p style={{ color: message.type === 'ok' ? 'var(--green)' : 'var(--red)', fontWeight: 700 }}>{message.text}</p>
        </div>
      )}

      <div className="kpi-grid">
        <KpiCard label="Platform Status" value={health.status || 'unknown'} deltaLabel={`${statusSummary.services} core checks`} />
        <KpiCard label="Database" value={statusSummary.database} deltaLabel="Persistence path" />
        <KpiCard label="Simulator Feed" value={statusSummary.simulator} deltaLabel="Devices with fresh data" />
        <KpiCard label="Connectors" value={connectors.length} deltaLabel="Commissioned endpoints" />
      </div>

      <div className="grid-2 mb-24">
        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Platform Health</span>
            <span className={`badge ${health.status === 'healthy' ? 'badge-stable' : 'badge-watch'}`}>{health.status || 'unknown'}</span>
          </div>
          <table className="data-table">
            <thead><tr><th>Service</th><th>Status</th></tr></thead>
            <tbody>
              {Object.entries(checks).map(([name, check]) => (
                <tr key={name}>
                  <td style={{ fontWeight: 700, textTransform: 'capitalize' }}>{name}</td>
                  <td><HealthPill label="" status={check.status || 'unknown'} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Rollout Controls</span>
            <span className="glass-panel-note">V2 readiness and demo governance</span>
          </div>
          <p className="text-secondary" style={{ fontSize: '.9rem', lineHeight: 1.6, marginBottom: 18 }}>
            {BRAND.name} v{BRAND.version} keeps the public demo clean while exposing the Phase 2 control plane: machine setup, shift calendars, target standards, connector validation, and report windows.
          </p>
          {canReset ? (
            <button className="btn btn-primary" onClick={handleReset}>Reset demo factory</button>
          ) : (
            <p className="text-secondary">Demo reset is available to manager and admin roles.</p>
          )}
          <div style={{ marginTop: 20 }}>
            <div style={{ fontWeight: 700, marginBottom: 8 }}>About {BRAND.name}</div>
            <p className="text-secondary" style={{ fontSize: '.85rem', lineHeight: 1.6 }}>
              {BRAND.owner}<br />
              {BRAND.tagline}
            </p>
          </div>
        </div>
      </div>

      <div className="grid-2 mb-24">
        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Connector Commissioning</span>
            <span className="glass-panel-note">MC Protocol, Modbus TCP, OPC UA, MQTT</span>
          </div>
          {canManageConnectors ? (
            <form onSubmit={handleSaveConnector}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12 }}>
                <div className="form-group"><label className="form-label">Name</label><input className="form-input" value={connectorForm.name} onChange={(event) => setConnectorForm((current) => ({ ...current, name: event.target.value }))} placeholder="line-a-imm" required /></div>
                <div className="form-group"><label className="form-label">Protocol</label><select className="form-select" value={connectorForm.protocol} onChange={(event) => setConnectorForm((current) => ({ ...current, protocol: event.target.value }))}><option value="mitsubishi_mc">Mitsubishi MC</option><option value="modbus_tcp">Modbus TCP</option><option value="opc_ua">OPC UA</option><option value="mqtt">MQTT</option><option value="simulator">Simulator</option></select></div>
                <div className="form-group" style={{ gridColumn: '1 / -1' }}><label className="form-label">Endpoint</label><input className="form-input" value={connectorForm.endpoint} onChange={(event) => setConnectorForm((current) => ({ ...current, endpoint: event.target.value }))} placeholder="192.168.10.20:5007" required /></div>
                <div className="form-group" style={{ gridColumn: '1 / -1' }}><label className="form-label">Tag map JSON</label><textarea className="form-textarea" value={connectorForm.tagMapText} onChange={(event) => setConnectorForm((current) => ({ ...current, tagMapText: event.target.value }))} /></div>
              </div>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <button className="btn btn-primary" type="submit" disabled={saving}>{saving ? 'Saving...' : 'Save connector'}</button>
                <button className="btn btn-secondary" type="button" onClick={handleTestConnector} disabled={saving}>{saving ? 'Testing...' : 'Test connector'}</button>
              </div>
            </form>
          ) : (
            <p className="text-secondary">Connector commissioning is available to maintenance, manager, and admin roles.</p>
          )}
        </div>

        <div className="glass-panel">
          <div className="glass-panel-header">
            <span className="glass-panel-title">Probe Result</span>
            <span className="glass-panel-note">Last connector validation response</span>
          </div>
          {testResult ? (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 14 }}>
                <span style={{ fontWeight: 700 }}>{testResult.protocol} / {testResult.endpoint}</span>
                <span className={`badge ${testResult.ok ? 'badge-stable' : 'badge-critical'}`}>{testResult.ok ? 'Ready' : 'Failed'}</span>
              </div>
              <p className="text-secondary" style={{ marginBottom: 12 }}>{testResult.message}</p>
              <pre style={{ margin: 0, background: 'rgba(0, 0, 0, 0.22)', border: '1px solid var(--border)', borderRadius: 8, padding: 14, fontSize: '.8rem', color: 'var(--text-secondary)', overflowX: 'auto' }}>{JSON.stringify(testResult.sample || {}, null, 2)}</pre>
            </>
          ) : (
            <p className="text-secondary">Run a connector test to validate the endpoint and preview the payload mapping.</p>
          )}
        </div>
      </div>

      <div className="glass-panel">
        <div className="glass-panel-header">
          <span className="glass-panel-title">Connector Registry</span>
          <span className="glass-panel-note">Saved connection paths for the edge rollout</span>
        </div>
        {connectors.length === 0 ? (
          <p className="text-muted">No connectors are configured yet.</p>
        ) : (
          <table className="data-table">
            <thead><tr><th>Name</th><th>Protocol</th><th>Endpoint</th><th>Tags</th></tr></thead>
            <tbody>
              {connectors.map((item) => (
                <tr key={item.name}>
                  <td style={{ fontWeight: 700 }}>{item.name}</td>
                  <td><span className="badge badge-info">{item.protocol}</span></td>
                  <td style={{ fontFamily: 'monospace', fontSize: '.8rem' }}>{item.endpoint}</td>
                  <td style={{ fontSize: '.8rem' }}>{JSON.stringify(item.tag_map || {})}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

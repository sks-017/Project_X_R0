import { API_BASE } from '../utils/constants'

function buildQuery(params = {}) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    query.set(key, value)
  })
  const result = query.toString()
  return result ? `?${result}` : ''
}

async function request(path, options = {}) {
  const token = localStorage.getItem('acron_token')
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (res.status === 401) {
    localStorage.removeItem('acron_token')
    localStorage.removeItem('acron_user')
    window.location.reload()
    throw new Error('Session expired')
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),

  login: async (username, password) => {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    const res = await fetch(`${API_BASE}/token`, { method: 'POST', body: form })
    if (!res.ok) throw new Error('Invalid credentials')
    return res.json()
  },

  demoLogin: (role) => request('/api/v1/auth/demo-login', { method: 'POST', body: JSON.stringify({ role }) }),

  getHealth: () => request('/api/v1/health').catch(() => ({ status: 'degraded', checks: {} })),
  getTelemetry: () => request('/api/v1/telemetry/latest').catch(() => ({})),
  getMachines: () => request('/api/v1/factory/machines').catch(() => []),
  saveMachine: (data) => request('/api/v1/factory/machines', { method: 'POST', body: JSON.stringify(data) }),

  getOee: (hours = 8) => request(`/api/v1/oee?hours=${hours}`).catch(() => []),
  getOeeReport: ({ scope = 'shift', plantCode, shiftName, referenceDate } = {}) =>
    request(`/api/v1/reports/oee${buildQuery({ scope, plant_code: plantCode, shift_name: shiftName, reference_date: referenceDate })}`).catch(() => null),

  getShiftCalendars: () => request('/api/v1/factory/shift-calendars').catch(() => []),
  saveShiftCalendar: (data) => request('/api/v1/factory/shift-calendars', { method: 'POST', body: JSON.stringify(data) }),
  getTargetStandards: () => request('/api/v1/factory/target-standards').catch(() => []),
  saveTargetStandard: (data) => request('/api/v1/factory/target-standards', { method: 'POST', body: JSON.stringify(data) }),

  getDowntimeReasons: () => request('/api/v1/downtime/reasons').catch(() => []),
  postDowntime: (data) => request('/api/v1/downtime', { method: 'POST', body: JSON.stringify(data) }),

  getConnectors: () => request('/api/v1/connectors').catch(() => []),
  saveConnector: (data) => request('/api/v1/connectors', { method: 'POST', body: JSON.stringify(data) }),
  testConnector: (data) => request('/api/v1/connectors/test', { method: 'POST', body: JSON.stringify(data) }),

  resetDemo: () => request('/api/v1/demo/reset', { method: 'POST', body: '{}' }),
  getAnalytics: () => request('/api/v1/analytics/summary').catch(() => null),
  getAiAnomalies: () => request('/api/v1/ai/anomalies').catch(() => []),
  getAiHealthScores: () => request('/api/v1/ai/health-scores').catch(() => []),
  askTechMate: (message) => request('/api/v1/ai/chat', { method: 'POST', body: JSON.stringify({ message }) }),
}

export function connectWebSocket(onMessage) {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const host = API_BASE ? new URL(API_BASE).host : window.location.host
  const ws = new WebSocket(`${proto}://${host}/ws/andons`)
  ws.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data))
    } catch {
      // ignore malformed packets
    }
  }
  ws.onerror = () => setTimeout(() => connectWebSocket(onMessage), 3000)
  ws.onclose = () => setTimeout(() => connectWebSocket(onMessage), 3000)
  return ws
}

import { API_BASE } from '../utils/constants'

async function request(path, options = {}) {
  const token = localStorage.getItem('acron_token')
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`
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

  // Auth
  login: async (username, password) => {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    const res = await fetch(`${API_BASE}/token`, { method: 'POST', body: form })
    if (!res.ok) throw new Error('Invalid credentials')
    return res.json()
  },

  demoLogin: (role) => request('/api/v1/auth/demo-login', { method: 'POST', body: JSON.stringify({ role }) }),

  // Data
  getHealth: () => request('/api/v1/health').catch(() => ({ status: 'degraded', checks: {} })),
  getTelemetry: () => request('/api/v1/telemetry/latest').catch(() => ({})),
  getMachines: () => request('/api/v1/factory/machines').catch(() => []),
  getOee: (hours = 8) => request(`/api/v1/oee?hours=${hours}`).catch(() => []),
  getDowntimeReasons: () => request('/api/v1/downtime/reasons').catch(() => []),
  getConnectors: () => request('/api/v1/connectors').catch(() => []),
  postDowntime: (data) => request('/api/v1/downtime', { method: 'POST', body: JSON.stringify(data) }),
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
  ws.onmessage = (e) => {
    try { onMessage(JSON.parse(e.data)) } catch {}
  }
  ws.onerror = () => setTimeout(() => connectWebSocket(onMessage), 3000)
  ws.onclose = () => setTimeout(() => connectWebSocket(onMessage), 3000)
  return ws
}

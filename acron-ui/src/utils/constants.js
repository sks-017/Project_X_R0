export const BRAND = {
  name: 'Acron',
  owner: 'S7 Corp',
  tagline: 'Intelligence meets reality.',
  version: '2.1',
}

export const API_BASE = import.meta.env.VITE_API_URL || ''

export const ROLES = ['operator', 'supervisor', 'maintenance', 'manager', 'admin']

export function getStatusColor(value, thresholds = { critical: 75, watch: 85 }) {
  if (value == null) return 'var(--text-muted)'
  if (value < thresholds.critical) return 'var(--red)'
  if (value < thresholds.watch) return 'var(--amber)'
  return 'var(--green)'
}

export function getStatusClass(value, thresholds = { critical: 75, watch: 85 }) {
  if (value == null) return ''
  if (value < thresholds.critical) return 'critical'
  if (value < thresholds.watch) return 'watch'
  return 'stable'
}

export function formatNumber(value, decimals = 1) {
  if (value == null) return '-'
  return Number(value).toFixed(decimals)
}

export function formatPercent(value) {
  if (value == null) return '-'
  return `${Number(value).toFixed(1)}%`
}

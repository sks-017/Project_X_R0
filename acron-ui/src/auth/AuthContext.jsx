import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const persistProfile = useCallback((profile, accessToken) => {
    localStorage.setItem('acron_token', accessToken)
    localStorage.setItem('acron_user', JSON.stringify(profile))
    setUser(profile)
  }, [])

  const login = useCallback(async (username, password) => {
    const data = await api.login(username, password)
    const profile = { username, role: data.role || 'operator' }
    persistProfile(profile, data.access_token)
  }, [persistProfile])

  const demoLogin = useCallback(async (role) => {
    const data = await api.demoLogin(role)
    const profile = { username: role === 'admin' ? 'admin' : role, role: data.role || role }
    persistProfile(profile, data.access_token)
    return data
  }, [persistProfile])

  useEffect(() => {
    const token = localStorage.getItem('acron_token')
    const saved = localStorage.getItem('acron_user')
    const params = new URLSearchParams(window.location.search)
    const demoRole = params.get('demoRole')

    if (token && saved) {
      try {
        setUser(JSON.parse(saved))
        setLoading(false)
        return
      } catch {
        localStorage.clear()
      }
    }

    if (demoRole) {
      demoLogin(demoRole)
        .catch(() => {})
        .finally(() => setLoading(false))
      return
    }

    setLoading(false)
  }, [demoLogin])

  const logout = useCallback(() => {
    localStorage.removeItem('acron_token')
    localStorage.removeItem('acron_user')
    setUser(null)
  }, [])

  if (loading) return <div className="loading-page"><div className="spinner" /><span className="text-muted">Loading Acron...</span></div>

  return (
    <AuthContext.Provider value={{ user, login, demoLogin, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}

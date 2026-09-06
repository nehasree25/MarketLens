/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { clearSession } from '../services/api'
import { getCurrentUser, loginRequest, logoutRequest, signupRequest } from '../services/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('marketlens_token'))
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(() => Boolean(localStorage.getItem('marketlens_token')))

  useEffect(() => {
    if (!token) {
      return
    }

    getCurrentUser()
      .then(setUser)
      .catch(() => {
        clearSession()
        setToken(null)
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [token])

  const login = useCallback(async (email, password) => {
    const result = await loginRequest(email, password)
    localStorage.setItem('marketlens_token', result.access_token)
    setLoading(true)
    setToken(result.access_token)
    return result
  }, [])

  const signup = useCallback(async (name, email, password) => {
    return signupRequest(name, email, password)
  }, [])

  const logout = useCallback(async () => {
    try {
      if (token) await logoutRequest()
    } finally {
      clearSession()
      setToken(null)
      setUser(null)
    }
  }, [token])

  const value = useMemo(() => ({ user, token, loading, login, signup, logout }), [user, token, loading, login, signup, logout])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}

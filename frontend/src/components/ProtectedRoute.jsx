import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <main className="auth-loading"><div className="brand-mark" aria-hidden="true"><span /></div><p>Restoring your workspace…</p></main>
  return user ? children : null
}

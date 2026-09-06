import { useState } from 'react'

export default function LoginScreen({ onLogin, onSignup }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setError(null)
    if (!email.trim()) return setError('Please enter your email.')
    if (!email.includes('@')) return setError('Please enter a valid email address.')
    if (!password) return setError('Please enter your password.')
    setSubmitting(true)
    try {
      await onLogin(email.trim(), password)
    } catch (requestError) {
      setError(requestError.status === 401 ? 'Invalid email or password.' : 'Unable to sign in right now. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return <main className="login-shell"><div className="login-card"><div className="brand-lockup"><div className="brand-mark" aria-hidden="true"><span /></div><div><strong>MarketLens</strong><small>See what changed. Know what matters.</small></div></div><form onSubmit={submit}><label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" /></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required autoComplete="current-password" /></label>{error && <p className="form-error">{error}</p>}<button className="primary-button" disabled={submitting}>{submitting ? 'Signing in…' : 'Sign in'} <span>→</span></button></form><p className="auth-switch">Don&apos;t have an account? <button type="button" onClick={onSignup}>Create account</button></p></div></main>
}

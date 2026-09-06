import { useState } from 'react'

function validatePassword(value) {
  return value.length >= 8 && /[A-Z]/.test(value) && /[a-z]/.test(value) && /\d/.test(value) && /[^A-Za-z0-9]/.test(value)
}

export default function Signup({ onSignup, onLogin }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setError(null)
    if (!name.trim()) return setError('Please enter your name.')
    if (!email.includes('@')) return setError('Please enter a valid email address.')
    if (!validatePassword(password)) return setError('Password must be at least 8 characters and include uppercase, lowercase, number, and special character.')
    setSubmitting(true)
    try {
      await onSignup(name.trim(), email.trim(), password)
      onLogin()
    } catch (requestError) {
      setError(requestError.status === 400 ? 'This email may already be registered.' : 'Unable to create your account right now. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return <main className="login-shell"><div className="login-card"><div className="brand-lockup"><div className="brand-mark" aria-hidden="true"><span /></div><div><strong>MarketLens</strong><small>See what changed. Know what matters.</small></div></div><span className="eyebrow">Create your workspace</span><h1>Start seeing clearly.</h1><p className="muted">Create an account to track the signals that matter to you.</p><form onSubmit={submit}><label>Name<input value={name} onChange={(event) => setName(event.target.value)} autoComplete="name" required /></label><label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required /></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" required /></label>{error && <p className="form-error">{error}</p>}<button className="primary-button" disabled={submitting}>{submitting ? 'Creating account…' : 'Create account'} <span>→</span></button></form><p className="auth-switch">Already have an account? <button type="button" onClick={onLogin}>Sign in</button></p></div></main>
}

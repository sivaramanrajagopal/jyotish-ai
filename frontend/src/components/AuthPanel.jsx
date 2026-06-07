/**
 * Supabase Auth — magic-link sign-in (Step 2).
 * Always visible; shows setup hint when VITE_SUPABASE_* env vars are missing.
 */

import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { readAuthCallbackError, clearAuthCallbackParams } from '../lib/authRedirect'

function truncateEmail(email) {
  if (!email || email.length <= 24) return email
  const [local, domain] = email.split('@')
  if (!domain) return email
  const head = local.length > 8 ? `${local.slice(0, 6)}…` : local
  return `${head}@${domain}`
}

export default function AuthPanel({ compact = false, variant = compact ? 'compact' : 'card' }) {
  const { configured, user, loading, email, signInWithMagicLink, signOut } = useAuth()
  const [inputEmail, setInputEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState(false)

  // Show friendly message when Supabase redirects back with otp_expired etc.
  useEffect(() => {
    const callbackError = readAuthCallbackError()
    if (callbackError) {
      setError(callbackError.message)
      clearAuthCallbackParams()
    }
  }, [])

  const isCard = variant === 'card'

  const handleMagicLink = async (e) => {
    e.preventDefault()
    if (!configured) return
    setBusy(true)
    setError('')
    setMessage('')
    try {
      await signInWithMagicLink(inputEmail)
      setMessage('Check your email for the sign-in link.')
      setInputEmail('')
      setExpanded(false)
    } catch (err) {
      setError(err.message || 'Could not send sign-in link.')
    } finally {
      setBusy(false)
    }
  }

  const handleSignOut = async () => {
    setBusy(true)
    setError('')
    try {
      await signOut()
      setMessage('')
    } catch (err) {
      setError(err.message || 'Could not sign out.')
    } finally {
      setBusy(false)
    }
  }

  if (loading) {
    return (
      <div className={isCard ? 'auth-card' : 'auth-panel auth-panel--compact'} aria-busy="true">
        <span style={{ color: 'var(--text-muted)', fontSize: isCard ? '13px' : '11px' }}>
          Checking session…
        </span>
      </div>
    )
  }

  if (user) {
    if (isCard) return null
    return (
      <div className="auth-panel auth-panel--compact">
        <span className="auth-panel__signed-in" title={email}>
          {compact ? '✓' : `Signed in · ${truncateEmail(email)}`}
        </span>
        <button
          type="button"
          className="auth-panel__btn auth-panel__btn--ghost"
          onClick={handleSignOut}
          disabled={busy}
        >
          Sign out
        </button>
        {error && <p className="auth-panel__error">{error}</p>}
      </div>
    )
  }

  if (compact && !expanded) {
    return (
      <button
        type="button"
        className="auth-panel__btn auth-panel__btn--primary auth-panel--compact"
        onClick={() => setExpanded(true)}
        aria-expanded="false"
      >
        Sign in
      </button>
    )
  }

  const form = (
    <>
      <form onSubmit={handleMagicLink} className="auth-panel__form">
        <input
          type="email"
          value={inputEmail}
          onChange={(e) => setInputEmail(e.target.value)}
          placeholder="your@email.com"
          required
          autoComplete="email"
          className="auth-panel__input"
          disabled={busy}
          aria-label="Email address"
        />
        <button
          type="submit"
          className="auth-panel__btn auth-panel__btn--primary"
          disabled={busy || !inputEmail.trim() || !configured}
        >
          {busy ? 'Sending…' : 'Send magic link'}
        </button>
        {compact && (
          <button
            type="button"
            className="auth-panel__btn auth-panel__btn--ghost"
            onClick={() => { setExpanded(false); setError(''); setMessage('') }}
            aria-label="Close sign in"
          >
            ✕
          </button>
        )}
      </form>
      {message && <p className="auth-panel__message">{message}</p>}
      {error && <p className="auth-panel__error">{error}</p>}
      {!configured && (
        <p className="auth-panel__setup">
          Add <code>VITE_SUPABASE_URL</code> and <code>VITE_SUPABASE_ANON_KEY</code> in Vercel → Settings → Environment Variables, then redeploy.
        </p>
      )}
      {isCard && configured && (
        <p className="auth-panel__hint">No password — we email you a one-time link.</p>
      )}
    </>
  )

  if (isCard) {
    return (
      <div className="auth-card">
        <h2 className="auth-card__title">Sign in to save your chart</h2>
        <p className="auth-card__subtitle">
          Link your birth chart to your account and access it from any device.
        </p>
        {form}
      </div>
    )
  }

  return (
    <div className={`auth-panel auth-panel--compact${compact && expanded ? ' auth-panel--expanded' : ''}`}>
      {form}
      {!isCard && configured && (
        <p className="auth-panel__hint">No password — we email you a one-time link.</p>
      )}
    </div>
  )
}

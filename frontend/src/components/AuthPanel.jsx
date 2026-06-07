/**
 * Supabase Auth — magic-link sign-in (Step 2).
 * Variants: card (home), nudge (has chart), compact (header nav).
 */

import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { readAuthCallbackError, clearAuthCallbackParams } from '../lib/authRedirect'

function truncateEmail(email) {
  if (!email || email.length <= 28) return email
  const [local, domain] = email.split('@')
  if (!domain) return email
  const head = local.length > 10 ? `${local.slice(0, 8)}…` : local
  return `${head}@${domain}`
}

function EmailSentView({
  email,
  busy,
  onResend,
  onChangeEmail,
  compact = false,
}) {
  if (compact) {
    return (
      <div className="auth-sent auth-sent--compact" role="status">
        <span className="auth-sent__compact-text">
          Link sent to <strong>{truncateEmail(email)}</strong>
        </span>
        <button
          type="button"
          className="auth-panel__btn auth-panel__btn--ghost"
          onClick={onResend}
          disabled={busy}
        >
          {busy ? 'Sending…' : 'Resend'}
        </button>
      </div>
    )
  }

  return (
    <div className="auth-sent" role="status">
      <div className="auth-sent__icon" aria-hidden="true">✉️</div>
      <h3 className="auth-sent__title">Check your inbox</h3>
      <p className="auth-sent__body">
        We sent a sign-in link to <strong>{email}</strong>.
        Open that email on this device and tap the link to continue.
      </p>
      <p className="auth-sent__hint">
        The link expires in about an hour. Check your spam folder if it doesn&apos;t arrive within a few minutes.
      </p>
      <div className="auth-sent__actions">
        <button
          type="button"
          className="auth-panel__btn auth-panel__btn--primary auth-sent__btn"
          onClick={onResend}
          disabled={busy}
        >
          {busy ? 'Sending…' : 'Resend link'}
        </button>
        <button
          type="button"
          className="auth-panel__btn auth-panel__btn--ghost auth-sent__btn"
          onClick={onChangeEmail}
          disabled={busy}
        >
          Use a different email
        </button>
      </div>
    </div>
  )
}

export default function AuthPanel({
  compact = false,
  variant = compact ? 'compact' : 'card',
  onDarkBg = false,
}) {
  const { configured, user, loading, email, signInWithMagicLink, signOut } = useAuth()
  const [inputEmail, setInputEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState(false)
  const [sentToEmail, setSentToEmail] = useState(null)

  useEffect(() => {
    const callbackError = readAuthCallbackError()
    if (callbackError) {
      setError(callbackError.message)
      clearAuthCallbackParams()
    }
  }, [])

  const isCard = variant === 'card'
  const isNudge = variant === 'nudge'
  const panelClass = [
    'auth-panel',
    compact && 'auth-panel--compact',
    compact && expanded && 'auth-panel--expanded',
    onDarkBg && 'auth-panel--on-dark',
  ].filter(Boolean).join(' ')

  const sendLink = async (targetEmail) => {
    const trimmed = targetEmail.trim()
    if (!trimmed || !configured) return
    setBusy(true)
    setError('')
    try {
      await signInWithMagicLink(trimmed)
      setSentToEmail(trimmed)
      setInputEmail('')
      if (compact) setExpanded(true)
    } catch (err) {
      setError(err.message || 'Could not send the sign-in link. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  const handleMagicLink = async (e) => {
    e.preventDefault()
    await sendLink(inputEmail)
  }

  const handleSignOut = async () => {
    setBusy(true)
    setError('')
    try {
      await signOut()
      setSentToEmail(null)
    } catch (err) {
      setError(err.message || 'Could not sign out.')
    } finally {
      setBusy(false)
    }
  }

  const resetSent = () => {
    setSentToEmail(null)
    setError('')
  }

  if (loading) {
    return (
      <div className={isCard ? 'auth-card' : panelClass} aria-busy="true">
        <span className="auth-panel__loading">Checking session…</span>
      </div>
    )
  }

  if (user) {
    if (isCard || isNudge) return null
    return (
      <div className={panelClass}>
        <span className="auth-panel__signed-in" title={email}>
          {compact ? truncateEmail(email) : `Signed in · ${truncateEmail(email)}`}
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

  if (sentToEmail && (isCard || isNudge)) {
    return (
      <div className={isCard ? 'auth-card auth-card--sent' : 'auth-nudge auth-nudge--sent'}>
        <EmailSentView
          email={sentToEmail}
          busy={busy}
          onResend={() => sendLink(sentToEmail)}
          onChangeEmail={() => {
            setInputEmail(sentToEmail)
            resetSent()
          }}
        />
        {error && <p className="auth-panel__error">{error}</p>}
      </div>
    )
  }

  if (compact && sentToEmail) {
    return (
      <div className={panelClass}>
        <EmailSentView
          compact
          email={sentToEmail}
          busy={busy}
          onResend={() => sendLink(sentToEmail)}
          onChangeEmail={() => {
            setInputEmail(sentToEmail)
            resetSent()
            setExpanded(true)
          }}
        />
        {error && <p className="auth-panel__error">{error}</p>}
      </div>
    )
  }

  if (compact && !expanded) {
    return (
      <button
        type="button"
        className="auth-panel__btn auth-panel__btn--primary auth-panel--compact-trigger"
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
          placeholder="you@email.com"
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
          {busy ? 'Sending…' : isNudge ? 'Email me a link' : 'Continue with email'}
        </button>
        {compact && (
          <button
            type="button"
            className="auth-panel__btn auth-panel__btn--ghost"
            onClick={() => { setExpanded(false); setError(''); resetSent() }}
            aria-label="Close sign in"
          >
            ✕
          </button>
        )}
      </form>
      {error && <p className="auth-panel__error">{error}</p>}
      {!configured && (
        <p className="auth-panel__setup">
          Add <code>VITE_SUPABASE_URL</code> and <code>VITE_SUPABASE_ANON_KEY</code> in Vercel → Settings → Environment Variables, then redeploy.
        </p>
      )}
      {(isCard || isNudge) && configured && (
        <p className="auth-panel__hint">No password needed — we&apos;ll email you a one-time link.</p>
      )}
    </>
  )

  if (isNudge) {
    return (
      <div className="auth-nudge">
        <div className="auth-nudge__copy">
          <span className="auth-nudge__title">Save your chart to your account</span>
          <span className="auth-nudge__sub">Access it from any device — sign in with email.</span>
        </div>
        {form}
      </div>
    )
  }

  if (isCard) {
    return (
      <div className="auth-card">
        <h2 className="auth-card__title">Sign in to save your chart</h2>
        <p className="auth-card__subtitle">
          Link your birth chart to your account and pick up where you left off on any device.
        </p>
        {form}
      </div>
    )
  }

  return (
    <div className={panelClass}>
      {form}
    </div>
  )
}

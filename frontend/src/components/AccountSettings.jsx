import { useState } from 'react'
import api from '../api/client'
import { useAuth } from '../hooks/useAuth'
import ConfirmDialog from './ConfirmDialog'
import { clearSessionChart } from '../lib/chartStorage'

export default function AccountSettings() {
  const { userId, signOut } = useAuth()
  const [showConfirm, setShowConfirm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  if (!userId) return null

  const handleDelete = async () => {
    setBusy(true)
    setError('')
    try {
      await api.delete('/auth/account')
      clearSessionChart()
      await signOut()
      setDone(true)
      window.location.reload()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not delete account. Please try again.')
      setBusy(false)
      setShowConfirm(false)
    }
  }

  return (
    <div className="account-settings">
      <h3 className="account-settings__title">Account</h3>
      <p className="account-settings__hint">
        Permanently removes your saved chart, AI usage history, and sign-in from our servers.
      </p>
      <button
        type="button"
        className="account-settings__delete"
        onClick={() => setShowConfirm(true)}
        disabled={busy || done}
      >
        Delete my account
      </button>
      {error && <p className="account-settings__error" role="alert">{error}</p>}
      <ConfirmDialog
        open={showConfirm}
        title="Delete account permanently?"
        message="This cannot be undone. Your natal chart, forecasts history, and sign-in will be removed from our database."
        confirmLabel="Delete everything"
        cancelLabel="Cancel"
        danger
        onConfirm={handleDelete}
        onCancel={() => setShowConfirm(false)}
      />
    </div>
  )
}

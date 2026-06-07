import { useState, useEffect } from 'react'
import api from '../api/client'
import { isOwnerEmail } from '../lib/isOwner'

/**
 * True when the signed-in user is an app owner (ADMIN_EMAILS on Render).
 * Falls back to VITE_ADMIN_EMAILS for local dev before backend is updated.
 */
export function useIsAdmin(userId, email) {
  const [isAdmin, setIsAdmin] = useState(() => isOwnerEmail(email))
  const [loading, setLoading] = useState(!!userId)

  useEffect(() => {
    if (!userId) {
      setIsAdmin(false)
      setLoading(false)
      return undefined
    }

    let cancelled = false
    setLoading(true)

    api.get('/auth/me')
      .then(({ data }) => {
        if (cancelled) return
        const fromServer = data?.is_admin === true
        const fromEnv = isOwnerEmail(data?.email || email)
        setIsAdmin(fromServer || fromEnv)
      })
      .catch(() => {
        if (!cancelled) setIsAdmin(isOwnerEmail(email))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [userId, email])

  return { isAdmin, loading }
}

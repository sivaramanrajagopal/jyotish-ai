import api from '../api/client'
import { isOwnerEmail } from '../lib/isOwner'
import { useApiResult } from './useApiResult'

/**
 * True when the signed-in user is an app owner (ADMIN_EMAILS on Render).
 * Falls back to VITE_ADMIN_EMAILS for local dev before backend is updated.
 */
export function useIsAdmin(userId, email) {
  const req = useApiResult(
    userId ? `${userId}|${email || ''}` : null,
    () => api.get('/auth/me')
      .then(({ data }) => data?.is_admin === true || isOwnerEmail(data?.email || email))
      .catch(() => isOwnerEmail(email)),
  )

  if (!userId) return { isAdmin: false, loading: false }
  const isAdmin = req.loading ? isOwnerEmail(email) : req.data === true
  return { isAdmin, loading: req.loading }
}

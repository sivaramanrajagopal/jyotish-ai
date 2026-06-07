/** True when the signed-in email is in VITE_ADMIN_EMAILS (owner dashboard). */
export function isOwnerEmail(email) {
  if (!email) return false
  const raw = import.meta.env.VITE_ADMIN_EMAILS || ''
  const allowed = raw.split(',').map(e => e.trim().toLowerCase()).filter(Boolean)
  if (!allowed.length) return false
  return allowed.includes(email.trim().toLowerCase())
}

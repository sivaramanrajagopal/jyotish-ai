/**
 * Auth redirect URL and callback error handling for Supabase magic links.
 */

const AUTH_ERROR_MESSAGES = {
  otp_expired: 'That sign-in link has expired. Request a new magic link below.',
  access_denied: 'Sign-in was cancelled or the link is no longer valid.',
  email_not_confirmed: 'Please confirm your email before signing in.',
}

/** Production site URL — set VITE_SITE_URL on Vercel so magic links never go to localhost. */
export function getAuthRedirectUrl() {
  const configured = import.meta.env.VITE_SITE_URL?.trim()
  if (configured) return configured.replace(/\/$/, '')
  if (typeof window !== 'undefined') return window.location.origin
  return ''
}

/** Read Supabase auth errors from URL after a failed magic-link redirect. */
export function readAuthCallbackError() {
  if (typeof window === 'undefined') return null

  const search = new URLSearchParams(window.location.search)
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ''))

  const errorCode = search.get('error_code') || hash.get('error_code')
  const error = search.get('error') || hash.get('error')
  const description = search.get('error_description') || hash.get('error_description')

  if (!error && !errorCode) return null

  const message =
    (errorCode && AUTH_ERROR_MESSAGES[errorCode]) ||
    (description ? decodeURIComponent(description.replace(/\+/g, ' ')) : null) ||
    AUTH_ERROR_MESSAGES[error] ||
    'Sign-in failed. Please try again.'

  return { errorCode, message }
}

/** Remove auth error params from the address bar after showing them. */
export function clearAuthCallbackParams() {
  if (typeof window === 'undefined') return
  try {
    const url = new URL(window.location.href)
    const authKeys = ['error', 'error_code', 'error_description', 'error_hint']
    authKeys.forEach((k) => {
      url.searchParams.delete(k)
    })
    url.hash = ''
    window.history.replaceState({}, '', url)
  } catch {
    // ignore
  }
}

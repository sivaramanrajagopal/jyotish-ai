/**
 * Error tracking (Sentry) — opt-in.
 * No-op unless VITE_SENTRY_DSN is set, so local/dev builds are unaffected.
 */
import * as Sentry from '@sentry/react'

export function initSentry() {
  const dsn = import.meta.env.VITE_SENTRY_DSN
  if (!dsn) return

  try {
    Sentry.init({
      dsn,
      environment: import.meta.env.MODE || 'development',
      // Light sampling on the free tier; raise later if needed.
      tracesSampleRate: Number(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || 0),
      // Never capture birth data / PII in requests.
      sendDefaultPii: false,
    })
  } catch (e) {
    console.warn('[sentry] init skipped', e)
  }
}

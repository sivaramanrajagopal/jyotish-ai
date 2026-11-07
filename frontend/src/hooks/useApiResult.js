import { useCallback, useEffect, useRef, useState } from 'react'

const objectIds = new WeakMap()
let nextObjectId = 1

/** Stable id for an object (e.g. a chart), so it can be part of a request key. */
export function objectKey(value) {
  if (!value || typeof value !== 'object') return String(value)
  if (!objectIds.has(value)) objectIds.set(value, nextObjectId++)
  return `#${objectIds.get(value)}`
}

/**
 * Runs `request` (a function returning a promise of data) whenever `key` changes.
 * A null key skips the request. Loading is derived from whether the stored result
 * belongs to the current key, so a stale response can never replace a newer one.
 * The previous data stays available while the next request is in flight.
 */
export function useApiResult(key, request) {
  const requestRef = useRef(request)
  useEffect(() => { requestRef.current = request })

  const [nonce, setNonce] = useState(0)
  const [result, setResult] = useState({ key: null, nonce: -1, data: null, error: null })

  useEffect(() => {
    if (key == null) return undefined
    let cancel = false
    Promise.resolve()
      .then(() => requestRef.current())
      .then(
        (data) => { if (!cancel) setResult({ key, nonce, data, error: null }) },
        (error) => { if (!cancel) setResult((prev) => ({ ...prev, key, nonce, error })) },
      )
    return () => { cancel = true }
  }, [key, nonce])

  const reload = useCallback(() => setNonce((n) => n + 1), [])
  const loading = key != null && (result.key !== key || result.nonce !== nonce)
  return {
    data: result.data,
    error: loading ? null : result.error,
    loading,
    resultKey: result.key,
    reload,
  }
}

/** API error detail as text, or the fallback when the server sent none. */
export function errorText(error, fallback) {
  const detail = error?.response?.data?.detail
  return typeof detail === 'string' && detail ? detail : fallback
}

/** User-facing message from axios/API errors (429 quota, validation, etc.). */
export function formatApiError(err, fallback = 'Something went wrong. Please try again.') {
  const status = err?.response?.status
  const detail = err?.response?.data?.detail

  if (status === 429) {
    if (typeof detail === 'string' && detail.includes('limit')) {
      return detail
    }
    return 'Daily AI limit reached. Sign in for higher limits, or try again tomorrow.'
  }

  if (status === 503) {
    return typeof detail === 'string' ? detail : 'Service temporarily unavailable. Try again shortly.'
  }

  if (Array.isArray(detail)) {
    return detail.map(e => `${e.loc?.slice(-1)[0] ?? 'field'}: ${e.msg}`).join(' · ')
  }

  if (typeof detail === 'string' && detail) return detail
  return fallback
}

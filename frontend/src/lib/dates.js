/** YYYY-MM-DD in the device's local timezone (toISOString would give the UTC date). */
export function localISODate(d = new Date()) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** Local date `days` from today. */
export function localISODateOffset(days) {
  const d = new Date()
  d.setDate(d.getDate() + days)
  return localISODate(d)
}

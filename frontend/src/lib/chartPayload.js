/**
 * Build API request body — authenticated users rely on server-side chart (Step 4).
 */
export function chartFingerprint(chart) {
  if (!chart) return ''
  const pp = chart.planet_positions || {}
  const asc = chart.ascendant || {}
  const ascSign = typeof asc === 'object' ? asc.sign : String(asc)
  const parts = [ascSign]
  for (const planet of ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']) {
    parts.push(pp[planet]?.sign || '')
  }
  const ayan = chart.ayanamsa_value
  parts.push(ayan != null ? Number(ayan).toFixed(4) : '')
  return parts.join('|')
}

export function chartPayload(chart, userId, extra = {}) {
  if (userId) return { ...extra }
  if (!chart) return { ...extra }
  return { natal_chart: chart, ...extra }
}

/** Forecast API extras: pass current local time when scoring today. */
export function forecastPayload(chart, userId, transitDate) {
  const extra = { transit_date: transitDate }
  const today = new Date().toISOString().split('T')[0]
  if (transitDate === today) {
    const n = new Date()
    extra.transit_time = `${String(n.getHours()).padStart(2, '0')}:${String(n.getMinutes()).padStart(2, '0')}`
  }
  return chartPayload(chart, userId, extra)
}

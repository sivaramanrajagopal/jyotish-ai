/** Approximate Lahiri ayanamsa for a YYYY-MM-DD date (within 0.005° for 1900–2060). */
function expectedLahiri(dob) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(dob || ''))
  if (!m) return null
  const years = Number(m[1]) + (Number(m[2]) - 1) / 12 + (Number(m[3]) - 1) / 365.25 - 2000
  return 23.8531 + 0.013969 * years
}

/**
 * Detect charts saved before the Lahiri ayanamsa fix: those carry Fagan–Bradley
 * values labelled Lahiri, about 0.88° above the Lahiri value for the birth date.
 */
export function isChartLikelyStale(chart) {
  if (!chart) return false
  const ayan = chart.ayanamsa_value
  if (ayan == null) return true
  if (chart.ayanamsa !== 'Lahiri') return false
  const expected = expectedLahiri(chart.birth_data?.dob)
  if (expected == null) return Number(ayan) > 24.0
  return Math.abs(Number(ayan) - expected) > 0.3
}

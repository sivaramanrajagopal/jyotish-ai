/** Detect charts saved before the Lahiri ayanamsa fix (Fagan–Bradley mislabeled). */
export function isChartLikelyStale(chart) {
  if (!chart) return false
  const ayan = chart.ayanamsa_value
  if (ayan == null || ayan === undefined) return true
  return chart.ayanamsa === 'Lahiri' && Number(ayan) > 24.0
}

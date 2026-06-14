/**
 * Backfill Vimshottari dasha on charts saved before the dasha engine shipped.
 */
import api from '../api/client'

export function chartNeedsDasha(chart) {
  if (!chart) return false
  return !chart.dasha?.mahadasha?.planet
}

export async function backfillChartDasha(chart) {
  const { data } = await api.post('/chart/ensure-dasha', { natal_chart: chart })
  return data
}

/**
 * Backfill Vimshottari dasha on charts saved before the dasha engine
 * (or the full timeline) shipped.
 */
import api from '../api/client'

export function chartNeedsDasha(chart) {
  if (!chart) return false
  return !chart.dasha?.mahadasha?.planet || !Array.isArray(chart.dasha?.timeline)
}

export async function backfillChartDasha(chart) {
  const { data } = await api.post('/chart/ensure-dasha', { natal_chart: chart })
  return data
}

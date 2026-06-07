/**
 * Build API request body — authenticated users rely on server-side chart (Step 4).
 */
export function chartPayload(chart, userId, extra = {}) {
  if (userId) return { ...extra }
  if (!chart) return { ...extra }
  return { natal_chart: chart, ...extra }
}

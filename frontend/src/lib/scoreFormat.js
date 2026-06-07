/** Round 0–100 scores for display (no decimal places). */
export function roundScore(value) {
  if (value == null || value === '') return 0
  const n = Number(value)
  return Number.isFinite(n) ? Math.round(n) : 0
}

/** Format API moment objects for display (never render raw objects in JSX). */

export function formatTransitMoment(moment) {
  if (!moment || typeof moment !== 'object') return ''
  const parts = []
  if (moment.date) parts.push(String(moment.date))
  if (moment.time) parts.push(String(moment.time))
  let line = parts.join(' ').trim()
  const tz = moment.timezone?.split('/').pop()
  if (tz) line += line ? ` (${tz})` : tz
  if (moment.note) line += line ? ` · ${moment.note}` : String(moment.note)
  return line
}

export function formatPrashnaMoment(moment) {
  if (!moment || typeof moment !== 'object') return ''
  if (moment.date && moment.time) {
    return `${moment.date} ${moment.time}`.trim()
  }
  if (moment.iso) return String(moment.iso)
  return formatTransitMoment(moment)
}

/** Shared chart label helpers (testable, used by SouthIndianChart). */

export function nakshatraAbbr(name) {
  if (!name || typeof name !== 'string') return ''
  return name.length <= 4 ? name : name.substring(0, 3)
}

export function formatNakshatraLine(nakshatra, pada, useFullName = true) {
  if (!nakshatra && pada == null) return null
  const name = useFullName ? nakshatra : nakshatraAbbr(nakshatra)
  if (!name) return pada != null ? `P${pada}` : null
  return pada != null ? `${name} · P${pada}` : name
}

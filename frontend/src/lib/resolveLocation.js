/** Match birth place to backend Panchangam LOCATIONS key (mirrors sky_today_agent). */
const KNOWN_LOCATIONS = [
  'Chennai', 'Bangalore', 'Mumbai', 'Delhi', 'Hyderabad', 'Coimbatore', 'Erlangen',
]

export function resolvePanchangamLocation(place, chart) {
  const fromChart = chart?.birth_data?.panchangam_location
    || chart?.panchangam_location
  if (fromChart && KNOWN_LOCATIONS.includes(fromChart)) return fromChart

  const text = (place || chart?.birth_data?.place_of_birth || '').trim()
  if (!text) return 'Chennai'

  const exact = KNOWN_LOCATIONS.find(c => c.toLowerCase() === text.toLowerCase())
  if (exact) return exact

  const lower = text.toLowerCase()
  for (const key of KNOWN_LOCATIONS) {
    const kl = key.toLowerCase()
    if (lower.includes(kl) || kl.includes(lower)) return key
  }
  return 'Chennai'
}

export { KNOWN_LOCATIONS }

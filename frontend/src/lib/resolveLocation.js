/** Match birth place to backend Panchangam LOCATIONS key (mirrors sky_today_agent). */
const KNOWN_LOCATIONS = [
  'Chennai', 'Bangalore', 'Mumbai', 'Delhi', 'Hyderabad', 'Coimbatore', 'Erlangen',
]

const LOCATION_COORDS = {
  Chennai: [13.0827, 80.2707],
  Bangalore: [12.9716, 77.5946],
  Mumbai: [19.0760, 72.8777],
  Delhi: [28.6139, 77.2090],
  Hyderabad: [17.3850, 78.4867],
  Coimbatore: [11.0168, 76.9558],
  Erlangen: [49.5897, 11.0078],
}

function haversineKm(lat1, lon1, lat2, lon2) {
  const r = 6371
  const p1 = (lat1 * Math.PI) / 180
  const p2 = (lat2 * Math.PI) / 180
  const dlat = ((lat2 - lat1) * Math.PI) / 180
  const dlon = ((lon2 - lon1) * Math.PI) / 180
  const a = Math.sin(dlat / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dlon / 2) ** 2
  return 2 * r * Math.asin(Math.sqrt(a))
}

function nearestKnownCity(lat, lon) {
  let best = 'Chennai'
  let bestD = Infinity
  for (const [name, [clat, clon]] of Object.entries(LOCATION_COORDS)) {
    const d = haversineKm(lat, lon, clat, clon)
    if (d < bestD) {
      bestD = d
      best = name
    }
  }
  return best
}

export function resolvePanchangamLocation(place, chart) {
  const bd = chart?.birth_data || {}
  const lat = bd.lat ?? chart?.lat
  const lon = bd.lon ?? chart?.lon
  if (lat != null && lon != null) {
    return nearestKnownCity(Number(lat), Number(lon))
  }

  const fromChart = chart?.birth_data?.panchangam_location
    || chart?.panchangam_location
  if (fromChart && KNOWN_LOCATIONS.includes(fromChart)) return fromChart

  const text = (place || bd.place_of_birth || '').trim()
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

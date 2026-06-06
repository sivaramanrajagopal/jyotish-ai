/**
 * skyToday.js — fetch & cache cosmos strip data (30 min TTL).
 */

import api from '../api/client'

const TTL_MS = 30 * 60 * 1000
let cache = { key: null, data: null, fetchedAt: 0 }

const KNOWN_LOCATIONS = [
  'Chennai', 'Bangalore', 'Mumbai', 'Delhi',
  'Hyderabad', 'Coimbatore', 'Erlangen',
]

export function resolveSkyLocation(placeOfBirth) {
  if (!placeOfBirth) return 'Chennai'
  const lower = placeOfBirth.toLowerCase()
  for (const loc of KNOWN_LOCATIONS) {
    if (lower.includes(loc.toLowerCase())) return loc
  }
  return 'Chennai'
}

function cacheKey(location, chart) {
  const p = chart
    ? `${chart.moon_nakshatra_index}-${chart.moon_rasi_index}-${chart.ascendant?.sign_index}`
    : 'anon'
  return `${location}|${p}`
}

/**
 * @param {{ location?: string, chart?: object|null, force?: boolean }} opts
 */
export async function fetchSkyToday({ location = 'Chennai', chart = null, force = false } = {}) {
  const loc = resolveSkyLocation(location)
  const key = cacheKey(loc, chart)
  const now = Date.now()

  if (!force && cache.key === key && cache.data && now - cache.fetchedAt < TTL_MS) {
    return cache.data
  }

  const params = { location: loc }
  if (chart?.moon_nakshatra_index != null && chart?.moon_rasi_index != null) {
    params.moon_nak_index = chart.moon_nakshatra_index
    params.moon_rasi_index = chart.moon_rasi_index
    if (chart.ascendant?.sign_index != null) {
      params.natal_asc_sign_index = chart.ascendant.sign_index
    }
  }

  const { data } = await api.get('/sky/today', { params })
  cache = { key, data, fetchedAt: now }
  return data
}

export function invalidateSkyCache() {
  cache = { key: null, data: null, fetchedAt: 0 }
}

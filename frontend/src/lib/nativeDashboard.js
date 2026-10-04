/** Glance facts for the My Chart native card. Mirrors the app's existing lords and panchanga. */

import { buildJanmaPanchanga } from './janmaPanchanga'

const SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
]

const SIGN_LORDS = [
  'Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury',
  'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter',
]

const NAKSHATRAS = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
  'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
  'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
  'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
  'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
]

const NAKSHATRA_LORDS = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']

const RASI_VALUES = [6, 12, 8, 16, 30, 8, 12, 6, 10, 1, 1, 10]

const WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

const OWN_SIGNS = {
  Sun: [4],
  Moon: [3],
  Mars: [0, 7],
  Mercury: [2, 5],
  Jupiter: [8, 11],
  Venus: [1, 6],
  Saturn: [9, 10],
}

/** Chara 11, sthira 9, ubhaya 7. */
const BADHAKA_HOUSE = { 0: 11, 3: 11, 6: 11, 9: 11, 1: 9, 4: 9, 7: 9, 10: 9, 2: 7, 5: 7, 8: 7, 11: 7 }

const TITHI_SOONYA = {
  1: [6, 9],
  2: [8, 11],
  3: [4, 9],
  4: [1, 10],
  5: [2, 5],
  6: [0, 4],
  7: [3, 8],
  8: [2, 5],
  9: [4, 7],
  10: [4, 7],
  11: [8, 11],
  12: [6, 9],
  13: [1, 4],
  14: [11, 2, 5, 8],
  0: [],
}

function wrap360(value) {
  return ((Number(value) % 360) + 360) % 360
}

function signIndexFromLongitude(lon) {
  return Math.floor(wrap360(lon) / 30) % 12
}

function signIndexOf(row) {
  if (!row) return null
  if (row.sign_index != null && row.sign_index !== '') return Number(row.sign_index) % 12
  if (row.longitude != null && row.longitude !== '') return signIndexFromLongitude(row.longitude)
  const named = SIGNS.indexOf(row.sign)
  return named >= 0 ? named : null
}

function nakshatraIndex(lon) {
  return Math.floor(wrap360(lon) / (360 / 27)) % 27
}

function nakshatraName(lon) {
  return NAKSHATRAS[nakshatraIndex(lon)]
}

function nakshatraLord(lon) {
  return NAKSHATRA_LORDS[nakshatraIndex(lon) % 9]
}

function soonyaTithiIndex(moonLon, sunLon) {
  const angle = wrap360(moonLon - sunLon)
  let tithiNumber = Math.ceil(angle / 12)
  if (tithiNumber === 0) tithiNumber = 30
  if (tithiNumber === 15 || tithiNumber === 30) return 0
  return ((tithiNumber - 1) % 15) + 1
}

function weekdayName(dob) {
  if (!dob) return ''
  const day = new Date(`${String(dob).slice(0, 10)}T12:00:00`).getDay()
  return Number.isNaN(day) ? '' : WEEKDAYS[day]
}

function seatOf(planet, chart) {
  const row = chart?.planet_positions?.[planet]
  if (!row) return { house: null, signIndex: null }
  const signIndex = signIndexOf(row)
  const house = row.house != null ? Number(row.house) : null
  return { house, signIndex }
}

function starPlaces(planet, house, signIndex) {
  const places = []
  if ([1, 4, 7, 10].includes(house)) places.push('kendra')
  else if ([5, 9].includes(house)) places.push('trikona')
  if (signIndex != null && (OWN_SIGNS[planet] || []).includes(signIndex)) places.push('own sign')
  return places
}

function induLagna(ascIndex, moonIndex) {
  const total = RASI_VALUES[(ascIndex + 8) % 12] + RASI_VALUES[(moonIndex + 8) % 12]
  let remainder = total % 12
  if (remainder === 0) remainder = 12
  const index = (moonIndex + remainder - 1) % 12
  return {
    sign: SIGNS[index],
    house: (index - ascIndex + 12) % 12 + 1,
    lord: SIGN_LORDS[index],
  }
}

const GANDANTA_JUNCTIONS = [
  [0, 'Pisces/Aries'],
  [120, 'Cancer/Leo'],
  [240, 'Scorpio/Sagittarius'],
]
const GANDANTA_ORB = 10 / 3
const BODY_ORDER = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']

export function gandantaAt(longitude) {
  const lon = wrap360(longitude)
  let bestOrb = 999
  let junction = ''
  for (const [deg, name] of GANDANTA_JUNCTIONS) {
    const dist = Math.min(Math.abs(lon - deg), Math.abs(lon - deg + 360), Math.abs(lon - deg - 360))
    if (dist < bestOrb) {
      bestOrb = dist
      junction = name
    }
  }
  return {
    gandanta: bestOrb <= GANDANTA_ORB,
    junction,
    orb: Math.round(bestOrb * 100) / 100,
  }
}

function houseFromLagna(signIndex, lagnaIndex) {
  return (Number(signIndex) - Number(lagnaIndex) + 12) % 12 + 1
}

function gandantaRows(positions, lagnaIndex, { useStoredHouse = false } = {}) {
  const points = []
  for (const name of BODY_ORDER) {
    const row = positions?.[name]
    if (row?.longitude == null) continue
    const hit = gandantaAt(row.longitude)
    if (!hit.gandanta) continue
    const signIndex = signIndexOf(row)
    const house = useStoredHouse && row.house != null
      ? Number(row.house)
      : (signIndex != null && lagnaIndex != null ? houseFromLagna(signIndex, lagnaIndex) : null)
    points.push({ planet: name, house, junction: hit.junction })
  }
  return points
}

export function natalGandanta(chart) {
  const asc = chart?.ascendant
  const lagnaIndex = signIndexOf(asc)
  const points = gandantaRows(chart?.planet_positions, lagnaIndex, { useStoredHouse: true })
  if (asc?.longitude != null) {
    const hit = gandantaAt(asc.longitude)
    if (hit.gandanta) points.unshift({ planet: 'Lagna', house: 1, junction: hit.junction })
  }
  return points
}

export function transitGandanta(transitChart, natalChart) {
  const lagnaIndex = signIndexOf(natalChart?.ascendant)
  return gandantaRows(transitChart?.planet_positions, lagnaIndex)
}

function houseList(houses) {
  return (houses || []).filter((house) => house != null).join(', ')
}

export function formatHotspotValue(hotspot, triggers) {
  const byLabel = new Map((triggers || []).map((item) => [item.planet_label, item.houses_ruled || []]))
  const parts = (hotspot?.planet_labels || []).map((label) => {
    const houses = houseList(byLabel.get(label))
    return houses ? `${label} ${houses}` : label
  })
  return `${hotspot?.nakshatra || ''} (${parts.join(' · ')})`
}

export function formatTriggerItem(item) {
  const houses = houseList(item?.houses_ruled)
  if (!houses) return `${item.planet_label} (${item.trigger_nakshatra})`
  return `${item.planet_label} (${item.trigger_nakshatra} · ${houses})`
}

function yogiTrio(sunLon, moonLon) {
  const point = wrap360(sunLon + moonLon + (93 + 20 / 60))
  const ava = wrap360(point + (186 + 40 / 60))
  const yogiStar = nakshatraName(point)
  return {
    yogi: nakshatraLord(point),
    yogiStar,
    duplicateYogi: SIGN_LORDS[signIndexFromLongitude(point)],
    duplicateStar: yogiStar,
    avayogi: nakshatraLord(ava),
    avayogiStar: nakshatraName(ava),
  }
}

export function buildNativeDashboard(chart) {
  const birth = chart?.birth_data || {}
  const janma = buildJanmaPanchanga(chart)
  const ascIndex = signIndexOf(chart?.ascendant)
  const moon = chart?.planet_positions?.Moon
  const sun = chart?.planet_positions?.Sun
  const moonIndex = signIndexOf(moon)
  const lagnaLord = ascIndex == null ? '' : SIGN_LORDS[ascIndex]
  const lagnaSeat = seatOf(lagnaLord, chart)

  let badhaka = null
  if (ascIndex != null && BADHAKA_HOUSE[ascIndex]) {
    const house = BADHAKA_HOUSE[ascIndex]
    const signIndex = (ascIndex + house - 1) % 12
    const planet = SIGN_LORDS[signIndex]
    const seat = seatOf(planet, chart)
    const places = starPlaces(planet, seat.house, seat.signIndex)
    const bits = [`Lord of house ${house}`]
    if (seat.house) bits.push(`sits in house ${seat.house}`)
    bits.push(...places)
    badhaka = {
      planet,
      house,
      star: places.length > 0,
      detail: bits.join(' · '),
    }
  }

  const indu = ascIndex != null && moonIndex != null ? induLagna(ascIndex, moonIndex) : null
  const trio = sun?.longitude != null && moon?.longitude != null
    ? yogiTrio(Number(sun.longitude), Number(moon.longitude))
    : { yogi: '', yogiStar: '', duplicateYogi: '', duplicateStar: '', avayogi: '', avayogiStar: '' }

  const soonyaIdx = sun?.longitude != null && moon?.longitude != null
    ? soonyaTithiIndex(Number(moon.longitude), Number(sun.longitude))
    : null
  const soonya = soonyaIdx == null
    ? ''
    : (TITHI_SOONYA[soonyaIdx] || []).map((index) => SIGNS[index]).join(', ') || 'None'

  const maha = chart?.dasha?.mahadasha?.planet || ''
  const bhukti = chart?.dasha?.bhukti?.planet || ''

  return {
    name: birth.name || '',
    date: birth.dob || '',
    time: birth.birth_time_approximate ? '12:00 noon, time unknown' : (birth.tob || ''),
    place: birth.place_of_birth || chart?.place_of_birth || '',
    weekday: weekdayName(birth.dob),
    tithi: janma?.tithi?.name ? `${janma.tithi.paksha} ${janma.tithi.name}` : '',
    karana: janma?.karana?.name || '',
    yoga: janma?.yoga?.name || '',
    ...trio,
    soonya,
    lagnaLord: lagnaLord ? {
      planet: lagnaLord,
      house: lagnaSeat.house,
      detail: lagnaSeat.house ? `Sits in house ${lagnaSeat.house}` : '',
    } : null,
    badhaka,
    indu: indu ? {
      ...indu,
      detail: `House ${indu.house} · ${indu.sign}`,
    } : null,
    period: [maha, bhukti].filter(Boolean).join(' / '),
  }
}

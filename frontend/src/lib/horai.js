/**
 * Horai (Hora) & Uba Horai — weekday planet sequences.
 *
 * Midnight rule (fixed 6 AM mode):
 *   Times in [00:00, 06:00) belong to the PREVIOUS calendar day's night horas.
 *   The selected date's horai cycle STARTS at 06:00 on that calendar date.
 *
 * Sunrise mode:
 *   Times before today's sunrise belong to the previous calendar day's night horas.
 */

export const HORAI_MODES = {
  FIXED: 'fixed',
  SUNRISE: 'sunrise',
}

/** Sunday = 0 … Saturday = 6 (matches hora-calculator planetSequences keys). */
export const PLANET_SEQUENCES = {
  0: ['Sun', 'Venus', 'Mercury', 'Moon', 'Saturn', 'Jupiter', 'Mars'],
  1: ['Moon', 'Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury'],
  2: ['Mars', 'Sun', 'Venus', 'Mercury', 'Moon', 'Saturn', 'Jupiter'],
  3: ['Mercury', 'Moon', 'Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus'],
  4: ['Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon', 'Saturn'],
  5: ['Venus', 'Mercury', 'Moon', 'Saturn', 'Jupiter', 'Mars', 'Sun'],
  6: ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon'],
}

export const UBA_SEQUENCES = {
  Sun: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter'],
  Venus: ['Venus', 'Saturn', 'Sun', 'Moon', 'Mars'],
  Mercury: ['Mercury', 'Jupiter', 'Venus', 'Saturn', 'Sun'],
  Moon: ['Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus'],
  Saturn: ['Saturn', 'Sun', 'Moon', 'Mars', 'Mercury'],
  Jupiter: ['Jupiter', 'Venus', 'Saturn', 'Sun', 'Moon'],
  Mars: ['Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'],
}

export const PLANET_INFO = {
  Sun: { en: 'Sun', ta: 'சூரியன்', malefic: false },
  Venus: { en: 'Venus', ta: 'சுக்ரன்', malefic: false },
  Mercury: { en: 'Mercury', ta: 'புதன்', malefic: false },
  Moon: { en: 'Moon', ta: 'சந்திரன்', malefic: false },
  Saturn: { en: 'Saturn', ta: 'சனி', malefic: true },
  Jupiter: { en: 'Jupiter', ta: 'குரு', malefic: false },
  Mars: { en: 'Mars', ta: 'செவ்வாய்', malefic: true },
}

export const HORA_ACTIVITY_TA = {
  Sun: 'அரசு அதிகாரிகளை சந்திக்க, பதவி ஏற்க, மருந்து உண்ண, உயில் எழுத, வேலைக்கு முயற்சி செய்ய.',
  Moon: 'ஆடை, ஆபரணங்கள், பயணம், பாஸ்போர்ட், வியாபாரம், கல்வி.',
  Mars: 'நிலம், அடுப்பு, குளை தீ, போர் கருவிகள், மருந்து உண்ண.',
  Mercury: 'கணக்கு, கடிதம், தேர்வு, ஜோதிடம், அறிவியல், தரகு வேலை.',
  Jupiter: 'சேமிப்பு, முதலீடு, பெரிய மனிதர், குரு ஆசி, பயிர்.',
  Venus: 'ஆடை, வாகனம், கால்நடை, திருமணம், விருந்து, கலை.',
  Saturn: 'இரும்பு, மின் சாதனங்கள், எர் உழுதல், எருவிடுதல்.',
}

const VAARAM_SUN0 = {
  Somavaram: 1,
  Mangalavaram: 2,
  Budhavaram: 3,
  Guruvaram: 4,
  Shukravaram: 5,
  Shanivaram: 6,
  Bhanuavaram: 0,
}

const FIXED_DAY_START_MIN = 6 * 60
const FIXED_DAY_END_MIN = 18 * 60
const SLOTS_PER_HALF = 12

export function addDaysYmd(ymd, delta) {
  const [y, m, d] = ymd.split('-').map(Number)
  const dt = new Date(Date.UTC(y, m - 1, d + delta, 12, 0, 0))
  return dt.toISOString().slice(0, 10)
}

export function weekdaySunZeroFromYmd(ymd, timeZone) {
  const ref = new Date(`${ymd}T12:00:00.000Z`)
  const day = new Intl.DateTimeFormat('en-US', { timeZone, weekday: 'short' }).format(ref)
  const map = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 }
  return map[day] ?? 0
}

export function weekdaySunZeroFromVaaram(vaaramName) {
  if (vaaramName && VAARAM_SUN0[vaaramName] != null) {
    return VAARAM_SUN0[vaaramName]
  }
  return 0
}

export function expandPlanetSequence(weekdaySun0) {
  const base = PLANET_SEQUENCES[weekdaySun0 % 7] || PLANET_SEQUENCES[0]
  const out = []
  for (let i = 0; i < 24; i += 1) {
    out.push(base[i % 7])
  }
  return out
}

/**
 * Calendar date whose weekday sequence governs `localMinutes` on `calendarYmd`.
 * Before 6 AM (fixed) or before sunrise → previous calendar day.
 */
export function resolveHoraiOwnerDate(calendarYmd, localMinutes, mode, sunriseMinutes = null) {
  if (mode === HORAI_MODES.SUNRISE && sunriseMinutes != null) {
    if (localMinutes < sunriseMinutes) {
      return addDaysYmd(calendarYmd, -1)
    }
    return calendarYmd
  }
  if (localMinutes < FIXED_DAY_START_MIN) {
    return addDaysYmd(calendarYmd, -1)
  }
  return calendarYmd
}

/** Slot index 0–23 within the owner horai-day (day 0–11, night 12–23). */
export function slotIndexFromLocalMinutes(localMinutes, mode, sunriseMinutes, sunsetMinutes) {
  if (mode === HORAI_MODES.SUNRISE && sunriseMinutes != null && sunsetMinutes != null) {
    if (localMinutes < sunriseMinutes) {
      const nightSpan = (24 * 60 - sunsetMinutes) + sunriseMinutes
      const elapsed = localMinutes + (24 * 60 - sunsetMinutes)
      const idx = Math.min(SLOTS_PER_HALF - 1, Math.floor((elapsed / nightSpan) * SLOTS_PER_HALF))
      return SLOTS_PER_HALF + idx
    }
    if (localMinutes < sunsetMinutes) {
      const daySpan = sunsetMinutes - sunriseMinutes
      const elapsed = localMinutes - sunriseMinutes
      const idx = Math.min(SLOTS_PER_HALF - 1, Math.floor((elapsed / daySpan) * SLOTS_PER_HALF))
      return idx
    }
    const nightSpan = (24 * 60 - sunsetMinutes) + sunriseMinutes
    const elapsed = localMinutes - sunsetMinutes
    const idx = Math.min(SLOTS_PER_HALF - 1, Math.floor((elapsed / nightSpan) * SLOTS_PER_HALF))
    return SLOTS_PER_HALF + idx
  }

  if (localMinutes < FIXED_DAY_START_MIN) {
    const hour = Math.floor(localMinutes / 60)
    return hour + 18
  }
  const hour = Math.floor(localMinutes / 60)
  return hour - 6
}

export function getUbaPlanet(mainPlanet, minuteInHour) {
  const seq = UBA_SEQUENCES[mainPlanet] || UBA_SEQUENCES.Sun
  const idx = Math.min(4, Math.floor((minuteInHour % 60) / 12))
  return seq[idx]
}

export function isoToLocalParts(iso, timeZone) {
  if (!iso) return null
  const d = new Date(iso)
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(d)
  const get = (t) => parts.find(p => p.type === t)?.value
  const hour = Number(get('hour'))
  const minute = Number(get('minute'))
  return {
    ymd: `${get('year')}-${get('month')}-${get('day')}`,
    hour: hour === 24 ? 0 : hour,
    minute,
    localMinutes: (hour === 24 ? 0 : hour) * 60 + minute,
  }
}

export function nowInTimezone(timeZone) {
  return isoToLocalParts(new Date().toISOString(), timeZone)
}

function minutesFromIsoOnDate(iso, displayYmd, timeZone) {
  const p = isoToLocalParts(iso, timeZone)
  if (!p) return null
  if (p.ymd === displayYmd) return p.localMinutes
  if (p.ymd === addDaysYmd(displayYmd, 1)) return p.localMinutes + 24 * 60
  if (p.ymd === addDaysYmd(displayYmd, -1)) return p.localMinutes - 24 * 60
  return p.localMinutes
}

function formatMinutesLabel(minutes) {
  if (minutes == null || Number.isNaN(minutes)) return '—'
  const total = Math.round(minutes)
  const withinDay = ((total % (24 * 60)) + 24 * 60) % (24 * 60)
  const h = Math.floor(withinDay / 60)
  const m = withinDay % 60
  const pad = (n) => String(n).padStart(2, '0')
  const hour12 = h % 12 || 12
  const ampm = h < 12 ? 'am' : 'pm'
  return `${pad(hour12)}:${pad(m)} ${ampm}`
}

/** `parts` equal segments → `parts + 1` rounded boundary minutes (inclusive start/end). */
function divideSpanMinutes(start, end, parts) {
  const boundaries = [Math.round(start)]
  for (let i = 1; i < parts; i += 1) {
    boundaries.push(Math.round(start + ((end - start) * i) / parts))
  }
  boundaries.push(Math.round(end))
  return boundaries
}

function buildFixedSlotBounds(slotIndex) {
  const startMin = slotIndex < SLOTS_PER_HALF
    ? FIXED_DAY_START_MIN + slotIndex * 60
    : FIXED_DAY_END_MIN + (slotIndex - SLOTS_PER_HALF) * 60
  const endMin = startMin + 60
  return { startMin, endMin }
}

function buildSunriseSlotBounds(slotIndex, sunriseMin, sunsetMin, nextSunriseMin) {
  if (slotIndex < SLOTS_PER_HALF) {
    const bounds = divideSpanMinutes(sunriseMin, sunsetMin, SLOTS_PER_HALF)
    return { startMin: bounds[slotIndex], endMin: bounds[slotIndex + 1] }
  }
  const i = slotIndex - SLOTS_PER_HALF
  const bounds = divideSpanMinutes(sunsetMin, nextSunriseMin, SLOTS_PER_HALF)
  return { startMin: bounds[i], endMin: bounds[i + 1] }
}

/**
 * Build 24 display slots for calendar date `displayYmd` (labels day + night on that date).
 * Sequence weekday comes from displayYmd's vaaram (not owner date).
 */
export function buildHoraiDay({
  displayYmd,
  weekdaySun0,
  mode = HORAI_MODES.FIXED,
  timeZone = 'Asia/Kolkata',
  sunriseIso = null,
  sunsetIso = null,
  nextSunriseIso = null,
}) {
  const sequence = expandPlanetSequence(weekdaySun0)
  const sunriseMin = sunriseIso ? minutesFromIsoOnDate(sunriseIso, displayYmd, timeZone) : null
  const sunsetMin = sunsetIso ? minutesFromIsoOnDate(sunsetIso, displayYmd, timeZone) : null
  let nextSunriseMin = sunriseMin != null ? sunriseMin + 24 * 60 : null
  if (mode === HORAI_MODES.SUNRISE && nextSunriseIso) {
    const fetched = minutesFromIsoOnDate(nextSunriseIso, displayYmd, timeZone)
    if (fetched != null) {
      nextSunriseMin = fetched < (sunsetMin ?? 0) ? fetched + 24 * 60 : fetched
    }
  }

  const slots = sequence.map((planet, slotIndex) => {
    const bounds = mode === HORAI_MODES.SUNRISE && sunriseMin != null && sunsetMin != null
      ? buildSunriseSlotBounds(slotIndex, sunriseMin, sunsetMin, nextSunriseMin ?? sunriseMin)
      : buildFixedSlotBounds(slotIndex)
    const isDay = slotIndex < SLOTS_PER_HALF
    return {
      slotIndex,
      planet,
      isDay,
      startMin: bounds.startMin,
      endMin: bounds.endMin,
      labelStart: formatMinutesLabel(bounds.startMin),
      labelEnd: formatMinutesLabel(bounds.endMin),
      ...PLANET_INFO[planet],
    }
  })

  return {
    displayYmd,
    weekdaySun0,
    mode,
    daySlots: slots.filter(s => s.isDay),
    nightSlots: slots.filter(s => !s.isDay),
    slots,
  }
}

/**
 * Live horai state at `now` in location timezone.
 */
export function computeLiveHorai({
  now = new Date(),
  timeZone = 'Asia/Kolkata',
  weekdaySun0ForDate,
  mode = HORAI_MODES.FIXED,
  sunriseIso = null,
  sunsetIso = null,
  getWeekdayForYmd = () => weekdaySun0ForDate ?? 0,
}) {
  const local = isoToLocalParts(now.toISOString(), timeZone)
  if (!local) return null

  const sunriseMin = sunriseIso ? isoToLocalParts(sunriseIso, timeZone)?.localMinutes : null
  const sunsetMin = sunsetIso ? isoToLocalParts(sunsetIso, timeZone)?.localMinutes : null

  const ownerYmd = resolveHoraiOwnerDate(local.ymd, local.localMinutes, mode, sunriseMin)
  const ownerWeekday = getWeekdayForYmd(ownerYmd) ?? weekdaySun0ForDate ?? 0
  const sequence = expandPlanetSequence(ownerWeekday)
  const slotIndex = slotIndexFromLocalMinutes(local.localMinutes, mode, sunriseMin, sunsetMin)
  const planet = sequence[slotIndex]
  const minuteInHour = local.minute
  const ubaPlanet = getUbaPlanet(planet, minuteInHour)

  const beforeSixAm = mode === HORAI_MODES.FIXED && local.localMinutes < FIXED_DAY_START_MIN
  const beforeSunrise = mode === HORAI_MODES.SUNRISE && sunriseMin != null && local.localMinutes < sunriseMin

  return {
    calendarYmd: local.ymd,
    ownerYmd,
    ownerWeekday,
    slotIndex,
    planet,
    ubaPlanet,
    localHour: local.hour,
    localMinute: local.minute,
    beforeAnchor: beforeSixAm || beforeSunrise,
    anchorLabel: mode === HORAI_MODES.SUNRISE ? 'sunrise' : '6 AM',
  }
}

export function isSlotActive(slot, live, displayYmd) {
  if (!live || live.ownerYmd !== displayYmd) return false
  return slot.slotIndex === live.slotIndex
}

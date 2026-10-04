import { describe, expect, it } from 'vitest'
import { buildNativeDashboard, formatHotspotValue, formatTodayLine, formatTriggerItem, gandantaAt, natalGandanta, transitGandanta } from './nativeDashboard'

const CHENNAI = {
  birth_data: {
    name: 'Sample',
    dob: '1978-09-18',
    tob: '17:35',
    place_of_birth: 'Chennai, India',
  },
  ascendant: { sign: 'Aquarius', sign_index: 10 },
  planet_positions: {
    Sun: { longitude: 151.6622, sign_index: 5, house: 8, sign: 'Virgo' },
    Moon: { longitude: 354.14, sign_index: 11, house: 2, sign: 'Pisces' },
    Venus: { sign_index: 6, house: 9, sign: 'Libra' },
    Saturn: { sign_index: 4, house: 7, sign: 'Leo' },
  },
  dasha: { mahadasha: { planet: 'Moon' }, bhukti: { planet: 'Ketu' } },
}

describe('buildNativeDashboard', () => {
  it('reads the Chennai Aquarius native in one glance', () => {
    const out = buildNativeDashboard(CHENNAI)
    expect(out.weekday).toBe('Monday')
    expect(out.tithi).toBe('Krishna Dwitiya')
    expect(out.yogi).toBe('Mercury')
    expect(out.yogiStar).toBe('Jyeshtha')
    expect(out.duplicateYogi).toBe('Mars')
    expect(out.duplicateStar).toBe('Jyeshtha')
    expect(out.avayogi).toBe('Mars')
    expect(out.avayogiStar).toBe('Mrigashira')
    expect(out.soonya).toBe('Sagittarius, Pisces')
    expect(out.lagnaLord).toMatchObject({ planet: 'Saturn', house: 7 })
    expect(out.badhaka).toMatchObject({ planet: 'Venus', house: 9, star: true })
    expect(out.badhaka.detail).toContain('trikona')
    expect(out.badhaka.detail).toContain('own sign')
    expect(out.indu).toMatchObject({ sign: 'Leo', house: 7, lord: 'Sun' })
    expect(out.period).toBe('Moon / Ketu')
    expect(natalGandanta(CHENNAI)).toEqual([])
    expect(gandantaAt(354.14).gandanta).toBe(false)
  })

  it('uses the 11th lord for a chara lagna and stars an own-sign seat', () => {
    const out = buildNativeDashboard({
      ascendant: { sign: 'Aries', sign_index: 0 },
      planet_positions: {
        Sun: { longitude: 10, sign_index: 0, house: 1 },
        Moon: { longitude: 40, sign_index: 1, house: 2 },
        Saturn: { sign_index: 9, house: 10, sign: 'Capricorn' },
      },
    })
    expect(out.badhaka.planet).toBe('Saturn')
    expect(out.badhaka.house).toBe(11)
    expect(out.badhaka.star).toBe(true)
    expect(out.badhaka.detail).toContain('kendra')
    expect(out.badhaka.detail).toContain('own sign')
  })

  it('uses the 7th lord for a dual lagna', () => {
    const out = buildNativeDashboard({
      ascendant: { sign_index: 2 },
      planet_positions: {
        Sun: { longitude: 70, house: 1, sign_index: 2 },
        Moon: { longitude: 100, house: 2, sign_index: 3 },
        Jupiter: { house: 3, sign_index: 4 },
      },
    })
    expect(out.badhaka.planet).toBe('Jupiter')
    expect(out.badhaka.house).toBe(7)
    expect(out.badhaka.star).toBe(false)
  })

  it('marks a planet in the last or first 3°20′ of a gandanta junction', () => {
    expect(gandantaAt(359).gandanta).toBe(true)
    expect(gandantaAt(1).junction).toBe('Pisces/Aries')
    const natal = {
      ascendant: { sign_index: 10, longitude: 300 },
      planet_positions: {
        Mercury: { longitude: 121, sign_index: 4, house: 7 },
        Moon: { longitude: 354.14, sign_index: 11, house: 2 },
      },
    }
    expect(natalGandanta(natal)).toEqual([
      { planet: 'Mercury', house: 7, junction: 'Cancer/Leo' },
    ])
    expect(transitGandanta({
      planet_positions: {
        Mars: { longitude: 241, sign_index: 8, house: 1 },
      },
    }, natal)).toEqual([
      { planet: 'Mars', house: 11, junction: 'Scorpio/Sagittarius' },
    ])
  })

  it('places ruled houses next to a hotspot and a trigger star', () => {
    const triggers = [
      { planet_label: 'Mars', trigger_nakshatra: 'Hasta', houses_ruled: [3, 10] },
      { planet_label: 'Mercury', trigger_nakshatra: 'Hasta', houses_ruled: [5, 8] },
      { planet_label: 'Jupiter', trigger_nakshatra: 'Hasta', houses_ruled: [2, 11] },
      { planet_label: 'Moon', trigger_nakshatra: 'Revati', houses_ruled: [6] },
    ]
    expect(formatHotspotValue({
      nakshatra: 'Hasta',
      planet_labels: ['Mars', 'Mercury', 'Jupiter'],
    }, triggers)).toBe('Hasta (Mars 3, 10 · Mercury 5, 8 · Jupiter 2, 11)')
    expect(formatTriggerItem(triggers[3])).toBe('Moon (Revati · 6)')
  })

  it('says whether today’s Moon star is the hotspot', () => {
    const status = {
      today_moon_nak: 'Rohini',
      is_trigger_day: false,
      active_planets: [],
      hotspots: [{ nakshatra: 'Hasta', is_triple_trigger: true, planet_labels: ['Mars', 'Mercury', 'Jupiter'] }],
      all_triggers: [
        { planet_label: 'Mars', houses_ruled: [3, 10] },
        { planet_label: 'Mercury', houses_ruled: [5, 8] },
        { planet_label: 'Jupiter', houses_ruled: [2, 11] },
        { planet_label: 'Saturn', houses_ruled: [1, 12], trigger_nakshatra: 'Punarvasu' },
      ],
    }
    expect(formatTodayLine(status)).toBe(
      "Today the Moon is in Rohini. Hasta is quiet, so houses 3, 10, 5, 8, 2, and 11 are not the day's subject.",
    )
    expect(formatTodayLine({
      ...status,
      today_moon_nak: 'Hasta',
      is_trigger_day: true,
      active_planets: [
        { planet_label: 'Mars' },
        { planet_label: 'Mercury' },
        { planet_label: 'Jupiter' },
      ],
    })).toBe('Today the Moon is in Hasta. Houses 3, 10, 5, 8, 2, and 11 are louder today.')
    expect(formatTodayLine({
      ...status,
      today_moon_nak: 'Punarvasu',
      is_trigger_day: true,
      active_planets: [{ planet_label: 'Saturn' }],
    })).toBe(
      "Today the Moon is in Punarvasu. Houses 1 and 12 are louder today. Hasta is quiet, so houses 3, 10, 5, 8, 2, and 11 are not the day's subject.",
    )
  })
})

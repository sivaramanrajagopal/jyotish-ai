import { describe, it, expect } from 'vitest'
import {
  addDaysYmd,
  resolveHoraiOwnerDate,
  slotIndexFromLocalMinutes,
  computeLiveHorai,
  HORAI_MODES,
  expandPlanetSequence,
} from './horai.js'

describe('horai midnight rule (fixed 6 AM)', () => {
  it('before 6 AM uses previous calendar day as owner', () => {
    expect(resolveHoraiOwnerDate('2026-06-18', 3 * 60, HORAI_MODES.FIXED)).toBe('2026-06-17')
    expect(resolveHoraiOwnerDate('2026-06-18', 5 * 60 + 59, HORAI_MODES.FIXED)).toBe('2026-06-17')
  })

  it('from 6 AM onward uses same calendar day as owner', () => {
    expect(resolveHoraiOwnerDate('2026-06-18', 6 * 60, HORAI_MODES.FIXED)).toBe('2026-06-18')
    expect(resolveHoraiOwnerDate('2026-06-18', 23 * 60, HORAI_MODES.FIXED)).toBe('2026-06-18')
  })

  it('maps 2 AM to night slot 20 (previous day sequence)', () => {
    expect(slotIndexFromLocalMinutes(2 * 60, HORAI_MODES.FIXED)).toBe(20)
  })

  it('maps 6 AM to day slot 0', () => {
    expect(slotIndexFromLocalMinutes(6 * 60, HORAI_MODES.FIXED)).toBe(0)
  })

  it('maps 11 PM to night slot 17', () => {
    expect(slotIndexFromLocalMinutes(23 * 60, HORAI_MODES.FIXED)).toBe(17)
  })

  it('Sunday sequence: 6 AM starts Sun; 6 PM continues cycle', () => {
    const seq = expandPlanetSequence(0)
    expect(seq[0]).toBe('Sun')
    expect(seq[12]).toBe('Jupiter')
  })
})

describe('addDaysYmd', () => {
  it('steps backward across month boundary', () => {
    expect(addDaysYmd('2026-06-01', -1)).toBe('2026-05-31')
  })
})

describe('computeLiveHorai owner date', () => {
  it('3 AM Chennai on June 18 → owner June 17', () => {
    const live = computeLiveHorai({
      now: new Date('2026-06-17T21:30:00.000Z'),
      timeZone: 'Asia/Kolkata',
      weekdaySun0ForDate: 3,
      mode: HORAI_MODES.FIXED,
      getWeekdayForYmd: () => 3,
    })
    expect(live.ownerYmd).toBe('2026-06-17')
    expect(live.beforeAnchor).toBe(true)
  })
})

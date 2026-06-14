import { describe, expect, it } from 'vitest'
import { formatPrashnaMoment, formatTransitMoment } from './formatMoment'

describe('formatTransitMoment', () => {
  it('formats date, time, timezone, and note', () => {
    const s = formatTransitMoment({
      date: '2026-06-06',
      time: '06:00',
      timezone: 'Asia/Kolkata',
      note: 'local',
    })
    expect(s).toContain('2026-06-06')
    expect(s).toContain('06:00')
    expect(s).toContain('Kolkata')
    expect(s).toContain('local')
  })

  it('returns empty string for invalid input', () => {
    expect(formatTransitMoment(null)).toBe('')
  })
})

describe('formatPrashnaMoment', () => {
  it('formats prashna moment strings', () => {
    expect(formatPrashnaMoment({ date: '2026-06-06', time: '14:30' })).toBe('2026-06-06 14:30')
  })
})

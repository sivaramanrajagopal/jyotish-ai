import { describe, expect, it } from 'vitest'
import { formatNakshatraLine, nakshatraAbbr } from './chartFormat'

describe('nakshatraAbbr', () => {
  it('returns short names unchanged', () => {
    expect(nakshatraAbbr('Ashwini')).toBe('Ash')
  })

  it('handles empty input', () => {
    expect(nakshatraAbbr('')).toBe('')
    expect(nakshatraAbbr(null)).toBe('')
  })
})

describe('formatNakshatraLine', () => {
  it('formats full name with pada', () => {
    expect(formatNakshatraLine('Rohini', 3)).toBe('Rohini · P3')
  })

  it('returns null when no data', () => {
    expect(formatNakshatraLine(null, null)).toBeNull()
  })

  it('returns pada only when name missing', () => {
    expect(formatNakshatraLine(null, 2)).toBe('P2')
  })
})

import { describe, expect, it } from 'vitest'
import { PRASHNA_CATALOG, mergePrashnaCatalog, firstQuestionId } from './prashnaCatalog'

describe('PRASHNA_CATALOG', () => {
  it('has unique question ids across categories', () => {
    const ids = PRASHNA_CATALOG.flatMap(c => c.questions.map(q => q.id))
    expect(new Set(ids).size).toBe(ids.length)
  })

  it('includes key_interest house questions', () => {
    const ki = PRASHNA_CATALOG.find(c => c.key === 'key_interest')
    expect(ki?.questions.some(q => q.id === 'h10_career')).toBe(true)
  })
})

describe('mergePrashnaCatalog', () => {
  it('falls back to local catalog when API empty', () => {
    expect(mergePrashnaCatalog(null)).toEqual(PRASHNA_CATALOG)
  })

  it('keeps local questions when API category has none', () => {
    const merged = mergePrashnaCatalog([{ key: 'career', label: 'Career', questions: [] }])
    expect(merged[0].questions.length).toBeGreaterThan(0)
  })
})

describe('firstQuestionId', () => {
  it('returns first question for category', () => {
    expect(firstQuestionId(PRASHNA_CATALOG, 'money')).toBe('financial_gain')
  })
})

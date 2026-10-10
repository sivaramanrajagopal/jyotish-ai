import api from '../api/client'
import { chartFingerprint, chartPayload } from './chartPayload'
import { getNativeNote } from './nativeNote'

const RULES = [
  ['work', /\b(work|career|job|profession|office)\b/],
  ['money', /\b(money|wealth|income|finance|salary)\b/],
  ['marriage', /\b(marri\w*|spouse|wife|husband|wedding)\b/],
  ['health', /\b(health|illness|disease|sick)\b/],
  ['children', /\b(child|children|son|daughter|progeny)\b/],
  ['home', /\b(home|mother|property)\b/],
  ['father', /\b(father|guru|dharma)\b/],
  ['skill', /\b(skill|sibling|courage|brother|sister)\b/],
  ['gains', /\b(gains?|profit|friends?)\b/],
  ['foreign', /\b(foreign|abroad|immigration)\b/],
  ['breaks', /\b(break|obstacle|longevity|inheritance)\b/],
  ['self', /\b(myself|personality|lagna)\b/],
]

let cached = null
let cachedKey = ''

export function matchQuestion(text, note = getNativeNote()) {
  const source = String(text || '').toLowerCase()
  for (const [id, pattern] of RULES) {
    if (pattern.test(source)) return id
  }
  return note === 'work' ? 'work' : ''
}

export async function loadSitting(chart, userId) {
  const note = getNativeNote()
  const gender = chart?.birth_data?.gender || 'male'
  const key = `${chartFingerprint(chart)}|${note}|${gender}|${userId || ''}`
  if (cached && cachedKey === key) return cached
  const { data } = await api.post('/reading', chartPayload(chart, userId, { gender, note }))
  cached = data
  cachedKey = key
  return data
}

const KEY = 'jyotish-native-note-v1'

export function getNativeNote() {
  try {
    const value = localStorage.getItem(KEY)
    return value === 'married' || value === 'work' ? value : ''
  } catch {
    return ''
  }
}

export function saveNativeNote(note) {
  const value = note === 'married' || note === 'work' ? note : ''
  try {
    localStorage.setItem(KEY, value)
  } catch {}
  return value
}

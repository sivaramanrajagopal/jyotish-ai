import { LEGAL_STORAGE_KEY } from '../constants/legal'

export function hasLegalConsent() {
  try {
    return localStorage.getItem(LEGAL_STORAGE_KEY) === 'accepted'
  } catch {
    return false
  }
}

export function saveLegalConsent() {
  try {
    localStorage.setItem(LEGAL_STORAGE_KEY, 'accepted')
  } catch {}
}

/** Returns age in full years on referenceDate (default today). */
export function ageFromDob(dob, referenceDate = new Date()) {
  if (!dob) return 0
  const birth = new Date(`${dob}T12:00:00`)
  if (Number.isNaN(birth.getTime())) return 0
  let age = referenceDate.getFullYear() - birth.getFullYear()
  const monthDiff = referenceDate.getMonth() - birth.getMonth()
  if (monthDiff < 0 || (monthDiff === 0 && referenceDate.getDate() < birth.getDate())) {
    age -= 1
  }
  return age
}

export function isAtLeast18(dob) {
  return ageFromDob(dob) >= 18
}

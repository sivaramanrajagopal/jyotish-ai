/** Prokerala-style Ashtakavarga grid helpers (fixed South Indian rasi layout). */

export const SIGN_ABBR = [
  'Ar', 'Ta', 'Ge', 'Cn', 'Le', 'Vi', 'Li', 'Sc', 'Sg', 'Cp', 'Aq', 'Pi',
]

export const RASHI_NAMES = [
  'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
  'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena',
]

/** House-wise [H1..H12] → rasi-wise [Aries..Pisces]. ascRasi is 1-based. */
export function houseWiseToRasiWise(houseWise, ascRasi) {
  const rasi = Array(12).fill(0)
  for (let h = 1; h <= 12; h++) {
    const houseRasi = ((ascRasi - 1 + h - 1) % 12) + 1
    rasi[houseRasi - 1] = houseWise[h - 1] ?? 0
  }
  return rasi
}

/** Which house (1–12) occupies this fixed rasi slot. */
export function houseForRasi(rasiNum, ascRasi) {
  for (let h = 1; h <= 12; h++) {
    const hr = ((ascRasi - 1 + h - 1) % 12) + 1
    if (hr === rasiNum) return h
  }
  return rasiNum
}

export function binduStrength(value, isSav = false) {
  if (isSav) {
    if (value >= 30) return 'high'
    if (value >= 25) return 'medium'
    return 'low'
  }
  if (value > 4) return 'high'
  if (value === 4) return 'medium'
  return 'low'
}

/** Fixed South Indian 4×4 rasi layout for BAV grids. */
export const BAV_RASI_LAYOUT = [
  { rasi: 12, slot: 'top-1' },
  { rasi: 1, slot: 'top-2' },
  { rasi: 2, slot: 'top-3' },
  { rasi: 3, slot: 'top-4' },
  { rasi: 11, slot: 'middle-left' },
  { rasi: 4, slot: 'middle-right' },
  { rasi: 10, slot: 'row3-left' },
  { rasi: 5, slot: 'row3-right' },
  { rasi: 9, slot: 'bottom-1' },
  { rasi: 8, slot: 'bottom-2' },
  { rasi: 7, slot: 'bottom-3' },
  { rasi: 6, slot: 'bottom-4' },
]

/** SAV house layout (house-based, not fixed rasi). */
export const BAV_CONTRIBUTOR_LABELS = [
  { key: 'SUN', short: 'Su' },
  { key: 'MOON', short: 'Mo' },
  { key: 'MARS', short: 'Ma' },
  { key: 'MERCURY', short: 'Me' },
  { key: 'JUPITER', short: 'Ju' },
  { key: 'VENUS', short: 'Ve' },
  { key: 'SATURN', short: 'Sa' },
  { key: 'ASCENDANT', short: 'Lg' },
]

export const SAV_HOUSE_LAYOUT = [
  { house: 9, slot: 'top-1' },
  { house: 10, slot: 'top-2' },
  { house: 11, slot: 'top-3' },
  { house: 12, slot: 'top-4' },
  { house: 7, slot: 'middle-left' },
  { house: 1, slot: 'middle-right' },
  { house: 8, slot: 'row3-left' },
  { house: 2, slot: 'row3-right' },
  { house: 3, slot: 'bottom-1' },
  { house: 4, slot: 'bottom-2' },
  { house: 5, slot: 'bottom-3' },
  { house: 6, slot: 'bottom-4' },
]

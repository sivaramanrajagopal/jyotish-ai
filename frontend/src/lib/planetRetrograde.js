/** Vedic retrograde: Rahu/Ketu always; others from API speed. */
export function isPlanetRetrograde(planet, data) {
  if (planet === 'Rahu' || planet === 'Ketu') return true
  return !!data?.retrograde
}

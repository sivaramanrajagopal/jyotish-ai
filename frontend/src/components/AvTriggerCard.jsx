/**
 * AvTriggerCard — Shodhya Pinda trigger nakshatra status (Moon transit activation).
 */

const PLANET_ICONS = {
  SUN: '☉', MOON: '☽', MARS: '♂', MERCURY: '☿',
  JUPITER: '♃', VENUS: '♀', SATURN: '♄',
}

function formatHouses(houses) {
  if (!houses?.length) return ''
  return houses.map(h => `H${h}`).join(', ')
}

function PlanetRow({ planet }) {
  const icon = PLANET_ICONS[planet.planet] || '•'
  const houses = formatHouses(planet.houses_ruled)
  return (
    <div className="av-trigger-row">
      <span className="av-trigger-row__name">
        {icon} {planet.planet_label}
        <span className="av-trigger-row__pinda"> ({planet.shodhya_pinda})</span>
      </span>
      <span className="av-trigger-row__meta">
        {houses && <span>{houses}</span>}
        {planet.theme && <span className="av-trigger-row__theme">{planet.theme}</span>}
      </span>
    </div>
  )
}

export default function AvTriggerCard({ status, compact = false, className = '' }) {
  if (!status?.available) return null

  const { is_trigger_day, active_nakshatra, active_planets, next_trigger, hotspots } = status
  const tripleHotspot = hotspots?.find(h => h.is_triple_trigger)

  if (compact) {
    if (is_trigger_day) {
      const labels = active_planets?.map(p => p.planet_label).join(', ')
      return (
        <div className={`av-trigger-card av-trigger-card--active ${className}`}>
          <div className="av-trigger-card__head">
            <span className="av-trigger-card__badge">✦ AV Trigger active</span>
            <strong>{active_nakshatra}</strong>
          </div>
          <p className="av-trigger-card__sub">
            Moon in your trigger nakshatra — {labels} themes may stand out today.
          </p>
          {active_planets?.length > 0 && (
            <div className="av-trigger-card__rows">
              {active_planets.map(p => (
                <PlanetRow key={p.planet} planet={p} />
              ))}
            </div>
          )}
        </div>
      )
    }

    if (next_trigger) {
      const labels = next_trigger.planet_labels?.join(', ')
      const dayLabel = next_trigger.days_until === 0 ? 'today' : `in ${next_trigger.days_until} day${next_trigger.days_until === 1 ? '' : 's'}`
      return (
        <div className={`av-trigger-card av-trigger-card--next ${className}`}>
          <div className="av-trigger-card__head">
            <span className="av-trigger-card__badge av-trigger-card__badge--muted">Next AV trigger</span>
            <strong>{next_trigger.nakshatra}</strong>
            <span className="av-trigger-card__when">{dayLabel}</span>
          </div>
          <p className="av-trigger-card__sub">
            {labels}{next_trigger.is_hotspot ? ' · hotspot' : ''}
          </p>
        </div>
      )
    }

    return null
  }

  return (
    <div className={`av-trigger-card av-trigger-card--full ${is_trigger_day ? 'av-trigger-card--active' : ''} ${className}`}>
      <div className="av-trigger-card__head">
        <span className="av-trigger-card__title">Shodhya Pinda triggers</span>
        <span className="av-trigger-card__moon">Moon today: {status.today_moon_nak}</span>
      </div>

      {is_trigger_day ? (
        <>
          <p className="av-trigger-card__lead">
            <strong>{active_nakshatra}</strong> — trigger active today
            {active_planets?.length >= 3 && ' (triple hotspot)'}
          </p>
          <div className="av-trigger-card__rows">
            {active_planets.map(p => (
              <PlanetRow key={p.planet} planet={p} />
            ))}
          </div>
        </>
      ) : next_trigger ? (
        <p className="av-trigger-card__lead">
          Next trigger: <strong>{next_trigger.nakshatra}</strong>
          {' '}in {next_trigger.days_until} day{next_trigger.days_until === 1 ? '' : 's'}
          {' '}({next_trigger.planet_labels?.join(', ')})
        </p>
      ) : null}

      {tripleHotspot && !is_trigger_day && (
        <p className="av-trigger-card__hint">
          Hotspot: {tripleHotspot.planet_labels.join(', ')} → {tripleHotspot.nakshatra}
        </p>
      )}

      {!compact && status.all_triggers?.length > 0 && (
        <details className="av-trigger-details">
          <summary>All planet triggers</summary>
          <ul className="av-trigger-list">
            {status.all_triggers.map(t => (
              <li key={t.planet}>
                {PLANET_ICONS[t.planet]} {t.planet_label}: {t.trigger_nakshatra}
                {' '}({t.shodhya_pinda}, {t.pinda_category})
              </li>
            ))}
          </ul>
        </details>
      )}

      <p className="av-trigger-card__help">{status.help}</p>
    </div>
  )
}

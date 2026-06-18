/**
 * HoraiPanel — daily Horai & Uba Horai inside Panchangam tab.
 */
import { useState, useEffect, useMemo, useCallback } from 'react'
import api from '../api/client'
import {
  HORAI_MODES,
  HORA_ACTIVITY_TA,
  PLANET_INFO,
  addDaysYmd,
  buildHoraiDay,
  computeLiveHorai,
  isSlotActive,
  nowInTimezone,
  weekdaySunZeroFromVaaram,
  weekdaySunZeroFromYmd,
} from '../lib/horai'

function useNowTick(intervalMs = 1000) {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), intervalMs)
    return () => clearInterval(id)
  }, [intervalMs])
  return now
}

function Countdown({ endMin, localMinutes, timeZone, displayYmd }) {
  if (endMin == null || localMinutes == null) return null
  let diff = endMin - localMinutes
  if (diff < 0) diff += 24 * 60
  const mins = Math.floor(diff % 60)
  const secs = 59 - (new Date().getSeconds())
  return (
    <span className="hr-countdown">
      {String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
    </span>
  )
}

function HoraiCell({ slot, active, ubaPlanet, showUba }) {
  const info = PLANET_INFO[slot.planet] || { en: slot.planet, ta: slot.planet }
  const ubaInfo = ubaPlanet ? PLANET_INFO[ubaPlanet] : null
  const malefic = info.malefic
  return (
    <article
      className={`hr-cell ${malefic ? 'hr-cell--malefic' : 'hr-cell--benefic'} ${active ? 'hr-cell--active' : ''}`}
    >
      <div className="hr-cell__planet">{info.ta}</div>
      <div className="hr-cell__en">{info.en}</div>
      <div className="hr-cell__time">{slot.labelStart} – {slot.labelEnd}</div>
      {active && showUba && ubaInfo && (
        <div className="hr-cell__uba">உப: {ubaInfo.ta}</div>
      )}
    </article>
  )
}

export default function HoraiPanel({ displayDate, location, panch, enabled = true, onSelectDate }) {
  const [mode, setMode] = useState(HORAI_MODES.FIXED)
  const [nextSunrise, setNextSunrise] = useState(null)
  const [nightOpen, setNightOpen] = useState(() => (
    typeof window !== 'undefined' ? window.matchMedia('(min-width: 640px)').matches : true
  ))
  const now = useNowTick(1000)

  useEffect(() => {
    const mq = window.matchMedia('(min-width: 640px)')
    const sync = () => setNightOpen(mq.matches)
    sync()
    mq.addEventListener('change', sync)
    return () => mq.removeEventListener('change', sync)
  }, [])

  const timeZone = panch?.timezone || 'Asia/Kolkata'
  const weekdaySun0 = weekdaySunZeroFromVaaram(panch?.vaaram_name)

  const fetchNextSunrise = useCallback(async () => {
    if (!enabled || mode !== HORAI_MODES.SUNRISE || !displayDate || !location) return
    try {
      const nextDate = addDaysYmd(displayDate, 1)
      const res = await api.get('/panchangam/date', { params: { date: nextDate, location } })
      setNextSunrise(res.data?.sunrise || null)
    } catch {
      setNextSunrise(null)
    }
  }, [displayDate, location, mode, enabled])

  useEffect(() => {
    fetchNextSunrise()
  }, [fetchNextSunrise])

  const horaiDay = useMemo(() => {
    if (!panch || !displayDate) return null
    return buildHoraiDay({
      displayYmd: displayDate,
      weekdaySun0,
      mode,
      timeZone,
      sunriseIso: panch.sunrise,
      sunsetIso: panch.sunset,
      nextSunriseIso: nextSunrise,
    })
  }, [panch, displayDate, weekdaySun0, mode, timeZone, nextSunrise])

  const live = useMemo(() => {
    if (!enabled || !panch) return null
    return computeLiveHorai({
      now,
      timeZone,
      weekdaySun0ForDate: weekdaySun0,
      mode,
      sunriseIso: panch.sunrise,
      sunsetIso: panch.sunset,
      getWeekdayForYmd: (ymd) => (
        ymd === displayDate
          ? weekdaySun0
          : weekdaySunZeroFromYmd(ymd, timeZone)
      ),
    })
  }, [enabled, panch, now, timeZone, weekdaySun0, mode])

  const localNow = nowInTimezone(timeZone)

  if (!enabled || !panch) {
    return (
      <div className="hr-panel hr-panel--muted" id="horai">
        Load Panchangam to see Horai…
      </div>
    )
  }

  const liveInfo = live ? PLANET_INFO[live.planet] : null
  const liveUba = live?.ubaPlanet ? PLANET_INFO[live.ubaPlanet] : null
  const showMismatchBanner = live && live.ownerYmd !== displayDate
  const activeSlot = horaiDay?.slots.find(s => isSlotActive(s, live, displayDate))

  return (
    <section className="hr-panel" id="horai">
      <header className="hr-header">
        <div>
          <h3 className="hr-title">🕐 Horai & Uba Horai</h3>
          <p className="hr-subtitle">
            {mode === HORAI_MODES.FIXED
              ? 'Fixed 6 AM–6 PM day · 6 PM–6 AM night (location time)'
              : 'Classical: 12 day + 12 night slots from sunrise/sunset'}
          </p>
        </div>
        <div className="hr-mode-toggle" role="group" aria-label="Horai calculation mode">
          <button
            type="button"
            className={`hr-mode-btn ${mode === HORAI_MODES.FIXED ? 'hr-mode-btn--on' : ''}`}
            onClick={() => setMode(HORAI_MODES.FIXED)}
          >
            6 AM
          </button>
          <button
            type="button"
            className={`hr-mode-btn ${mode === HORAI_MODES.SUNRISE ? 'hr-mode-btn--on' : ''}`}
            onClick={() => setMode(HORAI_MODES.SUNRISE)}
          >
            Sunrise
          </button>
        </div>
      </header>

      {showMismatchBanner && (
        <div className="hr-banner" role="status">
          <strong>Before {live.anchorLabel}:</strong> live horai follows{' '}
          <button
            type="button"
            className="hr-banner__link"
            onClick={() => onSelectDate?.(live.ownerYmd)}
          >
            {live.ownerYmd}
          </button>
          {' '}(night ending now). Horai for <strong>{displayDate}</strong> starts at{' '}
          {mode === HORAI_MODES.FIXED ? '6:00 AM' : 'sunrise'}.
        </div>
      )}

      {live && liveInfo && (
        <div className="hr-now">
          <div className="hr-now__label">Current horai · {location}</div>
          <div className="hr-now__main">
            <span className="hr-now__planet">{liveInfo.ta}</span>
            <span className="hr-now__en">({liveInfo.en})</span>
            {live.ownerYmd === displayDate && activeSlot && (
              <span className="hr-now__range">
                {activeSlot.labelStart} – {activeSlot.labelEnd}
              </span>
            )}
          </div>
          {liveUba && (
            <div className="hr-now__uba">
              Uba Horai: {liveUba.ta} ({liveUba.en})
            </div>
          )}
          {live.ownerYmd === displayDate && activeSlot && localNow && (
            <div className="hr-now__count">
              Next horai in{' '}
              <Countdown
                endMin={activeSlot.endMin}
                localMinutes={localNow.localMinutes}
                timeZone={timeZone}
                displayYmd={displayDate}
              />
            </div>
          )}
        </div>
      )}

      {horaiDay && (
        <>
          <details className="hr-section" open>
            <summary className="hr-section__summary">
              <span className="hr-section__title">Day horai</span>
              <span className="hr-section__hint">
                {mode === HORAI_MODES.FIXED ? '6 AM – 6 PM' : 'Sunrise – Sunset'}
              </span>
            </summary>
            <div className="hr-grid">
              {horaiDay.daySlots.map(slot => (
                <HoraiCell
                  key={`d-${slot.slotIndex}`}
                  slot={slot}
                  active={isSlotActive(slot, live, displayDate)}
                  ubaPlanet={live?.ubaPlanet}
                  showUba={isSlotActive(slot, live, displayDate)}
                />
              ))}
            </div>
          </details>

          <details className="hr-section" open={nightOpen} onToggle={e => setNightOpen(e.target.open)}>
            <summary className="hr-section__summary">
              <span className="hr-section__title">Night horai</span>
              <span className="hr-section__hint">
                {mode === HORAI_MODES.FIXED
                  ? `6 PM ${displayDate} – 6 AM ${addDaysYmd(displayDate, 1)}`
                  : 'Sunset – next sunrise'}
              </span>
            </summary>
            <div className="hr-grid">
              {horaiDay.nightSlots.map(slot => (
                <HoraiCell
                  key={`n-${slot.slotIndex}`}
                  slot={slot}
                  active={isSlotActive(slot, live, displayDate)}
                  ubaPlanet={live?.ubaPlanet}
                  showUba={isSlotActive(slot, live, displayDate)}
                />
              ))}
            </div>
          </details>
        </>
      )}

      <details className="hr-primer">
        <summary className="hr-primer__summary">Planet activities (Tamil tradition)</summary>
        <ul className="hr-primer__list">
          {Object.entries(HORA_ACTIVITY_TA).map(([planet, text]) => (
            <li key={planet}>
              <strong>{PLANET_INFO[planet]?.ta || planet}</strong> — {text}
            </li>
          ))}
        </ul>
      </details>
    </section>
  )
}

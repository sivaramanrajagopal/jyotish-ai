/**
 * CosmosStrip — static header bar: today's sky + personal Tara (when chart exists).
 * Tap anywhere → Panchangam tab. Alert state for Rahu Kalam / Chandra Ashtama.
 */

import { useState, useEffect, useCallback, Fragment } from 'react'
import { fetchSkyToday } from '../lib/skyToday'

function Segment({ children, accent }) {
  return (
    <span
      className="cosmos-strip__seg"
      style={accent ? { color: 'var(--orange-dark)', fontWeight: 700 } : undefined}
    >
      {children}
    </span>
  )
}

function Dot() {
  return <span className="cosmos-strip__dot" aria-hidden="true">·</span>
}

export default function CosmosStrip({ location, chart, onOpenPanchangam }) {
  const [sky, setSky] = useState(null)
  const [err, setErr] = useState(false)

  const load = useCallback(async (force = false) => {
    try {
      setErr(false)
      const data = await fetchSkyToday({ location, chart, force })
      setSky(data)
    } catch {
      setErr(true)
    }
  }, [location, chart])

  useEffect(() => {
    load()
    const id = setInterval(() => load(true), 30 * 60 * 1000)
    const onFocus = () => load(true)
    window.addEventListener('focus', onFocus)
    return () => {
      clearInterval(id)
      window.removeEventListener('focus', onFocus)
    }
  }, [load])

  if (err || !sky) return null

  const alert = sky.alert
  const personal = sky.personal

  const items = [
    { key: 'date', text: sky.date_label },
    sky.vaaram && { key: 'vaaram', text: sky.vaaram },
    { key: 'moon', text: `🌙 ${sky.moon_sign_short}`, accent: true },
    { key: 'sun', text: `☀️ ${sky.sun_sign_short}` },
    sky.retrograde_short?.length > 0 && {
      key: 'retro', text: sky.retrograde_short.join(' '),
    },
    personal?.tara_name && {
      key: 'tara',
      text: `Tara: ${personal.tara_name}`,
      accent: personal.tara_favourable,
    },
  ].filter(Boolean)

  return (
    <div className="cosmos-strip-wrap">
      {alert && (
        <div
          className={`cosmos-alert cosmos-alert--${alert.severity}`}
          role="status"
        >
          <span>{alert.message}</span>
          {alert.until && (
            <span className="cosmos-alert__until">until {alert.until}</span>
          )}
        </div>
      )}

      <button
        type="button"
        className="cosmos-strip"
        onClick={onOpenPanchangam}
        aria-label="Today's sky and panchangam — tap for full details"
      >
        <span className="cosmos-strip__live" aria-hidden="true" />
        <span className="cosmos-strip__inner">
          {items.map((item, i) => (
            <Fragment key={item.key}>
              {i > 0 && <Dot />}
              <Segment accent={item.accent}>{item.text}</Segment>
            </Fragment>
          ))}
        </span>
        <span className="cosmos-strip__chev" aria-hidden="true">›</span>
      </button>
    </div>
  )
}

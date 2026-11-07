/**
 * GocharamTab — personal Gochara on House Links, rule engine only.
 * Uses POST /forecast/links — no AI calls. For AI daily narrative, see Forecast tab.
 */

import { useState } from 'react'
import api from '../api/client'
import { useApiResult, objectKey } from '../hooks/useApiResult'
import { forecastPayload } from '../lib/chartPayload'
import { formatApiError } from '../lib/apiError'
import { formatTransitMoment } from '../lib/formatMoment'
import { localISODate, localISODateOffset } from '../lib/dates'
import { GocharaPlanetTable, HouseStatusDetail, HouseStatusTiles, PeriodSummary } from './TransitHouseStatus'

function todayISO() {
  return localISODate()
}

function tomorrowISO() {
  return localISODateOffset(1)
}

function DateTimePicker({ transitDate, setTransitDate, transitTime, setTransitTime, transitMoment }) {
  const isToday = transitDate === todayISO()
  return (
    <div className="gochar-picker">
      <div className="gochar-picker__row">
        <label htmlFor="gochar-date">📅 Gochara date</label>
        <input
          id="gochar-date"
          type="date"
          value={transitDate}
          min="2020-01-01"
          max="2035-12-31"
          onChange={e => setTransitDate(e.target.value)}
        />
        {!isToday && (
          <button type="button" className="gochar-picker__chip" onClick={() => setTransitDate(todayISO())}>
            Today
          </button>
        )}
      </div>
      <div className="gochar-picker__row">
        <label htmlFor="gochar-time">🕐 Local time</label>
        <input
          id="gochar-time"
          type="time"
          value={transitTime}
          onChange={e => setTransitTime(e.target.value)}
        />
        {transitTime && (
          <button type="button" className="gochar-picker__chip" onClick={() => setTransitTime('')}>
            {isToday ? 'Now' : '06:00'}
          </button>
        )}
      </div>
      <p className="gochar-picker__hint">
        House status from House Links; planet results from your natal Moon (Parasara Gochara + Vedha).{' '}
        {isToday ? 'Empty time = now.' : 'Empty time = 06:00 local.'}
      </p>
      {transitMoment && (
        <p className="gochar-picker__hint">Computed: {formatTransitMoment(transitMoment)}</p>
      )}
    </div>
  )
}

function scrollToDetail() {
  setTimeout(() => {
    document.getElementById('gochar-house-detail')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, 150)
}

export default function GocharamTab({ chart, userId, enabled = true, onOpenForecast }) {
  const [transitDate, setTransitDate] = useState(todayISO)
  const [transitTime, setTransitTime] = useState('')
  const linksKey = chart && enabled
    ? `${objectKey(chart)}|${userId}|${transitDate}|${transitTime}`
    : null
  const req = useApiResult(
    linksKey,
    () => api.post('/forecast/links', forecastPayload(chart, userId, transitDate, transitTime || undefined))
      .then(r => r.data),
  )
  const { loading } = req
  const data = req.error ? null : req.data
  const error = req.error ? formatApiError(req.error, 'Could not load Gochara.') : ''
  // A selection belongs to one chart and moment; changing either clears it.
  const [selection, setSelection] = useState({ key: null, house: null })
  const selectedHouse = selection.key === linksKey ? selection.house : null
  const setSelectedHouse = (house) => setSelection({ key: linksKey, house })

  if (!enabled) {
    return (
      <p className="gochar-placeholder">Open Gochara to load your personal transits…</p>
    )
  }

  if (loading) {
    return (
      <div className="gochar-loading">
        <div style={{ fontSize: 36, marginBottom: 12 }}>🪐</div>
        Computing Gochara from your natal Moon…
      </div>
    )
  }

  if (error) {
    return <div className="gochar-error">⚠️ {error}</div>
  }

  if (!data) return null

  const isToday = transitDate === todayISO()
  const selected = data.houses.find(r => r.house === selectedHouse)
  const open = (h) => { setSelectedHouse(h); scrollToDetail() }

  return (
    <div className="gochar-tab">
      <DateTimePicker
        transitDate={transitDate}
        setTransitDate={setTransitDate}
        transitTime={transitTime}
        setTransitTime={setTransitTime}
        transitMoment={data.transit_moment}
      />

      {isToday && (
        <button type="button" className="gochar-tomorrow-btn" onClick={() => setTransitDate(tomorrowISO())}>
          Check tomorrow →
        </button>
      )}

      <PeriodSummary data={data} onOpen={open} />
      <GocharaPlanetTable planets={data.planets} />

      <div className="gochar-section">
        <div className="gochar-section__head">
          <h2 className="gochar-section__title">12 life areas</h2>
          <span className="prashna-engine-badge prashna-engine-badge--rule">Rule engine</span>
        </div>
        <p className="gochar-section__hint">Tap a house to see why it is live, waiting or quiet.</p>
        <HouseStatusTiles houses={data.houses} selected={selectedHouse} onSelect={setSelectedHouse} />
      </div>

      {selected && (
        <div id="gochar-house-detail">
          <HouseStatusDetail row={selected} planets={data.planets} onClose={() => setSelectedHouse(null)} />
        </div>
      )}

      <p className="gochar-footer">
        Natal Moon {data.natal_moon_en} · Lagna {data.lagna_en} · rule-based, no AI on this tab.{' '}
        {onOpenForecast && (
          <button type="button" className="gochar-link-btn" onClick={onOpenForecast}>
            Daily AI reading → Forecast
          </button>
        )}
      </p>
    </div>
  )
}

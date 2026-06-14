/**
 * GocharamTab — personal Gochara (transits from natal Moon), rule engine only.
 * Uses POST /forecast/scores — no AI calls. For AI daily narrative, see Forecast tab.
 */

import { useState, useEffect } from 'react'
import api from '../api/client'
import { forecastPayload } from '../lib/chartPayload'
import { roundScore } from '../lib/scoreFormat'
import { formatApiError } from '../lib/apiError'
import { formatTransitMoment } from '../lib/formatMoment'

const HOUSE_ICONS = {
  1: '🧘', 2: '💰', 3: '💬', 4: '🏠', 5: '🎨', 6: '⚔️',
  7: '💑', 8: '🔮', 9: '🍀', 10: '🏆', 11: '🤝', 12: '🕊️',
}

const RAG = {
  GREEN: { bg: 'var(--rag-green-bg)', border: 'var(--rag-green-border)', text: 'var(--rag-green-text)', badge: '#27ae60' },
  AMBER: { bg: 'var(--rag-amber-bg)', border: 'var(--rag-amber-border)', text: 'var(--rag-amber-text)', badge: '#f39c12' },
  RED: { bg: 'var(--rag-red-bg)', border: 'var(--rag-red-border)', text: 'var(--rag-red-text)', badge: '#e74c3c' },
}

const PLANET_SHORT = {
  Sun: 'Su', Moon: 'Mo', Mercury: 'Me', Venus: 'Ve', Mars: 'Ma',
  Jupiter: 'Ju', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
}

function todayISO() {
  return new Date().toISOString().split('T')[0]
}

function tomorrowISO() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().split('T')[0]
}

function rankedHouses(houses) {
  return Object.values(houses || {}).sort((a, b) => b.score - a.score)
}

function ScoreBar({ score, status }) {
  const colour = RAG[status]?.badge || '#999'
  const pct = roundScore(score)
  return (
    <div className="gochar-score-bar">
      <div className="gochar-score-bar__labels">
        <span>Blended score</span>
        <span style={{ fontWeight: 700, color: colour }}>{pct}/100</span>
      </div>
      <div className="gochar-score-bar__track">
        <div className="gochar-score-bar__fill" style={{ width: `${pct}%`, background: colour }} />
      </div>
    </div>
  )
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
        Transits from your natal Moon (Parasara Gochara + Vedha).{' '}
        {isToday ? 'Empty time = now.' : 'Empty time = 06:00 local.'}
      </p>
      {transitMoment && (
        <p className="gochar-picker__hint">Computed: {formatTransitMoment(transitMoment)}</p>
      )}
    </div>
  )
}

function OverallCard({ scores }) {
  const oh = scores.overall_health || {}
  const status = oh.rag?.status || 'AMBER'
  const rc = RAG[status] || RAG.AMBER
  const ranked = rankedHouses(scores.houses)
  const top2 = ranked.slice(0, 2)
  const watch2 = ranked.slice(-2).reverse()

  return (
    <div className="gochar-overall" style={{ borderColor: rc.border, background: rc.bg }}>
      <div className="gochar-overall__head">
        <div>
          <div className="gochar-overall__title">கோசாரம் · Gochara</div>
          <div className="gochar-overall__sub">
            Natal Moon: {scores.natal_moon_en || scores.natal_moon} · Lagna: {scores.lagna_en || scores.lagna}
          </div>
        </div>
        <div className="gochar-overall__score" style={{ color: rc.badge }}>
          {oh.rag?.emoji} {roundScore(oh.average_score)}
        </div>
      </div>
      <p className="gochar-overall__note">{scores.gochara_note}</p>
      <div className="gochar-overall__chips">
        <span>🟢 {oh.green_count ?? 0} favourable</span>
        <span>🟡 {oh.amber_count ?? 0} mixed</span>
        <span>🔴 {oh.red_count ?? 0} challenging</span>
      </div>
      <div className="gochar-overall__highlights">
        <div>
          <div className="gochar-overall__hl-label">Strongest</div>
          {top2.map(h => (
            <div key={h.house_num} className="gochar-overall__hl-best">
              {HOUSE_ICONS[h.house_num]} H{h.house_num} {roundScore(h.score)}
            </div>
          ))}
        </div>
        <div>
          <div className="gochar-overall__hl-label">Needs care</div>
          {watch2.map(h => (
            <div key={h.house_num} className="gochar-overall__hl-watch">
              {HOUSE_ICONS[h.house_num]} H{h.house_num} {roundScore(h.score)}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function PlanetTable({ rows }) {
  const sorted = [...(rows || [])].sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
  return (
    <div className="gochar-section">
      <div className="gochar-section__head">
        <h2 className="gochar-section__title">Planet Gochara (from Moon)</h2>
        <span className="prashna-engine-badge prashna-engine-badge--rule">Rule engine</span>
      </div>
      <div className="gochar-planet-table-wrap">
        <table className="gochar-planet-table">
          <thead>
            <tr>
              <th>Planet</th>
              <th>Sign</th>
              <th>H from Moon</th>
              <th>Score</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(row => {
              const st = row.rag?.status || 'AMBER'
              const rc = RAG[st] || RAG.AMBER
              return (
                <tr key={row.planet}>
                  <td>
                    <strong>{PLANET_SHORT[row.planet] || row.planet}</strong>
                    {row.retrograde && <sup className="retro-sup-r">R</sup>}
                  </td>
                  <td>{row.transit_sign_en || row.transit_sign}</td>
                  <td>{row.pos_from_moon}</td>
                  <td style={{ color: rc.badge, fontWeight: 700 }}>{row.rag?.emoji} {roundScore(row.score)}</td>
                  <td>
                    {row.result}
                    {row.vedha_blocked && row.vedha_by && (
                      <span className="gochar-vedha"> · Vedha {row.vedha_by}</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function DashaCard({ dtc }) {
  if (!dtc?.correlation_score && !dtc?.summary) return null
  const score = roundScore(dtc.correlation_score ?? 50)
  const st = dtc.rag?.status || 'AMBER'
  const rc = RAG[st] || RAG.AMBER
  return (
    <div className="gochar-section gochar-dasha">
      <div className="gochar-section__head">
        <h2 className="gochar-section__title">Dasha–Gochara</h2>
        <span className="prashna-engine-badge prashna-engine-badge--rule">Rule engine</span>
      </div>
      <p style={{ margin: '0 0 8px', fontSize: 13, color: 'var(--text-secondary)' }}>
        MD {dtc.mahadasha?.planet || '—'} · Bhukti {dtc.bhukti?.planet || '—'}
      </p>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: 22, fontWeight: 800, color: rc.badge }}>{score}</span>
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>/100</span>
      </div>
      <p style={{ margin: 0, fontSize: 13, lineHeight: 1.55, color: 'var(--text-secondary)' }}>
        {dtc.summary || dtc.overall || ''}
      </p>
    </div>
  )
}

function HouseDetail({ house, onClose }) {
  if (!house) return null
  const status = house.rag?.status || 'AMBER'
  const rc = RAG[status] || RAG.AMBER
  return (
    <div className="gochar-house-detail" style={{ borderColor: rc.border, background: rc.bg }}>
      <div className="gochar-house-detail__head">
        <div>
          <div className="gochar-house-detail__title">
            {HOUSE_ICONS[house.house_num]} H{house.house_num} — {house.name}
          </div>
          <div className="gochar-house-detail__sub">{house.simple}</div>
        </div>
        <button type="button" className="gochar-house-detail__close" onClick={onClose} aria-label="Close">
          ✕
        </button>
      </div>
      <ScoreBar score={house.score} status={status} />
      <div className="gochar-house-detail__grid">
        <div><span>Natal lord strength</span><strong>{roundScore(house.natal_score)}/100</strong></div>
        <div><span>Gochara score</span><strong>{roundScore(house.transit_score)}/100</strong></div>
        <div><span>House lord</span><strong>{house.lord} → H{house.lord_placed_house}</strong></div>
        <div><span>Lord Gochara</span><strong>{house.lord_gochara_result || '—'}</strong></div>
        <div><span>Natal in house</span><strong>{house.planets_in_house?.join(', ') || '—'}</strong></div>
        <div><span>Transiting now</span><strong>{house.transit_planets?.join(', ') || '—'}</strong></div>
        {house.sav_points != null && (
          <div><span>SAV bindus</span><strong>{house.sav_points} ({house.sav_label})</strong></div>
        )}
      </div>
      <p className="gochar-house-detail__blend">{house.meta?.blend || '55% natal lord + 35% Gochara + 10% SAV'}</p>
    </div>
  )
}

export default function GocharamTab({ chart, userId, enabled = true, onOpenForecast }) {
  const [transitDate, setTransitDate] = useState(todayISO)
  const [transitTime, setTransitTime] = useState('')
  const [scores, setScores] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedHouse, setSelectedHouse] = useState(null)

  useEffect(() => {
    if (!chart || !enabled) return
    setLoading(true)
    setError('')
    setSelectedHouse(null)
    api.post('/forecast/scores', forecastPayload(chart, userId, transitDate, transitTime || undefined))
      .then(r => setScores(r.data))
      .catch(err => {
        setError(formatApiError(err, 'Could not load Gochara scores.'))
        setScores(null)
      })
      .finally(() => setLoading(false))
  }, [chart, transitDate, transitTime, userId, enabled])

  if (!enabled) {
    return (
      <p className="gochar-placeholder">Open Gochara to load your personal transit scores…</p>
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

  if (!scores) return null

  const houses = scores.houses || {}
  const isToday = transitDate === todayISO()

  return (
    <div className="gochar-tab">
      <DateTimePicker
        transitDate={transitDate}
        setTransitDate={setTransitDate}
        transitTime={transitTime}
        setTransitTime={setTransitTime}
        transitMoment={scores.transit_moment}
      />

      {isToday && (
        <button type="button" className="gochar-tomorrow-btn" onClick={() => setTransitDate(tomorrowISO())}>
          Check tomorrow →
        </button>
      )}

      <OverallCard scores={scores} />
      <DashaCard dtc={scores.dasha_transit} />
      <PlanetTable rows={scores.transit_analysis} />

      <div className="gochar-section">
        <div className="gochar-section__head">
          <h2 className="gochar-section__title">12 life areas</h2>
          <span className="prashna-engine-badge prashna-engine-badge--rule">Rule engine</span>
        </div>
        <p className="gochar-section__hint">Tap a house for lord + Gochara breakdown.</p>
        <div className="forecast-tag-grid gochar-house-grid">
          {Object.values(houses).map(h => {
            const status = h.rag?.status || 'AMBER'
            const rc = RAG[status] || RAG.AMBER
            const active = selectedHouse === h.house_num
            return (
              <button
                key={h.house_num}
                type="button"
                className={`gochar-house-chip${active ? ' gochar-house-chip--active' : ''}`}
                style={{
                  borderColor: active ? rc.badge : rc.border,
                  background: active ? rc.badge : 'var(--card-bg)',
                  color: active ? '#fff' : undefined,
                }}
                onClick={() => setSelectedHouse(active ? null : h.house_num)}
              >
                <span className="gochar-house-chip__icon">{HOUSE_ICONS[h.house_num]}</span>
                <span className="gochar-house-chip__label">H{h.house_num}</span>
                <span className="gochar-house-chip__score" style={{ color: active ? '#fff' : rc.badge }}>
                  {h.rag?.emoji} {roundScore(h.score)}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {selectedHouse && houses[selectedHouse] && (
        <div id="gochar-house-detail">
          <HouseDetail
            house={{ ...houses[selectedHouse], meta: scores.meta }}
            onClose={() => setSelectedHouse(null)}
          />
        </div>
      )}

      <p className="gochar-footer">
        Rule-based Parasara Gochara — no AI on this tab.{' '}
        {onOpenForecast && (
          <button type="button" className="gochar-link-btn" onClick={onOpenForecast}>
            Daily AI reading → Forecast
          </button>
        )}
      </p>
    </div>
  )
}

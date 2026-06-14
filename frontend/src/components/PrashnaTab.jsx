/**
 * PrashnaTab.jsx — Vedic horary (Prashna) analysis at question time.
 * Rule-based testimonies from Swiss Ephemeris; no fabricated positions.
 */

import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import SouthIndianChart from './SouthIndianChart'
import { formatApiError } from '../lib/apiError'
import { loadPrashnaHistory, savePrashnaSession, clearPrashnaHistory } from '../lib/prashnaStorage'

const CATEGORIES = [
  { key: 'career', label: 'Career / Promotion', icon: '🏆' },
  { key: 'marriage', label: 'Marriage / Relationship', icon: '💑' },
  { key: 'money', label: 'Money / Finance', icon: '💰' },
  { key: 'property', label: 'Property / Real Estate', icon: '🏠' },
  { key: 'health', label: 'Health', icon: '⚕️' },
  { key: 'travel', label: 'Travel', icon: '✈️' },
  { key: 'education', label: 'Education', icon: '📚' },
  { key: 'general', label: 'General', icon: '🔮' },
]

const VERDICT_STYLE = {
  likely_yes:       { bg: '#1a3d2e', border: '#27ae60', color: '#81C784' },
  likely_no:          { bg: '#3d1a1a', border: '#e74c3c', color: '#EF9A9A' },
  delayed:            { bg: '#3d2e1a', border: '#f39c12', color: '#FFB74D' },
  obstructed:         { bg: '#2e1a3d', border: '#9b59b6', color: '#CE93D8' },
  unclear:            { bg: '#1a253d', border: '#5c6bc0', color: '#9FA8DA' },
  possible_delayed:   { bg: '#3d321a', border: '#ff9800', color: '#FFCC80' },
}

function useLiveClock() {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  return now
}

function formatClock(d) {
  return d.toLocaleString(undefined, {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function TestimonyList({ title, items, tone }) {
  if (!items?.length) return null
  const colors = {
    positive: { dot: '#27ae60', label: 'Positive Testimonies' },
    negative: { dot: '#e74c3c', label: 'Challenging Testimonies' },
    neutral:  { dot: '#f39c12', label: 'Neutral Testimonies' },
  }[tone] || { dot: '#999', label: title }

  return (
    <div className="prashna-glass" style={{ padding: '14px 16px', marginBottom: 12 }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: colors.dot, marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        {colors.label}
      </div>
      <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, lineHeight: 1.6, color: 'rgba(255,255,255,0.82)' }}>
        {items.map((t, i) => (
          <li key={i} style={{ marginBottom: 6 }}>{t.description}</li>
        ))}
      </ul>
    </div>
  )
}

function AnalysisCard({ title, children }) {
  return (
    <div className="prashna-glass" style={{ padding: '14px 16px', marginBottom: 12 }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: '#C9A227', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        {title}
      </div>
      <div style={{ fontSize: 13, lineHeight: 1.65, color: 'rgba(255,255,255,0.82)' }}>{children}</div>
    </div>
  )
}

export default function PrashnaTab({ enabled = true, chart = null }) {
  const now = useLiveClock()
  const [question, setQuestion] = useState('')
  const [category, setCategory] = useState('general')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState(() => loadPrashnaHistory())
  const [location, setLocation] = useState(null)
  const [locLoading, setLocLoading] = useState(false)

  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata'

  const defaultFromChart = useCallback(() => {
    const bd = chart?.birth_data
    if (!bd?.lat || !bd?.lon) return null
    return { lat: bd.lat, lon: bd.lon, place: chart?.birth_data?.place || 'Birth place' }
  }, [chart])

  useEffect(() => {
    if (!location && chart) {
      const d = defaultFromChart()
      if (d) setLocation(d)
    }
  }, [chart, location, defaultFromChart])

  const requestLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported in this browser.')
      return
    }
    setLocLoading(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocation({
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          place: 'Current location',
        })
        setLocLoading(false)
      },
      (err) => {
        setLocLoading(false)
        const blocked = err?.code === 1 || String(err?.message || '').includes('policy')
        setError(
          blocked
            ? 'Location blocked by browser or site policy. Using Chennai or your birth place — Prashna still works.'
            : 'Could not get location. Using default or birth place.',
        )
      },
      { timeout: 10000, maximumAge: 60000 },
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!enabled) return
    setError('')
    setLoading(true)
    setResult(null)

    const payload = {
      question: question.trim(),
      category,
      timestamp: new Date().toISOString(),
      timezone,
    }
    if (location?.lat != null && location?.lon != null) {
      payload.lat = location.lat
      payload.lon = location.lon
      payload.place = location.place
    }

    try {
      const { data } = await api.post('/prashna/analyze', payload)
      setResult(data)
      savePrashnaSession({
        question: data.question?.text,
        category: data.question?.category,
        verdict: data.verdict?.label,
        timestamp: data.question?.timestamp,
      })
      setHistory(loadPrashnaHistory())
    } catch (err) {
      setError(formatApiError(err, 'Prashna analysis failed.'))
    } finally {
      setLoading(false)
    }
  }

  const loadHistoryItem = (item) => {
    setQuestion(item.question || '')
    setCategory(item.category || 'general')
  }

  if (!enabled) {
    return (
      <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--text-muted)' }}>
        Open Prashna to cast a horary chart…
      </div>
    )
  }

  const vs = result ? (VERDICT_STYLE[result.verdict?.result] || VERDICT_STYLE.unclear) : null

  return (
    <div className="prashna-root max-w-3xl mx-auto px-3 py-4 sm:px-4 sm:py-6">
      {/* Hero */}
      <div className="prashna-hero" style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          Prashna AI · Vedic Horary
        </div>
        <h2 style={{ margin: '6px 0 4px', fontSize: 22, fontWeight: 800, color: '#E8D5A3' }}>
          Ask the Cosmos
        </h2>
        <p style={{ margin: '0 0 12px', fontSize: 13, color: 'rgba(255,255,255,0.6)' }}>
          Chart cast at the exact moment of your question — Lahiri sidereal, rule-based testimonies.
        </p>
        <div className="prashna-glass" style={{ padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 20 }}>🕐</span>
          <div>
            <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase' }}>Live cosmic clock</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#FFF', fontVariantNumeric: 'tabular-nums' }}>{formatClock(now)}</div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)' }}>{timezone}</div>
          </div>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="prashna-glass" style={{ padding: '16px 18px', marginBottom: 16 }}>
        <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: 'rgba(255,255,255,0.7)', marginBottom: 6 }}>
          Your question
        </label>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Will I receive the job offer this month?"
          required
          minLength={5}
          maxLength={500}
          rows={3}
          style={{
            width: '100%', boxSizing: 'border-box', padding: '12px 14px', borderRadius: 10,
            border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(0,0,0,0.25)',
            color: '#FFF', fontSize: 16, resize: 'vertical', marginBottom: 14,
          }}
        />

        <div style={{ fontSize: 12, fontWeight: 700, color: 'rgba(255,255,255,0.7)', marginBottom: 8 }}>Category</div>
        <div className="prashna-category-grid" style={{ marginBottom: 14 }}>
          {CATEGORIES.map((c) => (
            <button
              key={c.key}
              type="button"
              onClick={() => setCategory(c.key)}
              style={{
                padding: '10px 8px', borderRadius: 10, cursor: 'pointer', fontSize: 11, fontWeight: 600,
                border: category === c.key ? '2px solid #C9A227' : '1px solid rgba(255,255,255,0.12)',
                background: category === c.key ? 'rgba(201,162,39,0.15)' : 'rgba(0,0,0,0.2)',
                color: category === c.key ? '#E8D5A3' : 'rgba(255,255,255,0.75)',
              }}
            >
              {c.icon}<br />{c.label.split(' / ')[0]}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center', marginBottom: 14, fontSize: 12, color: 'rgba(255,255,255,0.55)' }}>
          <span>📍 {location?.place || 'Chennai (default)'}</span>
          <button
            type="button"
            onClick={requestLocation}
            disabled={locLoading}
            style={{
              padding: '6px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)',
              background: 'transparent', color: '#C9A227', fontSize: 11, fontWeight: 600, cursor: 'pointer',
            }}
          >
            {locLoading ? 'Locating…' : 'Use my location'}
          </button>
        </div>

        {error && (
          <div style={{ color: '#EF9A9A', background: 'rgba(231,76,60,0.12)', border: '1px solid rgba(231,76,60,0.35)', borderRadius: 10, padding: '10px 12px', marginBottom: 12, fontSize: 13 }}>
            ⚠️ {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading || question.trim().length < 5}
          style={{
            width: '100%', padding: '14px', borderRadius: 10, border: 'none',
            background: loading ? 'rgba(201,162,39,0.4)' : 'linear-gradient(135deg, #C9A227, #E8B923)',
            color: '#1a1033', fontSize: 15, fontWeight: 800, cursor: loading ? 'wait' : 'pointer',
          }}
        >
          {loading ? '✦ Casting Prashna chart…' : '🔮 Analyze Question'}
        </button>
      </form>

      {/* Results */}
      {result && (
        <div>
          <div
            style={{
              borderRadius: 16, padding: '20px 18px', marginBottom: 16,
              background: vs.bg, border: `2px solid ${vs.border}`, textAlign: 'center',
            }}
          >
            <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', marginBottom: 6 }}>Verdict</div>
            <div style={{ fontSize: 28, fontWeight: 800, color: vs.color, marginBottom: 8 }}>{result.verdict?.label}</div>
            <p style={{ fontSize: 13, lineHeight: 1.65, color: 'rgba(255,255,255,0.85)', margin: '0 0 10px' }}>{result.verdict?.explanation}</p>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)' }}>
              🟢 {result.verdict?.positive_count} supportive · 🔴 {result.verdict?.negative_count} challenging · ⚪ {result.verdict?.neutral_count} neutral
            </div>
          </div>

          <AnalysisCard title="Summary">
            <p style={{ margin: 0 }}>{result.interpretation?.summary}</p>
          </AnalysisCard>

          <TestimonyList items={result.testimonies?.positive} tone="positive" />
          <TestimonyList items={result.testimonies?.negative} tone="negative" />
          <TestimonyList items={result.testimonies?.neutral} tone="neutral" />

          <AnalysisCard title="Moon analysis">
            <strong>{result.analysis?.moon?.moon_sign}</strong> in house {result.analysis?.moon?.moon_house} · {result.analysis?.moon?.strength_label}<br />
            {result.analysis?.moon?.explanation}
          </AnalysisCard>

          <AnalysisCard title={`Relevant house — ${result.analysis?.relevant_house?.category_label}`}>
            House {result.analysis?.relevant_house?.house_num} ({result.analysis?.relevant_house?.house_sign}) ·
            Lord {result.analysis?.relevant_house?.house_lord} · {result.analysis?.relevant_house?.lord_strength_label}<br />
            {result.analysis?.relevant_house?.explanation}
          </AnalysisCard>

          <AnalysisCard title="Timing indication">
            <strong>{result.analysis?.timing?.timing_band}</strong><br />
            {result.analysis?.timing?.explanation}<br />
            <em style={{ fontSize: 12, opacity: 0.7 }}>{result.analysis?.timing?.note}</em>
          </AnalysisCard>

          <AnalysisCard title="Practical guidance">
            {result.interpretation?.practical_guidance}
          </AnalysisCard>

          {result.chart && (
            <div className="prashna-glass" style={{ padding: '14px', marginBottom: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#C9A227', marginBottom: 10, textTransform: 'uppercase' }}>Prashna chart</div>
              <SouthIndianChart
                title="Prashna"
                subtitle={`${result.chart.moment?.date} ${result.chart.moment?.time}`}
                planetPositions={result.chart.planet_positions}
                lagnaSignIndex={result.chart.ascendant?.sign_index}
              />
              <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', margin: '10px 0 0', textAlign: 'center' }}>
                Lagna: {result.chart.ascendant?.sign} · {result.question?.location?.place} · Lahiri
              </p>
            </div>
          )}

          <div style={{
            fontSize: 11, lineHeight: 1.6, color: 'rgba(255,255,255,0.45)',
            borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 14, marginTop: 8,
          }}>
            {result.disclaimer}
          </div>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)' }}>Session history</div>
            <button
              type="button"
              onClick={() => { clearPrashnaHistory(); setHistory([]) }}
              style={{ fontSize: 11, color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer' }}
            >
              Clear
            </button>
          </div>
          {history.map((h, i) => (
            <button
              key={i}
              type="button"
              onClick={() => loadHistoryItem(h)}
              style={{
                display: 'block', width: '100%', textAlign: 'left', padding: '10px 12px',
                marginBottom: 8, borderRadius: 10, border: '1px solid var(--card-border)',
                background: 'var(--card-bg)', cursor: 'pointer', fontSize: 12,
              }}
            >
              <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{h.verdict}</div>
              <div style={{ color: 'var(--text-muted)', marginTop: 2 }}>{h.question?.slice(0, 80)}{h.question?.length > 80 ? '…' : ''}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

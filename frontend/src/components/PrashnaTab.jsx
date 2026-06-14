/**
 * PrashnaTab.jsx — Category + question dropdowns, rule-based engine, Phase 2 AI narration.
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import api from '../api/client'
import SouthIndianChart from './SouthIndianChart'
import { formatApiError } from '../lib/apiError'
import { loadPrashnaHistory, savePrashnaSession, clearPrashnaHistory } from '../lib/prashnaStorage'
import { PRASHNA_CATALOG, mergePrashnaCatalog, firstQuestionId } from '../constants/prashnaCatalog'

const VERDICT_STYLE = {
  likely_yes:     { bg: '#1a3d2e', border: '#27ae60', color: '#81C784' },
  likely_no:      { bg: '#3d1a1a', border: '#e74c3c', color: '#EF9A9A' },
  delayed:        { bg: '#3d2e1a', border: '#f39c12', color: '#FFB74D' },
  obstructed:     { bg: '#2e1a3d', border: '#9b59b6', color: '#CE93D8' },
  unclear:        { bg: '#1a253d', border: '#5c6bc0', color: '#9FA8DA' },
  possible_delayed: { bg: '#3d321a', border: '#ff9800', color: '#FFCC80' },
}

const selectStyle = {
  display: 'block',
  width: '100%',
  boxSizing: 'border-box',
  minHeight: 48,
  padding: '0 14px',
  fontSize: 16,
  borderRadius: 10,
  WebkitAppearance: 'none',
  appearance: 'none',
  backgroundRepeat: 'no-repeat',
  backgroundPosition: 'right 14px center',
  paddingRight: 40,
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
    weekday: 'short', year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

function TestimonyList({ items, tone }) {
  if (!items?.length) return null
  const colors = {
    positive: { dot: '#27ae60', label: 'Positive Testimonies' },
    negative: { dot: '#e74c3c', label: 'Challenging Testimonies' },
    neutral:  { dot: '#f39c12', label: 'Neutral Testimonies' },
  }[tone] || { dot: '#999', label: 'Testimonies' }

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
  const [categories, setCategories] = useState(PRASHNA_CATALOG)
  const [category, setCategory] = useState('career')
  const [questionId, setQuestionId] = useState(() => firstQuestionId(PRASHNA_CATALOG, 'career'))
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState(() => loadPrashnaHistory())
  const [location, setLocation] = useState(null)
  const [locLoading, setLocLoading] = useState(false)

  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata'

  const activeCategory = useMemo(
    () => categories.find(c => c.key === category) || categories[0],
    [categories, category],
  )

  const questions = activeCategory?.questions || []

  useEffect(() => {
    if (!enabled) return
    api.get('/prashna/categories')
      .then(({ data }) => {
        const merged = mergePrashnaCatalog(data?.categories)
        setCategories(merged)
      })
      .catch(() => {
        setCategories(PRASHNA_CATALOG)
      })
  }, [enabled])

  const handleCategoryChange = (nextKey) => {
    setCategory(nextKey)
    setQuestionId(firstQuestionId(categories, nextKey))
  }

  useEffect(() => {
    const qs = categories.find(c => c.key === category)?.questions || []
    if (qs.length && !qs.some(q => q.id === questionId)) {
      setQuestionId(qs[0].id)
    }
  }, [categories, category, questionId])

  const selectedQuestion = questions.find(q => q.id === questionId)?.text || ''

  const defaultFromChart = useCallback(() => {
    const bd = chart?.birth_data
    if (!bd?.lat || !bd?.lon) return null
    return { lat: bd.lat, lon: bd.lon, place: bd.place || 'Birth place' }
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
    setError('')
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocation({ lat: pos.coords.latitude, lon: pos.coords.longitude, place: 'Current location' })
        setLocLoading(false)
      },
      () => {
        setLocLoading(false)
        setError('Could not get GPS. Using birth place or Chennai — analysis still works.')
      },
      { timeout: 10000, maximumAge: 60000 },
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!enabled || !questionId) return
    setError('')
    setLoading(true)
    setResult(null)

    const payload = {
      category,
      question_id: questionId,
      timestamp: new Date().toISOString(),
      timezone,
      include_ai: true,
      language: 'english',
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
      <div className="prashna-hero" style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          Prashna AI · Vedic Horary
        </div>
        <h2 style={{ margin: '6px 0 4px', fontSize: 22, fontWeight: 800, color: '#E8D5A3' }}>
          Ask the Cosmos
        </h2>
        <p style={{ margin: '0 0 12px', fontSize: 13, color: 'rgba(255,255,255,0.6)' }}>
          Pick a category and question — chart cast at this moment with rule-based testimonies + AI narration.
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

      <form onSubmit={handleSubmit} className="prashna-form-card">
        <div style={{ marginBottom: 16 }}>
          <label htmlFor="prashna-category" className="prashna-label">Category</label>
          <select
            id="prashna-category"
            className="prashna-select"
            value={category}
            onChange={(e) => handleCategoryChange(e.target.value)}
            style={selectStyle}
          >
            {categories.map(c => (
              <option key={c.key} value={c.key}>{c.icon} {c.label}</option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label htmlFor="prashna-question" className="prashna-label">Your question</label>
          {questions.length === 0 ? (
            <p className="prashna-question-preview" role="alert">No questions loaded — refresh the page.</p>
          ) : (
            <select
              id="prashna-question"
              className="prashna-select"
              value={questionId}
              onChange={(e) => setQuestionId(e.target.value)}
              style={selectStyle}
              required
            >
              {questions.map(q => (
                <option key={q.id} value={q.id}>{q.text}</option>
              ))}
            </select>
          )}
          {selectedQuestion && (
            <p className="prashna-question-preview" role="status">
              {selectedQuestion}
            </p>
          )}
        </div>

        <div className="prashna-location-row">
          <span>📍 {location?.place || 'Chennai (default)'}</span>
          <button type="button" onClick={requestLocation} disabled={locLoading} className="prashna-link-btn">
            {locLoading ? 'Locating…' : 'Use my location'}
          </button>
        </div>

        {error && (
          <div className="prashna-error" role="alert">⚠️ {error}</div>
        )}

        <button type="submit" disabled={loading || !questionId} className="prashna-submit-btn">
          {loading ? '✦ Casting Prashna chart…' : '🔮 Analyze Question'}
        </button>
      </form>

      {result && (
        <div>
          <div className="prashna-verdict-card" style={{ background: vs.bg, borderColor: vs.border }}>
            <div className="prashna-verdict-label">Verdict</div>
            <div className="prashna-verdict-title" style={{ color: vs.color }}>{result.verdict?.label}</div>
            <p className="prashna-verdict-text">{result.verdict?.explanation}</p>
            <div className="prashna-verdict-counts">
              🟢 {result.verdict?.positive_count} supportive · 🔴 {result.verdict?.negative_count} challenging · ⚪ {result.verdict?.neutral_count} neutral
            </div>
          </div>

          {result.ai_reading && (
            <AnalysisCard title="🤖 AI Prashna reading">
              <p style={{ margin: '0 0 8px' }}>{result.ai_reading}</p>
              <p style={{ margin: 0, fontSize: 11, opacity: 0.65, fontStyle: 'italic' }}>
                AI narration based only on computed testimonies — not a guarantee.
              </p>
            </AnalysisCard>
          )}

          <AnalysisCard title="Rule-based summary">
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
            {result.analysis?.timing?.explanation}
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
            </div>
          )}

          <p className="prashna-disclaimer">{result.disclaimer}</p>
        </div>
      )}

      {history.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)' }}>Session history</div>
            <button type="button" onClick={() => { clearPrashnaHistory(); setHistory([]) }} className="prashna-link-btn" style={{ color: 'var(--text-muted)' }}>
              Clear
            </button>
          </div>
          {history.map((h, i) => (
            <div key={i} className="prashna-history-item">
              <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{h.verdict}</div>
              <div style={{ color: 'var(--text-muted)', marginTop: 2, fontSize: 12 }}>{h.question}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

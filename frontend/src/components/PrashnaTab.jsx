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
  const toneClass = {
    positive: 'prashna-result-card-title--positive',
    negative: 'prashna-result-card-title--negative',
    neutral:  'prashna-result-card-title--neutral',
  }[tone] || ''
  const labels = {
    positive: 'Positive Testimonies',
    negative: 'Challenging Testimonies',
    neutral:  'Neutral Testimonies',
  }

  return (
    <div className="prashna-result-card">
      <div className={`prashna-result-card-title ${toneClass}`}>
        {labels[tone] || 'Testimonies'}
      </div>
      <ul className="prashna-result-card-list">
        {items.map((t, i) => (
          <li key={i}>{t.description}</li>
        ))}
      </ul>
    </div>
  )
}

function AnalysisCard({ title, children, badge, badgeVariant = 'rule' }) {
  return (
    <div className="prashna-result-card">
      <div className="prashna-result-card-header">
        <div className="prashna-result-card-title">{title}</div>
        {badge && (
          <span className={`prashna-engine-badge prashna-engine-badge--${badgeVariant}`}>
            {badge}
          </span>
        )}
      </div>
      <div className="prashna-result-card-body">{children}</div>
    </div>
  )
}

function AuditTable({ headers, rows }) {
  if (!rows?.length) return <p className="prashna-audit-empty">None</p>
  return (
    <div className="prashna-audit-table-wrap">
      <table className="prashna-audit-table">
        <thead>
          <tr>
            {headers.map(h => <th key={h}>{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => <td key={j}>{cell ?? '—'}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function PrashnaAuditCard({ audit }) {
  const [expanded, setExpanded] = useState(true)
  if (!audit) return null

  const fmtDeg = (d) => (d != null && d !== '' ? `${Number(d).toFixed(2)}°` : '—')
  const fmtCoord = (lat, lon) => {
    if (lat == null || lon == null) return '—'
    return `${Number(lat).toFixed(4)}, ${Number(lon).toFixed(4)}`
  }

  const planetRows = (audit.planets || []).map(p => [
    p.planet,
    p.sign,
    fmtDeg(p.degree_in_sign),
    `H${p.house}`,
    p.nakshatra || '—',
    p.retrograde ? '℞' : '—',
    (p.roles || []).join('; '),
    (p.used_in || []).join('; '),
  ])

  const aspectRows = (audit.aspects_to_matter_house || []).map(a => [
    a.planet,
    `H${a.from_house}`,
    `H${a.target_house}`,
    a.polarity,
    a.description,
  ])

  const sigChecks = (audit.significators?.checks || []).map(c => [
    c.check,
    c.result,
    c.detail,
  ])

  const testimonyRows = (audit.testimonies_summary || []).map(t => [
    t.polarity === 'positive' ? '🟢' : t.polarity === 'negative' ? '🔴' : '⚪',
    t.category,
    t.description,
  ])

  return (
    <div className="prashna-result-card prashna-audit-card">
      <div className="prashna-result-card-header">
        <div className="prashna-result-card-title">📋 Calculation audit</div>
        <span className="prashna-engine-badge prashna-engine-badge--rule">Verify calculation</span>
      </div>
      <p className="prashna-audit-intro">
        {audit.method?.note}
      </p>
      <button
        type="button"
        className="prashna-audit-toggle"
        onClick={() => setExpanded(v => !v)}
        aria-expanded={expanded}
      >
        {expanded ? 'Hide audit tables ▲' : 'Show audit tables ▼'}
      </button>

      {expanded && (
        <div className="prashna-audit-sections">
          <section>
            <h4 className="prashna-audit-heading">Question & cast moment</h4>
            <AuditTable
              headers={['Field', 'Value']}
              rows={[
                ['Question', audit.question?.text],
                ['Category', audit.question?.category_label],
                ['Matter house', audit.matter_house?.house_num ? `H${audit.matter_house.house_num} (${audit.matter_house.house_sign})` : '—'],
                ['Cast time (ISO)', audit.moment?.timestamp_iso],
                ['Local date / time', `${audit.moment?.date || '—'} ${audit.moment?.time || ''}`.trim()],
                ['Timezone', audit.moment?.timezone],
                ['Place', audit.moment?.place],
                ['Coordinates', fmtCoord(audit.moment?.latitude, audit.moment?.longitude)],
                ['Ayanamsa', `${audit.moment?.ayanamsa || 'Lahiri'} (${audit.moment?.ayanamsa_value ?? '—'})`],
              ]}
            />
          </section>

          <section>
            <h4 className="prashna-audit-heading">Lagna (querent)</h4>
            <AuditTable
              headers={['Field', 'Value']}
              rows={[
                ['Lagna sign', `${audit.lagna?.sign} ${fmtDeg(audit.lagna?.degree_in_sign)}`],
                ['Lagna nakshatra', audit.lagna?.nakshatra ? `${audit.lagna.nakshatra} P${audit.lagna.pada}` : '—'],
                ['Querent lord (Lagna lord)', audit.lagna?.lagna_lord],
                ['Lord placement', `${audit.lagna?.lord_sign} · H${audit.lagna?.lord_house}`],
                ['Lord dignity', `${audit.lagna?.dignity} (${audit.lagna?.strength})`],
              ]}
            />
          </section>

          <section>
            <h4 className="prashna-audit-heading">Matter house (quesited)</h4>
            <AuditTable
              headers={['Field', 'Value']}
              rows={[
                ['House', `H${audit.matter_house?.house_num} ${audit.matter_house?.house_sign}`],
                ['Quesited lord', audit.matter_house?.house_lord],
                ['Lord placement', `${audit.matter_house?.lord_sign} · H${audit.matter_house?.lord_house}`],
                ['Lord dignity', `${audit.matter_house?.lord_dignity} (${audit.matter_house?.lord_strength})`],
                ['Occupants', (audit.matter_house?.occupants || []).join(', ') || 'None'],
              ]}
            />
          </section>

          <section>
            <h4 className="prashna-audit-heading">Significator link (querent ↔ quesited)</h4>
            <p className="prashna-audit-line">
              <strong>{audit.significators?.connection_label}</strong>
              {' — '}{audit.significators?.explanation}
            </p>
            <AuditTable headers={['Check', 'Result', 'Detail']} rows={sigChecks} />
          </section>

          <section>
            <h4 className="prashna-audit-heading">Drishti to matter house</h4>
            <AuditTable
              headers={['Planet', 'From', 'Aspects', 'Tone', 'Rule']}
              rows={aspectRows}
            />
          </section>

          <section>
            <h4 className="prashna-audit-heading">Moon</h4>
            <AuditTable
              headers={['Field', 'Value']}
              rows={[
                ['Sign / house', `${audit.moon?.sign} · H${audit.moon?.house}`],
                ['Nakshatra', audit.moon?.nakshatra ? `${audit.moon.nakshatra} (lord ${audit.moon.nakshatra_lord})` : '—'],
                ['Dignity', `${audit.moon?.dignity} (${audit.moon?.strength})`],
                ['Relation to matter', audit.moon?.relation_to_matter],
                ['Outcome weight', audit.moon?.outcome],
              ]}
            />
          </section>

          <section>
            <h4 className="prashna-audit-heading">All planets (ephemeris)</h4>
            <AuditTable
              headers={['Planet', 'Sign', 'Degree', 'House', 'Nakshatra', '℞', 'Role', 'Used in']}
              rows={planetRows}
            />
          </section>

          <section>
            <h4 className="prashna-audit-heading">Testimonies → verdict</h4>
            <AuditTable
              headers={['Tone', 'Category', 'Testimony']}
              rows={testimonyRows}
            />
            <div className="prashna-audit-verdict-box">
              <div><strong>Verdict:</strong> {audit.verdict_logic?.label}</div>
              <div><strong>Counts:</strong> 🟢 {audit.verdict_logic?.positive_count} · 🔴 {audit.verdict_logic?.negative_count} · ⚪ {audit.verdict_logic?.neutral_count}</div>
              <div><strong>Rule applied:</strong> {audit.verdict_logic?.rule_applied}</div>
            </div>
          </section>
        </div>
      )}
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
            <div className="prashna-verdict-header">
              <div className="prashna-verdict-label">Verdict</div>
              <span className="prashna-engine-badge prashna-engine-badge--rule">Rule engine</span>
            </div>
            <div className="prashna-verdict-title" style={{ color: vs.color }}>{result.verdict?.label}</div>
            <p className="prashna-verdict-text">{result.verdict?.explanation}</p>
            <div className="prashna-verdict-counts">
              🟢 {result.verdict?.positive_count} supportive · 🔴 {result.verdict?.negative_count} challenging · ⚪ {result.verdict?.neutral_count} neutral
            </div>
            <p className="prashna-verdict-note">
              Based on {result.testimonies?.counts?.total ?? 0} computed testimonies — not a guarantee.
            </p>
          </div>

          <PrashnaAuditCard audit={result.calculation_audit} />

          {result.ai_reading && (
            <AnalysisCard title="🤖 AI Prashna reading" badge="AI narration" badgeVariant="ai">
              <p className="prashna-result-card-para">{result.ai_reading}</p>
              <p className="prashna-result-card-note">
                AI narration based only on computed testimonies — not a guarantee.
              </p>
            </AnalysisCard>
          )}

          <AnalysisCard title="Rule-based summary" badge="Rule engine" badgeVariant="rule">
            <p className="prashna-result-card-para">{result.interpretation?.summary}</p>
          </AnalysisCard>

          <TestimonyList items={result.testimonies?.positive} tone="positive" />
          <TestimonyList items={result.testimonies?.negative} tone="negative" />
          <TestimonyList items={result.testimonies?.neutral} tone="neutral" />

          <AnalysisCard title="Moon analysis" badge="Rule engine" badgeVariant="rule">
            <strong>{result.analysis?.moon?.moon_sign}</strong> in house {result.analysis?.moon?.moon_house}
            {result.analysis?.moon?.moon_nakshatra && (
              <> · {result.analysis.moon.moon_nakshatra} (lord {result.analysis.moon.moon_nakshatra_lord})</>
            )}
            {' '}· {result.analysis?.moon?.strength_label}<br />
            {result.analysis?.moon?.explanation}
          </AnalysisCard>

          <AnalysisCard title={`Relevant house — ${result.analysis?.relevant_house?.category_label}`} badge="Rule engine" badgeVariant="rule">
            House {result.analysis?.relevant_house?.house_num} ({result.analysis?.relevant_house?.house_sign}) ·
            Lord {result.analysis?.relevant_house?.house_lord} · {result.analysis?.relevant_house?.lord_strength_label}<br />
            {result.analysis?.relevant_house?.explanation}
          </AnalysisCard>

          <AnalysisCard title="Timing indication" badge="Rule engine" badgeVariant="rule">
            <strong>{result.analysis?.timing?.timing_band}</strong><br />
            {result.analysis?.timing?.explanation}
          </AnalysisCard>

          <AnalysisCard title="Practical guidance" badge="Rule engine" badgeVariant="rule">
            {result.interpretation?.practical_guidance}
          </AnalysisCard>

          {result.chart && (
            <div className="prashna-result-card">
              <div className="prashna-result-card-title">Prashna chart</div>
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

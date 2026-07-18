/**
 * LifeCycleSimulatorPanel — Phase 2 Parasara timeline:
 * event themes, D9 overlay, rule + optional AI narration, mobile-first layout.
 */
import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import api from '../api/client'
import { chartFingerprint, chartPayload } from '../lib/chartPayload'
import SouthIndianChart from './SouthIndianChart'

const SIM_TIMEOUT_MS = 90_000

const RAG_CLASS = {
  strong: 'lcs-rag--strong',
  moderate: 'lcs-rag--moderate',
  weak: 'lcs-rag--weak',
}

const VERDICT_CLASS = {
  highly_active: 'lcs-verdict--high',
  active: 'lcs-verdict--active',
  moderate: 'lcs-verdict--mod',
  quiet: 'lcs-verdict--quiet',
}

const VERDICT_LABEL = {
  highly_active: 'Highly active',
  active: 'Active',
  moderate: 'Moderate',
  quiet: 'Quiet',
}

const THEME_ICONS = {
  marriage: '💍',
  career: '💼',
  health: '🏥',
  property: '🏠',
  foreign: '✈️',
  education: '📚',
}

const PLANET_COLOURS = {
  Sun: '#E47911', Moon: '#5B8DD9', Mars: '#D13212', Mercury: '#27ae60',
  Jupiter: '#8B6914', Venus: '#C471D4', Saturn: '#667788', Rahu: '#555555',
}

function formatRange(start, end) {
  if (!start || !end) return '—'
  const s = new Date(start + 'T12:00:00')
  const e = new Date(end + 'T12:00:00')
  const opts = { month: 'short', year: 'numeric' }
  return `${s.toLocaleDateString('en-IN', opts)} – ${e.toLocaleDateString('en-IN', opts)}`
}

function DasaTimelineBar({ segments, selected, onSelect }) {
  if (!segments?.length) return null
  const startMs = new Date(segments[0].start + 'T12:00:00').getTime()
  const endMs = new Date(segments[segments.length - 1].end + 'T12:00:00').getTime()
  const total = endMs - startMs || 1

  return (
    <div className="lcs-timeline" role="list" aria-label="Vimshottari timeline">
      {segments.map(seg => {
        const s = new Date(seg.start + 'T12:00:00').getTime()
        const e = new Date(seg.end + 'T12:00:00').getTime()
        const left = ((s - startMs) / total) * 100
        const width = Math.max(((e - s) / total) * 100, 1.5)
        const key = `${seg.mahadasha}-${seg.antardasha}-${seg.start}`
        const isSel = selected?.start === seg.start && selected?.antardasha === seg.antardasha
        const col = PLANET_COLOURS[seg.antardasha] || '#888'
        return (
          <button
            key={key}
            type="button"
            role="listitem"
            className={`lcs-timeline__seg${isSel ? ' lcs-timeline__seg--sel' : ''}${seg.is_current ? ' lcs-timeline__seg--current' : ''}`}
            style={{ left: `${left}%`, width: `${width}%`, background: col }}
            title={`${seg.mahadasha} MD / ${seg.antardasha} AD`}
            onClick={() => onSelect(seg)}
          >
            <span className="lcs-timeline__seg-label">{seg.antardasha}</span>
          </button>
        )
      })}
    </div>
  )
}

function DasaSegmentList({ segments, selected, onSelect }) {
  if (!segments?.length) return null
  return (
    <ul className="lcs-seg-list">
      {segments.map(seg => {
        const key = `${seg.mahadasha}-${seg.antardasha}-${seg.start}`
        const isSel = selected?.start === seg.start && selected?.antardasha === seg.antardasha
        return (
          <li key={key}>
            <button
              type="button"
              className={`lcs-seg-list__btn${isSel ? ' lcs-seg-list__btn--sel' : ''}${seg.is_current ? ' lcs-seg-list__btn--current' : ''}`}
              onClick={() => onSelect(seg)}
            >
              <span className="lcs-seg-list__dasa">{seg.mahadasha}–{seg.antardasha}</span>
              <span className="lcs-seg-list__range">{formatRange(seg.start, seg.end)}</span>
              {seg.is_current && <span className="lcs-seg-list__now">Now</span>}
            </button>
          </li>
        )
      })}
    </ul>
  )
}

function ThemeChipStrip({ themes, selectedKey, onSelect }) {
  if (!themes?.length) return null
  return (
    <div className="lcs-theme-scroll" role="tablist" aria-label="Life event themes">
      {themes.map(t => (
        <button
          key={t.key}
          type="button"
          role="tab"
          aria-selected={selectedKey === t.key}
          className={`lcs-theme-chip${selectedKey === t.key ? ' lcs-theme-chip--sel' : ''}`}
          onClick={() => onSelect(t.key)}
        >
          <span className="lcs-theme-chip__icon">{THEME_ICONS[t.key] || '◆'}</span>
          <span className="lcs-theme-chip__label">{t.label.split(' ')[0]}</span>
          <span className={`lcs-verdict lcs-verdict--sm ${VERDICT_CLASS[t.verdict] || ''}`}>
            {VERDICT_LABEL[t.verdict] || t.verdict}
          </span>
          {t.has_caution && <span className="lcs-verdict lcs-verdict--sm lcs-verdict--caution">Caution</span>}
        </button>
      ))}
    </div>
  )
}

function ThemeDetailCard({ theme }) {
  if (!theme) return null
  const d9 = theme.d9_overlay || {}
  const sav = theme.sav || {}
  return (
    <article className="lcs-theme-detail">
      <header className="lcs-theme-detail__head">
        <h3 className="lcs-theme-detail__title">
          {THEME_ICONS[theme.key]} {theme.label}
        </h3>
        <span className={`lcs-verdict ${VERDICT_CLASS[theme.verdict] || ''}`}>
          {VERDICT_LABEL[theme.verdict]}
        </span>
        {theme.has_caution && (
          <span className="lcs-verdict lcs-verdict--caution">Caution</span>
        )}
      </header>
      <div className="lcs-theme-detail__scores">
        <span>Natal {theme.natal_promise_score}</span>
        <span>Act {Math.round(theme.activation_score)}</span>
        <span>D9 {theme.d9_support}</span>
        {sav.average != null && (
          <span className={`lcs-sav lcs-sav--${(sav.label || '').toLowerCase()}`}>
            SAV {sav.average} · {sav.label}
          </span>
        )}
      </div>
      {sav.by_house?.length > 0 && (
        <div className="lcs-sav-row">
          {sav.by_house.map(h => (
            <span key={h.house} className="lcs-sav-chip">
              H{h.house} {h.points}
            </span>
          ))}
        </div>
      )}
      {theme.peak_window && (
        <p className="lcs-theme-detail__peak">
          <strong>Peak:</strong> {theme.peak_window.summary}
          {theme.peak_window.theme_houses?.length > 0 && (
            <> · H{theme.peak_window.theme_houses.join(', H')}</>
          )}
          {' · '}{formatRange(theme.peak_window.start, theme.peak_window.end)}
        </p>
      )}
      {theme.pratyantar_windows?.length > 0 && (
        <div className="lcs-pd-block">
          <p className="lcs-pd-block__title">Pratyantar (finer timing)</p>
          <ul className="lcs-pd-list">
            {theme.pratyantar_windows.slice(0, 4).map((pd, i) => (
              <li key={i} className={pd.is_current ? 'lcs-pd-list__item--now' : ''}>
                <strong>{pd.pratyantar}</strong> PD
                {' · '}{formatRange(pd.start, pd.end)}
                {pd.theme_houses?.length > 0 && <> · H{pd.theme_houses.join(', H')}</>}
              </li>
            ))}
          </ul>
        </div>
      )}
      {theme.yogas?.length > 0 && (
        <p className="lcs-theme-detail__yoga">Yoga: {theme.yogas.join(', ')}</p>
      )}
      {d9.house_lords?.length > 0 && (
        <ul className="lcs-d9-list">
          {d9.house_lords.map(hl => (
            <li key={hl.house}>
              H{hl.house} lord {hl.lord}: D1 H{hl.d1_house} → D9 {hl.d9_sign}
              {hl.vargottama ? ' · Vg' : ''}
            </li>
          ))}
        </ul>
      )}
      {theme.caution_windows?.length > 0 && (
        <div className="lcs-theme-detail__caution">
          {theme.caution_windows.slice(0, 2).map((c, i) => (
            <p key={i}>⚠ {c.summary}</p>
          ))}
        </div>
      )}
    </article>
  )
}

function TransitCards({ hits }) {
  if (!hits?.length) return <p className="td-card__hint">No transit hits in this period.</p>
  return (
    <ul className="lcs-transit-cards">
      {hits.slice(0, 20).map((h, i) => (
        <li key={i} className={`lcs-transit-card${h.currently_active ? ' lcs-transit-card--active' : ''}`}>
          <div className="lcs-transit-card__head">
            <strong>{h.planet}</strong>
            {h.currently_active && <span className="lcs-transit-card__badge">Active</span>}
          </div>
          <p className="lcs-transit-card__target">{h.target}</p>
          <p className="lcs-transit-card__meta">{formatRange(h.start, h.end)} · {h.duration_days}d</p>
        </li>
      ))}
    </ul>
  )
}

export default function LifeCycleSimulatorPanel({ chart, userId, enabled = true }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedSeg, setSelectedSeg] = useState(null)
  const [highlightHouses, setHighlightHouses] = useState([])
  const [selectedThemeKey, setSelectedThemeKey] = useState(null)
  const [chartView, setChartView] = useState('d1')
  const [impactOpen, setImpactOpen] = useState(false)
  const abortRef = useRef(null)
  const fingerprint = useMemo(() => chartFingerprint(chart), [chart])

  const fetchSim = useCallback(async (includeAi = false) => {
    if (!chart || !enabled) return
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller
    const timer = setTimeout(() => controller.abort(), SIM_TIMEOUT_MS)

    if (includeAi) setAiLoading(true)
    else setLoading(true)
    setError(null)
    try {
      const res = await api.post(
        '/prediction/simulate',
        chartPayload(chart, userId, { horizon_years: 10, include_ai: includeAi }),
        { signal: controller.signal, timeout: SIM_TIMEOUT_MS },
      )
      if (controller.signal.aborted) return
      setData(prev => {
        const next = includeAi && prev
          ? { ...prev, ai_reading: res.data.ai_reading, meta: { ...prev.meta, ...res.data.meta } }
          : res.data
        return next
      })
      if (includeAi && !res.data?.ai_reading) {
        setError(res.data?.meta?.ai_error || 'AI narration unavailable — showing rule-based reading.')
      }
      if (!includeAi) {
        const current = res.data?.current_period || res.data?.dasha_timeline?.[0]
        setSelectedSeg(current || null)
        setHighlightHouses(current?.focus_houses || [])
        const topTheme = res.data?.event_themes?.[0]
        setSelectedThemeKey(topTheme?.key || null)
      }
    } catch (e) {
      if (e.code === 'ERR_CANCELED' || e.name === 'CanceledError' || e.name === 'AbortError') {
        return
      }
      const timedOut = e.code === 'ECONNABORTED' || /timeout/i.test(e.message || '')
      const detail = e.response?.data?.detail
      const msg = timedOut
        ? 'Life cycle calculation timed out. Please try again.'
        : (typeof detail === 'string' ? detail : (detail?.msg || e.message || 'Simulation failed'))
      console.error('[LifeCycle]', msg, e)
      setError(msg)
      if (!includeAi) setData(null)
    } finally {
      clearTimeout(timer)
      if (abortRef.current === controller) abortRef.current = null
      setLoading(false)
      setAiLoading(false)
    }
  }, [chart, userId, enabled])

  useEffect(() => {
    if (!enabled || !chart) return undefined
    fetchSim(false)
    return () => {
      if (abortRef.current) abortRef.current.abort()
    }
    // fingerprint (not chart object identity) avoids refetch storms on parent re-renders
  }, [enabled, fingerprint, userId]) // eslint-disable-line react-hooks/exhaustive-deps

  const selectedTheme = useMemo(
    () => data?.event_themes?.find(t => t.key === selectedThemeKey) || data?.event_themes?.[0],
    [data, selectedThemeKey],
  )

  const themeHighlightHouses = useMemo(() => {
    if (selectedTheme?.houses?.length) return selectedTheme.houses
    return highlightHouses
  }, [selectedTheme, highlightHouses])

  const filteredHits = useMemo(() => {
    if (!data?.transit_hits) return []
    let hits = data.transit_hits
    if (selectedSeg) {
      hits = hits.filter(h => h.start <= selectedSeg.end && h.end >= selectedSeg.start)
    }
    if (selectedTheme?.houses?.length) {
      const th = new Set(selectedTheme.houses)
      const filtered = hits.filter(h =>
        h.matched_houses?.some(mh => th.has(mh)) ||
        selectedTheme.karakas?.includes(h.planet),
      )
      if (filtered.length) hits = filtered
    }
    return hits
  }, [data, selectedSeg, selectedTheme])

  const selectSeg = useCallback(seg => {
    setSelectedSeg(seg)
    setHighlightHouses(seg.focus_houses || [])
  }, [])

  if (!enabled) return null

  return (
    <div className="lcs-panel">
      <header className="lcs-hero td-card">
        <h2 className="lcs-hero__title">Life Cycle Simulator</h2>
        <p className="lcs-hero__sub">
          Parasara: Bhava → SAV → D9 → MD/AD/PD → Gochara (10 years)
        </p>
        {data?.meta && (
          <p className="lcs-hero__meta">
            {data.meta.lagna} lagna · D9 {data.meta.navamsa_lagna} · Moon {data.meta.moon_sign}
            {' · '}{data.meta.start_date} → {data.meta.end_date}
          </p>
        )}
        <p className="lcs-hero__disc">{data?.meta?.disclaimer}</p>
      </header>

      {loading && !data && (
        <p className="lcs-loading" role="status">Calculating 10-year life cycle…</p>
      )}
      {loading && data && (
        <p className="lcs-loading" role="status">Refreshing life cycle…</p>
      )}
      {error && (
        <p className="lcs-error" role="alert">
          {error}{' '}
          <button type="button" className="lcs-ai-btn" onClick={() => fetchSim(false)}>
            Retry
          </button>
        </p>
      )}

      {data && (
        <>
          {/* Narration */}
          {data.narration && (
            <section className="td-card lcs-narration">
              <h3 className="td-card__title">Life-cycle reading</h3>
              <p className="lcs-narration__headline">{data.narration.headline}</p>
              {data.current_period && (
                <p className="lcs-narration__body">{data.narration.current_period}</p>
              )}
              {data.ai_reading ? (
                <p className="lcs-narration__ai">{data.ai_reading}</p>
              ) : (
                <ul className="lcs-narration__themes">
                  {data.narration.theme_summaries?.slice(0, 3).map(t => (
                    <li key={t.key}>{t.text}</li>
                  ))}
                </ul>
              )}
              {!data.ai_reading && (
                <button
                  type="button"
                  className="lcs-ai-btn"
                  disabled={aiLoading}
                  onClick={() => fetchSim(true)}
                >
                  {aiLoading ? 'Generating…' : 'Short AI reading'}
                </button>
              )}
              {data.narration.caution && (
                <p className="lcs-narration__caution">{data.narration.caution}</p>
              )}
            </section>
          )}

          {/* Event themes */}
          {data.event_themes?.length > 0 && (
            <section className="td-card lcs-themes-section">
              <h3 className="td-card__title">Event themes</h3>
              <p className="td-card__hint">Tap a theme for SAV, Pratyantar peaks, and chart filter.</p>
              <ThemeChipStrip
                themes={data.event_themes}
                selectedKey={selectedThemeKey || data.event_themes[0]?.key}
                onSelect={setSelectedThemeKey}
              />
              <ThemeDetailCard theme={selectedTheme} />
            </section>
          )}

          {/* Current period */}
          {data.current_period && (
            <section className="td-card lcs-current">
              <h3 className="td-card__title">Current period</h3>
              <p className="lcs-current__dasa">
                <strong>{data.current_period.mahadasha}</strong> MD ·{' '}
                <strong>{data.current_period.antardasha}</strong> AD
                {data.current_period.pratyantar && (
                  <> · <strong>{data.current_period.pratyantar}</strong> PD</>
                )}
              </p>
              <p className="td-card__hint">
                {formatRange(data.current_period.start, data.current_period.end)}
                {data.current_period.pratyantar_start && (
                  <> · PD {formatRange(data.current_period.pratyantar_start, data.current_period.pratyantar_end)}</>
                )}
              </p>
              {data.current_period.life_themes?.length > 0 && (
                <p className="lcs-tags">
                  {data.current_period.life_themes.map(t => (
                    <span key={t} className="lcs-tag">{t}</span>
                  ))}
                </p>
              )}
            </section>
          )}

          {/* Dasa timeline */}
          <section className="td-card">
            <h3 className="td-card__title">Vimshottari timeline</h3>
            <p className="td-card__hint">Select a segment to filter transits.</p>
            <div className="lcs-timeline-desktop">
              <DasaTimelineBar
                segments={data.dasha_timeline}
                selected={selectedSeg}
                onSelect={selectSeg}
              />
            </div>
            <DasaSegmentList
              segments={data.dasha_timeline}
              selected={selectedSeg}
              onSelect={selectSeg}
            />
            {selectedSeg && (
              <div className="lcs-seg-detail">
                <strong>{selectedSeg.mahadasha}–{selectedSeg.antardasha}</strong>
                {' · '}{formatRange(selectedSeg.start, selectedSeg.end)}
                {' · H'}{selectedSeg.focus_houses?.join(', H')}
              </div>
            )}
          </section>

          {/* D1 / D9 charts */}
          <section className="td-card">
            <div className="lcs-chart-tabs" role="tablist">
              {['d1', 'd9'].map(v => (
                <button
                  key={v}
                  type="button"
                  role="tab"
                  aria-selected={chartView === v}
                  className={`lcs-chart-tab${chartView === v ? ' lcs-chart-tab--sel' : ''}`}
                  onClick={() => setChartView(v)}
                >
                  {v === 'd1' ? 'D1 Rasi' : 'D9 Navamsa'}
                </button>
              ))}
            </div>
            {chartView === 'd1' ? (
              <SouthIndianChart
                title="D1 Rasi"
                subtitle={themeHighlightHouses.length
                  ? `Theme houses: H${themeHighlightHouses.join(', H')}`
                  : 'Select a theme or Dasa segment'}
                planetPositions={chart.planet_positions}
                lagnaSignIndex={chart.ascendant?.sign_index}
                highlightBhavaHouses={themeHighlightHouses}
              />
            ) : (
              <SouthIndianChart
                title="D9 Navamsa"
                subtitle={selectedTheme
                  ? `${selectedTheme.label} — lords in D9`
                  : `Navamsa lagna ${data.meta?.navamsa_lagna || ''}`}
                planetPositions={chart.navamsa_positions}
                lagnaSignIndex={chart.navamsa_ascendant?.sign_index}
                highlightBhavaHouses={themeHighlightHouses}
                navamsa
              />
            )}
          </section>

          {/* Top windows */}
          {data.top_windows?.length > 0 && (
            <section className="td-card">
              <h3 className="td-card__title">Strongest activation windows</h3>
              <ul className="lcs-windows">
                {data.top_windows.slice(0, 6).map((w, i) => (
                  <li key={i} className="lcs-windows__item">
                    <span className="lcs-windows__score">{Math.round(w.score)}</span>
                    <div>
                      <p className="lcs-windows__summary">{w.summary}</p>
                      {w.themes?.length > 0 && (
                        <p className="lcs-windows__themes">{w.themes.join(' · ')}</p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Transit hits — cards on mobile, table on desktop */}
          <section className="td-card">
            <h3 className="td-card__title">
              Transit hits
              {selectedSeg ? ` · ${selectedSeg.antardasha} AD` : ''}
              {selectedTheme ? ` · ${selectedTheme.label.split(' ')[0]}` : ''}
            </h3>
            <div className="lcs-transit-cards-wrap">
              <TransitCards hits={filteredHits} />
            </div>
            <div className="cr-table-wrap lcs-transit-table-wrap">
              <table className="cr-table lcs-table">
                <thead>
                  <tr>
                    <th>Planet</th>
                    <th>Target</th>
                    <th>Period</th>
                    <th>Days</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredHits.slice(0, 25).map((h, i) => (
                    <tr key={i} className={h.currently_active ? 'lcs-table__active' : ''}>
                      <td><strong>{h.planet}</strong></td>
                      <td className="lcs-table__target">{h.target}</td>
                      <td>{formatRange(h.start, h.end)}</td>
                      <td>{h.duration_days}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Impact areas — collapsible */}
          <section className="td-card">
            <button
              type="button"
              className="td-section__toggle lcs-impact-toggle"
              onClick={() => setImpactOpen(o => !o)}
            >
              <span>Impact areas (natal + drishti)</span>
              <span aria-hidden="true">{impactOpen ? '▾' : '▸'}</span>
            </button>
            {impactOpen && (
              <div className="lcs-impact-grid">
                {data.impact_areas?.map(a => (
                  <article key={a.house} className="lcs-impact">
                    <header className="lcs-impact__head">
                      <span className="lcs-impact__h">H{a.house}</span>
                      <span className={`lcs-rag ${RAG_CLASS[a.rag] || ''}`}>{a.strength}</span>
                    </header>
                    <p className="lcs-impact__theme">{a.theme}</p>
                    <p className="lcs-impact__lord">Lord: {a.lord} in H{a.lord_house}</p>
                    {a.planets_aspecting?.length > 0 && (
                      <p className="lcs-impact__asp">Drishti: {a.planets_aspecting.join(', ')}</p>
                    )}
                  </article>
                ))}
              </div>
            )}
          </section>

          <p className="lcs-footnote">
            {data.meta?.drishti_rules}
            {data.narration?.d9_note ? ` · ${data.narration.d9_note}` : ''}
          </p>
        </>
      )}
    </div>
  )
}

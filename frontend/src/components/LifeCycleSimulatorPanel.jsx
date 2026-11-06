/**
 * LifeCycleSimulatorPanel — the next ten years theme by theme, on the House Links rules:
 * dasha switches a house on, Jupiter + Saturn make it live, Saturn is also read from the Moon.
 */
import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import api from '../api/client'
import { chartFingerprint, chartPayload } from '../lib/chartPayload'

const SIM_TIMEOUT_MS = 90_000
const MARRIED_KEY = 'lc-married:'

const THEME_ICONS = {
  career: '💼',
  wealth: '💰',
  marriage: '💍',
  children: '👶',
  property: '🏠',
  health: '🏥',
  foreign: '✈️',
  education: '📚',
}

function Badge({ status }) {
  if (!status) return null
  return <span className={`hl-badge hl-badge--${status.key}`}>{status.en}</span>
}

function FruitLine({ fruit }) {
  return (
    <li>
      <span className={`hl-badge hl-badge--fruit-${fruit.tone}`}>{fruit.ordinal}</span>{' '}
      {fruit.lord}: {fruit.en}
      <span className="hl-line__ta">{fruit.ta}</span>
    </li>
  )
}

function readMarried(fp) {
  try {
    const v = localStorage.getItem(MARRIED_KEY + fp)
    return v === null ? null : v === '1'
  } catch {
    return null
  }
}

function NowCard({ now }) {
  if (!now) return null
  return (
    <section className="td-card lc-card" aria-label="Current period">
      <h3 className="td-card__title">Now</h3>
      <p className="lc-now__dasa">
        <strong>{now.mahadasha}</strong> mahadasha · <strong>{now.bhukti}</strong> bhukti
      </p>
      <p className="td-card__hint">{now.start} to {now.end}</p>
      <ul className="lc-list">
        <li>
          Houses on: {now.on.map(r => `${r.ordinal} (by ${r.by_en})`).join(', ') || 'none'}
        </li>
        {now.live.length > 0 && (
          <li>Live with transit: {now.live.map(r => `${r.ordinal} until ${r.until}`).join(', ')}</li>
        )}
        {now.relation && <li>{now.relation.en}</li>}
      </ul>
    </section>
  )
}

function SaturnCard({ saturn }) {
  if (!saturn?.length) return null
  return (
    <section className="td-card lc-card" aria-label="Saturn from the Moon">
      <h3 className="td-card__title">Saturn from your Moon</h3>
      <ul className="lc-saturn">
        {saturn.map(s => (
          <li key={s.start_iso} className={`lc-saturn__item${s.now ? ' lc-saturn__item--now' : ''}`}>
            <p className="lc-saturn__head">
              <strong>{s.en}</strong> · {s.start} to {s.end}
              {s.now && <span className="hl-badge hl-badge--waiting">Now</span>}
            </p>
            <p className="lc-saturn__text">
              {s.meaning_en}
              <span className="hl-line__ta">{s.ta}: {s.meaning_ta}</span>
            </p>
            {s.phases.length > 1 && (
              <ul className="lc-list lc-list--sub">
                {s.phases.map(p => (
                  <li key={p.start} className={p.now ? 'lc-now-row' : ''}>
                    {p.en}: {p.start} to {p.end}
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}

function WindowRow({ w }) {
  return (
    <li className={`lc-win${w.now ? ' lc-win--now' : ''}`}>
      <p className="lc-win__head">
        <strong>{w.bhukti} bhukti</strong> in {w.mahadasha} · {w.start} to {w.end}
        {w.now && <span className="hl-badge hl-badge--waiting">Now</span>}
      </p>
      <ul className="lc-win__houses">
        {w.houses.map(h => (
          <li key={h.house}>
            {h.ordinal} on by {h.by_en}.{' '}
            {h.live.length
              ? <>Jupiter and Saturn join: <strong>{h.live.map(r => `${r.start} to ${r.end}`).join('; ')}</strong>.</>
              : 'No double transit in this bhukti.'}
          </li>
        ))}
      </ul>
      {w.saturn.length > 0 && <p className="lc-win__note">Alongside: {w.saturn.join(', ')}.</p>}
      {w.relation?.tone === 'uneasy' && <p className="lc-win__note">{w.relation.en}</p>}
    </li>
  )
}

function ThemeCard({ theme, open, onToggle }) {
  const next = theme.next_live
  return (
    <details className="lc-theme" open={open} onToggle={e => onToggle(theme.key, e.currentTarget.open)}>
      <summary className="lc-theme__summary">
        <span className="lc-theme__icon" aria-hidden="true">{THEME_ICONS[theme.key] || '◆'}</span>
        <span className="lc-theme__label">
          {theme.label_en}
          <span className="lc-theme__houses"> · {theme.key_houses.map(h => `H${h}`).join(', ')}</span>
          <span className="hl-line__ta">{theme.label_ta}</span>
        </span>
        <span className="lc-theme__status">
          <Badge status={theme.status} />
          {theme.live_now && <span className="lc-theme__when">until {theme.live_now.end}</span>}
          {!theme.live_now && next && <span className="lc-theme__when">next {next.start}</span>}
        </span>
      </summary>
      <div className="lc-theme__body">
        {theme.notes.map(n => (
          <p key={n.en} className="lc-theme__note">
            {n.en}
            <span className="hl-line__ta">{n.ta}</span>
          </p>
        ))}
        <h4 className="lc-h">Natal promise</h4>
        <ul className="lc-list">
          {theme.fruit.map(f => <FruitLine key={f.house} fruit={f} />)}
        </ul>
        {theme.support.length > 0 && (
          <p className="lc-muted">Supporting houses: {theme.support.map(h => `H${h}`).join(', ')}.</p>
        )}
        <h4 className="lc-h">When it is on</h4>
        {theme.windows.length ? (
          <ul className="lc-wins">{theme.windows.map(w => <WindowRow key={w.start_iso} w={w} />)}</ul>
        ) : (
          <p className="lc-muted">No bhukti in these years switches this theme on.</p>
        )}
        {theme.more_windows > 0 && (
          <p className="lc-muted">{theme.more_windows} more later in the horizon; see the timeline below.</p>
        )}
        {theme.remedies.map(r => (
          <div key={r.lord} className="lc-remedy">
            <h4 className="lc-h">Remedy for {r.lord}</h4>
            <p className="lc-muted">{r.why_en}</p>
            <ul className="lc-list">
              <li>
                <strong>Mantra</strong> ({r.count} times): {r.mantra}
                <span className="hl-line__ta">{r.mantra_ta}</span>
              </li>
              <li><strong>Deity</strong>: {r.deity} · <strong>Day</strong>: {r.day}</li>
              <li><strong>Charity</strong>: {r.charity.join(', ')}</li>
              {r.when?.length > 0 && (
                <li>
                  <strong>Best in</strong>:{' '}
                  {r.when.map(p => (p.now ? `${p.label}, now to ${p.end}` : `${p.label}, ${p.start} to ${p.end}`)).join('; ')}
                </li>
              )}
            </ul>
            <p className="lc-muted">{r.note_en}</p>
          </div>
        ))}
      </div>
    </details>
  )
}

function Timeline({ rows, themes }) {
  const label = useMemo(() => Object.fromEntries(themes.map(t => [t.key, t.label_en.split(' ')[0]])), [themes])
  if (!rows?.length) return null
  return (
    <details className="td-card lc-card lc-timeline">
      <summary className="lc-timeline__summary">Bhukti timeline ({rows.length})</summary>
      <div className="hl-tbl-wrap">
        <table className="hl-tbl lc-tbl">
          <thead>
            <tr>
              <th scope="col">Period</th>
              <th scope="col">Houses on</th>
              <th scope="col">Themes</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={`${r.mahadasha}-${r.bhukti}-${r.start}`} className={r.now ? 'lc-tbl__now' : ''}>
                <th scope="row">
                  {r.mahadasha}–{r.bhukti}
                  <span className="lc-tbl__dates">{r.start} to {r.end}</span>
                </th>
                <td>
                  {r.on.map(h => (
                    <span key={h} className={r.live.includes(h) ? 'lc-tbl__live' : ''}>{h} </span>
                  ))}
                </td>
                <td>{r.themes.map(k => label[k]).filter(Boolean).join(', ') || '–'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="hl-tbl-note">Bold house numbers have a Jupiter and Saturn double transit inside the bhukti.</p>
      </div>
    </details>
  )
}

export default function LifeCycleSimulatorPanel({ chart, userId, enabled = true }) {
  const fingerprint = useMemo(() => chartFingerprint(chart), [chart])
  const [marriedPick, setMarriedPick] = useState({ fp: null, value: null })
  const married = marriedPick.fp === fingerprint ? marriedPick.value : readMarried(fingerprint)
  const [nonce, setNonce] = useState(0)
  const [result, setResult] = useState({ key: null, data: null, error: '' })
  const [openKey, setOpenKey] = useState(undefined)
  const chartRef = useRef(chart)

  const requestKey = `${fingerprint}|${userId || ''}|${married}|${nonce}`

  useEffect(() => { chartRef.current = chart }, [chart])

  useEffect(() => {
    if (!enabled || !chartRef.current) return undefined
    const controller = new AbortController()
    api.post(
      '/prediction/simulate',
      chartPayload(chartRef.current, userId, { horizon_years: 10, married }),
      { signal: controller.signal, timeout: SIM_TIMEOUT_MS },
    )
      .then(res => setResult({ key: requestKey, data: res.data, error: '' }))
      .catch(e => {
        if (e.code === 'ERR_CANCELED' || e.name === 'CanceledError' || e.name === 'AbortError') return
        const timedOut = e.code === 'ECONNABORTED' || /timeout/i.test(e.message || '')
        const detail = e.response?.data?.detail
        setResult({
          key: requestKey,
          data: null,
          error: timedOut
            ? 'Life cycle calculation timed out. Please try again.'
            : (typeof detail === 'string' ? detail : (detail?.msg || e.message || 'Life cycle failed')),
        })
      })
    return () => controller.abort()
  }, [enabled, requestKey, userId, married])

  const current = result.key === requestKey
  const data = result.data
  const error = current ? result.error : ''
  const loading = Boolean(chart && enabled && !current)
  const shownKey = openKey === undefined ? data?.themes?.[0]?.key : openKey

  const toggleMarried = () => {
    const next = !married
    setMarriedPick({ fp: fingerprint, value: next })
    try { localStorage.setItem(MARRIED_KEY + fingerprint, next ? '1' : '0') } catch { /* private mode */ }
  }

  const onToggle = useCallback((key, isOpen) => {
    setOpenKey(prev => {
      if (isOpen) return key
      return prev === key || prev === undefined ? null : prev
    })
  }, [])

  if (!enabled) return null
  const meta = data?.meta
  const fetchLife = () => setNonce(n => n + 1)

  return (
    <div className="lc-panel">
      <header className="td-card lc-card lc-hero">
        <h2 className="lc-hero__title">Life Cycle</h2>
        <p className="lc-hero__sub">The next ten years, theme by theme, on the House Links rules.</p>
        {meta && (
          <p className="lc-hero__meta">
            {meta.lagna} lagna · Moon {meta.moon_sign}{meta.age != null ? ` · age ${meta.age}` : ''} · {meta.start} to {meta.end}
          </p>
        )}
        <label className="lc-married">
          <input type="checkbox" checked={!!married} onChange={toggleMarried} />
          <span>Already married</span>
        </label>
      </header>

      {loading && !data && <p className="lc-status" role="status">Working out the next ten years…</p>}
      {loading && data && <p className="lc-status" role="status">Refreshing…</p>}
      {error && (
        <p className="lc-error" role="alert">
          {error}{' '}
          <button type="button" className="lc-retry" onClick={fetchLife}>Retry</button>
        </p>
      )}

      {data && (
        <>
          <NowCard now={data.now} />
          <section className="td-card lc-card" aria-label="Life themes">
            <h3 className="td-card__title">Themes</h3>
            <p className="td-card__hint">
              On now first, then by the next window. A theme is on when the dasha reaches its key house;
              it is live when Jupiter and Saturn also touch that house or its lord.
            </p>
            <div className="lc-themes">
              {data.themes.map(t => (
                <ThemeCard key={t.key} theme={t} open={shownKey === t.key} onToggle={onToggle} />
              ))}
            </div>
          </section>
          <SaturnCard saturn={data.saturn} />
          <Timeline rows={data.timeline} themes={data.themes} />
          <p className="lc-footnote">
            {meta?.method_en} {meta?.disclaimer_en}
            <span className="hl-line__ta">{meta?.disclaimer_ta}</span>
          </p>
        </>
      )}
    </div>
  )
}

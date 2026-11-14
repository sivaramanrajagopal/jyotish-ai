/**
 * RipusPanel — D1 + D6 Shashthamsa, obstacle themes, Dasa on 6/8.
 */
import { useState } from 'react'
import { useApiResult, objectKey, errorText } from '../hooks/useApiResult'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'
import SouthIndianChart from './SouthIndianChart'

const TONE_CLASS = {
  present: 'rp-tone--present',
  mixed: 'rp-tone--mixed',
  quiet: 'rp-tone--quiet',
}

function ToneBadge({ tone }) {
  return (
    <span className={`rp-tone ${TONE_CLASS[tone] || TONE_CLASS.quiet}`}>
      {tone || 'quiet'}
    </span>
  )
}

function ThemeCards({ cards }) {
  if (!cards?.length) return null
  return (
    <div className="rp-themes">
      {cards.map((card) => (
        <article key={card.id} className="td-card rp-theme">
          <div className="rp-theme__top">
            <h4 className="td-card__title">{card.title}</h4>
            <ToneBadge tone={card.tone} />
          </div>
          {card.primer && <p className="td-card__hint">{card.primer}</p>}
          <p className="rp-theme__line">{card.d1}</p>
          <p className="rp-theme__line">{card.d6}</p>
          <p className="rp-theme__dasa">{card.dasa}</p>
          {card.now && <p className="rp-theme__now">{card.now}</p>}
          {card.eases && <p className="rp-theme__eases">{card.eases}</p>}
        </article>
      ))}
    </div>
  )
}

function ReadBadge({ row }) {
  const tone = row?.read || 'watch'
  return (
    <span className={`rp-read rp-read--${tone}`}>
      {row?.read_en || 'Watch'}
    </span>
  )
}

function WindowList({ rows, showWhy = false }) {
  if (!rows?.length) return null
  return (
    <ul className="rp-windows">
      {rows.map((row, i) => (
        <li key={`${row.start}-${i}`} className="rp-window">
          <div className="rp-window__head">
            <strong className="rp-window__label">{row.label}</strong>
            <ReadBadge row={row} />
          </div>
          <p className="rp-window__meta">
            {row.start} → {row.end}
            {row.links?.length ? ` · ${row.links.join(', ')}` : ''}
          </p>
          {showWhy && row.why_en && <p className="rp-read__why">{row.why_en}</p>}
        </li>
      ))}
    </ul>
  )
}

function TimingTable({ title, rows, emptyText }) {
  const isNow = title === 'Active now'
  if (!rows?.length) {
    return (
      <article className="td-card">
        <h4 className="td-card__title">{title}</h4>
        <p className="td-card__hint">{emptyText}</p>
      </article>
    )
  }
  return (
    <article className="td-card">
      <h4 className="td-card__title">{title}</h4>
      <div className="cr-table-wrap rp-timing-desktop">
        <table className="cr-table">
          <thead>
            <tr>
              <th>Period</th>
              <th>Read</th>
              <th>Start</th>
              <th>End</th>
              <th>Links</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={`${row.start}-${i}`}>
                <td>{row.label}</td>
                <td><ReadBadge row={row} /></td>
                <td>{row.start}</td>
                <td>{row.end}</td>
                <td>{(row.links || []).join(', ') || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <WindowList rows={rows} showWhy={isNow} />
      {isNow && rows[0]?.why_en && (
        <p className="rp-read__why rp-read__why--desktop">{rows[0].why_en}</p>
      )}
      {isNow && rows[0]?.remedy_en && (
        <p className="rp-read__remedy">{rows[0].remedy_en}</p>
      )}
      {isNow && rows[0]?.sky_read_en && (
        <p className="rp-read__sky">
          This month (Gochara):{' '}
          <span className={`rp-read rp-read--${rows[0].sky || 'watch'}`}>
            {rows[0].sky_read_en}
          </span>
          {rows[0].sky_en ? ` — ${rows[0].sky_en}` : ''}
        </p>
      )}
    </article>
  )
}

function GocharaCard({ sky }) {
  if (!sky) return null
  return (
    <article className="td-card rp-gochara">
      <div className="rp-theme__top">
        <h4 className="td-card__title">Gochara this month (houses 1, 6, 8)</h4>
        <span className={`rp-read rp-read--${sky.read || 'watch'}`}>
          {sky.read_en || 'Watch'}
        </span>
      </div>
      <p className="td-card__hint">
        Counted from YOUR lagna — same sky, different houses for each native.
        {sky.as_of ? ` As of ${sky.as_of}.` : ''}
      </p>
      <p className="rp-gochara__now">{sky.line_en || sky.now_en}</p>
      {(sky.line_ta || sky.now_ta) && (
        <p className="hl-bi__ta rp-gochara__ta">{sky.line_ta || sky.now_ta}</p>
      )}
      <ul className="rp-gochara__houses">
        {(sky.houses || []).map((h) => (
          <li key={h.house}>
            <strong>H{h.house} {h.sign}</strong> — {h.theme_en}
            {': '}
            {(h.occupants || []).join(', ') || 'empty'}
            {h.aspects?.length ? `; aspected by ${h.aspects.join(', ')}` : ''}
          </li>
        ))}
      </ul>
      {sky.remedy_en && <p className="rp-read__remedy">{sky.remedy_en}</p>}
    </article>
  )
}

function FullTiming({ periods }) {
  const [open, setOpen] = useState(false)
  if (!periods?.length) return null
  return (
    <section className="td-section td-section--tier3">
      <button type="button" className="td-section__toggle" onClick={() => setOpen((o) => !o)}>
        <span>Full Ripu Dasa timeline ({periods.length} windows)</span>
        <span aria-hidden="true">{open ? '▾' : '▸'}</span>
      </button>
      {open && (
        <>
          <div className="cr-table-wrap rp-timing-desktop">
            <table className="cr-table">
              <thead>
                <tr>
                  <th>Maha</th>
                  <th>Bhukti</th>
                  <th>Read</th>
                  <th>Start</th>
                  <th>End</th>
                  <th>Links</th>
                </tr>
              </thead>
              <tbody>
                {periods.map((p, i) => (
                  <tr key={`${p.start}-${i}`}>
                    <td>{p.maha_dasa}</td>
                    <td>{p.bukti}</td>
                    <td><ReadBadge row={p} /></td>
                    <td>{p.start}</td>
                    <td>{p.end}</td>
                    <td>{(p.links || []).join(', ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <WindowList rows={periods} />
        </>
      )}
    </section>
  )
}

export default function RipusPanel({ chart, userId, enabled = true }) {
  const req = useApiResult(
    chart && enabled ? `${objectKey(chart)}|${userId}|d6` : null,
    () => api.post('/d6/analyze', chartPayload(chart, userId)).then((r) => r.data),
  )
  const { data, loading } = req
  const error = req.error ? errorText(req.error, 'Could not load D6 Ripu analysis.') : ''

  if (!enabled) {
    return <div className="td-loading" style={{ opacity: 0.6 }}>Open Ripu tab after calculating your chart…</div>
  }
  if (loading && !data) return <div className="td-loading">Computing D1 + D6 Ripu chart…</div>
  if (error) return <div className="td-error" role="alert">{error}</div>
  if (!data) return null

  const s = data.summary || {}
  const d6Asc = data.shashthamsa_ascendant || {}
  const d6Pos = data.shashthamsa_positions || {}

  return (
    <div className="td-panel cr-panel rp-panel">
      <p className="hl-disclaimer" role="note">{data.disclaimer}</p>

      <div className="cr-hero">
        <div className="cr-hero__top">
          <span className="cr-hero__label">Ripu (D6)</span>
          <span className="cr-hero__rules">
            Dasa {s.maha_dasa}–{s.bhukti}
          </span>
        </div>
        {data.hero?.headline && <p className="cr-hero__headline">{data.hero.headline}</p>}
        <p className="cr-hero__meta">
          D6 Lagna <strong>{s.d6_lagna}</strong> ({s.d6_lagna_lord}) · D1 6th lord{' '}
          <strong>{s.d1_sixth_lord}</strong> · D6 6th lord <strong>{s.d6_sixth_lord}</strong>
        </p>
        <p className="cr-hero__meta">
          {s.dasa_period}
        </p>
      </div>

      {data.meaning?.en && (
        <article className="td-card rp-meaning">
          <h3 className="td-card__title">What this means for you</h3>
          <p className="rp-meaning__en">{data.meaning.en}</p>
          {data.meaning.ta && <p className="hl-bi__ta rp-meaning__ta">{data.meaning.ta}</p>}
        </article>
      )}

      <p className="td-card__hint rp-primer">
        D6 is Shashthamsa (Narasimha Rao / Jagannatha Hora): five-degree slices,
        odd signs counted from Aries, even from Libra. This is not D60, and not one of
        Parashara’s sixteen vargas. Competitive exams here mean defeating rivals, not the subject.
        Illness here is the fight, not the body map — that stays on Health. Profession type stays on Career.
      </p>

      <h3 className="cr-layer-title">D1 &amp; D6 charts</h3>
      <div className="cr-charts-grid">
        <div className="cr-chart-card">
          <h4 className="cr-chart-card__title">D1 — Rasi (houses 6 and 8)</h4>
          <SouthIndianChart
            title="D1"
            subtitle={`${chart.birth_data?.dob || ''} · 6th lord ${s.d1_sixth_lord}`}
            planetPositions={chart.planet_positions}
            lagnaSignIndex={chart.ascendant?.sign_index}
            variant="classic"
            showDetails
            chartKind="natal"
            highlightBhavaHouses={data.highlight_d1}
          />
        </div>
        <div className="cr-chart-card">
          <h4 className="cr-chart-card__title">D6 — Shashthamsa</h4>
          <SouthIndianChart
            title="D6"
            subtitle={`Lagna: ${d6Asc.sign || '—'} · lord ${d6Asc.sign_lord || '—'}`}
            planetPositions={d6Pos}
            lagnaSignIndex={d6Asc.sign_index}
            shashthamsa
            variant="classic"
            showDetails
            chartKind="natal"
            highlightBhavaHouses={data.highlight_d6}
          />
        </div>
      </div>

      <h3 className="cr-layer-title">6th-house karakas</h3>
      {data.outlook && (
        <article className="td-card rp-outlook">
          <h4 className="td-card__title">Now and when it eases</h4>
          <p className="rp-outlook__now">{data.outlook.now_en}</p>
          <p className="rp-outlook__eases">{data.outlook.eases_en}</p>
          {data.outlook.recover_en && (
            <p className="rp-outlook__recover">{data.outlook.recover_en}</p>
          )}
          {data.outlook.now_ta && <p className="hl-bi__ta rp-outlook__ta">{data.outlook.now_ta}</p>}
          {data.outlook.eases_ta && <p className="hl-bi__ta rp-outlook__ta">{data.outlook.eases_ta}</p>}
        </article>
      )}
      <GocharaCard sky={data.gochara} />
      <ThemeCards cards={data.themes} />

      <h3 className="cr-layer-title">Ripu timing (Dasa / Bhukti)</h3>
      {data.timing?.guide && (
        <article className="td-card rp-guide">
          <h4 className="td-card__title">How to read these windows</h4>
          <p className="rp-guide__intro">{data.timing.guide.intro_en}</p>
          {data.timing.guide.intro_ta && (
            <p className="hl-bi__ta rp-guide__intro">{data.timing.guide.intro_ta}</p>
          )}
          <ul className="rp-guide__tones">
            {(data.timing.guide.tones || []).map((tone) => (
              <li key={tone.id}>
                <span className={`rp-read rp-read--${tone.id}`}>{tone.label_en}</span>
                {' '}{tone.en}
              </li>
            ))}
          </ul>
          <ul className="rp-guide__links">
            {(data.timing.guide.links || []).map((link) => (
              <li key={link.id}>
                <strong>{link.id}</strong> — {link.en}
              </li>
            ))}
          </ul>
          {data.timing.guide.remedy_note_en && (
            <p className="rp-read__remedy">{data.timing.guide.remedy_note_en}</p>
          )}
        </article>
      )}
      <p className="td-card__hint cr-timing-note">
        Windows when Maha or Bhukti is D1 6th lord, D1 8th lord, D6 lagna lord, or D6 6th lord.
      </p>
      <div className="cr-grid">
        <TimingTable
          title="Active now"
          rows={data.timing?.current}
          emptyText="No 6th/8th Dasa link today."
        />
        <TimingTable
          title="Upcoming windows"
          rows={data.timing?.upcoming}
          emptyText="No upcoming Ripu windows in horizon."
        />
      </div>
      <FullTiming periods={data.timing?.all} />

      {data.consult?.paragraphs_en?.length > 0 && (
        <article className="td-card rp-consult">
          <h3 className="td-card__title">{data.consult.title_en || 'Say this to the client'}</h3>
          {data.consult.title_ta && (
            <p className="hl-bi__ta rp-consult__kicker">{data.consult.title_ta}</p>
          )}
          {data.consult.paragraphs_en.map((p, i) => (
            <p key={`en-${i}`} className="rp-consult__en">{p}</p>
          ))}
          {data.consult.paragraphs_ta?.length > 0 && (
            <div className="rp-consult__ta-wrap">
              {data.consult.paragraphs_ta.map((p, i) => (
                <p key={`ta-${i}`} className="hl-bi__ta rp-consult__ta">{p}</p>
              ))}
            </div>
          )}
        </article>
      )}
    </div>
  )
}

/**
 * DoshaRadarPanel — obstruction doshas, Pushkara Navamsa, live transit scan, 90-day forecast.
 */
import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'

const SEV_CLASS = {
  clear: 'dr-sev--clear',
  soonya: 'dr-sev--soonya',
  mild: 'dr-sev--mild',
  mild_divine: 'dr-sev--mild-divine',
  critical: 'dr-sev--critical',
  critical_divine: 'dr-sev--divine',
  chandrashtama: 'dr-sev--chandra',
  red_zone: 'dr-sev--red',
  mudakku: 'dr-sev--mudakku',
}

const SEV_LABEL = {
  clear: { en: 'Clear', ta: 'தெளிவு' },
  soonya: { en: 'Soonya transit', ta: 'சூன்ய கோசாரம்' },
  mild: { en: 'Mild obstruction', ta: 'மிதமான தடை' },
  mild_divine: { en: 'Mild — Pushkara relief', ta: 'மிதம் — புஷ்கர நிவர்த்தி' },
  critical: { en: 'Critical obstruction', ta: 'கடுமையான தடை' },
  critical_divine: { en: 'Critical — Divine Protection', ta: 'கடுமை — தெய்வ பாதுகாப்பு' },
  chandrashtama: { en: 'Chandrashtama', ta: 'சந்திராஷ்டமம்' },
  red_zone: { en: 'Red zone', ta: 'சிவப்பு மண்டலம்' },
  mudakku: { en: 'Mudakku', ta: 'முடக்கு' },
}

const FLAG_CLASS = {
  Soonya: 'dr-flag--soonya',
  Chandrashtama: 'dr-flag--chandra',
  Mudakku: 'dr-flag--mudakku',
  Pushkara: 'dr-flag--pushkara',
  Transformational: 'dr-flag--divine',
  Vadhai: 'dr-flag--red',
  Vainasikam: 'dr-flag--red',
}

function Bilingual({ en, ta, className = '', inline = false }) {
  if (inline) {
    return (
      <span className={className}>
        <span className="dr-bi__en">{en}</span>
        {ta && <span className="dr-bi__ta"> · {ta}</span>}
      </span>
    )
  }
  return (
    <span className={className}>
      <span className="dr-bi__en">{en}</span>
      {ta && <span className="dr-bi__ta">{ta}</span>}
    </span>
  )
}

function Section({ id, titleEn, titleTa, count, defaultOpen = true, children }) {
  return (
    <details className="dr-section" id={id} open={defaultOpen}>
      <summary className="dr-section__summary">
        <Bilingual en={titleEn} ta={titleTa} inline />
        {count != null && <span className="dr-section__count">({count})</span>}
      </summary>
      <div className="dr-section__body">{children}</div>
    </details>
  )
}

function DoshaPrimer() {
  return (
    <details className="dr-primer">
      <summary className="dr-primer__summary">
        <Bilingual
          en="What is Dosha Radar?"
          ta="தோஷ ரேடார் என்றால்?"
          inline
        />
      </summary>
      <p className="dr-primer__body">
        <Bilingual
          en="Soonya = void signs for your birth tithi. Chandrashtama = Moon in 8th from natal Moon. Mudakku = 22nd Drekkana blocked sign. Vadhai/Vainasikam = red-zone nakshatras from Janma Moon. Pushkara Navamsa can neutralise harsh afflictions (Divine Protection). This tab scans live transits and the next 90 days — not medical or financial advice."
          ta="சூன்யம் = பிறந்த திதிக்கான வெற்று ராசிகள். சந்திராஷ்டமம் = ஜன்ம சந்திரத்தின் 8ம் ராசி. முடக்கு = 22ம் திரேக்கான தடை. வதை/வைனாசிகம் = சிவப்பு மண்டல நட்சத்திரங்கள். புஷ்கரம் கடுமையான தோஷங்களை மென்மையாக்கலாம். இது நேரடி கோசாரம் + 90 நாள் முன்னறிவிப்பு — மருத்துவ/நிதி ஆலோசனை அல்ல."
          inline
        />
      </p>
    </details>
  )
}

function FlagChips({ flags }) {
  if (!flags?.length) return null
  return (
    <span className="dr-flags">
      {flags.map(f => (
        <span key={f} className={`dr-flag ${FLAG_CLASS[f] || 'dr-flag--default'}`}>{f}</span>
      ))}
    </span>
  )
}

function AlertCard({ alert }) {
  const cls = SEV_CLASS[alert.severity] || 'dr-sev--mild'
  const label = SEV_LABEL[alert.severity] || { en: alert.severity, ta: '' }
  return (
    <article className={`dr-alert ${cls}`}>
      <div className="dr-alert__top">
        <strong>{alert.planet}</strong>
        <span className="dr-alert__badge">{label.en}</span>
      </div>
      <p className="dr-alert__sign">{alert.sign}</p>
      <p className="dr-alert__note">
        <Bilingual en={alert.note_en} ta={alert.note_ta} inline />
      </p>
      {alert.has_divine_protection && (
        <p className="dr-alert__divine">✨ Divine Protection (Pushkara)</p>
      )}
    </article>
  )
}

function TransitHighlightCard({ row }) {
  return (
    <article className="dr-transit-card">
      <div className="dr-transit-card__top">
        <strong>{row.planet}</strong>
        <span className="dr-transit-card__meta">{row.sign} · H{row.house_num}</span>
      </div>
      {row.nak_name && <p className="dr-transit-card__nak">{row.nak_name}</p>}
      <FlagChips flags={row.flags} />
      {row.has_divine_protection && (
        <p className="dr-transit-card__divine">✨ Pushkara / Divine Protection</p>
      )}
    </article>
  )
}

function TransitHighlightGrid({ rows }) {
  if (!rows?.length) {
    return (
      <p className="dr-hint dr-clear-msg">
        <Bilingual
          en="No flagged transits right now — scan is clear for obstruction doshas."
          ta="இப்போது குறிக்கப்பட்ட கோசாரங்கள் இல்லை — தடை தோஷங்களுக்கு தெளிவு."
          inline
        />
      </p>
    )
  }
  return (
    <div className="dr-transit-grid">
      {rows.map(row => (
        <TransitHighlightCard key={row.planet} row={row} />
      ))}
    </div>
  )
}

function TransitTable({ planets }) {
  const rows = Object.entries(planets || {})
  if (!rows.length) return null
  return (
    <div className="dr-table-wrap dr-table-wrap--desktop">
      <table className="dr-table">
        <thead>
          <tr>
            <th>Planet</th>
            <th>Sign</th>
            <th>H</th>
            <th>Flags</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([name, d]) => {
            const flags = []
            if (d.in_soonya) flags.push('Soonya')
            if (d.in_chandrashtama) flags.push('Chandrashtama')
            if (d.in_mudakku) flags.push('Mudakku')
            if (d.red_zone) flags.push(d.red_zone)
            if (d.pushkara?.pushkara) flags.push('Pushkara')
            const crit = d.critical_obstruction?.severity
            if (crit && crit !== 'none') flags.push(crit)
            return (
              <tr key={name}>
                <td>{name}</td>
                <td>{d.sign}</td>
                <td>{d.house_num}</td>
                <td className="dr-table__flags">{flags.join(' · ') || '—'}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function NatalAfflictionList({ afflictions }) {
  const rows = Object.entries(afflictions || {}).filter(([, d]) => {
    const crit = d.critical_obstruction?.severity
    return d.in_soonya || d.combust?.combust || d.gandanta?.gandanta
      || d.pushkara?.pushkara || (crit && crit !== 'none')
  })
  if (!rows.length) {
    return (
      <p className="dr-hint">
        <Bilingual en="No natal combustion, gandanta, or Soonya placements flagged." ta="ஜாதகத்தில் குறிக்கப்பட்ட தோஷங்கள் இல்லை." inline />
      </p>
    )
  }
  return (
    <ul className="dr-natal-list">
      {rows.map(([name, d]) => {
        const tags = []
        if (d.in_soonya) tags.push('Soonya (natal)')
        if (d.combust?.combust) tags.push(d.combust.deep ? 'Deep combust' : 'Combust')
        if (d.gandanta?.gandanta) tags.push('Gandanta')
        if (d.pushkara?.pushkara) tags.push('Pushkara')
        const crit = d.critical_obstruction?.severity
        if (crit && crit !== 'none') tags.push(crit.replace('_', ' '))
        return (
          <li key={name} className="dr-natal-list__item">
            <strong>{name}</strong> in {d.sign} H{d.house}
            <FlagChips flags={tags} />
          </li>
        )
      })}
    </ul>
  )
}

function ForecastList({ forecast }) {
  if (!forecast) return null
  const ch = forecast.chandrashtama_windows || []
  const rz = forecast.red_zone_entries || []
  const crit = forecast.critical_windows || []
  if (!ch.length && !rz.length && !crit.length) {
    return (
      <p className="dr-hint">
        <Bilingual en="No major obstruction windows in the next 90 days." ta="அடுத்த 90 நாட்களில் பெரிய தடை சாளரங்கள் இல்லை." inline />
      </p>
    )
  }
  return (
    <ul className="dr-forecast-list">
      {ch.slice(0, 4).map((w, i) => (
        <li key={`ch-${i}`}>
          <strong>Chandrashtama</strong> {w.start_date} → {w.end_date} ({w.duration_days}d)
        </li>
      ))}
      {rz.slice(0, 6).map((e, i) => (
        <li key={`rz-${i}`}>
          <strong>{e.planet}</strong> → {e.has_pushkara ? 'Transformational' : e.type} ({e.nak_name}) on {e.entry_date}
        </li>
      ))}
      {crit.slice(0, 4).map((c, i) => (
        <li key={`cr-${i}`}>
          <strong>{c.planet}</strong> critical in {c.soonya_sign} ({c.affliction_type})
          {c.has_divine ? ' · Pushkara' : ''} on {c.date}
        </li>
      ))}
    </ul>
  )
}

function PushkaraTransitList({ items }) {
  if (!items?.length) return null
  const active = items.filter(p => p.currently_pushkara)
  const upcoming = items.filter(p => !p.currently_pushkara && p.next_entry_days != null).slice(0, 5)
  return (
    <div className="dr-pushkara-grid">
      {active.length > 0 && (
        <div>
          <h4 className="dr-subtitle">Currently in Pushkara</h4>
          <ul className="dr-forecast-list">
            {active.map(p => (
              <li key={p.planet}><strong>{p.planet}</strong> — {p.current_zone}</li>
            ))}
          </ul>
        </div>
      )}
      {upcoming.length > 0 && (
        <div>
          <h4 className="dr-subtitle">Next Pushkara entries</h4>
          <ul className="dr-forecast-list">
            {upcoming.map(p => (
              <li key={p.planet}>
                <strong>{p.planet}</strong> in {p.next_entry_days}d ({p.next_entry_date})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default function DoshaRadarPanel({ chart, userId, enabled = true }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    if (!chart || !enabled) return
    setLoading(true)
    setError('')
    api.post('/dosha-radar/analyze', chartPayload(chart, userId))
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Could not load Dosha Radar.'))
      .finally(() => setLoading(false))
  }, [chart, userId, enabled])

  useEffect(() => {
    if (enabled && chart) load()
  }, [enabled, chart, load])

  if (!chart) {
    return <div className="dr-loading" style={{ opacity: 0.6 }}>Open My Chart first…</div>
  }
  if (loading && !data) return <div className="dr-loading">Scanning doshas…</div>
  if (error) return <div className="dr-error" role="alert">{error}</div>
  if (!data) return null

  const s = data.summary || {}
  const sevCls = SEV_CLASS[s.overall_status] || SEV_CLASS.clear
  const sevLabel = SEV_LABEL[s.overall_status] || SEV_LABEL.clear
  const tamil = data.tamil_blueprint || {}
  const thithi = tamil.thithi_soonyam || {}
  const pushkaraNatal = data.pushkara_natal || []
  const highlights = data.transit_highlights || []
  const criticalAlerts = (data.active_alerts || []).filter(a => a.severity !== 'soonya')

  return (
    <div className="dr-panel" id="dosha-radar-panel">
      {data.disclaimer?.en && (
        <div className="dr-disclaimer" role="alert">
          <strong>⚠️ {data.disclaimer.en}</strong>
          <p>{data.disclaimer.ta}</p>
        </div>
      )}

      <DoshaPrimer />

      <header className="dr-hero">
        <div className="dr-hero__top">
          <h2 className="dr-hero__title">
            <Bilingual en="Dosha Radar" ta="தோஷ ரேடார்" inline />
          </h2>
          <span className={`dr-hero__badge ${sevCls}`}>{sevLabel.en}</span>
        </div>
        <p className="dr-hero__meta">
          as of {s.transit_date} · {s.active_alert_count} alert{s.active_alert_count === 1 ? '' : 's'}
          {s.transit_highlight_count != null && ` · ${s.transit_highlight_count} flagged transit${s.transit_highlight_count === 1 ? '' : 's'}`}
        </p>
        <div className="dr-hero__grid">
          <div><span className="dr-hero__label">Soonya</span><span>{(s.soonya_signs || []).join(', ') || '—'}</span></div>
          <div><span className="dr-hero__label">Chandrashtama</span><span>{s.chandrashtama_sign}</span></div>
          <div><span className="dr-hero__label">Mudakku</span><span>{s.mudakku_sign}</span></div>
          <div><span className="dr-hero__label">Pushkara (natal)</span><span>{s.natal_pushkara_count}</span></div>
        </div>
      </header>

      <Section
        id="dr-highlights"
        titleEn="Today's transit highlights"
        titleTa="இன்றைய கோசார சிறப்பம்சங்கள்"
        count={highlights.length}
        defaultOpen
      >
        <TransitHighlightGrid rows={highlights} />
      </Section>

      {criticalAlerts.length > 0 && (
        <Section
          id="dr-alerts"
          titleEn="Active obstruction alerts"
          titleTa="செயலில் உள்ள தடை எச்சரிக்கைகள்"
          count={criticalAlerts.length}
          defaultOpen
        >
          <div className="dr-alert-grid">
            {criticalAlerts.map((a, i) => (
              <AlertCard key={`${a.planet}-${a.severity}-${i}`} alert={a} />
            ))}
          </div>
        </Section>
      )}

      <Section
        id="dr-blueprint"
        titleEn="Natal blueprint"
        titleTa="ஜாதக அடிப்படை"
        defaultOpen={false}
      >
        <div className="dr-blueprint">
          <p><strong>Thithi Soonyam:</strong> {thithi.tithi_name} ({thithi.paksha}) — dagdha: {(thithi.dagdha_rasis || []).map(r => r.name).join(', ') || 'none'}</p>
          <p><strong>Vadhai:</strong> {s.vadhai_nakshatra} · <strong>Vainasikam:</strong> {s.vainasikam_nakshatra}</p>
          <p className="dr-hint">
            <Bilingual
              en="Full Thithi/Mudakku/Yogi detail on My Chart → Tamil Doshas."
              ta="முழு விவரம் என் வரைபடம் → தமிழ் தோஷங்கள்."
              inline
            />
          </p>
        </div>
      </Section>

      <Section
        id="dr-natal-afflictions"
        titleEn="Natal afflictions"
        titleTa="ஜாதக தோஷங்கள்"
        defaultOpen={false}
      >
        <NatalAfflictionList afflictions={data.natal_afflictions} />
      </Section>

      <Section
        id="dr-pushkara-natal"
        titleEn="Natal Pushkara Navamsa"
        titleTa="ஜாதக புஷ்கர நவாம்சம்"
        count={pushkaraNatal.length}
        defaultOpen={pushkaraNatal.length > 0}
      >
        {pushkaraNatal.length ? (
          <ul className="dr-forecast-list">
            {pushkaraNatal.map(p => (
              <li key={p.planet}><strong>{p.planet}</strong> — {p.zone}</li>
            ))}
          </ul>
        ) : (
          <p className="dr-hint"><Bilingual en="No natal planets in Pushkara zones." ta="ஜாதகத்தில் புஷ்கர மண்டலம் இல்லை." inline /></p>
        )}
      </Section>

      <Section
        id="dr-transit"
        titleEn="Full transit table"
        titleTa="முழு கோசார அட்டவணை"
        defaultOpen={false}
      >
        <TransitTable planets={data.transit_status?.planets} />
        <div className="dr-table-wrap--mobile">
          <TransitHighlightGrid rows={highlights} />
        </div>
      </Section>

      <Section
        id="dr-forecast"
        titleEn="90-day forecast"
        titleTa="90 நாள் முன்னறிவிப்பு"
        defaultOpen={false}
      >
        <ForecastList forecast={data.forecast} />
      </Section>

      <Section
        id="dr-pushkara-transit"
        titleEn="Pushkara transit windows"
        titleTa="புஷ்கர கோசார சாளரங்கள்"
        defaultOpen={false}
      >
        <PushkaraTransitList items={data.pushkara_transits} />
      </Section>

      <button type="button" className="dr-refresh" onClick={load} disabled={loading}>
        {loading ? 'Refreshing…' : 'Refresh scan'}
      </button>
    </div>
  )
}

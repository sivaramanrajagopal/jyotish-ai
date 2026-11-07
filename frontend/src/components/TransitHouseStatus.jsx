/**
 * TransitHouseStatus — House Links status for a chosen date, shared by
 * Gochar and Forecast. Live / Dasha on / Transit only / Quiet, with reasons.
 * Planet rows show the classical Gochara result from the natal Moon.
 */
import { houseTitle, ordinal } from '../lib/houseStatus'

const PLANET_SHORT = {
  Sun: 'Su', Moon: 'Mo', Mercury: 'Me', Venus: 'Ve', Mars: 'Ma',
  Jupiter: 'Ju', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
}

const PLANET_ORDER = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']

const RESULT_CLASS = { favourable: 'live', blocked: 'waiting', unfavourable: 'fruit-hard' }

const ROLE = {
  maha: { en: 'Mahadasha lord', ta: 'மகாதசை அதிபதி' },
  bhukti: { en: 'Bhukti lord', ta: 'புத்தி அதிபதி' },
}

const LABEL = {
  english: {
    period: 'Running period',
    live: 'Live now',
    waiting: 'Dasha on, waiting for transit',
    sky: 'Transit only',
    noneLive: 'No house is live on this date; the dasha houses below are building up.',
    skyNote: 'Jupiter and Saturn touch these, but the running lords do not, so effects stay light.',
    dasha: 'Dasha',
    transit: 'Transit',
    noDasha: 'The running lords do not touch this house.',
    noTransit: 'Jupiter and Saturn are not touching this house or its lord.',
    passing: 'Passing through',
    aspecting: 'Aspecting',
    lordGochara: 'House lord in Gochara',
    sav: 'Ashtakavarga',
    bindus: 'bindus',
    planetTitle: 'Planet Gochara (from natal Moon)',
    planet: 'Planet', sign: 'Sign', fromMoon: 'From Moon', result: 'Result',
    vedhaFrom: 'from',
    fromMoonSuffix: 'from Moon',
  },
  tamil: {
    period: 'நடப்பு தசை',
    live: 'இப்போது செயலில்',
    waiting: 'தசை இயக்கம், கோசாரம் காத்திருக்கிறது',
    sky: 'கோசாரம் மட்டும்',
    noneLive: 'இந்த தேதியில் செயலில் உள்ள வீடு இல்லை; கீழுள்ள தசை வீடுகள் வளர்கின்றன.',
    skyNote: 'குரு, சனி தொடுகின்றன; தசா அதிபதிகள் தொடவில்லை, எனவே பலன் லேசானது.',
    dasha: 'தசை',
    transit: 'கோசாரம்',
    noDasha: 'நடப்பு தசா அதிபதிகள் இந்த வீட்டைத் தொடவில்லை.',
    noTransit: 'குரு, சனி இந்த வீட்டையோ அதிபதியையோ தொடவில்லை.',
    passing: 'சஞ்சாரம்',
    aspecting: 'பார்வை',
    lordGochara: 'அதிபதி கோசாரம்',
    sav: 'அஷ்டகவர்க்கம்',
    bindus: 'பிந்துக்கள்',
    planetTitle: 'கிரக கோசாரம் (ஜன்ம சந்திரனிலிருந்து)',
    planet: 'கிரகம்', sign: 'ராசி', fromMoon: 'சந்திரனிலிருந்து', result: 'பலன்',
    vedhaFrom: 'காரணம்:',
    fromMoonSuffix: 'சந்திரனிலிருந்து',
  },
}

const lbl = (language) => LABEL[language] || LABEL.english
const isTa = (language) => language === 'tamil'

function pick(obj, language) {
  if (!obj) return ''
  return isTa(language) ? obj.ta || obj.en : obj.en
}

export function StatusBadge({ status, language = 'english' }) {
  if (!status) return null
  return <span className={`hl-badge hl-badge--${status.key}`}>{pick(status, language)}</span>
}

function HouseButton({ row, language, onOpen }) {
  const why = row.dasha?.reasons?.[0]
  return (
    <li>
      <button type="button" className="hl-now__item" onClick={() => onOpen(row.house)}>
        <span className="hl-now__head">
          <strong>{houseTitle(row, language)}</strong>
          <StatusBadge status={row.status} language={language} />
        </span>
        {why && <span className="hl-now__why">{pick(why, language)}.</span>}
        {row.transit?.lines?.[0] && <span className="hl-now__why">{pick(row.transit.lines[0], language)}.</span>}
      </button>
    </li>
  )
}

/** Running period, Moon of the day, and the live and waiting houses. */
export function PeriodSummary({ data, language = 'english', onOpen }) {
  if (!data) return null
  const tx = lbl(language)
  const p = data.period
  const rows = Object.fromEntries((data.houses || []).map(r => [r.house, r]))
  const by = data.by_status || {}
  const live = (by.live || []).map(h => rows[h]).filter(Boolean)
  const waiting = (by.waiting || []).map(h => rows[h]).filter(Boolean)
  const sky = (by.sky || []).map(h => rows[h]).filter(Boolean)
  return (
    <section className="hl-now" aria-label={tx.period}>
      {p && (
        <p className="hl-now__period">
          <strong>{p.mahadasha.planet}</strong> mahadasha to {p.mahadasha.end}
          {' · '}
          <strong>{p.bhukti.planet}</strong> bhukti to {p.bhukti.end}
        </p>
      )}
      {data.relation && (
        <p className={`hl-now__line hl-now__line--${data.relation.tone}`}>{pick(data.relation, language)}</p>
      )}
      {data.moon_today && <p className="hl-now__line">{pick(data.moon_today, language)}</p>}

      <h3 className="hl-section-title">{tx.live}</h3>
      {live.length ? (
        <ul className="hl-now__list">
          {live.map(row => <HouseButton key={row.house} row={row} language={language} onOpen={onOpen} />)}
        </ul>
      ) : (
        <p className="hl-now__line hl-now__line--muted">{tx.noneLive}</p>
      )}

      {waiting.length > 0 && (
        <>
          <h3 className="hl-section-title" style={{ marginTop: '0.75rem' }}>{tx.waiting}</h3>
          <ul className="hl-now__list">
            {waiting.map(row => <HouseButton key={row.house} row={row} language={language} onOpen={onOpen} />)}
          </ul>
        </>
      )}

      {sky.length > 0 && (
        <p className="hl-now__line hl-now__line--muted">
          {tx.sky}: {sky.map(r => houseTitle(r, language)).join(', ')}. {tx.skyNote}
        </p>
      )}
    </section>
  )
}

/** Twelve tappable house tiles coloured by House Links status. */
export function HouseStatusTiles({ houses, selected, onSelect, language = 'english', marked = {} }) {
  return (
    <ul className="hl-tiles">
      {(houses || []).map(row => {
        const t = row.transit || {}
        const on = selected === row.house
        return (
          <li key={row.house}>
            <button
              type="button"
              className={`hl-tile hl-tile--${row.status.key}${on ? ' hl-tile--selected' : ''}`}
              aria-pressed={on}
              onClick={() => onSelect(on ? null : row.house)}
            >
              <span className="hl-tile__num">{row.ordinal}{marked[row.house] ? ' •' : ''}</span>
              <span className="hl-tile__theme">{isTa(language) ? row.theme_ta || row.theme_en : row.theme_en}</span>
              <span className="hl-tile__tags">
                <StatusBadge status={row.status} language={language} />
              </span>
              {(t.jupiter || t.saturn) && (
                <span className="hl-tile__tags">
                  {t.jupiter && <span className="hl-badge">Jupiter</span>}
                  {t.saturn && <span className="hl-badge">Saturn</span>}
                </span>
              )}
            </button>
          </li>
        )
      })}
    </ul>
  )
}

/** Why a house has its status: dasha reasons, transit lines, lord in Gochara. */
export function HouseStatusDetail({ row, planets, language = 'english', onClose, children }) {
  if (!row) return null
  const tx = lbl(language)
  const t = row.transit || {}
  const reasons = row.dasha?.reasons || []
  const lord = (planets || []).find(p => p.planet === row.lord)
  return (
    <article className="hl-detail" aria-live="polite">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <h4 className="hl-detail__title" style={{ margin: 0 }}>{houseTitle(row, language)}</h4>
        {onClose && (
          <button type="button" className="gochar-house-detail__close" onClick={onClose} aria-label="Close">✕</button>
        )}
      </div>
      <p className="hl-detail__lede">
        {row.sign} · lord {row.lord} in the {ordinal(row.lord_house)} · {pick(row.fruit, language)}
      </p>
      <p className="hl-detail__text"><StatusBadge status={row.status} language={language} /></p>

      <h5>{tx.dasha}</h5>
      {reasons.length ? (
        <ul>{reasons.map(r => <li key={r.en}>{pick(r, language)}.</li>)}</ul>
      ) : (
        <p className="hl-detail__muted">{tx.noDasha}</p>
      )}

      <h5>{tx.transit}</h5>
      {(t.lines || []).length ? (
        <ul>{t.lines.map(l => <li key={l.en}>{pick(l, language)}.</li>)}</ul>
      ) : (
        <p className="hl-detail__muted">{tx.noTransit}</p>
      )}
      <p className="hl-detail__muted">
        {row.transit_in?.length ? `${tx.passing}: ${row.transit_in.join(', ')}. ` : ''}
        {row.transit_aspecting?.length ? `${tx.aspecting}: ${row.transit_aspecting.join(', ')}. ` : ''}
        {lord ? `${tx.lordGochara}: ${lord.planet} ${ordinal(lord.pos_from_moon)} ${tx.fromMoonSuffix}, ${pick(lord.result, language).toLowerCase()}. ` : ''}
        {t.sav_points != null ? `${tx.sav}: ${t.sav_points} ${tx.bindus} (${t.sav_label}).` : ''}
      </p>
      {children}
    </article>
  )
}

/** Classical Gochara from the natal Moon, without numbers. */
export function GocharaPlanetTable({ planets, language = 'english' }) {
  const tx = lbl(language)
  const rows = [...(planets || [])].sort(
    (a, b) => PLANET_ORDER.indexOf(a.planet) - PLANET_ORDER.indexOf(b.planet),
  )
  return (
    <div className="gochar-section">
      <div className="gochar-section__head">
        <h2 className="gochar-section__title">{tx.planetTitle}</h2>
      </div>
      <div className="gochar-planet-table-wrap">
        <table className="gochar-planet-table">
          <thead>
            <tr>
              <th>{tx.planet}</th>
              <th>{tx.sign}</th>
              <th>{tx.fromMoon}</th>
              <th>{tx.result}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(row => (
              <tr key={row.planet}>
                <td>
                  <strong>{PLANET_SHORT[row.planet] || row.planet}</strong>
                  {row.retrograde && <sup className="retro-sup-r">R</sup>}
                  {row.role && <span className="gochar-vedha"> · {pick(ROLE[row.role], language)}</span>}
                </td>
                <td>{isTa(language) ? row.sign_ta || row.sign_en : row.sign_en}</td>
                <td>{ordinal(row.pos_from_moon)}</td>
                <td>
                  <span className={`hl-badge hl-badge--${RESULT_CLASS[row.result.key]}`} style={{ whiteSpace: 'normal' }}>
                    {pick(row.result, language)}
                  </span>
                  {row.vedha_by && <span className="gochar-vedha"> · {tx.vedhaFrom} {row.vedha_by}</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

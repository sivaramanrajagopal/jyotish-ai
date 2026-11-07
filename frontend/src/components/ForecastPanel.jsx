/**
 * ForecastPanel.jsx
 * =================
 * House Links status of the 12 houses for a chosen date (rule engine),
 * with an optional AI daily note and per-house AI insight.
 */

import { useState, useEffect } from 'react'
import api from '../api/client'
import { formatTransitMoment } from '../lib/formatMoment'
import LanguageToggle from './LanguageToggle'
import { forecastPayload } from '../lib/chartPayload'
import { formatApiError } from '../lib/apiError'
import QuotaHint from './QuotaHint'
import { localISODate, localISODateOffset } from '../lib/dates'
import { houseTitle } from '../lib/houseStatus'
import { GocharaPlanetTable, HouseStatusDetail, HouseStatusTiles, PeriodSummary } from './TransitHouseStatus'

// ── Translations ───────────────────────────────────────────────────────────
const TR = {
  english: {
    dailyReading: '🔮 Your Daily Reading',
    forecastDate: 'Forecast date',
    forecastDateHint: 'Pick any date — e.g. “Is Tuesday good for my interview?”',
    forecastTime: 'Transit time (local)',
    forecastTimeHintToday: 'Leave empty to use the current time.',
    forecastTimeHintOther: 'Time used for Gochara positions on that date (default 06:00).',
    today: 'Today',
    generatingReading: 'Generating your daily reading…',
    aiForecast: '🤖 AI Forecast', generating: 'Generating personalised insight…',
    footer: (lagna, date) => `Lagna: ${lagna} · ${date} · Lahiri Ayanamsa`,
    calculating: 'Reading your houses for this date…',
    atGlance: 'Your day at a glance',
    readFullNote: 'Read AI daily note',
    hideFullNote: 'Hide AI daily note',
    loadDailyReading: 'Load AI daily note',
    ruleEngine: 'Rule engine',
    aiNarration: 'AI narration',
    transitComputedAt: 'Transits computed at',
    exploreAll: 'Explore all 12 life areas',
    hideAreas: 'Hide life areas',
    checkTomorrow: 'Check tomorrow',
    askAi: 'Ask AI',
    tapForAi: 'Tap any area for its status and an AI insight',
    liveHead: (list) => `Live now: ${list}.`,
    waitingHead: (list) => `Dasha on, waiting for transit: ${list}.`,
    noneLive: 'No house is fully live on this date.',
    placeholder: 'Open Forecast to load your houses…',
  },
  tamil: {
    dailyReading: '🔮 இன்றைய கணிப்பு',
    forecastDate: 'கணிப்பு தேதி',
    forecastDateHint: 'எந்த தேதியையும் தேர்ந்தெடுக்கவும் — நேர்முகம், திருமணம் போன்றவற்றுக்கு',
    forecastTime: 'கோசார நேரம் (உள்ளூர்)',
    forecastTimeHintToday: 'தற்போதைய நேரத்தைப் பயன்படுத்த காலியாக விடுங்கள்.',
    forecastTimeHintOther: 'அந்த தேதியில் கோசாரம் கணக்கிடப்படும் நேரம் (இயல்பு 06:00).',
    today: 'இன்று',
    generatingReading: 'இன்றைய கணிப்பு உருவாகிறது…',
    aiForecast: '🤖 ஜோதிட கணிப்பு', generating: 'தனிப்பட்ட கணிப்பு உருவாகிறது…',
    footer: (lagna, date) => `லக்னம்: ${lagna} · ${date} · லாஹிரி அயனாம்சம்`,
    calculating: 'இந்த தேதிக்கான வீடுகள் கணக்கிடப்படுகின்றன…',
    atGlance: 'இன்றைய நிலை — ஒரு பார்வையில்',
    readFullNote: 'AI தினசரி குறிப்பு',
    hideFullNote: 'AI குறிப்பை மறை',
    loadDailyReading: 'AI தினசரி குறிப்பு ஏற்று',
    ruleEngine: 'விதி இயந்திரம்',
    aiNarration: 'AI விளக்கம்',
    transitComputedAt: 'கோசாரம் கணக்கிடப்பட்ட நேரம்',
    exploreAll: '12 துறைகளையும் பார்க்க',
    hideAreas: 'துறைகளை மறை',
    checkTomorrow: 'நாளை பார்க்க',
    askAi: 'AI கேள்',
    tapForAi: 'நிலையும் AI கணிப்பும் காண ஒரு துறையைத் தட்டவும்',
    liveHead: (list) => `இப்போது செயலில்: ${list}.`,
    waitingHead: (list) => `தசை இயக்கம், கோசாரம் காத்திருக்கிறது: ${list}.`,
    noneLive: 'இந்த தேதியில் முழுமையாக செயலில் உள்ள வீடு இல்லை.',
    placeholder: 'உங்கள் வீடுகளை ஏற்ற Forecast திறக்கவும்…',
  },
}

const t = (lang) => TR[lang] || TR.english

function todayISO() {
  return localISODate()
}

function tomorrowISO() {
  return localISODateOffset(1)
}

function firstSentence(text) {
  if (!text) return ''
  const m = text.match(/^[^.!?]+[.!?]?/)
  return m ? m[0].trim() : text.slice(0, 160).trim()
}

function buildHeadline({ reading, data, language }) {
  if (reading) {
    const line = firstSentence(reading)
    if (line.length > 24 && line.length <= 140) return line
  }
  const tx = t(language)
  const rows = Object.fromEntries(data.houses.map(r => [r.house, r]))
  const names = (hs) => hs.map(h => rows[h].ordinal).join(', ')
  const { live = [], waiting = [] } = data.by_status || {}
  const parts = [live.length ? tx.liveHead(names(live)) : tx.noneLive]
  if (waiting.length) parts.push(tx.waitingHead(names(waiting)))
  return parts.join(' ')
}

function InsightText({ text }) {
  if (!text) return null
  const sections = text.split(/\n(?=\d\.)/).filter(Boolean)
  const icons    = ['📍','✅','⚠️']
  if (sections.length <= 1) {
    return <p style={{ color:'var(--text-primary)', lineHeight:1.7, fontSize:14, margin:0 }}>{text}</p>
  }
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
      {sections.map((s, i) => {
        const clean = s.replace(/^\d\.\s*/, '').trim()
        const nl    = clean.indexOf('\n')
        const title = nl > -1 ? clean.slice(0, nl) : clean
        const body  = nl > -1 ? clean.slice(nl + 1).trim() : ''
        return (
          <div key={i} style={{
            background: i === 2 ? 'var(--insight-caution-bg)' : 'var(--insight-pos-bg)',
            border:`1px solid ${i === 2 ? 'var(--insight-caution-border)' : 'var(--insight-pos-border)'}`,
            borderRadius:8, padding:'10px 12px',
          }}>
            <div style={{ fontWeight:700, color:'var(--text-primary)', fontSize:13, marginBottom:4 }}>
              {icons[i]} {title}
            </div>
            {body && <p style={{ color:'var(--text-secondary)', fontSize:13, lineHeight:1.6, margin:0 }}>{body}</p>}
          </div>
        )
      })}
    </div>
  )
}

function AtGlanceHero({ data, headline, language, onLanguageChange, isToday, onCheckTomorrow, transitDate, onAskAi }) {
  const tx = t(language)
  const { live = [], waiting = [] } = data.by_status || {}
  const focus = live[0] ?? waiting[0] ?? null
  const focusRow = data.houses.find(r => r.house === focus)

  return (
    <div style={{
      background: 'var(--daily-card-bg)', borderRadius: 16, padding: '16px 18px',
      marginBottom: 14, boxShadow: 'var(--card-shadow)',
    }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10, marginBottom: 12 }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            {tx.atGlance}{!isToday ? ` · ${transitDate}` : ''}
          </div>
          <span className="prashna-engine-badge prashna-engine-badge--rule">{tx.ruleEngine}</span>
        </div>
        <LanguageToggle language={language} onChange={onLanguageChange} />
      </div>

      <p style={{ color: 'rgba(255,255,255,0.88)', fontSize: 14, lineHeight: 1.6, margin: '0 0 12px' }}>
        {headline}
      </p>

      {focusRow && onAskAi && (
        <button
          type="button"
          onClick={() => onAskAi(focus)}
          style={{
            width: '100%', minHeight: 44, marginBottom: 12, padding: '11px 14px', borderRadius: 10,
            border: 'none', background: 'var(--orange)', color: '#FFF',
            fontSize: 14, fontWeight: 700, cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            WebkitTapHighlightColor: 'transparent',
          }}
        >
          🤖 {tx.askAi} · {houseTitle(focusRow, language)} →
        </button>
      )}

      {isToday && onCheckTomorrow && (
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            type="button"
            onClick={onCheckTomorrow}
            style={{
              minHeight: 44, padding: '6px 12px', borderRadius: 8,
              border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.06)',
              color: 'rgba(255,255,255,0.75)', fontSize: 12, fontWeight: 600, cursor: 'pointer',
            }}
          >
            {tx.checkTomorrow} →
          </button>
        </div>
      )}
    </div>
  )
}

function DailyReadingExpandable({ expanded, onToggle, children, language, hasReading, onLoad, loading }) {
  const tx = t(language)
  const label = expanded ? tx.hideFullNote : (hasReading ? tx.readFullNote : tx.loadDailyReading)
  return (
    <div style={{ marginBottom: 16 }}>
      <button
        type="button"
        onClick={() => {
          if (!expanded && !hasReading && onLoad) onLoad()
          onToggle()
        }}
        aria-expanded={expanded}
        disabled={loading}
        style={{
          width: '100%', minHeight: 44, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8,
          padding: '12px 14px', borderRadius: 12, cursor: loading ? 'wait' : 'pointer',
          border: '1px solid var(--card-border)', background: 'var(--card-bg)',
          color: 'var(--text-secondary)', fontSize: 13, fontWeight: 600,
          boxShadow: 'var(--card-shadow)', marginBottom: expanded ? 10 : 0,
          opacity: loading ? 0.7 : 1,
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span>{loading ? tx.generatingReading : label}</span>
          <span className="prashna-engine-badge prashna-engine-badge--ai">{tx.aiNarration}</span>
        </span>
        <span style={{ fontSize: 10, opacity: 0.6 }}>{expanded ? '▲' : '▼'}</span>
      </button>
      {expanded && children}
    </div>
  )
}

function DailyReadingCard({ reading, language }) {
  if (!reading) return null
  return (
    <div style={{ background:'var(--daily-card-bg)', borderRadius:16, padding:'18px 20px', boxShadow:'var(--card-shadow)' }}>
      <div style={{ fontSize:14, fontWeight:800, color:'#FF9900', marginBottom:10 }}>{t(language).dailyReading}</div>
      <p style={{ color:'rgba(255,255,255,0.88)', fontSize:13, lineHeight:1.75, margin:0 }}>{reading}</p>
    </div>
  )
}

function pickerInputStyle() {
  return {
    flex:'1 1 160px', minWidth:0, width:'100%', maxWidth:'100%',
    height:44, padding:'0 12px', fontSize:16,
    borderRadius:8, border:'1px solid var(--input-border)',
    background:'var(--input-bg)', color:'var(--input-text)',
  }
}

const chipStyle = {
  padding:'10px 14px', minHeight:44, borderRadius:8, border:'1px solid var(--chip-border)',
  background:'var(--chip-bg)', color:'var(--text-secondary)',
  fontSize:12, fontWeight:600, cursor:'pointer',
}

// ── Main ───────────────────────────────────────────────────────────────────
export default function ForecastPanel({ chart, gender = 'male', showDatePicker = false, userId, enabled = true }) {
  const [transitDate,  setTransitDate]  = useState(todayISO)
  const [transitTime,  setTransitTime]  = useState('')
  const [data,           setData]           = useState(null)
  const [dataLoading,    setDataLoading]    = useState(false)
  const [dataError,      setDataError]      = useState('')
  const [selectedHouse,  setSelectedHouse]  = useState(null)
  const [insightLoading, setInsightLoading] = useState(false)
  const [insightError,   setInsightError]   = useState('')
  const [insightCache,   setInsightCache]   = useState({})
  const [dailyReading,   setDailyReading]   = useState(null)
  const [readingLoading, setReadingLoading] = useState(false)
  const [readingError,   setReadingError]   = useState('')
  const [language,       setLanguage]       = useState('english')
  const [readingExpanded, setReadingExpanded] = useState(false)
  const [gridExpanded, setGridExpanded] = useState(() =>
    typeof window !== 'undefined' && window.matchMedia('(min-width: 640px)').matches
  )

  useEffect(() => {
    const mq = window.matchMedia('(min-width: 640px)')
    const sync = () => { if (mq.matches) setGridExpanded(true) }
    sync()
    mq.addEventListener('change', sync)
    return () => mq.removeEventListener('change', sync)
  }, [])

  const insightKey = (houseNum) => `${houseNum}:${transitDate}:${transitTime || 'auto'}:${language}`

  // House status — refetch on chart/date/time only (not language)
  useEffect(() => {
    if (!chart || !enabled) return
    setDataLoading(true)
    setDataError('')
    setSelectedHouse(null)
    setInsightCache({})
    setReadingExpanded(false)
    setDailyReading(null)
    api.post('/forecast/links', forecastPayload(chart, userId, transitDate, transitTime || undefined))
      .then(r => setData(r.data))
      .catch(err => {
        setDataError(formatApiError(err, 'Could not load the forecast.'))
        setData(null)
      })
      .finally(() => setDataLoading(false))
  }, [chart, transitDate, transitTime, userId, enabled])

  const loadDailyReading = () => {
    if (!chart || !enabled || readingLoading || dailyReading?.reading) return
    setReadingLoading(true)
    setReadingError('')
    api.post('/forecast/daily-reading', {
      ...forecastPayload(chart, userId, transitDate, transitTime || undefined),
      gender,
      language,
    })
      .then(r => setDailyReading(r.data))
      .catch(err => {
        setReadingError(formatApiError(err, 'Could not load daily reading.'))
      })
      .finally(() => setReadingLoading(false))
  }

  const tx = t(language)

  if (!enabled) {
    return (
      <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--text-muted)', fontSize: 14 }}>
        {tx.placeholder}
      </div>
    )
  }

  const handleLanguageChange = (lang) => {
    setLanguage(lang)
    setDailyReading(null)
  }

  const handleTagClick = async (houseNum) => {
    if (houseNum == null || selectedHouse === houseNum) { setSelectedHouse(null); return }
    setSelectedHouse(houseNum)
    setInsightError('')
    const key = insightKey(houseNum)
    if (insightCache[key]) return

    setInsightLoading(true)
    try {
      const res = await api.post('/forecast/house', {
        ...forecastPayload(chart, userId, transitDate, transitTime || undefined),
        house_num:   houseNum,
        gender,
        language,
      })
      setInsightCache(prev => ({ ...prev, [key]: res.data.insight || '' }))
    } catch (err) {
      setInsightError(formatApiError(err, 'Could not load AI insight.'))
    } finally {
      setInsightLoading(false)
    }
  }

  const scrollToHouseDetail = (houseNum) => {
    setGridExpanded(true)
    if (selectedHouse !== houseNum) handleTagClick(houseNum)
    setTimeout(() => {
      document.getElementById('forecast-house-detail')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }, 200)
  }

  const isToday = transitDate === todayISO()

  if (dataLoading) return (
    <div style={{ textAlign:'center', padding:'48px 0', color:'var(--orange)' }}>
      <div style={{ fontSize:36, marginBottom:12 }}>🔮</div>
      <div style={{ fontSize:14, fontWeight:600, color:'var(--text-secondary)' }}>{tx.calculating}</div>
    </div>
  )

  if (dataError) return (
    <div style={{ color:'var(--error-text)', background:'var(--error-bg)', border:'1px solid var(--error-border)', borderRadius:12, padding:'16px 20px', fontSize:14 }}>
      ⚠️ {dataError}
    </div>
  )

  if (!data) return null

  const headline = buildHeadline({ reading: dailyReading?.reading, data, language })
  const selected = data.houses.find(r => r.house === selectedHouse)
  const loaded = Object.fromEntries(data.houses.map(r => [r.house, !!insightCache[insightKey(r.house)]]))

  return (
    <div>
      <QuotaHint userId={userId} />
      {showDatePicker && (
        <div style={{
          background:'var(--card-bg)', border:'1px solid var(--card-border)',
          borderRadius:12, padding:'12px 14px', marginBottom:16,
          boxShadow:'var(--card-shadow)',
        }}>
          <div style={{ display:'flex', flexWrap:'wrap', alignItems:'center', gap:10 }} className="forecast-date-row">
            <label style={{ fontSize:12, fontWeight:700, color:'var(--text-secondary)', flex:'1 1 120px' }}>
              📅 {tx.forecastDate}
            </label>
            <input
              type="date"
              value={transitDate}
              min="2020-01-01"
              max="2035-12-31"
              onChange={e => setTransitDate(e.target.value)}
              style={pickerInputStyle()}
            />
            {!isToday && (
              <button type="button" onClick={() => setTransitDate(todayISO())} style={chipStyle}>
                {tx.today}
              </button>
            )}
          </div>
          <div style={{ display:'flex', flexWrap:'wrap', alignItems:'center', gap:10, marginTop:10 }} className="forecast-date-row">
            <label style={{ fontSize:12, fontWeight:700, color:'var(--text-secondary)', flex:'1 1 120px' }}>
              🕐 {tx.forecastTime}
            </label>
            <input
              type="time"
              value={transitTime}
              onChange={e => setTransitTime(e.target.value)}
              style={pickerInputStyle()}
            />
            {transitTime && (
              <button type="button" onClick={() => setTransitTime('')} style={chipStyle}>
                {isToday ? tx.today : '06:00'}
              </button>
            )}
          </div>
          <p style={{ fontSize:11, color:'var(--text-muted)', margin:'8px 0 0' }}>
            {tx.forecastDateHint}
            {' '}
            {isToday ? tx.forecastTimeHintToday : tx.forecastTimeHintOther}
          </p>
          {data.transit_moment && (
            <p style={{ fontSize:11, color:'var(--text-muted)', margin:'6px 0 0' }}>
              {tx.transitComputedAt}: {formatTransitMoment(data.transit_moment)}
            </p>
          )}
        </div>
      )}

      <AtGlanceHero
        data={data}
        headline={headline}
        language={language}
        onLanguageChange={handleLanguageChange}
        isToday={isToday}
        onCheckTomorrow={isToday ? () => setTransitDate(tomorrowISO()) : undefined}
        transitDate={data.transit_date || transitDate}
        onAskAi={scrollToHouseDetail}
      />

      <DailyReadingExpandable
        expanded={readingExpanded}
        onToggle={() => setReadingExpanded(v => !v)}
        language={language}
        hasReading={!!dailyReading?.reading}
        onLoad={loadDailyReading}
        loading={readingLoading}
      >
        {readingError && (
          <div style={{ color:'var(--error-text)', background:'var(--error-bg)', border:'1px solid var(--error-border)', borderRadius:12, padding:'12px 16px', marginBottom:10, fontSize:13 }}>
            ⚠️ {readingError}
          </div>
        )}
        {dailyReading?.reading && <DailyReadingCard reading={dailyReading.reading} language={language} />}
      </DailyReadingExpandable>

      <PeriodSummary data={data} language={language} onOpen={scrollToHouseDetail} />

      <button
        type="button"
        onClick={() => setGridExpanded(v => !v)}
        aria-expanded={gridExpanded}
        className="forecast-grid-toggle"
        style={{
          width: '100%', minHeight: 44, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '10px 0', marginBottom: gridExpanded ? 10 : 4,
          border: 'none', background: 'transparent', cursor: 'pointer',
          color: 'var(--text-secondary)', fontSize: 13, fontWeight: 700,
        }}
      >
        <span>{gridExpanded ? tx.hideAreas : tx.exploreAll}</span>
        <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{gridExpanded ? '▲' : '▼'}</span>
      </button>

      {gridExpanded && (
        <>
          <div style={{ display:'flex', flexWrap:'wrap', alignItems:'center', gap:8, margin:'0 0 12px' }}>
            <p style={{ fontSize:12, color:'var(--text-muted)', margin:0, flex:'1 1 200px' }}>{tx.tapForAi}</p>
            <span className="prashna-engine-badge prashna-engine-badge--rule">{tx.ruleEngine}</span>
            <span className="prashna-engine-badge prashna-engine-badge--ai">{tx.aiNarration}</span>
          </div>
          <HouseStatusTiles
            houses={data.houses}
            selected={selectedHouse}
            onSelect={handleTagClick}
            language={language}
            marked={loaded}
          />
        </>
      )}

      {selected && (
        <div id="forecast-house-detail" style={{ marginTop: 12 }}>
          <HouseStatusDetail row={selected} planets={data.planets} language={language} onClose={() => setSelectedHouse(null)}>
            <div style={{ borderTop:'1px solid var(--card-border)', paddingTop:12, marginTop:12 }}>
              <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:10 }}>
                <div style={{ fontSize:11, fontWeight:700, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.07em' }}>
                  {tx.aiForecast}
                </div>
                <span className="prashna-engine-badge prashna-engine-badge--ai">{tx.aiNarration}</span>
              </div>
              {insightLoading && !insightCache[insightKey(selected.house)] && (
                <div style={{ color:'var(--orange)', fontSize:13, display:'flex', gap:6, alignItems:'center' }}>
                  <span>✦</span> {tx.generating}
                </div>
              )}
              {insightError && <div style={{ color:'var(--error-text)', fontSize:13 }}>⚠️ {insightError}</div>}
              <InsightText text={insightCache[insightKey(selected.house)] || ''} />
            </div>
          </HouseStatusDetail>
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        <GocharaPlanetTable planets={data.planets} language={language} />
      </div>

      <div style={{ marginTop:20, textAlign:'center', fontSize:11, color:'var(--text-muted)' }}>
        {tx.footer(data.lagna_en, data.transit_date)}
        {data.transit_moment?.time && (
          <div style={{ marginTop: 4 }}>
            {tx.transitComputedAt} {formatTransitMoment(data.transit_moment)}
          </div>
        )}
      </div>
    </div>
  )
}

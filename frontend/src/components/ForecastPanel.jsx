/**
 * ForecastPanel.jsx
 * =================
 * 12 life-area tags with deterministic RAG scores.
 * Click any tag → detail card with score bar + AI interpretation.
 */

import { useState, useEffect } from 'react'
import api from '../api/client'
import LanguageToggle from './LanguageToggle'

const HOUSE_ICONS = {
  1:'🧘', 2:'💰', 3:'💬', 4:'🏠', 5:'🎨', 6:'⚔️',
  7:'💑', 8:'🔮', 9:'🍀', 10:'🏆', 11:'🤝', 12:'🕊️',
}

// ── Translations ───────────────────────────────────────────────────────────
const TR = {
  english: {
    ragLabel: { GREEN:'Favourable', AMBER:'Mixed', RED:'Challenging' },
    transitHealth: 'Transit Health', strongest: 'Strongest Today', needsCare: 'Needs Care',
    dailyReading: '🔮 Your Daily Reading', dashaTransit: 'Dasha-Transit',
    overallHealth: 'Overall Transit Health', favourable: 'Favourable',
    mixed: 'Mixed', challenging: 'Challenging',
    tapInstruction: 'Tap any life area to see your forecast',
    forecastDate: 'Forecast date',
    forecastDateHint: 'Pick any date — e.g. “Is Tuesday good for my interview?”',
    today: 'Today',
    generatingReading: 'Generating your daily reading…',
    strengthScore: 'Strength Score',
    houseLord: 'House Lord', lordDignity: 'Lord Dignity',
    planetsHere: 'Natal Planets', transitActivity: 'Current Transits',
    aiForecast: '🤖 AI Forecast', generating: 'Generating personalised insight…',
    none: 'None', footer: (lagna, date) => `Lagna: ${lagna} · ${date} · Lahiri Ayanamsa`,
    calculating: 'Calculating your Gochara scores and daily reading…',
    dignity: { Exalted:'Exalted', 'Own Sign':'Own Sign', Friend:'Friend',
               Neutral:'Neutral', Enemy:'Enemy', Debilitated:'Debilitated', 'N/A':'—' },
  },
  tamil: {
    ragLabel: { GREEN:'சாதகமானது', AMBER:'கலப்பு', RED:'சவாலானது' },
    transitHealth: 'கோசார நிலை', strongest: 'இன்று வலிமையானவை', needsCare: 'கவனம் தேவை',
    dailyReading: '🔮 இன்றைய கணிப்பு', dashaTransit: 'தசை-கோசாரம்',
    overallHealth: 'ஒட்டுமொத்த கோசார நிலை', favourable: 'சாதகம்',
    mixed: 'கலப்பு', challenging: 'சவால்',
    tapInstruction: 'உங்கள் கணிப்பைப் பார்க்க ஒரு துறையை தட்டவும்',
    forecastDate: 'கணிப்பு தேதி',
    forecastDateHint: 'எந்த தேதியையும் தேர்ந்தெடுக்கவும் — நேர்முகம், திருமணம் போன்றவற்றுக்கு',
    today: 'இன்று',
    generatingReading: 'இன்றைய கணிப்பு உருவாகிறது…',
    strengthScore: 'வலிமை மதிப்பு',
    houseLord: 'பாவாதிபதி', lordDignity: 'கிரக நிலை',
    planetsHere: 'ஜன்ம கிரகங்கள்', transitActivity: 'தற்போதைய கோசாரம்',
    aiForecast: '🤖 ஜோதிட கணிப்பு', generating: 'தனிப்பட்ட கணிப்பு உருவாகிறது…',
    none: 'இல்லை', footer: (lagna, date) => `லக்னம்: ${lagna} · ${date} · லாஹிரி அயனாம்சம்`,
    calculating: 'உங்கள் கோசார மதிப்புகளும் இன்றைய கணிப்பும் கணக்கிடப்படுகின்றன…',
    dignity: { Exalted:'உச்சம்', 'Own Sign':'சொந்த வீடு', Friend:'நட்பு வீடு',
               Neutral:'நடுநிலை', Enemy:'எதிரி வீடு', Debilitated:'நீசம்', 'N/A':'—' },
  },
}

// Tamil house names & descriptions (displayed in house detail card)
const HOUSE_TAMIL = {
  1:  { name:'தன்னலம் & ஆளுமை',        simple:'உங்கள் ஆரோக்கியம், உயிர்சக்தி மற்றும் தோற்றம்' },
  2:  { name:'செல்வம் & குடும்பம்',      simple:'உங்கள் நிதி நிலை, குடும்பம் மற்றும் பேச்சு' },
  3:  { name:'தைரியம் & திறமை',          simple:'உங்கள் தொடர்பு, தைரியம் மற்றும் உடன்பிறப்புகள்' },
  4:  { name:'வீடு & மகிழ்ச்சி',         simple:'உங்கள் வீடு, தாய் மற்றும் உள்ளமன அமைதி' },
  5:  { name:'படைப்பாற்றல் & பிள்ளைகள்', simple:'உங்கள் அறிவு, படைப்பு மற்றும் பிள்ளைகள்' },
  6:  { name:'ஆரோக்கியம் & போட்டி',      simple:'உடல்நல சவால்கள், தினசரி பணி மற்றும் தடைகள்' },
  7:  { name:'திருமணம் & கூட்டு',         simple:'உங்கள் வாழ்க்கைத்துணை, வணிக கூட்டாளர்' },
  8:  { name:'மாற்றம் & ஆயுள்',           simple:'திடீர் மாற்றங்கள், மரபுரிமை மற்றும் மறைவிஞ்ஞானம்' },
  9:  { name:'அதிர்ஷ்டம் & ஞானம்',       simple:'உங்கள் அதிர்ஷ்டம், தந்தை மற்றும் உயர்கல்வி' },
  10: { name:'தொழில் & புகழ்',            simple:'உங்கள் தொழில், புகழ் மற்றும் பொது வாழ்க்கை' },
  11: { name:'ஆதாயம் & நட்பு',            simple:'உங்கள் வருமானம், நண்பர்கள் மற்றும் ஆசைகள்' },
  12: { name:'ஆன்மீகம் & முக்தி',         simple:'செலவுகள், வெளிநாடு மற்றும் ஆன்மீக விடுதலை' },
}

// Tamil theme chip translations
const THEME_TAMIL = {
  'health':'ஆரோக்கியம்', 'appearance':'தோற்றம்', 'vitality':'உயிர்சக்தி',
  'overall well-being':'ஒட்டுமொத்த நலன்',
  'finances':'நிதி', 'family':'குடும்பம்', 'speech':'பேச்சு', 'food':'உணவு', 'assets':'சொத்து',
  'communication':'தொடர்பு', 'short travels':'குறுந்தூர பயணம்', 'siblings':'உடன்பிறப்பு',
  'skills':'திறமை', 'courage':'தைரியம்',
  'property':'சொத்து', 'vehicles':'வாகனம்', 'mother':'தாய்', 'happiness':'மகிழ்ச்சி', 'education':'கல்வி',
  'creativity':'படைப்பு', 'children':'பிள்ளைகள்', 'romance':'காதல்',
  'speculation':'கணிப்பு', 'intellect':'அறிவு',
  'disease':'நோய்', 'debts':'கடன்', 'enemies':'எதிரிகள்', 'competition':'போட்டி', 'service':'சேவை',
  'spouse':'வாழ்க்கைத்துணை', 'business partnerships':'வணிக கூட்டு', 'public relations':'பொது தொடர்பு',
  'sudden events':'திடீர் நிகழ்வுகள்', 'inheritance':'மரபுரிமை',
  'occult':'மறைவிஞ்ஞானம்', 'research':'ஆராய்ச்சி', 'longevity':'ஆயுள்',
  'luck':'அதிர்ஷ்டம்', 'father':'தந்தை', 'dharma':'தர்மம்',
  'long travels':'நீண்ட பயணம்', 'spirituality':'ஆன்மீகம்',
  'profession':'தொழில்', 'reputation':'புகழ்', 'authority':'அதிகாரம்',
  'government':'அரசாங்கம்', 'karma':'கர்மம்',
  'income':'வருமானம்', 'friends':'நண்பர்கள்', 'aspirations':'ஆசைகள்',
  'elder siblings':'மூத்த உடன்பிறப்பு', 'profits':'லாபம்',
  'expenses':'செலவுகள்', 'foreign lands':'வெளிநாடு', 'isolation':'தனிமை', 'losses':'இழப்புகள்',
}

const RAG = {
  GREEN: { bg:'var(--rag-green-bg)', border:'var(--rag-green-border)', text:'var(--rag-green-text)', badge:'#27ae60' },
  AMBER: { bg:'var(--rag-amber-bg)', border:'var(--rag-amber-border)', text:'var(--rag-amber-text)', badge:'#f39c12' },
  RED:   { bg:'var(--rag-red-bg)',   border:'var(--rag-red-border)',   text:'var(--rag-red-text)',   badge:'#e74c3c' },
}

// Helper to get translations for current language
const t = (lang) => TR[lang] || TR.english

function ScoreBar({ score, status, language = 'english' }) {
  const colour = RAG[status]?.badge || '#999'
  return (
    <div style={{ marginTop:8 }}>
      <div style={{ display:'flex', justifyContent:'space-between', fontSize:11, color:'var(--text-muted)', marginBottom:3 }}>
        <span>{t(language).strengthScore}</span>
        <span style={{ fontWeight:700, color:colour }}>{score}/100</span>
      </div>
      <div style={{ background:'var(--card-border)', borderRadius:6, height:8, overflow:'hidden' }}>
        <div style={{ width:`${score}%`, height:'100%', background:colour, borderRadius:6, transition:'width 0.6s ease' }} />
      </div>
    </div>
  )
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

function HouseDetailCard({ houseData, insight, insightLoading, insightError, language = 'english' }) {
  if (!houseData) return null
  const status = houseData.rag?.status || 'AMBER'
  const rc     = RAG[status] || RAG.AMBER
  const tx     = t(language)
  const isTamil = language === 'tamil'

  // Tamil overrides for house name/description
  const houseName   = isTamil ? (HOUSE_TAMIL[houseData.house_num]?.name   || houseData.name)   : houseData.name
  const houseSimple = isTamil ? (HOUSE_TAMIL[houseData.house_num]?.simple || houseData.simple) : houseData.simple
  const ragLabel    = tx.ragLabel[status] || status

  // Translate dignity
  const dignityVal = isTamil
    ? (tx.dignity[houseData.lord_dignity] || houseData.lord_dignity || '—')
    : (houseData.lord_dignity || '—')

  // Translate theme chips
  const themes = houseData.themes?.map(th =>
    isTamil ? (THEME_TAMIL[th] || th) : th
  ) || []

  return (
    <div style={{
      background:rc.bg, border:`2px solid ${rc.border}`,
      borderRadius:16, padding:'20px', marginTop:16,
      boxShadow:'0 4px 16px rgba(0,0,0,0.08)',
    }}>
      {/* Header */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:12 }}>
        <div>
          <div style={{ fontSize:18, fontWeight:800, color:'var(--text-primary)' }}>
            {HOUSE_ICONS[houseData.house_num]} H{houseData.house_num} — {houseName}
          </div>
          <div style={{ fontSize:13, color:'var(--text-secondary)', marginTop:3 }}>{houseSimple}</div>
        </div>
        <span style={{
          background:rc.badge, color:'#FFF',
          borderRadius:20, padding:'4px 12px',
          fontSize:12, fontWeight:700, whiteSpace:'nowrap', marginLeft:8,
        }}>
          {houseData.rag?.emoji} {ragLabel}
        </span>
      </div>

      <ScoreBar score={houseData.score} status={status} language={language} />

      {/* Key facts grid */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(130px,1fr))', gap:8, margin:'14px 0' }}>
        {[
          { label: tx.houseLord,       value:`${houseData.lord} → H${houseData.lord_placed_house}` },
          { label: tx.lordDignity,     value: dignityVal },
          { label: tx.planetsHere,     value: houseData.planets_in_house?.join(', ') || tx.none },
          { label: tx.transitActivity, value: houseData.transit_planets?.join(', ')  || tx.none },
          ...(houseData.sav_points != null ? [{
            label: 'SAV (Ashtakavarga)',
            value: `${houseData.sav_points} — ${houseData.sav_label || ''}`,
          }] : []),
        ].map(({ label, value }) => (
          <div key={label} style={{ background:'var(--card-bg)', borderRadius:8, padding:'8px 10px', border:'1px solid var(--card-border)' }}>
            <div style={{ fontSize:10, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:2 }}>{label}</div>
            <div style={{ fontSize:13, fontWeight:600, color:'var(--text-primary)' }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Theme chips */}
      <div style={{ display:'flex', flexWrap:'wrap', gap:6, marginBottom:14 }}>
        {themes.map(th => (
          <span key={th} style={{
            background:'var(--card-bg)', border:`1px solid ${rc.border}`,
            borderRadius:12, padding:'3px 10px',
            fontSize:11, color:rc.text, fontWeight:500,
          }}>{th}</span>
        ))}
      </div>

      {/* AI insight section */}
      <div style={{ borderTop:`1px solid ${rc.border}`, paddingTop:14 }}>
        <div style={{ fontSize:11, fontWeight:700, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.07em', marginBottom:10 }}>
          {tx.aiForecast}
        </div>
        {insightLoading && (
          <div style={{ color:'var(--orange)', fontSize:13, display:'flex', gap:6, alignItems:'center' }}>
            <span>✦</span> {tx.generating}
          </div>
        )}
        {insightError && <div style={{ color:'var(--error-text)', fontSize:13 }}>⚠️ {insightError}</div>}
        {insight && !insightLoading && <InsightText text={insight} />}
      </div>
    </div>
  )
}

// ── Daily Reading Card ────────────────────────────────────────────────────
function DailyReadingCard({ reading, dtc, overall, topHouses, challengingHouses, language = 'english' }) {
  if (!reading) return null
  const dtcRag  = dtc?.rag?.status || 'AMBER'
  const rc      = RAG[dtcRag] || RAG.AMBER
  const tx      = t(language)
  const isTamil = language === 'tamil'

  // House name in correct language
  const hName = (h) => isTamil
    ? (HOUSE_TAMIL[h.house]?.name?.split(' & ')[0] || h.name.split(' ')[0])
    : h.name.split(' ')[0]

  const overallLabel = tx.ragLabel[overall?.rag?.status] || overall?.rag?.label || ''

  return (
    <div style={{
      background:'var(--daily-card-bg)', borderRadius:16, padding:'18px 20px',
      marginBottom:20, boxShadow:'var(--card-shadow)',
    }}>
      {/* Header row */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:14 }}>
        <div style={{ fontSize:14, fontWeight:800, color:'#FF9900' }}>{tx.dailyReading}</div>
        <span style={{ background:rc.badge, color:'#FFF', borderRadius:20, padding:'3px 10px', fontSize:11, fontWeight:700 }}>
          {tx.dashaTransit}: {tx.ragLabel[dtcRag] || dtcRag}
        </span>
      </div>

      {/* Reading text */}
      <p style={{ color:'rgba(255,255,255,0.88)', fontSize:13, lineHeight:1.75, margin:'0 0 14px' }}>
        {reading}
      </p>

      {/* 3-column summary */}
      <div className="daily-summary-grid" style={{ marginBottom:14 }}>
        <div style={{ background:'rgba(255,255,255,0.07)', borderRadius:8, padding:'8px 10px' }}>
          <div style={{ fontSize:9, color:'rgba(255,255,255,0.4)', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:4 }}>{tx.transitHealth}</div>
          <div style={{ fontSize:16, fontWeight:800, color:'#FF9900' }}>{overall?.average_score}/100</div>
          <div style={{ fontSize:10, color:'rgba(255,255,255,0.5)' }}>{overallLabel}</div>
        </div>
        <div style={{ background:'rgba(255,255,255,0.07)', borderRadius:8, padding:'8px 10px' }}>
          <div style={{ fontSize:9, color:'rgba(255,255,255,0.4)', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:4 }}>{tx.strongest}</div>
          {(topHouses||[]).slice(0,2).map(h => (
            <div key={h.house} style={{ fontSize:11, color:'#81C784', fontWeight:600 }}>🟢 {hName(h)}</div>
          ))}
        </div>
        <div style={{ background:'rgba(255,255,255,0.07)', borderRadius:8, padding:'8px 10px' }}>
          <div style={{ fontSize:9, color:'rgba(255,255,255,0.4)', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:4 }}>{tx.needsCare}</div>
          {(challengingHouses||[]).slice(0,2).map(h => (
            <div key={h.house} style={{ fontSize:11, color:'#EF9A9A', fontWeight:600 }}>🔴 {hName(h)}</div>
          ))}
        </div>
      </div>

      {/* Dasha-Transit detail — English only (hardcoded template string) */}
      {dtc?.summary && !isTamil && (
        <div style={{ borderTop:'1px solid rgba(255,255,255,0.1)', paddingTop:10, fontSize:11, color:'rgba(255,255,255,0.55)', lineHeight:1.6 }}>
          {dtc.summary}
        </div>
      )}
    </div>
  )
}

// ── Main ───────────────────────────────────────────────────────────────────
function todayISO() {
  return new Date().toISOString().split('T')[0]
}

export default function ForecastPanel({ chart, gender = 'male', showDatePicker = false }) {
  const [transitDate,  setTransitDate]  = useState(todayISO)
  const [scores,         setScores]         = useState(null)
  const [scoresLoading,  setScoresLoading]  = useState(false)
  const [scoresError,    setScoresError]    = useState('')
  const [selectedHouse,  setSelectedHouse]  = useState(null)
  const [insightLoading, setInsightLoading] = useState(false)
  const [insightError,   setInsightError]   = useState('')
  const [insightCache,   setInsightCache]   = useState({})
  const [dailyReading,   setDailyReading]   = useState(null)
  const [readingLoading, setReadingLoading] = useState(false)
  const [language,       setLanguage]       = useState('english')

  const insightKey = (houseNum) => `${houseNum}:${transitDate}:${language}`

  // Load scores + daily reading when chart or selected date changes
  useEffect(() => {
    if (!chart) return
    setScoresLoading(true)
    setReadingLoading(true)
    setScoresError('')
    setSelectedHouse(null)
    setInsightCache({})
    const body = { natal_chart: chart, transit_date: transitDate }
    Promise.all([
      api.post('/forecast/scores', body),
      api.post('/forecast/daily-reading', { ...body, gender, language }),
    ]).then(([scoresRes, readingRes]) => {
      setScores(scoresRes.data)
      setDailyReading(readingRes.data)
    }).catch(err => {
      setScoresError(err.response?.data?.detail || 'Could not load forecast.')
      setScores(null)
      setDailyReading(null)
    }).finally(() => {
      setScoresLoading(false)
      setReadingLoading(false)
    })
  }, [chart, transitDate, gender, language])

  const handleLanguageChange = (lang) => {
    setLanguage(lang)
  }

  const handleTagClick = async (houseNum) => {
    if (selectedHouse === houseNum) { setSelectedHouse(null); return }
    setSelectedHouse(houseNum)
    setInsightError('')
    const key = insightKey(houseNum)
    if (insightCache[key]) return

    setInsightLoading(true)
    try {
      const res = await api.post('/forecast/house', {
        natal_chart: chart,
        house_num:   houseNum,
        gender,
        language,
        transit_date: transitDate,
      })
      setInsightCache(prev => ({ ...prev, [key]: res.data.insight || '' }))
    } catch (err) {
      setInsightError(err.response?.data?.detail || 'Could not load AI insight.')
    } finally {
      setInsightLoading(false)
    }
  }

  const tx      = t(language)
  const isTamil = language === 'tamil'
  const isToday = transitDate === todayISO()

  if (scoresLoading) return (
    <div style={{ textAlign:'center', padding:'48px 0', color:'var(--orange)' }}>
      <div style={{ fontSize:36, marginBottom:12 }}>🔮</div>
      <div style={{ fontSize:14, fontWeight:600, color:'var(--text-secondary)' }}>{tx.calculating}</div>
    </div>
  )

  if (scoresError) return (
    <div style={{ color:'var(--error-text)', background:'var(--error-bg)', border:'1px solid var(--error-border)', borderRadius:12, padding:'16px 20px', fontSize:14 }}>
      ⚠️ {scoresError}
    </div>
  )

  if (!scores) return null

  const oh     = scores.overall_health || {}
  const houses = scores.houses || {}

  return (
    <div>
      {/* Date picker */}
      {showDatePicker && (
        <div style={{
          background:'var(--card-bg)', border:'1px solid var(--card-border)',
          borderRadius:12, padding:'12px 14px', marginBottom:16,
          boxShadow:'var(--card-shadow)',
        }}>
          <div style={{ display:'flex', flexWrap:'wrap', alignItems:'center', gap:10 }}>
            <label style={{ fontSize:12, fontWeight:700, color:'var(--text-secondary)', flex:'1 1 120px' }}>
              📅 {tx.forecastDate}
            </label>
            <input
              type="date"
              value={transitDate}
              min="2020-01-01"
              max="2035-12-31"
              onChange={e => setTransitDate(e.target.value)}
              style={{
                flex:'1 1 160px', height:42, padding:'0 12px', fontSize:16,
                borderRadius:8, border:'1px solid var(--input-border)',
                background:'var(--input-bg)', color:'var(--input-text)',
              }}
            />
            {!isToday && (
              <button
                type="button"
                onClick={() => setTransitDate(todayISO())}
                style={{
                  padding:'8px 12px', borderRadius:8, border:'1px solid var(--chip-border)',
                  background:'var(--chip-bg)', color:'var(--text-secondary)',
                  fontSize:12, fontWeight:600, cursor:'pointer',
                }}
              >
                {tx.today}
              </button>
            )}
          </div>
          <p style={{ fontSize:11, color:'var(--text-muted)', margin:'8px 0 0' }}>
            {tx.forecastDateHint}
          </p>
        </div>
      )}

      {/* Daily Reading Card */}
      {readingLoading && !dailyReading && (
        <div style={{ background:'var(--daily-card-bg)', borderRadius:16, padding:'18px 20px', marginBottom:20, color:'rgba(255,255,255,0.5)', fontSize:13 }}>
          <span style={{ color:'var(--orange)' }}>✦</span> {tx.generatingReading}
        </div>
      )}
      {dailyReading && (
        <DailyReadingCard
          reading={dailyReading.reading}
          dtc={dailyReading.dasha_transit}
          overall={dailyReading.overall_health}
          topHouses={dailyReading.top_houses}
          challengingHouses={dailyReading.challenging_houses}
          language={language}
        />
      )}
      {!dailyReading && !readingLoading && (
        <div style={{ background:'var(--daily-card-bg)', borderRadius:16, padding:'16px 20px', marginBottom:20, display:'flex', alignItems:'center', gap:16, flexWrap:'wrap' }}>
          <div style={{ textAlign:'center', minWidth:60 }}>
            <div style={{ fontSize:30, fontWeight:800, color:'var(--orange)', lineHeight:1 }}>{oh.average_score}</div>
            <div style={{ fontSize:10, color:'rgba(255,255,255,0.45)', textTransform:'uppercase' }}>/100</div>
          </div>
          <div style={{ flex:1 }}>
            <div style={{ fontSize:14, fontWeight:700, color:'#FFF', marginBottom:6 }}>
              {oh.rag?.emoji} {tx.overallHealth} — {tx.ragLabel[oh.rag?.status] || ''}
            </div>
            <div style={{ display:'flex', gap:12, fontSize:12, flexWrap:'wrap' }}>
              <span style={{ color:'#81C784' }}>🟢 {oh.green_count} {tx.favourable}</span>
              <span style={{ color:'#FFB74D' }}>🟡 {oh.amber_count} {tx.mixed}</span>
              <span style={{ color:'#EF9A9A' }}>🔴 {oh.red_count} {tx.challenging}</span>
            </div>
          </div>
        </div>
      )}

      {/* Language toggle + instruction row */}
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:12, flexWrap:'wrap', gap:8 }}>
        <p style={{ fontSize:12, color:'var(--text-muted)', margin:0 }}>{tx.tapInstruction}</p>
        <LanguageToggle language={language} onChange={handleLanguageChange} />
      </div>

      {/* 12 tags: responsive grid */}
      <div className="forecast-tag-grid" style={{ marginBottom:8 }}>
        {Object.values(houses).map(h => {
          const status   = h.rag?.status || 'AMBER'
          const rc       = RAG[status] || RAG.AMBER
          const isActive = selectedHouse === h.house_num
          const loaded   = !!insightCache[insightKey(h.house_num)]
          return (
            <button
              key={h.house_num}
              onClick={() => handleTagClick(h.house_num)}
              style={{
                background:   isActive ? rc.badge : 'var(--card-bg)',
                border:       `2px solid ${isActive ? rc.badge : rc.border}`,
                borderRadius: 12,
                padding:      '10px 6px',
                cursor:       'pointer',
                textAlign:    'center',
                transition:   'all 0.18s',
                transform:    isActive ? 'scale(1.04)' : 'scale(1)',
                boxShadow:    isActive ? `0 4px 12px ${rc.badge}55` : 'var(--card-shadow)',
                position:     'relative',
              }}
            >
              {/* loaded indicator */}
              {loaded && !isActive && (
                <span style={{
                  position:'absolute', top:4, right:6,
                  width:6, height:6, borderRadius:'50%',
                  background: rc.badge, display:'block',
                }} />
              )}
              <div style={{ fontSize:22, lineHeight:1, marginBottom:4 }}>{HOUSE_ICONS[h.house_num]}</div>
              <div style={{
                fontSize:10, fontWeight:700,
                color: isActive ? '#FFF' : 'var(--text-secondary)',
                textTransform:'uppercase', letterSpacing:'0.03em',
                lineHeight:1.3, marginBottom:3,
              }}>
                H{h.house_num}<br/>
                {isTamil
                  ? (HOUSE_TAMIL[h.house_num]?.name?.split(' & ')[0] || h.name.split(' & ')[0])
                  : h.name.split(' & ')[0].split(' ')[0]
                }
              </div>
              <div style={{ fontSize:12, fontWeight:800, color: isActive ? '#FFF' : rc.badge }}>
                {h.rag?.emoji} {h.score}
              </div>
            </button>
          )
        })}
      </div>

      {/* Detail card */}
      {selectedHouse && houses[selectedHouse] && (
        <HouseDetailCard
          houseData={houses[selectedHouse]}
          insight={insightCache[insightKey(selectedHouse)] || ''}
          insightLoading={insightLoading && !insightCache[insightKey(selectedHouse)]}
          insightError={insightError}
          language={language}
        />
      )}

      <div style={{ marginTop:20, textAlign:'center', fontSize:11, color:'var(--text-muted)' }}>
        {tx.footer(scores.lagna_en, scores.transit_date)}
      </div>
    </div>
  )
}

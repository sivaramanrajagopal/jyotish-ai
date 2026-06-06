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

const RAG = {
  GREEN: { bg:'#E8F5E9', border:'#27ae60', text:'#1B5E20', badge:'#27ae60', label:'Favourable' },
  AMBER: { bg:'#FFF8E1', border:'#f39c12', text:'#E65100', badge:'#f39c12', label:'Mixed' },
  RED:   { bg:'#FFEBEE', border:'#e74c3c', text:'#B71C1C', badge:'#e74c3c', label:'Challenging' },
}

function ScoreBar({ score, status }) {
  const colour = RAG[status]?.badge || '#999'
  return (
    <div style={{ marginTop:8 }}>
      <div style={{ display:'flex', justifyContent:'space-between', fontSize:11, color:'#888', marginBottom:3 }}>
        <span>Strength Score</span>
        <span style={{ fontWeight:700, color:colour }}>{score}/100</span>
      </div>
      <div style={{ background:'#EEE', borderRadius:6, height:8, overflow:'hidden' }}>
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
    return <p style={{ color:'#333', lineHeight:1.7, fontSize:14, margin:0 }}>{text}</p>
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
            background: i === 2 ? '#FFF8F0' : '#F0FFF4',
            border:`1px solid ${i === 2 ? '#FFD580' : '#B2DFDB'}`,
            borderRadius:8, padding:'10px 12px',
          }}>
            <div style={{ fontWeight:700, color:'#232F3E', fontSize:13, marginBottom:4 }}>
              {icons[i]} {title}
            </div>
            {body && <p style={{ color:'#444', fontSize:13, lineHeight:1.6, margin:0 }}>{body}</p>}
          </div>
        )
      })}
    </div>
  )
}

function HouseDetailCard({ houseData, insight, insightLoading, insightError }) {
  if (!houseData) return null
  const status = houseData.rag?.status || 'AMBER'
  const rc     = RAG[status] || RAG.AMBER

  return (
    <div style={{
      background:rc.bg, border:`2px solid ${rc.border}`,
      borderRadius:16, padding:'20px', marginTop:16,
      boxShadow:'0 4px 16px rgba(0,0,0,0.08)',
    }}>
      {/* Header */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:12 }}>
        <div>
          <div style={{ fontSize:18, fontWeight:800, color:'#232F3E' }}>
            {HOUSE_ICONS[houseData.house_num]} House {houseData.house_num} — {houseData.name}
          </div>
          <div style={{ fontSize:13, color:'#666', marginTop:3 }}>{houseData.simple}</div>
        </div>
        <span style={{
          background:rc.badge, color:'#FFF',
          borderRadius:20, padding:'4px 12px',
          fontSize:12, fontWeight:700, whiteSpace:'nowrap', marginLeft:8,
        }}>
          {houseData.rag?.emoji} {rc.label}
        </span>
      </div>

      <ScoreBar score={houseData.score} status={status} />

      {/* Key facts grid */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(130px,1fr))', gap:8, margin:'14px 0' }}>
        {[
          { label:'House Lord',     value:`${houseData.lord} → H${houseData.lord_placed_house}` },
          { label:'Lord Dignity',   value:houseData.lord_dignity || '—' },
          { label:'Planets Here',   value:houseData.planets_in_house?.join(', ') || 'None' },
          { label:'Transit Activity', value:houseData.transit_planets?.join(', ') || 'None' },
        ].map(({ label, value }) => (
          <div key={label} style={{ background:'#FFF', borderRadius:8, padding:'8px 10px', border:'1px solid rgba(0,0,0,0.08)' }}>
            <div style={{ fontSize:10, color:'#999', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:2 }}>{label}</div>
            <div style={{ fontSize:13, fontWeight:600, color:'#232F3E' }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Theme chips */}
      <div style={{ display:'flex', flexWrap:'wrap', gap:6, marginBottom:14 }}>
        {houseData.themes?.map(t => (
          <span key={t} style={{
            background:'#FFF', border:`1px solid ${rc.border}`,
            borderRadius:12, padding:'3px 10px',
            fontSize:11, color:rc.text, fontWeight:500,
          }}>{t}</span>
        ))}
      </div>

      {/* AI insight section */}
      <div style={{ borderTop:`1px solid ${rc.border}`, paddingTop:14 }}>
        <div style={{ fontSize:11, fontWeight:700, color:'#888', textTransform:'uppercase', letterSpacing:'0.07em', marginBottom:10 }}>
          🤖 AI Forecast
        </div>
        {insightLoading && (
          <div style={{ color:'#FF9900', fontSize:13, display:'flex', gap:6, alignItems:'center' }}>
            <span style={{ animation:'pulse 1s infinite' }}>✦</span> Generating personalised insight…
          </div>
        )}
        {insightError && <div style={{ color:'#D13212', fontSize:13 }}>⚠️ {insightError}</div>}
        {insight && !insightLoading && <InsightText text={insight} />}
      </div>
    </div>
  )
}

// ── Daily Reading Card ────────────────────────────────────────────────────
function DailyReadingCard({ reading, dtc, overall, topHouses, challengingHouses }) {
  if (!reading) return null
  const dtcRag = dtc?.rag?.status || 'AMBER'
  const rc     = RAG[dtcRag] || RAG.AMBER

  return (
    <div style={{
      background: '#232F3E', borderRadius: 16, padding: '18px 20px',
      marginBottom: 20, boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
    }}>
      {/* Header row */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:14 }}>
        <div style={{ fontSize:14, fontWeight:800, color:'#FF9900' }}>
          🔮 Your Daily Reading
        </div>
        <span style={{
          background: rc.badge, color:'#FFF', borderRadius:20,
          padding:'3px 10px', fontSize:11, fontWeight:700,
        }}>
          Dasha-Transit: {rc.label}
        </span>
      </div>

      {/* Reading text */}
      <p style={{ color:'rgba(255,255,255,0.88)', fontSize:13, lineHeight:1.75, margin:'0 0 14px' }}>
        {reading}
      </p>

      {/* 3-column summary */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:8, marginBottom:14 }}>
        <div style={{ background:'rgba(255,255,255,0.07)', borderRadius:8, padding:'8px 10px' }}>
          <div style={{ fontSize:9, color:'rgba(255,255,255,0.4)', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:4 }}>Transit Health</div>
          <div style={{ fontSize:16, fontWeight:800, color:'#FF9900' }}>{overall?.average_score}/100</div>
          <div style={{ fontSize:10, color:'rgba(255,255,255,0.5)' }}>{overall?.rag?.label}</div>
        </div>
        <div style={{ background:'rgba(255,255,255,0.07)', borderRadius:8, padding:'8px 10px' }}>
          <div style={{ fontSize:9, color:'rgba(255,255,255,0.4)', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:4 }}>Strongest Today</div>
          {(topHouses||[]).slice(0,2).map(h => (
            <div key={h.house} style={{ fontSize:11, color:'#81C784', fontWeight:600 }}>
              🟢 {h.name.split(' ')[0]}
            </div>
          ))}
        </div>
        <div style={{ background:'rgba(255,255,255,0.07)', borderRadius:8, padding:'8px 10px' }}>
          <div style={{ fontSize:9, color:'rgba(255,255,255,0.4)', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:4 }}>Needs Care</div>
          {(challengingHouses||[]).slice(0,2).map(h => (
            <div key={h.house} style={{ fontSize:11, color:'#EF9A9A', fontWeight:600 }}>
              🔴 {h.name.split(' ')[0]}
            </div>
          ))}
        </div>
      </div>

      {/* Dasha-Transit correlation detail */}
      {dtc?.summary && (
        <div style={{
          borderTop:'1px solid rgba(255,255,255,0.1)', paddingTop:10,
          fontSize:11, color:'rgba(255,255,255,0.55)', lineHeight:1.6,
        }}>
          {dtc.summary}
        </div>
      )}
    </div>
  )
}

// ── Main ───────────────────────────────────────────────────────────────────
export default function ForecastPanel({ chart, gender = 'male' }) {
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

  // Load scores + daily reading on mount (scores cached, reading language-aware)
  useEffect(() => {
    if (!chart) return
    setScoresLoading(true)
    setReadingLoading(true)
    setScoresError('')
    Promise.all([
      api.post('/forecast/scores', { natal_chart: chart }),
      api.post('/forecast/daily-reading', { natal_chart: chart, gender, language }),
    ]).then(([scoresRes, readingRes]) => {
      setScores(scoresRes.data)
      setDailyReading(readingRes.data)
    }).catch(err => {
      setScoresError(err.response?.data?.detail || 'Could not load forecast.')
    }).finally(() => {
      setScoresLoading(false)
      setReadingLoading(false)
    })
  }, [chart]) // scores load once; language changes handled below

  // Re-fetch daily reading when language changes (scores are language-agnostic)
  const handleLanguageChange = async (lang) => {
    setLanguage(lang)
    setInsightCache({})       // clear insight cache — needs re-generation in new language
    setDailyReading(null)
    setReadingLoading(true)
    try {
      const res = await api.post('/forecast/daily-reading', {
        natal_chart: chart, gender, language: lang,
      })
      setDailyReading(res.data)
    } catch (_) {}
    finally { setReadingLoading(false) }
  }

  const handleTagClick = async (houseNum) => {
    if (selectedHouse === houseNum) { setSelectedHouse(null); return }
    setSelectedHouse(houseNum)
    setInsightError('')
    if (insightCache[houseNum]) return   // already cached

    setInsightLoading(true)
    try {
      const res = await api.post('/forecast/house', {
        natal_chart: chart,
        house_num:   houseNum,
        gender,
        language,
      })
      setInsightCache(prev => ({ ...prev, [houseNum]: res.data.insight || '' }))
    } catch (err) {
      setInsightError(err.response?.data?.detail || 'Could not load AI insight.')
    } finally {
      setInsightLoading(false)
    }
  }

  if (scoresLoading) return (
    <div style={{ textAlign:'center', padding:'48px 0', color:'#FF9900' }}>
      <div style={{ fontSize:36, marginBottom:12 }}>🔮</div>
      <div style={{ fontSize:14, fontWeight:600, color:'#555' }}>
        Calculating your Gochara scores and daily reading…
      </div>
    </div>
  )

  if (scoresError) return (
    <div style={{ color:'#D13212', background:'#FFF5F3', border:'1px solid #FDBDAD', borderRadius:12, padding:'16px 20px', fontSize:14 }}>
      ⚠️ {scoresError}
    </div>
  )

  if (!scores) return null

  const oh     = scores.overall_health || {}
  const houses = scores.houses || {}

  return (
    <div>
      {/* Daily Reading Card (replaces plain banner) */}
      {readingLoading && !dailyReading && (
        <div style={{
          background:'#232F3E', borderRadius:16, padding:'18px 20px',
          marginBottom:20, color:'rgba(255,255,255,0.5)', fontSize:13,
        }}>
          <span style={{ color:'#FF9900' }}>✦</span> Generating your daily reading…
        </div>
      )}
      {dailyReading && (
        <DailyReadingCard
          reading={dailyReading.reading}
          dtc={dailyReading.dasha_transit}
          overall={dailyReading.overall_health}
          topHouses={dailyReading.top_houses}
          challengingHouses={dailyReading.challenging_houses}
        />
      )}
      {!dailyReading && !readingLoading && (
        <div style={{
          background:'#232F3E', borderRadius:16, padding:'16px 20px',
          marginBottom:20, display:'flex', alignItems:'center', gap:16,
        }}>
          <div style={{ textAlign:'center', minWidth:60 }}>
            <div style={{ fontSize:30, fontWeight:800, color:'#FF9900', lineHeight:1 }}>{oh.average_score}</div>
            <div style={{ fontSize:10, color:'rgba(255,255,255,0.45)', textTransform:'uppercase' }}>/100</div>
          </div>
          <div style={{ flex:1 }}>
            <div style={{ fontSize:14, fontWeight:700, color:'#FFF', marginBottom:6 }}>
              {oh.rag?.emoji} Overall Transit Health — {oh.rag?.label}
            </div>
            <div style={{ display:'flex', gap:12, fontSize:12, flexWrap:'wrap' }}>
              <span style={{ color:'#81C784' }}>🟢 {oh.green_count} Favourable</span>
              <span style={{ color:'#FFB74D' }}>🟡 {oh.amber_count} Mixed</span>
              <span style={{ color:'#EF9A9A' }}>🔴 {oh.red_count} Challenging</span>
            </div>
          </div>
        </div>
      )}

      {/* Language toggle + instruction row */}
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:12 }}>
        <p style={{ fontSize:12, color:'#888', margin:0 }}>
          Tap any life area to see your forecast
        </p>
        <LanguageToggle language={language} onChange={handleLanguageChange} />
      </div>

      {/* 12 tags: 3 columns on mobile, 4 on desktop */}
      <div style={{
        display:'grid',
        gridTemplateColumns:'repeat(3, 1fr)',
        gap:10, marginBottom:8,
      }}>
        {Object.values(houses).map(h => {
          const status   = h.rag?.status || 'AMBER'
          const rc       = RAG[status] || RAG.AMBER
          const isActive = selectedHouse === h.house_num
          const loaded   = !!insightCache[h.house_num]
          return (
            <button
              key={h.house_num}
              onClick={() => handleTagClick(h.house_num)}
              style={{
                background:   isActive ? rc.badge : '#FFF',
                border:       `2px solid ${isActive ? rc.badge : rc.border}`,
                borderRadius: 12,
                padding:      '10px 6px',
                cursor:       'pointer',
                textAlign:    'center',
                transition:   'all 0.18s',
                transform:    isActive ? 'scale(1.04)' : 'scale(1)',
                boxShadow:    isActive ? `0 4px 12px ${rc.badge}55` : '0 1px 4px rgba(0,0,0,0.06)',
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
                color: isActive ? '#FFF' : '#444',
                textTransform:'uppercase', letterSpacing:'0.03em',
                lineHeight:1.3, marginBottom:3,
              }}>
                H{h.house_num}<br/>{h.name.split(' & ')[0].split(' ')[0]}
              </div>
              <div style={{
                fontSize:12, fontWeight:800,
                color: isActive ? '#FFF' : rc.badge,
              }}>
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
          insight={insightCache[selectedHouse] || ''}
          insightLoading={insightLoading && !insightCache[selectedHouse]}
          insightError={insightError}
        />
      )}

      <div style={{ marginTop:20, textAlign:'center', fontSize:11, color:'#AAA' }}>
        Lagna: {scores.lagna_en} · {scores.transit_date} · Lahiri Ayanamsa
      </div>
    </div>
  )
}

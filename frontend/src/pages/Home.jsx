/**
 * Home.jsx — Jyotish AI
 * Tabbed layout: Home · My Chart · Panchangam · Ask AI · Forecast
 * Desktop: top tab bar | Mobile: bottom nav bar
 */

import { useState, useEffect } from 'react'
import api from '../api/client'

// ── Render keep-alive: ping backend every 9 min to prevent 50s cold start ────
const PING_INTERVAL_MS = 9 * 60 * 1000  // 9 minutes
function useKeepAlive() {
  useEffect(() => {
    const ping = () => api.get('/ping').catch(() => {})
    ping() // immediate ping on mount
    const id = setInterval(ping, PING_INTERVAL_MS)
    return () => clearInterval(id)
  }, [])
}
import SouthIndianChart from '../components/SouthIndianChart'
import PlanetTable from '../components/PlanetTable'
import ForecastPanel from '../components/ForecastPanel'
import ChatPanel from '../components/ChatPanel'
import PersonalPanchangamCard from '../components/PersonalPanchangamCard'
import PanchangamTab from '../components/PanchangamTab'
// GaneshaIcon replaced by inline ॐ symbol in GaneshaBanner

// ── Shared colours — Amazon light + saffron ───────────────────────────────────
const G = {
  bg:      '#FFF8F0',
  card:    { background: '#FFFFFF', border: '1px solid #E8DDD0', boxShadow: '0 2px 8px rgba(0,0,0,0.07)' },
  input:   { background: '#FFFFFF', border: '1px solid #C8BAA8', color: '#1A1A1A' },
  gold:    '#FF9900',
  cream:   '#FFFFFF',
  sub:     '#666666',
  label:   '#444444',
  btn:     { background: '#FF9900', color: '#232F3E', fontWeight: '700' },
  nav:     { background: '#232F3E' },
  orange:  '#FF9900',
  dark:    '#232F3E',
}

// ── Tab definitions ───────────────────────────────────────────────────────────
const TABS = [
  { key: 'home',       label: 'Home',       icon: '🏠' },
  { key: 'chart',      label: 'My Chart',   icon: '⭐' },
  { key: 'panchangam', label: 'Panchangam', icon: '🗓' },
  { key: 'chat',       label: 'Ask AI',     icon: '🔮' },
  { key: 'forecast',   label: 'Forecast',   icon: '📊' },
]

// ── "No chart yet" placeholder ────────────────────────────────────────────────
function NeedChart({ onGoHome }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
      <div className="text-5xl mb-4">🪷</div>
      <p className="text-base font-semibold mb-2" style={{ color: '#232F3E' }}>Your chart hasn't been calculated yet</p>
      <p className="text-sm mb-6" style={{ color: '#888' }}>Go to Home and enter your birth details first.</p>
      <button
        onClick={onGoHome}
        className="font-bold px-6 py-2.5 rounded-lg text-sm"
        style={G.btn}
      >
        Go to Home →
      </button>
    </div>
  )
}

// ── Om symbol + mantra banner ─────────────────────────────────────────────────
function GaneshaBanner() {
  return (
    <div
      className="flex items-center justify-center gap-4 py-3 px-4"
      style={{ background: '#232F3E', borderBottom: '3px solid #FF9900' }}
    >
      {/* Om symbol */}
      <div style={{
        fontSize: '44px',
        lineHeight: 1,
        color: '#FF9900',
        fontFamily: 'serif',
        filter: 'drop-shadow(0 0 8px rgba(255,153,0,0.6))',
        userSelect: 'none',
      }}>
        ॐ
      </div>
      <div className="text-left">
        <div className="text-lg font-bold" style={{ color: '#FF9900', letterSpacing: '0.08em' }}>
          ॐ महा गणपतये नमः
        </div>
        <div className="text-xs mt-0.5" style={{ color: 'rgba(255,255,255,0.55)' }}>
          Jyotish AI — Vedic Astrology • Om Maha Ganapathaye Namaha
        </div>
      </div>
    </div>
  )
}

// ── HOME TAB ──────────────────────────────────────────────────────────────────
function HomeTab({ form, setForm, onChartReady, loading, error }) {
  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  return (
    <div className="max-w-lg mx-auto px-4 py-10">
      {/* Hero */}
      <div className="text-center mb-10">
        <div className="text-5xl mb-4" style={{ filter: 'drop-shadow(0 0 8px rgba(255,153,0,0.4))' }}>🪷</div>
        <h1 className="text-4xl md:text-5xl font-bold mb-3" style={{ color: '#232F3E' }}>
          Jyotish <span style={{ color: '#FF9900' }}>AI</span>
        </h1>
        <p className="text-base max-w-sm mx-auto" style={{ color: '#666' }}>
          Classical Vedic astrology powered by AI — precise charts, daily forecasts, and cosmic guidance.
        </p>
      </div>

      {/* Birth form */}
      <div className="rounded-2xl p-6" style={G.card}>
        <h2 className="text-lg font-semibold mb-1" style={{ color: '#232F3E' }}>Get Your Free Natal Chart</h2>
        <p className="text-xs mb-5" style={{ color: '#888' }}>Enter your birth details below</p>
        <form onSubmit={onChartReady} className="space-y-4">

          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: '#444' }}>Full Name</label>
            <input
              name="name" value={form.name} onChange={handleChange}
              placeholder="Your name" required
              className="w-full rounded-lg px-4 py-2.5 text-sm focus:outline-none"
              style={{ ...G.input, '::placeholder': { color: '#aaa' } }}
            />
          </div>

          {/* Mobile: stack vertically; sm+: side by side */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: '#444' }}>Date of Birth</label>
              <input
                type="date" name="dob" value={form.dob} onChange={handleChange} required
                className="rounded-lg px-4 py-2.5 text-sm focus:outline-none"
                style={{ ...G.input, width: '100%', boxSizing: 'border-box', display: 'block' }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: '#444' }}>Time of Birth</label>
              <input
                type="time" name="tob" value={form.tob} onChange={handleChange} required
                className="rounded-lg px-4 py-2.5 text-sm focus:outline-none"
                style={{ ...G.input, width: '100%', boxSizing: 'border-box', display: 'block' }}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: '#444' }}>Place of Birth</label>
            <input
              name="place_of_birth" value={form.place_of_birth} onChange={handleChange}
              placeholder="City, Country (e.g. Chennai, India)" required
              className="w-full rounded-lg px-4 py-2.5 text-sm focus:outline-none"
              style={G.input}
            />
          </div>

          {error && (
            <div className="text-sm rounded-lg px-4 py-3"
              style={{ color: '#D13212', background: '#FFF5F3', border: '1px solid #FDBDAD' }}>
              {error}
            </div>
          )}

          <button
            type="submit" disabled={loading}
            className="w-full font-bold py-3 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed text-base"
            style={G.btn}
          >
            {loading ? 'Calculating chart…' : 'Calculate My Chart →'}
          </button>
        </form>
      </div>
    </div>
  )
}

// ── MY CHART TAB ──────────────────────────────────────────────────────────────
function MyChartTab({ chart, onGoHome }) {
  if (!chart) return <NeedChart onGoHome={onGoHome} />
  return (
    <div className="max-w-5xl mx-auto px-4 py-8">

      {/* Big 3 */}
      <div className="grid grid-cols-3 gap-3 mb-8">
        {[
          { label: 'Ascendant (Lagna)', value: chart.ascendant.sign,
            sub: `${chart.ascendant.nakshatra} P${chart.ascendant.pada}` },
          { label: 'Sun Sign', value: chart.planet_positions.Sun.sign,
            sub: chart.planet_positions.Sun.nakshatra },
          { label: 'Moon Sign', value: chart.planet_positions.Moon.sign,
            sub: chart.planet_positions.Moon.nakshatra },
        ].map(({ label, value, sub }) => (
          <div key={label} className="rounded-xl p-4 text-center"
            style={{ background: '#FFF8F0', border: '2px solid #FF9900', boxShadow: '0 2px 6px rgba(255,153,0,0.12)' }}>
            <div className="text-xs mb-1 font-medium" style={{ color: '#888' }}>{label}</div>
            <div className="text-lg font-bold" style={{ color: '#232F3E' }}>{value}</div>
            <div className="text-xs mt-0.5" style={{ color: '#999' }}>{sub}</div>
          </div>
        ))}
      </div>

      {/* D1 + D9 Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {[
          { title: 'D1 — Rasi Chart (Janma Kundali)',
            sub: `${chart.birth_data.dob} · ${chart.birth_data.tob}`,
            pos: chart.planet_positions, lagnaIdx: chart.ascendant.sign_index, nav: false },
          { title: 'D9 — Navamsa Chart',
            sub: `Lagna: ${chart.navamsa_ascendant?.sign}`,
            pos: chart.navamsa_positions, lagnaIdx: chart.navamsa_ascendant?.sign_index, nav: true },
        ].map(({ title, sub, pos, lagnaIdx, nav }) => (
          <div key={title} className="rounded-xl p-4"
            style={{ background: '#FFFFFF', border: '1px solid #E8DDD0', boxShadow: '0 2px 6px rgba(0,0,0,0.06)' }}>
            <h3 className="text-sm font-semibold mb-3 text-center uppercase tracking-wide"
              style={{ color: '#888' }}>{title}</h3>
            <SouthIndianChart title={nav ? 'D9' : 'D1'} subtitle={sub}
              planetPositions={pos} lagnaSignIndex={lagnaIdx} navamsa={nav} />
          </div>
        ))}
      </div>

      {/* Planet Table */}
      <div className="rounded-xl overflow-hidden mb-8"
        style={{ background: '#FFFFFF', border: '1px solid #E8DDD0', boxShadow: '0 2px 6px rgba(0,0,0,0.05)' }}>
        <div className="px-5 py-3" style={{ borderBottom: '1px solid #EEE', background: '#FFF8F0' }}>
          <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: '#444' }}>
            Planet Details — D1 Rasi
          </h3>
          <p className="text-xs mt-0.5" style={{ color: '#999' }}>
            Ayanamsa: {chart.ayanamsa} {chart.ayanamsa_value?.toFixed(4)}° &nbsp;·&nbsp; ★ Vargottama &nbsp;·&nbsp; ℞ Retrograde
          </p>
        </div>
        <PlanetTable planetPositions={chart.planet_positions}
          navamsaPositions={chart.navamsa_positions} ascendant={chart.ascendant} />
      </div>

      {/* Yogas */}
      {chart.yogas?.length > 0 && (
        <div className="rounded-xl p-5 mb-8"
          style={{ background: '#FFFBF0', border: '2px solid #FF9900', boxShadow: '0 2px 6px rgba(255,153,0,0.1)' }}>
          <h3 className="font-bold mb-3 text-sm uppercase tracking-wide" style={{ color: '#E47911' }}>
            ✦ Yogas Detected
          </h3>
          <div className="space-y-2">
            {chart.yogas.map((y, i) => (
              <div key={i} className="text-sm">
                <span className="font-semibold" style={{ color: '#232F3E' }}>{y.name}</span>
                <span className="ml-2" style={{ color: '#666' }}>— {y.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Personal Panchangam */}
      <PersonalPanchangamCard chart={chart} />
    </div>
  )
}

// ── MAIN COMPONENT ────────────────────────────────────────────────────────────
export default function Home() {
  useKeepAlive()  // ping backend every 9 min — keeps Render free tier warm

  const [activeTab, setActiveTab] = useState('home')
  const [form, setForm]   = useState({ name: '', dob: '', tob: '', place_of_birth: '' })
  const [chart, setChart] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  const handleSubmit = async e => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setChart(null)
    try {
      const { data } = await api.post('/natal-chart', form)
      setChart(data)
      setActiveTab('chart')          // auto-navigate to chart tab
    } catch (err) {
      const detail = err.response?.data?.detail
      // Pydantic v2 returns an array of {type, loc, msg, input} objects
      const msg = Array.isArray(detail)
        ? detail.map(e => `${e.loc?.slice(-1)[0] ?? 'field'}: ${e.msg}`).join(' · ')
        : (typeof detail === 'string' ? detail : 'Something went wrong. Please try again.')
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const goHome = () => setActiveTab('home')

  // ── Top tab bar (desktop) / content area ────────────────────────────────
  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ background: G.bg, color: '#1A1A1A' }}
    >
      {/* Ganesha banner — always visible */}
      <GaneshaBanner />

      {/* ── Desktop top tab bar (hidden on mobile) ── */}
      <nav
        className="hidden sm:flex border-b sticky top-0 z-30"
        style={{ background: '#FFFFFF', borderColor: '#E8DDD0', boxShadow: '0 2px 4px rgba(0,0,0,0.06)' }}
      >
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className="flex items-center gap-1.5 px-5 py-3 text-sm font-semibold transition-all relative"
            style={{
              color: activeTab === tab.key ? '#FF9900' : '#555',
              borderBottom: activeTab === tab.key ? '3px solid #FF9900' : '3px solid transparent',
            }}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
            {chart && ['chart','chat','forecast'].includes(tab.key) && activeTab !== tab.key && (
              <span
                className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full"
                style={{ background: '#FF9900' }}
              />
            )}
          </button>
        ))}
      </nav>

      {/* ── Tab content ── */}
      <main className="flex-1 pb-20 sm:pb-0">
        {activeTab === 'home' && (
          <HomeTab
            form={form} setForm={setForm}
            onChartReady={handleSubmit}
            loading={loading} error={error}
          />
        )}

        {activeTab === 'chart' && (
          <MyChartTab chart={chart} onGoHome={goHome} />
        )}

        {activeTab === 'panchangam' && (
          <PanchangamTab />
        )}

        {activeTab === 'chat' && (
          chart
            ? <div className="max-w-3xl mx-auto px-4 py-8">
                <ChatPanel chart={chart} placeOfBirth={form.place_of_birth} />
              </div>
            : <NeedChart onGoHome={goHome} />
        )}

        {activeTab === 'forecast' && (
          chart
            ? <div className="max-w-3xl mx-auto px-4 py-8">
                <ForecastPanel chart={chart} placeOfBirth={form.place_of_birth} />
              </div>
            : <NeedChart onGoHome={goHome} />
        )}
      </main>

      {/* ── Mobile bottom nav (visible only on mobile) ── */}
      <nav
        className="sm:hidden fixed bottom-0 left-0 right-0 z-30 flex"
        style={{
          background: '#FFFFFF',
          borderTop: '1px solid #E8DDD0',
          paddingBottom: 'env(safe-area-inset-bottom)',
          boxShadow: '0 -2px 8px rgba(0,0,0,0.08)',
        }}
      >
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className="flex-1 flex flex-col items-center justify-center py-2 gap-0.5 relative"
            style={{ color: activeTab === tab.key ? '#FF9900' : '#888' }}
          >
            <span style={{ fontSize: '18px', lineHeight: 1 }}>{tab.icon}</span>
            <span style={{ fontSize: '9px', fontWeight: 600, letterSpacing: '0.04em' }}>
              {tab.label}
            </span>
            {/* active pill */}
            {activeTab === tab.key && (
              <span
                className="absolute top-1 left-1/2 -translate-x-1/2 rounded-full"
                style={{ width: '20px', height: '3px', background: '#f59e0b' }}
              />
            )}
            {/* dot when chart available */}
            {chart && ['chart','chat','forecast'].includes(tab.key) && activeTab !== tab.key && (
              <span
                className="absolute top-2 right-3 w-1.5 h-1.5 rounded-full"
                style={{ background: '#f59e0b' }}
              />
            )}
          </button>
        ))}
      </nav>
    </div>
  )
}

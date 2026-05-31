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
import GaneshaIcon from '../components/GaneshaIcon'

// ── Shared colours ────────────────────────────────────────────────────────────
const G = {
  bg:      'linear-gradient(180deg, #1a0e00 0%, #120c00 40%, #0e0900 100%)',
  card:    { background: 'rgba(251,191,36,0.06)', border: '1px solid rgba(251,191,36,0.18)' },
  input:   { background: 'rgba(251,191,36,0.07)', border: '1px solid rgba(251,191,36,0.2)', color: '#fef3c7' },
  gold:    '#fbbf24',
  cream:   '#fef3c7',
  sub:     'rgba(254,243,199,0.5)',
  label:   'rgba(251,191,36,0.5)',
  btn:     { background: 'linear-gradient(135deg,#d97706,#f59e0b)', color: '#1a0e00' },
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
      <div className="text-4xl mb-4" style={{ filter: 'drop-shadow(0 0 10px rgba(251,191,36,0.4))' }}>✦</div>
      <p className="text-base font-semibold mb-2" style={{ color: '#fef3c7' }}>Your chart hasn't been calculated yet</p>
      <p className="text-sm mb-6" style={{ color: 'rgba(254,243,199,0.45)' }}>Go to Home and enter your birth details first.</p>
      <button
        onClick={onGoHome}
        className="font-semibold px-6 py-2.5 rounded-xl text-sm"
        style={G.btn}
      >
        Go to Home ✦
      </button>
    </div>
  )
}

// ── Ganesha + mantra banner (shared across all tabs at top) ───────────────────
function GaneshaBanner() {
  return (
    <div
      className="text-center py-3 flex items-center justify-center gap-3 border-b"
      style={{ borderColor: 'rgba(251,191,36,0.15)', background: 'rgba(251,191,36,0.05)' }}
    >
      <GaneshaIcon size={32} glow />
      <div>
        <div className="text-xs font-bold tracking-widest" style={{ color: '#fbbf24', letterSpacing: '0.15em' }}>
          ॐ महा गणपतये नमः
        </div>
        <div className="text-xs hidden sm:block" style={{ color: 'rgba(251,191,36,0.4)' }}>
          Om Maha Ganapathaye Namaha
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
        <div className="text-5xl mb-4" style={{ filter: 'drop-shadow(0 0 12px rgba(251,191,36,0.5))' }}>✦</div>
        <h1 className="text-4xl md:text-5xl font-bold mb-3" style={{ color: '#fef3c7' }}>
          Jyotish <span style={{ color: '#fbbf24' }}>AI</span>
        </h1>
        <p className="text-base max-w-sm mx-auto" style={{ color: 'rgba(254,243,199,0.55)' }}>
          Classical Vedic astrology powered by AI — precise charts, daily forecasts, and cosmic guidance.
        </p>
      </div>

      {/* Birth form */}
      <div className="rounded-2xl p-6" style={G.card}>
        <h2 className="text-lg font-semibold mb-5" style={{ color: '#fef3c7' }}>Get Your Free Natal Chart</h2>
        <form onSubmit={onChartReady} className="space-y-4">

          <div>
            <label className="block text-sm mb-1" style={{ color: G.sub }}>Full Name</label>
            <input
              name="name" value={form.name} onChange={handleChange}
              placeholder="Your name" required
              className="w-full rounded-xl px-4 py-2.5 text-sm focus:outline-none placeholder-amber-100/20"
              style={G.input}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm mb-1" style={{ color: G.sub }}>Date of Birth</label>
              <input
                type="date" name="dob" value={form.dob} onChange={handleChange} required
                className="w-full rounded-xl px-4 py-2.5 text-sm focus:outline-none"
                style={G.input}
              />
            </div>
            <div>
              <label className="block text-sm mb-1" style={{ color: G.sub }}>Time of Birth</label>
              <input
                type="time" name="tob" value={form.tob} onChange={handleChange} required
                className="w-full rounded-xl px-4 py-2.5 text-sm focus:outline-none"
                style={G.input}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm mb-1" style={{ color: G.sub }}>Place of Birth</label>
            <input
              name="place_of_birth" value={form.place_of_birth} onChange={handleChange}
              placeholder="City, Country" required
              className="w-full rounded-xl px-4 py-2.5 text-sm focus:outline-none placeholder-amber-100/20"
              style={G.input}
            />
          </div>

          {error && (
            <div className="text-sm rounded-xl px-4 py-3"
              style={{ color: '#fca5a5', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)' }}>
              {error}
            </div>
          )}

          <button
            type="submit" disabled={loading}
            className="w-full font-semibold py-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            style={G.btn}
          >
            {loading ? 'Calculating chart…' : 'Calculate My Chart ✦'}
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
            style={{ background: 'rgba(251,191,36,0.1)', border: '1px solid rgba(251,191,36,0.3)' }}>
            <div className="text-xs mb-1" style={{ color: 'rgba(251,191,36,0.6)' }}>{label}</div>
            <div className="text-lg font-bold" style={{ color: '#fef3c7' }}>{value}</div>
            <div className="text-xs mt-0.5" style={{ color: 'rgba(254,243,199,0.4)' }}>{sub}</div>
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
            style={{ background: 'rgba(251,191,36,0.05)', border: '1px solid rgba(251,191,36,0.2)' }}>
            <h3 className="text-sm font-semibold mb-3 text-center uppercase tracking-wide"
              style={{ color: 'rgba(254,243,199,0.6)' }}>{title}</h3>
            <SouthIndianChart title={nav ? 'D9' : 'D1'} subtitle={sub}
              planetPositions={pos} lagnaSignIndex={lagnaIdx} navamsa={nav} />
          </div>
        ))}
      </div>

      {/* Planet Table */}
      <div className="rounded-xl overflow-hidden mb-8"
        style={{ background: 'rgba(251,191,36,0.04)', border: '1px solid rgba(251,191,36,0.18)' }}>
        <div className="px-5 py-3" style={{ borderBottom: '1px solid rgba(251,191,36,0.15)' }}>
          <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: 'rgba(254,243,199,0.6)' }}>
            Planet Details — D1 Rasi
          </h3>
          <p className="text-xs mt-0.5" style={{ color: 'rgba(254,243,199,0.3)' }}>
            Ayanamsa: {chart.ayanamsa} {chart.ayanamsa_value?.toFixed(4)}° &nbsp;·&nbsp; ★ Vargottama &nbsp;·&nbsp; ℞ Retrograde
          </p>
        </div>
        <PlanetTable planetPositions={chart.planet_positions}
          navamsaPositions={chart.navamsa_positions} ascendant={chart.ascendant} />
      </div>

      {/* Yogas */}
      {chart.yogas?.length > 0 && (
        <div className="rounded-xl p-5 mb-8"
          style={{ background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.35)' }}>
          <h3 className="font-semibold mb-3 text-sm uppercase tracking-wide" style={{ color: '#fbbf24' }}>
            ✦ Yogas Detected
          </h3>
          <div className="space-y-2">
            {chart.yogas.map((y, i) => (
              <div key={i} className="text-sm">
                <span className="font-semibold" style={{ color: '#fcd34d' }}>{y.name}</span>
                <span className="ml-2" style={{ color: 'rgba(254,243,199,0.5)' }}>— {y.description}</span>
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
      className="min-h-screen flex flex-col text-white"
      style={{ background: G.bg }}
    >
      {/* Ganesha banner — always visible */}
      <GaneshaBanner />

      {/* ── Desktop top tab bar (hidden on mobile) ── */}
      <nav
        className="hidden sm:flex border-b sticky top-0 z-30"
        style={{
          background: 'rgba(18,12,0,0.95)',
          borderColor: 'rgba(251,191,36,0.15)',
          backdropFilter: 'blur(12px)',
        }}
      >
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className="flex items-center gap-1.5 px-5 py-3 text-sm font-semibold transition-all relative"
            style={{
              color: activeTab === tab.key ? '#fbbf24' : 'rgba(254,243,199,0.4)',
              borderBottom: activeTab === tab.key ? '2px solid #f59e0b' : '2px solid transparent',
            }}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
            {/* dot indicator when chart loaded and on relevant tabs */}
            {chart && ['chart','chat','forecast'].includes(tab.key) && activeTab !== tab.key && (
              <span
                className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full"
                style={{ background: '#f59e0b' }}
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
          background: 'rgba(18,12,0,0.97)',
          borderTop: '1px solid rgba(251,191,36,0.2)',
          paddingBottom: 'env(safe-area-inset-bottom)',
          backdropFilter: 'blur(16px)',
        }}
      >
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className="flex-1 flex flex-col items-center justify-center py-2 gap-0.5 relative"
            style={{ color: activeTab === tab.key ? '#fbbf24' : 'rgba(254,243,199,0.35)' }}
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

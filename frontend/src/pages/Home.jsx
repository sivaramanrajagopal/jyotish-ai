/**
 * Home.jsx — Parashara Jyotish
 * Tabbed layout: Home · My Chart · Panchangam · Ask AI · Forecast
 */

import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { APP_NAME, APP_SHORT, APP_TAGLINE, APP_FEATURE_LINKS } from '../constants/brand'
import GaneshaIllustration from '../components/GaneshaIllustration'
import CosmosStrip from '../components/CosmosStrip'
import SouthIndianChart from '../components/SouthIndianChart'
import PlanetTable from '../components/PlanetTable'
import ForecastPanel from '../components/ForecastPanel'
import ChatPanel from '../components/ChatPanel'
import PersonalPanchangamCard from '../components/PersonalPanchangamCard'
import PanchangamTab from '../components/PanchangamTab'
import AshtakavargaPanel from '../components/AshtakavargaPanel'
import DashaRoadmap from '../components/DashaRoadmap'
import DashaSummaryCard from '../components/DashaSummaryCard'
import DarkModeToggle, { applyStoredTheme } from '../components/DarkModeToggle'
import AuthPanel from '../components/AuthPanel'
import NotificationSettings from '../components/NotificationSettings'
import { useAuth } from '../hooks/useAuth'
import { startNotificationWatcher } from '../lib/notifications'

// Apply persisted theme immediately on load
applyStoredTheme()

// ── localStorage helpers ───────────────────────────────────────────────────
const LS_KEY = 'jyotish-chart-v1'

function saveToStorage(form, chart) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify({
      form, chart, savedAt: new Date().toISOString()
    }))
  } catch {}
}

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    // Expire after 30 days
    const age = Date.now() - new Date(parsed.savedAt).getTime()
    if (age > 30 * 24 * 60 * 60 * 1000) { localStorage.removeItem(LS_KEY); return null }
    return parsed
  } catch { return null }
}

// ── Render keep-alive ──────────────────────────────────────────────────────
const PING_INTERVAL_MS = 9 * 60 * 1000
function useKeepAlive() {
  useEffect(() => {
    const ping = () => api.get('/ping').catch(() => {})
    ping()
    const id = setInterval(ping, PING_INTERVAL_MS)
    return () => clearInterval(id)
  }, [])
}

// ── Theme-aware style helpers (CSS variables from index.css) ─────────────────
const G = {
  card: {
    background: 'var(--card-bg)',
    border: '1px solid var(--card-border)',
    boxShadow: 'var(--card-shadow)',
  },
  btn: { background: 'var(--orange)', color: 'var(--accent-dark)', fontWeight: '700' },
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
      <p className="text-base font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Your chart hasn't been calculated yet</p>
      <p className="text-sm mb-6" style={{ color: 'var(--text-muted)' }}>Go to Home and enter your birth details first.</p>
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

function clearStorage() {
  try { localStorage.removeItem(LS_KEY) } catch {}
  window.location.reload()
}

// ── Compact header — Ganesha + app name (hidden on Home; hero has Ganesha) ───
function GaneshaBanner() {
  return (
    <div
      className="flex items-center gap-2.5 sm:gap-3 py-2.5 px-3 sm:px-4"
      style={{ background: 'var(--nav-bg)', borderBottom: '2px solid var(--banner-border)' }}
    >
      <GaneshaIllustration size={36} compact />
      <div className="flex-1 text-left min-w-0">
        <div className="text-sm sm:text-base font-bold truncate" style={{ color: 'var(--orange)', letterSpacing: '0.04em' }}>
          {APP_NAME}
        </div>
        <div className="text-[10px] sm:text-xs truncate" style={{ color: 'rgba(255,255,255,0.45)' }}>
          ॐ श्री கணபதியே நமஹ
        </div>
      </div>
      <DarkModeToggle small />
      <AuthPanel compact />
    </div>
  )
}

// ── HOME TAB ──────────────────────────────────────────────────────────────────
// Shared field style — enforces identical height/appearance on all inputs
// including iOS date/time pickers which default to different heights
const fieldStyle = {
  display: 'block',
  width: '100%',
  boxSizing: 'border-box',
  height: '46px',
  padding: '0 16px',
  fontSize: '16px',  // 16px prevents iOS zoom on focus
  lineHeight: '46px',
  borderRadius: '8px',
  border: '1px solid var(--input-border)',
  background: 'var(--input-bg)',
  color: 'var(--input-text)',
  WebkitAppearance: 'none',
  appearance: 'none',
  outline: 'none',
}

function HomeTab({ form, setForm, onChartReady, loading, error, chart, onGoToTab, userId, userEmail }) {
  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const handleFeatureClick = ({ tab, section }) => {
    onGoToTab(tab, section)
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-4 sm:py-8">
      {userId && (
        <div className="auth-save-hint">
          Signed in as <strong>{userEmail}</strong> — new charts save to your account.
        </div>
      )}

      {chart && form.name && (
        <div className="welcome-back">
          <div className="welcome-back__text">
            <span className="welcome-back__name">Welcome back, {form.name}</span>
            <span className="welcome-back__meta">{form.dob} · {form.place_of_birth}</span>
          </div>
          <div className="welcome-back__actions">
            <button
              type="button"
              className="welcome-back__btn welcome-back__btn--primary"
              onClick={() => onGoToTab('chart')}
            >
              View chart →
            </button>
            <button
              type="button"
              className="welcome-back__btn welcome-back__btn--ghost"
              onClick={clearStorage}
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {/* Hero — artistic Ganesha + short copy */}
      <header className="home-hero">
        <div className="home-hero__glow" aria-hidden="true" />
        <div className="home-hero__art">
          <div className="home-hero__img-wrap">
            <img
              src="/images/ganesha.png"
              alt="Lord Ganesha — Om"
              className="home-hero__img"
              width={152}
              height={152}
              loading="eager"
              decoding="async"
            />
          </div>
        </div>
        <h1 className="home-hero__title">
          {APP_SHORT} <span>Jyotish</span>
        </h1>
        <p className="home-hero__tagline">{APP_TAGLINE}</p>
        <div className="home-hero__features" aria-label="Features">
          {APP_FEATURE_LINKS.map((link) =>
            chart ? (
              <button
                key={link.label}
                type="button"
                className="home-hero__chip home-hero__chip--link"
                onClick={() => handleFeatureClick(link)}
              >
                {link.label}
              </button>
            ) : (
              <span key={link.label} className="home-hero__chip">{link.label}</span>
            )
          )}
        </div>
      </header>

      <div className="home-auth-block">
        {!userId && <AuthPanel variant="card" />}
      </div>

      {/* Birth form */}
      <div className="rounded-2xl p-4 sm:p-6" style={G.card}>
        <h2 className="text-base font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
          Enter birth details
        </h2>
        <form onSubmit={onChartReady} className="space-y-4">

          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Full Name</label>
            <input
              name="name" value={form.name} onChange={handleChange}
              placeholder="Your name" required
              style={{ ...fieldStyle }}
            />
          </div>

          {/* Mobile: stack vertically; sm+: side by side */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Date of Birth</label>
              <input
                type="date" name="dob" value={form.dob} onChange={handleChange} required
                style={{ ...fieldStyle }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Time of Birth</label>
              <input
                type="time" name="tob" value={form.tob} onChange={handleChange} required
                style={{ ...fieldStyle }}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Place of Birth</label>
            <input
              name="place_of_birth" value={form.place_of_birth} onChange={handleChange}
              placeholder="City, Country (e.g. Chennai, India)" required
              style={{ ...fieldStyle }}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Gender</label>
            <select
              name="gender" value={form.gender} onChange={handleChange}
              style={{ ...fieldStyle, cursor: 'pointer' }}
            >
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other / Prefer not to say</option>
            </select>
          </div>

          {error && (
            <div className="text-sm rounded-lg px-4 py-3"
              style={{ color: 'var(--error-text)', background: 'var(--error-bg)', border: '1px solid var(--error-border)' }}>
              {error}
            </div>
          )}

          <button
            type="submit" disabled={loading}
            className="w-full font-bold py-3 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed text-base"
            style={G.btn}
          >
            {loading ? 'Calculating…' : 'Calculate Chart →'}
          </button>
        </form>
      </div>
    </div>
  )
}

// ── MY CHART TAB ──────────────────────────────────────────────────────────────
function MyChartTab({ chart, onGoHome, placeOfBirth }) {
  if (!chart) return <NeedChart onGoHome={onGoHome} />
  return (
    <div className="max-w-5xl mx-auto px-3 sm:px-4 py-6 sm:py-8">

      <NotificationSettings placeOfBirth={placeOfBirth} />

      <DashaSummaryCard chart={chart} />

      {/* Big 3 */}
      <div className="big-three-grid mb-6 sm:mb-8">
        {[
          { label: 'Ascendant (Lagna)', value: chart.ascendant.sign,
            sub: `${chart.ascendant.nakshatra} P${chart.ascendant.pada}` },
          { label: 'Sun Sign', value: chart.planet_positions.Sun.sign,
            sub: chart.planet_positions.Sun.nakshatra },
          { label: 'Moon Sign', value: chart.planet_positions.Moon.sign,
            sub: chart.planet_positions.Moon.nakshatra },
        ].map(({ label, value, sub }) => (
          <div key={label} className="rounded-xl p-3 sm:p-4 text-center"
            style={{ background: 'var(--highlight-bg)', border: '2px solid var(--highlight-border)', boxShadow: 'var(--card-shadow)' }}>
            <div className="text-xs mb-1 font-medium" style={{ color: 'var(--text-muted)' }}>{label}</div>
            <div className="text-base sm:text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{value}</div>
            <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{sub}</div>
          </div>
        ))}
      </div>

      {/* D1 + D9 Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8">
        {[
          { title: 'D1 — Rasi Chart (Janma Kundali)',
            sub: `${chart.birth_data.dob} · ${chart.birth_data.tob}`,
            pos: chart.planet_positions, lagnaIdx: chart.ascendant.sign_index, nav: false },
          { title: 'D9 — Navamsa Chart',
            sub: `Lagna: ${chart.navamsa_ascendant?.sign}`,
            pos: chart.navamsa_positions, lagnaIdx: chart.navamsa_ascendant?.sign_index, nav: true },
        ].map(({ title, sub, pos, lagnaIdx, nav }) => (
          <div key={title} className="rounded-xl p-3 sm:p-4"
            style={{ background: 'var(--card-bg)', border: '1px solid var(--card-border)', boxShadow: 'var(--card-shadow)' }}>
            <h3 className="text-xs sm:text-sm font-semibold mb-3 text-center uppercase tracking-wide"
              style={{ color: 'var(--text-muted)' }}>{title}</h3>
            <SouthIndianChart title={nav ? 'D9' : 'D1'} subtitle={sub}
              planetPositions={pos} lagnaSignIndex={lagnaIdx} navamsa={nav} />
          </div>
        ))}
      </div>

      {/* Planet Table */}
      <div className="rounded-xl overflow-hidden mb-6 sm:mb-8"
        style={{ background: 'var(--card-bg)', border: '1px solid var(--card-border)', boxShadow: 'var(--card-shadow)' }}>
        <div className="px-4 sm:px-5 py-3" style={{ borderBottom: '1px solid var(--card-border)', background: 'var(--table-header)' }}>
          <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>
            Planet Details — D1 Rasi
          </h3>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
            Ayanamsa: {chart.ayanamsa} {chart.ayanamsa_value?.toFixed(4)}° &nbsp;·&nbsp; ★ Vargottama &nbsp;·&nbsp; ℞ Retrograde
          </p>
        </div>
        <PlanetTable planetPositions={chart.planet_positions}
          navamsaPositions={chart.navamsa_positions} ascendant={chart.ascendant} />
      </div>

      {/* Yogas */}
      {chart.yogas?.length > 0 && (
        <div className="rounded-xl p-4 sm:p-5 mb-6 sm:mb-8"
          style={{ background: 'var(--yoga-bg)', border: '2px solid var(--highlight-border)', boxShadow: 'var(--card-shadow)' }}>
          <h3 className="font-bold mb-3 text-sm uppercase tracking-wide" style={{ color: 'var(--orange-dark)' }}>
            ✦ Yogas Detected
          </h3>
          <div className="space-y-2">
            {chart.yogas.map((y, i) => (
              <div key={i} className="text-sm">
                <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>{y.name}</span>
                <span className="ml-2" style={{ color: 'var(--text-secondary)' }}>— {y.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Personal Panchangam */}
      <PersonalPanchangamCard chart={chart} />

      {/* Ashtakavarga */}
      <div
        id="ashtakavarga"
        className="rounded-xl overflow-hidden mb-6 sm:mb-8 scroll-mt-20"
        style={{ background:'var(--card-bg)', border:'1px solid var(--card-border)', boxShadow:'var(--card-shadow)' }}
      >
        <div className="px-4 sm:px-5 py-3" style={{ borderBottom:'1px solid var(--card-border)', background:'var(--table-header)' }}>
          <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color:'var(--text-secondary)' }}>
            Ashtakavarga — BAV &amp; SAV
          </h3>
          <p className="text-xs mt-0.5" style={{ color:'var(--text-muted)' }}>
            Bindu scores per house • Sarvashtakavarga • Shodhya Pinda
          </p>
        </div>
        <div className="px-4 sm:px-5 py-4">
          <AshtakavargaPanel chart={chart} />
        </div>
      </div>

      {/* Dasha Roadmap */}
      <div className="rounded-xl overflow-hidden mb-6 sm:mb-8"
        style={{ background:'var(--card-bg)', border:'1px solid var(--card-border)', boxShadow:'var(--card-shadow)' }}>
        <div className="px-4 sm:px-5 py-4">
          <DashaRoadmap chart={chart} />
        </div>
      </div>
    </div>
  )
}

// ── MAIN COMPONENT ────────────────────────────────────────────────────────────
export default function Home() {
  useKeepAlive()
  const { userId, email: userEmail } = useAuth()

  // Deep-link tabs from notification clicks (?tab=chart|panchangam|…)
  const urlTab = (() => {
    try {
      const t = new URLSearchParams(window.location.search).get('tab')
      return TABS.some(x => x.key === t) ? t : null
    } catch { return null }
  })()

  // Restore from localStorage on first render
  const saved = loadFromStorage()
  const [activeTab, setActiveTab] = useState(urlTab || (saved?.chart ? 'chart' : 'home'))
  const [form, setForm]   = useState(saved?.form  || { name:'', dob:'', tob:'', place_of_birth:'', gender:'male' })
  const [chart, setChart] = useState(saved?.chart || null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [chartRefreshing, setChartRefreshing] = useState(false)
  const [scrollTarget, setScrollTarget] = useState(() => {
    try {
      const hash = window.location.hash.replace('#', '')
      const tab = new URLSearchParams(window.location.search).get('tab')
      return tab === 'chart' && hash ? hash : null
    } catch { return null }
  })

  const setTab = useCallback((key, section) => {
    setActiveTab(key)
    if (section) setScrollTarget(section)
    try {
      const url = new URL(window.location.href)
      if (key === 'home') {
        url.searchParams.delete('tab')
        url.hash = ''
      } else {
        url.searchParams.set('tab', key)
        if (section) url.hash = section
        else url.hash = ''
      }
      window.history.replaceState({}, '', url)
    } catch {}
  }, [])

  // Scroll to in-chart section after tab switch (e.g. Ashtakavarga from home chip)
  useEffect(() => {
    if (!scrollTarget || activeTab !== 'chart') return undefined
    const id = scrollTarget
    const timer = setTimeout(() => {
      const el = document.getElementById(id)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' })
        el.style.transition = 'box-shadow 0.3s'
        el.style.boxShadow = '0 0 0 3px var(--orange), var(--card-shadow)'
        setTimeout(() => { el.style.boxShadow = 'var(--card-shadow)' }, 1800)
      }
      setScrollTarget(null)
    }, 100)
    return () => clearTimeout(timer)
  }, [activeTab, scrollTarget])

  // Refresh stale saved charts missing ISO dasha dates
  useEffect(() => {
    const s = loadFromStorage()
    if (!s?.form?.dob || !s?.chart) return
    if (s.chart.dasha?.mahadasha?.start_iso) return
    setChartRefreshing(true)
    const payload = userId ? { ...s.form, user_id: userId } : s.form
    api.post('/natal-chart', payload)
      .then(({ data }) => {
        setChart(data)
        saveToStorage(s.form, data)
      })
      .catch(() => {})
      .finally(() => setChartRefreshing(false))
  }, [userId])

  // When user signs in, sync existing chart to their account
  useEffect(() => {
    if (!userId || !chart || !form.dob) return
    api.post('/natal-chart', { ...form, user_id: userId }).catch(() => {})
  }, [userId]) // eslint-disable-line react-hooks/exhaustive-deps

  // Cosmic alert watcher (while app is open / installed as PWA)
  useEffect(() => {
    if (!chart) return undefined
    return startNotificationWatcher(chart, form.place_of_birth)
  }, [chart, form.place_of_birth])

  // Switch tab when user taps a notification while app is open
  useEffect(() => {
    if (!('serviceWorker' in navigator)) return undefined
    const onMsg = (e) => {
      const tab = e.data?.tab
      if (e.data?.type === 'NAV_TAB' && TABS.some(t => t.key === tab)) {
        setTab(tab)
      }
    }
    navigator.serviceWorker.addEventListener('message', onMsg)
    return () => navigator.serviceWorker.removeEventListener('message', onMsg)
  }, [setTab])

  const handleSubmit = async e => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setChart(null)
    try {
      const payload = userId ? { ...form, user_id: userId } : form
      const { data } = await api.post('/natal-chart', payload)
      setChart(data)
      saveToStorage(form, data)
      setTab('chart')
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

  const goHome = () => setTab('home')

  const tabPane = (key) => ({ display: activeTab === key ? 'block' : 'none' })

  // ── Top tab bar (desktop) / content area ────────────────────────────────
  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ background: 'var(--app-bg)', color: 'var(--text-primary)' }}
    >
      {/* Header — full banner on inner tabs; slim dark-mode bar on Home (mobile) */}
      {activeTab === 'home' ? (
        <div className="banner-minimal">
          <AuthPanel compact />
          <DarkModeToggle small />
        </div>
      ) : (
        <GaneshaBanner />
      )}

      {activeTab !== 'home' && (
        <CosmosStrip
          location={form.place_of_birth}
          chart={chart}
          onOpenPanchangam={() => setTab('panchangam')}
        />
      )}

      {/* ── Desktop top tab bar (hidden on mobile) ── */}
      <nav
        className="hidden sm:flex border-b sticky top-0 z-30"
        style={{ background: 'var(--nav-tab-bg)', borderColor: 'var(--nav-tab-border)', boxShadow: 'var(--card-shadow)' }}
      >
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setTab(tab.key)}
            className="flex items-center gap-1.5 px-4 lg:px-5 py-3 text-sm font-semibold transition-all relative"
            style={{
              color: activeTab === tab.key ? 'var(--nav-tab-active)' : 'var(--nav-tab-text)',
              borderBottom: activeTab === tab.key ? '3px solid var(--orange)' : '3px solid transparent',
            }}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
            {chart && ['chart','chat','forecast'].includes(tab.key) && activeTab !== tab.key && (
              <span
                className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full"
                style={{ background: 'var(--orange)' }}
              />
            )}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-2 px-3">
          <AuthPanel compact />
          <DarkModeToggle small onDarkBg={false} />
        </div>
      </nav>

      {/* ── Tab content (kept mounted to preserve Chat / Forecast state) ── */}
      <main className="flex-1 pb-20 sm:pb-0">
        {chartRefreshing && (
          <div style={{
            textAlign: 'center', padding: '8px', fontSize: 12,
            color: 'var(--orange)', background: 'var(--highlight-bg)',
            borderBottom: '1px solid var(--card-border)',
          }}>
            Refreshing chart data…
          </div>
        )}

        <div style={tabPane('home')}>
          <HomeTab
            form={form} setForm={setForm}
            onChartReady={handleSubmit}
            loading={loading} error={error}
            chart={chart}
            onGoToTab={setTab}
            userId={userId}
            userEmail={userEmail}
          />
        </div>

        <div style={tabPane('chart')}>
          <MyChartTab chart={chart} onGoHome={goHome} placeOfBirth={form.place_of_birth} />
        </div>

        <div style={tabPane('panchangam')}>
          <PanchangamTab />
        </div>

        <div style={tabPane('chat')}>
          {chart
            ? <div className="max-w-3xl mx-auto px-4 py-8">
                <ChatPanel chart={chart} placeOfBirth={form.place_of_birth} />
              </div>
            : <NeedChart onGoHome={goHome} />
          }
        </div>

        <div style={tabPane('forecast')}>
          {chart
            ? <div className="max-w-3xl mx-auto px-4 py-8">
                <ForecastPanel chart={chart} gender={form.gender} showDatePicker />
              </div>
            : <NeedChart onGoHome={goHome} />
          }
        </div>
      </main>

      {/* ── Mobile bottom nav (visible only on mobile) ── */}
      <nav
        className="sm:hidden fixed bottom-0 left-0 right-0 z-30 flex"
        style={{
          background: 'var(--nav-tab-bg)',
          borderTop: '1px solid var(--nav-tab-border)',
          paddingBottom: 'env(safe-area-inset-bottom)',
          boxShadow: '0 -2px 8px rgba(0,0,0,0.08)',
        }}
      >
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setTab(tab.key)}
            className="flex-1 flex flex-col items-center justify-center py-2 gap-0.5 relative min-h-[52px]"
            style={{ color: activeTab === tab.key ? 'var(--orange)' : 'var(--text-muted)' }}
          >
            <span style={{ fontSize: '18px', lineHeight: 1 }}>{tab.icon}</span>
            <span style={{ fontSize: '9px', fontWeight: 600, letterSpacing: '0.04em' }}>
              {tab.label}
            </span>
            {activeTab === tab.key && (
              <span
                className="absolute top-1 left-1/2 -translate-x-1/2 rounded-full"
                style={{ width: '20px', height: '3px', background: 'var(--orange)' }}
              />
            )}
            {chart && ['chart','chat','forecast'].includes(tab.key) && activeTab !== tab.key && (
              <span
                className="absolute top-2 right-3 w-1.5 h-1.5 rounded-full"
                style={{ background: 'var(--orange)' }}
              />
            )}
          </button>
        ))}
      </nav>
    </div>
  )
}

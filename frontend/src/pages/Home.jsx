/**
 * Home.jsx — Parashara Jyotish
 * Tabbed layout: Home · My Chart · Panchangam · Ask AI · Forecast
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import api from '../api/client'
import {
  APP_NAME,
  APP_SHORT,
  APP_TAGLINE,
  APP_TRUST_LINE,
  APP_VALUE_CARDS,
  APP_FEATURE_LINKS,
  APP_GANESHA_IMG,
  APP_MANTRA_EN,
  APP_MANTRA_SANSKRIT,
  APP_MANTRA_TAMIL,
} from '../constants/brand'
import CosmosStrip from '../components/CosmosStrip'
import SouthIndianChart from '../components/SouthIndianChart'
import PlanetTable from '../components/PlanetTable'
import ForecastPanel from '../components/ForecastPanel'
import GocharamTab from '../components/GocharamTab'
import ChatPanel from '../components/ChatPanel'
import PersonalPanchangamCard from '../components/PersonalPanchangamCard'
import PanchangamTab from '../components/PanchangamTab'
import PrashnaTab from '../components/PrashnaTab'
import AshtakavargaPanel from '../components/AshtakavargaPanel'
import TamilDoshasPanel from '../components/TamilDoshasPanel'
import StaleChartBanner from '../components/StaleChartBanner'
import DashaRoadmap from '../components/DashaRoadmap'
import DashaSummaryCard from '../components/DashaSummaryCard'
import DarkModeToggle, { applyStoredTheme } from '../components/DarkModeToggle'
import AuthPanel from '../components/AuthPanel'
import NotificationSettings from '../components/NotificationSettings'
import { useAuth } from '../hooks/useAuth'
import { chartNeedsDasha, backfillChartDasha } from '../lib/ensureChartDasha'
import { startNotificationWatcher } from '../lib/notifications'
import { saveSessionChart, loadSessionChart, clearSessionChart } from '../lib/chartStorage'
import AdminPanel from '../components/AdminPanel'
import { useIsAdmin } from '../hooks/useIsAdmin'
import ConfirmDialog from '../components/ConfirmDialog'
import ErrorBoundary from '../components/ErrorBoundary'
import AccountSettings from '../components/AccountSettings'
import LegalAcceptModal from '../components/LegalAcceptModal'
import LegalDocumentModal from '../components/LegalDocumentModal'
import LegalFooter from '../components/LegalFooter'
import { TERMS_SECTIONS, PRIVACY_SECTIONS, SHORT_DISCLAIMER } from '../constants/legal'
import { hasLegalConsent, isAtLeast18 } from '../lib/legalConsent'
import { trackTabView } from '../lib/analytics'

// Apply persisted theme immediately on load
applyStoredTheme()

// ── Session chart helpers (no localStorage PII — Step 6) ───────────────────
function saveToStorage(form, chart, userId) {
  if (userId) return
  saveSessionChart(form, chart)
}

function loadFromStorage(userId) {
  if (userId) return null
  return loadSessionChart()
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
const BASE_TABS = [
  { key: 'home',       label: 'Home',       icon: '🏠' },
  { key: 'chart',      label: 'My Chart',   icon: '⭐' },
  { key: 'gochar',     label: 'Gochar',     icon: '🪐', mobileLabel: 'Gochar' },
  { key: 'panchangam', label: 'Panchangam', icon: '🗓', mobileLabel: 'Panch' },
  { key: 'prashna',    label: 'Prashna',    icon: '🌙' },
  { key: 'chat',       label: 'Ask AI',     icon: '🔮' },
  { key: 'forecast',   label: 'Forecast',   icon: '📊' },
]
const ADMIN_TAB = { key: 'admin', label: 'Admin', icon: '⚙️' }

// ── "No chart yet" placeholder ────────────────────────────────────────────────
function NeedChart({ onGoHome }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 text-center max-w-lg mx-auto">
      <div className="w-full mb-6 text-left">
        <AuthPanel variant="card" />
      </div>
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

function clearSessionAndReload() {
  clearSessionChart()
  window.location.reload()
}

// ── Compact header — traditional Ganesha + trilingual mantra ─────────────────
function GaneshaBanner() {
  return (
    <header
      className="ganesha-banner"
      style={{ background: 'var(--nav-bg)', borderBottom: '2px solid var(--banner-border)' }}
    >
      <div className="ganesha-banner__brand">
        <img
          src={APP_GANESHA_IMG}
          alt=""
          className="ganesha-banner__photo"
          width={48}
          height={40}
          decoding="async"
        />
        <div className="ganesha-banner__text">
          <div className="ganesha-banner__title">{APP_NAME}</div>
          <div className="ganesha-banner__mantra-en">{APP_MANTRA_EN}</div>
          <div className="ganesha-banner__mantra-scripts">
            <span lang="sa">{APP_MANTRA_SANSKRIT}</span>
            <span className="ganesha-banner__mantra-dot" aria-hidden="true">·</span>
            <span lang="ta">{APP_MANTRA_TAMIL}</span>
          </div>
        </div>
      </div>
      <div className="ganesha-banner__actions">
        <DarkModeToggle small onDarkBg />
        <AuthPanel compact onDarkBg />
      </div>
    </header>
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

function HomeTab({ form, setForm, onChartReady, loading, error, chart, onGoToTab, userId, userEmail, onClearRequest }) {
  const handleChange = e => {
    const { name, value, type, checked } = e.target
    if (name === 'time_unknown') {
      setForm(f => ({
        ...f,
        time_unknown: checked,
        tob: checked ? '12:00' : f.tob,
      }))
      return
    }
    setForm(f => ({ ...f, [name]: type === 'checkbox' ? checked : value }))
  }

  const scrollToBirthForm = () => {
    document.getElementById('birth-form')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    window.setTimeout(() => document.getElementById('birth-name')?.focus(), 400)
  }

  const handleFeatureClick = ({ tab, section }) => {
    if (chart) {
      onGoToTab(tab, section)
      return
    }
    scrollToBirthForm()
  }

  const handleValueCardClick = (card) => {
    if (chart) {
      onGoToTab(card.tab)
      return
    }
    scrollToBirthForm()
  }

  const isNewVisitor = !chart

  const heroSection = (
    <header className={`home-hero home-hero--compact${isNewVisitor ? ' home-hero--guest' : ''}`}>
      <div className="home-hero__glow" aria-hidden="true" />
      <div className="home-hero__art">
        <div className="home-hero__img-wrap">
          <img
            src={APP_GANESHA_IMG}
            alt="Lord Ganesha"
            className="home-hero__img"
            width={180}
            height={159}
            loading="eager"
            decoding="async"
          />
        </div>
      </div>
      <h1 className="home-hero__title">
        {APP_SHORT} <span>Jyotish</span>
      </h1>
      <p className="home-hero__tagline">{APP_TAGLINE}</p>
      <p className="home-hero__trust">{APP_TRUST_LINE}</p>
      <p className="home-hero__mantra">{APP_MANTRA_EN}</p>
      <p className="home-hero__mantra-scripts">
        <span lang="sa">{APP_MANTRA_SANSKRIT}</span>
        <span aria-hidden="true"> · </span>
        <span lang="ta">{APP_MANTRA_TAMIL}</span>
      </p>
      {!isNewVisitor && (
        <div className="home-hero__features" aria-label="Features">
          {APP_FEATURE_LINKS.map((link) => (
            <button
              key={link.label}
              type="button"
              className="home-hero__chip home-hero__chip--link"
              onClick={() => handleFeatureClick(link)}
            >
              {link.label}
            </button>
          ))}
        </div>
      )}
    </header>
  )

  const valueCardsSection = (
    <div className="home-value-cards-block">
      <h2 className="home-value-cards__heading">
        {isNewVisitor ? 'Included free with your chart' : 'Quick access'}
      </h2>
      <p className="home-value-cards__hint" role="status">
        {isNewVisitor
          ? 'Calculate above first — then tap to open Chart, Gochar, or Ask AI'
          : 'Tap a card to open that feature'}
      </p>
      <div className="home-value-cards" aria-label="What you get">
        {APP_VALUE_CARDS.map((card) => (
          <button
            key={card.title}
            type="button"
            className="home-value-card home-value-card--link"
            onClick={() => handleValueCardClick(card)}
            title={card.hint}
          >
            <span className="home-value-card__icon" aria-hidden="true">{card.icon}</span>
            <span className="home-value-card__title">{card.title}</span>
            <span className="home-value-card__desc">{card.desc}</span>
          </button>
        ))}
      </div>
    </div>
  )

  const authSection = !userId ? (
    <div className="home-auth-block">
      {chart ? <AuthPanel variant="nudge" /> : <AuthPanel variant="card" />}
    </div>
  ) : null

  const formSection = (
    <div
      id="birth-form"
      className={`rounded-2xl p-4 sm:p-6${isNewVisitor ? ' home-birth-form-primary' : ''}`}
      style={G.card}
    >
      <h2 className="text-base font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
        {chart ? 'Update birth details' : 'Enter birth details'}
      </h2>
      <form onSubmit={onChartReady} className="space-y-4">

          <div>
            <label htmlFor="birth-name" className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Full Name</label>
            <input
              id="birth-name"
              name="name" value={form.name} onChange={handleChange}
              placeholder="Your name" required
              style={{ ...fieldStyle }}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label htmlFor="birth-dob" className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Date of Birth</label>
              <input
                id="birth-dob"
                type="date" name="dob" value={form.dob} onChange={handleChange} required
                style={{ ...fieldStyle }}
              />
            </div>
            <div>
              <label htmlFor="birth-tob" className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Time of Birth</label>
              <input
                id="birth-tob"
                type="time" name="tob" value={form.tob} onChange={handleChange}
                required={!form.time_unknown}
                disabled={form.time_unknown}
                style={{ ...fieldStyle, opacity: form.time_unknown ? 0.55 : 1 }}
              />
              <label className="approx-time-check" htmlFor="birth-time-unknown">
                <input
                  id="birth-time-unknown"
                  type="checkbox"
                  name="time_unknown"
                  checked={!!form.time_unknown}
                  onChange={handleChange}
                />
                I don&apos;t know my exact birth time (uses 12:00 noon)
              </label>
            </div>
          </div>

          <div>
            <label htmlFor="birth-place" className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Place of Birth</label>
            <input
              id="birth-place"
              name="place_of_birth" value={form.place_of_birth} onChange={handleChange}
              placeholder="City, Country (e.g. Chennai, India)" required
              style={{ ...fieldStyle }}
            />
          </div>

          <div>
            <label htmlFor="birth-gender" className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Gender</label>
            <select
              id="birth-gender"
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

          <p className="legal-form-note">
            You must be 18 or older. Birth date is used for chart calculation only.
          </p>

          <button
            type="submit" disabled={loading}
            className="w-full font-bold py-3 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed text-base"
            style={G.btn}
          >
            {loading ? 'Calculating…' : chart ? 'Recalculate chart' : 'Calculate my chart — free'}
          </button>
        </form>
    </div>
  )

  return (
    <div className="max-w-lg mx-auto px-4 py-4 sm:py-8">
      {!userId && chart && (
        <p className="guest-session-hint" role="status">
          Guest mode: your chart is saved for this browser session only (about 24 hours). Sign in to keep it permanently.
        </p>
      )}

      {userId && (
        <div className="auth-save-hint">
          Signed in as <strong>{userEmail}</strong> — new charts save to your account.
        </div>
      )}

      {userId && (
        <AccountSettings />
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
              onClick={onClearRequest}
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {isNewVisitor ? (
        <>
          {heroSection}
          {formSection}
          {authSection}
          {valueCardsSection}
        </>
      ) : (
        <>
          {heroSection}
          {valueCardsSection}
          {authSection}
          {formSection}
        </>
      )}
    </div>
  )
}

function ApproximateTimeBanner({ chart }) {
  if (!chart?.birth_data?.birth_time_approximate) return null
  return (
    <div className="approx-time-banner" role="status">
      <strong>Birth time approximate.</strong> Chart uses 12:00 noon local time — Lagna and house placements may differ from your actual chart. Moon sign and Dasha remain reliable.
    </div>
  )
}

// ── MY CHART TAB ──────────────────────────────────────────────────────────────
function MyChartTab({ chart, onGoHome, placeOfBirth, userId, chartTabActive }) {
  if (!chart) return <NeedChart onGoHome={onGoHome} />
  return (
    <div className="max-w-5xl mx-auto px-3 sm:px-4 py-6 sm:py-8">

      {!userId && (
        <div className="max-w-lg mx-auto mb-6">
          <AuthPanel variant="nudge" />
        </div>
      )}

      <ApproximateTimeBanner chart={chart} />

      <NotificationSettings placeOfBirth={placeOfBirth} />

      <StaleChartBanner chart={chart} onRecalculate={onGoHome} />

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
              planetPositions={pos} lagnaSignIndex={lagnaIdx} navamsa={nav}
              variant="classic" showDetails={true} chartKind="natal" />
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
      <PersonalPanchangamCard chart={chart} userId={userId} enabled={chartTabActive} />

      {/* Ashtakavarga */}
      <div
        id="ashtakavarga"
        className="rounded-xl mb-6 sm:mb-8 scroll-mt-20 av-pro-section-wrap"
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
          <AshtakavargaPanel chart={chart} userId={userId} enabled={chartTabActive} />
        </div>
      </div>

      {/* Tamil predictive doshas */}
      <div
        id="tamil-doshas"
        className="rounded-xl mb-6 sm:mb-8 scroll-mt-20 td-section-wrap"
        style={{ background:'var(--card-bg)', border:'1px solid var(--card-border)', boxShadow:'var(--card-shadow)' }}
      >
        <div className="px-4 sm:px-5 py-3" style={{ borderBottom:'1px solid var(--card-border)', background:'var(--table-header)' }}>
          <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color:'var(--text-secondary)' }}>
            Tamil Predictive Doshas
          </h3>
          <p className="text-xs mt-0.5" style={{ color:'var(--text-muted)' }}>
            Thithi Soonyam · Vadhai/Vainasikam · Yogi · Mudakku
          </p>
        </div>
        <div className="px-4 sm:px-5 py-4">
          <TamilDoshasPanel chart={chart} userId={userId} enabled={chartTabActive} />
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
function HomeApp() {
  useKeepAlive()
  const { userId, email: userEmail } = useAuth()
  const { isAdmin } = useIsAdmin(userId, userEmail)
  const TABS = useMemo(
    () => (isAdmin ? [...BASE_TABS, ADMIN_TAB] : BASE_TABS),
    [isAdmin],
  )

  const requestedTab = useMemo(() => {
    try {
      return new URLSearchParams(window.location.search).get('tab')
    } catch { return null }
  }, [])

  // Deep-link tabs (?tab=chart|admin|…) — admin waits until owner check completes
  const urlTab = (() => {
    if (!requestedTab) return null
    if (requestedTab === 'admin') return null
    return BASE_TABS.some(x => x.key === requestedTab) ? requestedTab : null
  })()

  // Restore anonymous session chart (signed-in users fetch from server)
  const saved = loadFromStorage(null)
  const [activeTab, setActiveTab] = useState(urlTab || (saved?.chart ? 'chart' : 'home'))
  const [mountedTabs, setMountedTabs] = useState(
    () => new Set([urlTab || (saved?.chart ? 'chart' : 'home')]),
  )
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const [syncNotice, setSyncNotice] = useState('')
  const [form, setForm]   = useState(saved?.form  || { name:'', dob:'', tob:'', place_of_birth:'', gender:'male', time_unknown: false })
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
  const [legalReady, setLegalReady] = useState(() => hasLegalConsent())
  const [legalDoc, setLegalDoc] = useState(null)

  const DISCLAIMER_SECTIONS = useMemo(
    () => [{ title: 'Disclaimer', body: SHORT_DISCLAIMER }],
    [],
  )

  const setTab = useCallback((key, section) => {
    setMountedTabs(prev => new Set(prev).add(key))
    setActiveTab(key)
    if (section) setScrollTarget(section)
    trackTabView(key)
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

  useEffect(() => {
    trackTabView(activeTab)
  }, []) // initial tab only — eslint-disable-line react-hooks/exhaustive-deps

  // Load chart from server when signed in; sync session chart if none saved yet
  useEffect(() => {
    if (!userId) return
    setChartRefreshing(true)
    api.get('/natal-chart')
      .then(({ data }) => {
        setChart(data)
        const bd = data?.birth_data || {}
        setForm(f => ({
          ...f,
          name: bd.name || f.name,
          dob: bd.dob || f.dob,
          tob: bd.tob || f.tob,
          place_of_birth: data.place_of_birth || f.place_of_birth,
          time_unknown: bd.birth_time_approximate ?? f.time_unknown,
        }))
      })
      .catch(async (err) => {
        if (err.response?.status !== 404) return
        const s = loadSessionChart()
        if (!s?.form?.dob || !s?.chart) return
        try {
          const { data } = await api.post('/natal-chart', { ...s.form, user_id: userId })
          setChart(data)
          setForm(s.form)
        } catch (syncErr) {
          console.error('[chart sync]', syncErr)
          setSyncNotice('Could not save your chart to your account. Please recalculate on Home.')
        }
      })
      .finally(() => setChartRefreshing(false))
  }, [userId])

  // Backfill dasha on guest session charts (signed-in users use GET /natal-chart)
  useEffect(() => {
    if (userId || !chart || !chartNeedsDasha(chart)) return
    setChartRefreshing(true)
    backfillChartDasha(chart)
      .then((data) => {
        setChart(data)
        saveToStorage(form, data, null)
      })
      .catch(() => {})
      .finally(() => setChartRefreshing(false))
  }, [chart, userId]) // eslint-disable-line react-hooks/exhaustive-deps

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
  }, [setTab, TABS])

  // Deep-link ?tab=admin once owner status is confirmed
  useEffect(() => {
    if (isAdmin && requestedTab === 'admin') {
      setMountedTabs(prev => new Set(prev).add('admin'))
      setActiveTab('admin')
    }
  }, [isAdmin, requestedTab])

  const handleSubmit = async e => {
    e.preventDefault()
    if (!legalReady && !hasLegalConsent()) {
      setError('Please accept the Terms and confirm you are 18 or older using the dialog above.')
      return
    }
    if (!isAtLeast18(form.dob)) {
      setError('You must be at least 18 years old to use this service.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const payload = userId
        ? { ...form, user_id: userId, birth_time_approximate: !!form.time_unknown }
        : { ...form, birth_time_approximate: !!form.time_unknown }
      const { data } = await api.post('/natal-chart', payload)
      setChart(data)
      saveToStorage(form, data, userId)
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
  const chartTabActive = activeTab === 'chart'

  const tabPane = (key) => ({ display: activeTab === key ? 'block' : 'none' })

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ background: 'var(--app-bg)', color: 'var(--text-primary)' }}
    >
      <LegalAcceptModal
        open={!legalReady}
        onAccepted={() => setLegalReady(true)}
        onOpenTerms={() => setLegalDoc('terms')}
        onOpenPrivacy={() => setLegalDoc('privacy')}
      />
      <LegalDocumentModal
        open={legalDoc === 'terms'}
        title="Terms of Use"
        sections={TERMS_SECTIONS}
        onClose={() => setLegalDoc(null)}
      />
      <LegalDocumentModal
        open={legalDoc === 'privacy'}
        title="Privacy Policy"
        sections={PRIVACY_SECTIONS}
        onClose={() => setLegalDoc(null)}
      />
      <LegalDocumentModal
        open={legalDoc === 'disclaimer'}
        title="Disclaimer"
        sections={DISCLAIMER_SECTIONS}
        onClose={() => setLegalDoc(null)}
      />
      <ConfirmDialog
        open={showClearConfirm}
        title="Clear chart data?"
        message="This removes your saved birth chart from this browser and reloads the app. Chat and forecast history will be lost."
        confirmLabel="Clear & reload"
        cancelLabel="Keep chart"
        danger
        onConfirm={clearSessionAndReload}
        onCancel={() => setShowClearConfirm(false)}
      />
      {/* Header — full banner on inner tabs; slim dark-mode bar on Home (mobile) */}
      {activeTab === 'home' ? (
        <div className="banner-minimal">
          <div className="banner-minimal__brand">
            <img
              src={APP_GANESHA_IMG}
              alt=""
              className="banner-minimal__icon"
              width={32}
              height={27}
              decoding="async"
            />
            <span className="banner-minimal__label">{APP_NAME}</span>
          </div>
          <div className="banner-minimal__actions">
            <DarkModeToggle small onDarkBg />
          </div>
        </div>
      ) : (
        <GaneshaBanner />
      )}

      <CosmosStrip
        location={form.place_of_birth}
        chart={chart}
        onOpenPanchangam={() => setTab('panchangam')}
      />

      {/* ── Desktop top tab bar (hidden on mobile) ── */}
      <nav
        className="hidden sm:flex border-b sticky top-0 z-30"
        role="tablist"
        aria-label="Main navigation"
        style={{ background: 'var(--nav-tab-bg)', borderColor: 'var(--nav-tab-border)', boxShadow: 'var(--card-shadow)' }}
      >
        {TABS.map(tab => (
          <button
            key={tab.key}
            type="button"
            role="tab"
            id={`tab-${tab.key}`}
            aria-selected={activeTab === tab.key}
            aria-controls={`panel-${tab.key}`}
            onClick={() => setTab(tab.key)}
            className="flex items-center gap-1.5 px-4 lg:px-5 py-3 text-sm font-semibold transition-all relative"
            style={{
              color: activeTab === tab.key ? 'var(--nav-tab-active)' : 'var(--nav-tab-text)',
              borderBottom: activeTab === tab.key ? '3px solid var(--orange)' : '3px solid transparent',
            }}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
            {chart && ['chart','gochar','chat','forecast'].includes(tab.key) && activeTab !== tab.key && (
              <span
                className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full"
                style={{ background: 'var(--orange)' }}
              />
            )}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-2 px-3">
          {activeTab !== 'home' && <AuthPanel compact />}
          <DarkModeToggle small onDarkBg={false} />
        </div>
      </nav>

      {/* ── Tab content (kept mounted to preserve Chat / Forecast state) ── */}
      <main className="flex-1 pb-20 sm:pb-0">
        {syncNotice && (
          <div className="app-notice app-notice--warn" role="alert">
            {syncNotice}
            <button type="button" className="app-notice__dismiss" onClick={() => setSyncNotice('')}>Dismiss</button>
          </div>
        )}
        {chartRefreshing && (
          <div style={{
            textAlign: 'center', padding: '8px', fontSize: 12,
            color: 'var(--orange)', background: 'var(--highlight-bg)',
            borderBottom: '1px solid var(--card-border)',
          }}>
            Refreshing chart data…
          </div>
        )}

        <div style={tabPane('home')} role="tabpanel" id="panel-home" aria-labelledby="tab-home">
          <HomeTab
            form={form} setForm={setForm}
            onChartReady={handleSubmit}
            loading={loading} error={error}
            chart={chart}
            onGoToTab={setTab}
            userId={userId}
            userEmail={userEmail}
            onClearRequest={() => setShowClearConfirm(true)}
          />
        </div>

        {mountedTabs.has('chart') && (
        <div style={tabPane('chart')} role="tabpanel" id="panel-chart" aria-labelledby="tab-chart">
          <MyChartTab chart={chart} onGoHome={goHome} placeOfBirth={form.place_of_birth} userId={userId} chartTabActive={chartTabActive} />
        </div>
        )}

        {mountedTabs.has('gochar') && (
        <div style={tabPane('gochar')} role="tabpanel" id="panel-gochar" aria-labelledby="tab-gochar">
          {chart
            ? <div className="tab-content-wrap max-w-3xl mx-auto px-3 py-4 sm:px-4 sm:py-8">
                <StaleChartBanner chart={chart} onRecalculate={goHome} />
                <GocharamTab
                  chart={chart}
                  userId={userId}
                  enabled={activeTab === 'gochar'}
                  onOpenForecast={() => setTab('forecast')}
                />
              </div>
            : <NeedChart onGoHome={goHome} />
          }
        </div>
        )}

        {mountedTabs.has('panchangam') && (
        <div style={tabPane('panchangam')} role="tabpanel" id="panel-panchangam" aria-labelledby="tab-panchangam">
          <PanchangamTab />
        </div>
        )}

        {mountedTabs.has('prashna') && (
        <div style={tabPane('prashna')} role="tabpanel" id="panel-prashna" aria-labelledby="tab-prashna">
          <PrashnaTab enabled={activeTab === 'prashna'} chart={chart} />
        </div>
        )}

        {mountedTabs.has('chat') && (
        <div style={tabPane('chat')} role="tabpanel" id="panel-chat" aria-labelledby="tab-chat">
          {chart
            ? <div className="tab-content-wrap max-w-3xl mx-auto px-3 py-4 sm:px-4 sm:py-8">
                <StaleChartBanner chart={chart} onRecalculate={goHome} />
                <ChatPanel chart={chart} placeOfBirth={form.place_of_birth} userId={userId} />
              </div>
            : <NeedChart onGoHome={goHome} />
          }
        </div>
        )}

        {mountedTabs.has('forecast') && (
        <div style={tabPane('forecast')} role="tabpanel" id="panel-forecast" aria-labelledby="tab-forecast">
          {chart
            ? <div className="tab-content-wrap max-w-3xl mx-auto px-3 py-4 sm:px-4 sm:py-8">
                <StaleChartBanner chart={chart} onRecalculate={goHome} />
                <ForecastPanel chart={chart} gender={form.gender} showDatePicker userId={userId} enabled={activeTab === 'forecast'} />
              </div>
            : <NeedChart onGoHome={goHome} />
          }
        </div>
        )}

        {isAdmin && mountedTabs.has('admin') && (
          <div style={tabPane('admin')} role="tabpanel" id="panel-admin" aria-labelledby="tab-admin">
            <AdminPanel />
          </div>
        )}
      </main>

      <LegalFooter
        onOpenTerms={() => setLegalDoc('terms')}
        onOpenPrivacy={() => setLegalDoc('privacy')}
        onOpenDisclaimer={() => setLegalDoc('disclaimer')}
      />

      {/* ── Mobile bottom nav (visible only on mobile) ── */}
      <nav
        className="mobile-bottom-nav sm:hidden fixed bottom-0 left-0 right-0 z-30 flex"
        role="tablist"
        aria-label="Main navigation"
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
            type="button"
            role="tab"
            id={`tab-mobile-${tab.key}`}
            aria-selected={activeTab === tab.key}
            aria-controls={`panel-${tab.key}`}
            onClick={() => setTab(tab.key)}
            className="mobile-bottom-nav__item flex flex-col items-center justify-center py-2 gap-0.5 relative min-h-[52px]"
            style={{ color: activeTab === tab.key ? 'var(--orange)' : 'var(--text-muted)' }}
          >
            <span style={{ fontSize: '18px', lineHeight: 1 }}>{tab.icon}</span>
            <span style={{ fontSize: '9px', fontWeight: 600, letterSpacing: '0.04em' }}>
              {tab.mobileLabel || tab.label}
            </span>
            {activeTab === tab.key && (
              <span
                className="absolute top-1 left-1/2 -translate-x-1/2 rounded-full"
                style={{ width: '20px', height: '3px', background: 'var(--orange)' }}
              />
            )}
            {chart && ['chart','gochar','chat','forecast'].includes(tab.key) && activeTab !== tab.key && (
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

export default function Home() {
  return (
    <ErrorBoundary>
      <HomeApp />
    </ErrorBoundary>
  )
}

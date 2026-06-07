/**
 * AdminPanel.jsx — owner-only analytics dashboard.
 * Requires sign-in as an email listed in VITE_ADMIN_EMAILS.
 */

import { useState, useEffect } from 'react'
import api from '../api/client'

function StatCard({ label, value, sub }) {
  return (
    <div className="admin-stat">
      <div className="admin-stat__label">{label}</div>
      <div className="admin-stat__value">{value ?? '—'}</div>
      {sub && <div className="admin-stat__sub">{sub}</div>}
    </div>
  )
}

function fmtDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
      timeZone: 'Asia/Kolkata',
    })
  } catch {
    return iso
  }
}

export default function AdminPanel() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [overview, setOverview] = useState(null)
  const [users, setUsers] = useState([])
  const [locations, setLocations] = useState({ birth_places: [], current_cities: [] })
  const [aiUsage, setAiUsage] = useState([])
  const [signups, setSignups] = useState([])

  const load = () => {
    setLoading(true)
    setError('')
    Promise.all([
      api.get('/admin/overview'),
      api.get('/admin/users', { params: { limit: 50 } }),
      api.get('/admin/locations'),
      api.get('/admin/ai-usage', { params: { days: 14 } }),
      api.get('/admin/signups', { params: { days: 30 } }),
    ])
      .then(([ov, us, loc, ai, su]) => {
        setOverview(ov.data)
        setUsers(us.data.users || [])
        setLocations(loc.data)
        setAiUsage(ai.data.days || [])
        setSignups(su.data.signups || [])
      })
      .catch((err) => {
        const status = err.response?.status
        if (status === 403) {
          setError('Admin access denied. Sign in with your owner email and set ADMIN_EMAILS on Render.')
        } else {
          setError(err.response?.data?.detail || 'Could not load admin dashboard.')
        }
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading) {
    return (
      <div className="admin-panel max-w-5xl mx-auto px-4 py-8">
        <p style={{ color: 'var(--orange)', textAlign: 'center' }}>Loading owner dashboard…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="admin-panel max-w-5xl mx-auto px-4 py-8">
        <div className="admin-error">{error}</div>
        <button type="button" className="admin-refresh" onClick={load}>Retry</button>
      </div>
    )
  }

  const maxAi = Math.max(
    1,
    ...aiUsage.map(d => (d.total_chat_calls || 0) + (d.total_forecast_calls || 0)),
  )

  return (
    <div className="admin-panel max-w-5xl mx-auto px-4 py-6 sm:py-8">
      <header className="admin-header">
        <div>
          <h1 className="admin-title">Owner Dashboard</h1>
          <p className="admin-subtitle">Users · locations · AI usage · sign-ups</p>
        </div>
        <button type="button" className="admin-refresh" onClick={load}>Refresh</button>
      </header>

      <div className="admin-stats">
        <StatCard label="Total users" value={overview?.total_users} />
        <StatCard label="Charts saved" value={overview?.total_charts} sub={`${overview?.full_charts ?? 0} full JSON`} />
        <StatCard label="With location" value={overview?.users_with_location} />
        <StatCard label="AI today" value={(overview?.chat_calls_today ?? 0) + (overview?.forecast_calls_today ?? 0)}
          sub={`${overview?.chat_calls_today ?? 0} chat · ${overview?.forecast_calls_today ?? 0} forecast`} />
      </div>

      <section className="admin-section">
        <h2 className="admin-section__title">Recent users</h2>
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Birth place</th>
                <th>Moon</th>
                <th>Chart</th>
                <th>Last login</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 && (
                <tr><td colSpan={5} className="admin-empty">No users yet</td></tr>
              )}
              {users.map((u) => (
                <tr key={u.email}>
                  <td>{u.email}</td>
                  <td>{u.birth_place || u.current_city || '—'}</td>
                  <td>{u.moon_sign || '—'}</td>
                  <td>{u.has_full_chart ? '✓ full' : u.has_chart ? 'partial' : '—'}</td>
                  <td>{fmtDate(u.last_sign_in_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="admin-grid-2">
        <section className="admin-section">
          <h2 className="admin-section__title">Top birth places</h2>
          <ul className="admin-list">
            {(locations.birth_places || []).slice(0, 10).map((row) => (
              <li key={row.birth_place}>
                <span>{row.birth_place}</span>
                <strong>{row.users}</strong>
              </li>
            ))}
            {!locations.birth_places?.length && <li className="admin-empty">No data</li>}
          </ul>
        </section>

        <section className="admin-section">
          <h2 className="admin-section__title">Current cities</h2>
          <ul className="admin-list">
            {(locations.current_cities || []).slice(0, 10).map((row) => (
              <li key={`${row.city}-${row.timezone}`}>
                <span>{row.city} <small>({row.timezone})</small></span>
                <strong>{row.users}</strong>
              </li>
            ))}
            {!locations.current_cities?.length && <li className="admin-empty">No locations set</li>}
          </ul>
        </section>
      </div>

      <section className="admin-section">
        <h2 className="admin-section__title">AI usage (14 days)</h2>
        <div className="admin-bars">
          {aiUsage.map((d) => {
            const total = (d.total_chat_calls || 0) + (d.total_forecast_calls || 0)
            return (
              <div key={d.usage_date} className="admin-bar-row">
                <span className="admin-bar-label">{d.usage_date?.slice(5)}</span>
                <div className="admin-bar-track">
                  <div className="admin-bar-fill" style={{ width: `${(total / maxAi) * 100}%` }} />
                </div>
                <span className="admin-bar-val">{total}</span>
              </div>
            )
          })}
          {!aiUsage.length && <p className="admin-empty">No AI usage recorded yet</p>}
        </div>
      </section>

      <section className="admin-section">
        <h2 className="admin-section__title">Sign-ups (30 days)</h2>
        <div className="admin-bars">
          {signups.map((d) => (
            <div key={d.signup_date} className="admin-bar-row">
              <span className="admin-bar-label">{d.signup_date?.slice(5)}</span>
              <div className="admin-bar-track">
                <div className="admin-bar-fill admin-bar-fill--signup" style={{ width: `${Math.min(100, (d.new_users || 0) * 20)}%` }} />
              </div>
              <span className="admin-bar-val">{d.new_users}</span>
            </div>
          ))}
          {!signups.length && <p className="admin-empty">No sign-ups in range</p>}
        </div>
      </section>

      <p className="admin-footer">Data from Supabase · PII visible to owner only · {overview?.as_of}</p>
    </div>
  )
}

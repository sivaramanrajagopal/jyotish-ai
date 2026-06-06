/**
 * NotificationSettings.jsx — enable cosmic push alerts
 */
import { useState, useEffect } from 'react'
import {
  getNotificationPrefs,
  saveNotificationPrefs,
  requestNotificationPermission,
  registerServiceWorker,
} from '../lib/notifications'

const LOCATIONS = ['Chennai', 'Bangalore', 'Mumbai', 'Delhi', 'Hyderabad', 'Coimbatore', 'Erlangen']

export default function NotificationSettings({ placeOfBirth }) {
  const [prefs, setPrefs] = useState(getNotificationPrefs)
  const [status, setStatus] = useState('')
  const [perm, setPerm] = useState(
    typeof Notification !== 'undefined' ? Notification.permission : 'default'
  )

  useEffect(() => {
    registerServiceWorker()
  }, [])

  const update = (patch) => {
    const next = { ...prefs, ...patch }
    setPrefs(next)
    saveNotificationPrefs(next)
  }

  const handleEnable = async () => {
    setStatus('')
    const { granted, reason } = await requestNotificationPermission()
    setPerm(typeof Notification !== 'undefined' ? Notification.permission : 'denied')
    if (!granted) {
      setStatus(reason || 'Could not enable notifications.')
      update({ enabled: false })
      return
    }
    update({ enabled: true })
    setStatus('Alerts enabled. You will be notified while the app is installed or open.')
  }

  const toggle = (key) => update({ [key]: !prefs[key] })

  return (
    <div
      className="rounded-xl mb-6 sm:mb-8"
      style={{
        background: 'var(--card-bg)',
        border: '1px solid var(--card-border)',
        boxShadow: 'var(--card-shadow)',
        padding: '14px 16px',
      }}
    >
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 10, marginBottom: 12 }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', margin: 0, flex: 1 }}>
          🔔 Cosmic Alerts
        </h3>
        {!prefs.enabled ? (
          <button
            type="button"
            onClick={handleEnable}
            style={{
              padding: '8px 14px', borderRadius: 8, border: 'none', cursor: 'pointer',
              background: 'var(--orange)', color: 'var(--accent-dark)', fontWeight: 700, fontSize: 12,
            }}
          >
            Enable alerts
          </button>
        ) : (
          <button
            type="button"
            onClick={() => update({ enabled: false })}
            style={{
              padding: '8px 14px', borderRadius: 8, cursor: 'pointer',
              background: 'var(--chip-bg)', border: '1px solid var(--chip-border)',
              color: 'var(--text-secondary)', fontWeight: 600, fontSize: 12,
            }}
          >
            Disable
          </button>
        )}
      </div>

      <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '0 0 12px', lineHeight: 1.5 }}>
        Get notified about Chandra Ashtama, Rahu Kalam, and unfavourable Tara Balam days.
        {perm === 'denied' && ' Enable notifications in your browser settings to use this feature.'}
      </p>

      {status && (
        <p style={{ fontSize: 12, color: 'var(--orange)', margin: '0 0 10px' }}>{status}</p>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, opacity: prefs.enabled ? 1 : 0.55 }}>
        {[
          { key: 'chandraAshtama', label: 'Chandra Ashtama', desc: 'When Moon transits your 8th sign' },
          { key: 'rahuKalam', label: 'Rahu Kalam', desc: '10 min before + during inauspicious period' },
          { key: 'taraWarnings', label: 'Tara Balam warnings', desc: 'Alert on Naidhana / unfavourable Tara days' },
        ].map(({ key, label, desc }) => (
          <label
            key={key}
            style={{
              display: 'flex', alignItems: 'flex-start', gap: 10, cursor: prefs.enabled ? 'pointer' : 'default',
              padding: '8px 10px', borderRadius: 8, background: 'var(--surface-muted)',
            }}
          >
            <input
              type="checkbox"
              checked={!!prefs[key]}
              disabled={!prefs.enabled}
              onChange={() => toggle(key)}
              style={{ marginTop: 2, accentColor: 'var(--orange)' }}
            />
            <span>
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{label}</span>
              <span style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)' }}>{desc}</span>
            </span>
          </label>
        ))}

        <div style={{ marginTop: 4 }}>
          <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
            Location for Rahu Kalam
          </label>
          <select
            value={prefs.location || guessLoc(placeOfBirth)}
            disabled={!prefs.enabled}
            onChange={e => update({ location: e.target.value })}
            style={{
              width: '100%', height: 40, padding: '0 12px', fontSize: 14,
              borderRadius: 8, border: '1px solid var(--input-border)',
              background: 'var(--input-bg)', color: 'var(--input-text)',
            }}
          >
            {LOCATIONS.map(l => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
      </div>
    </div>
  )
}

function guessLoc(place) {
  if (!place) return 'Chennai'
  const cities = ['Chennai', 'Bangalore', 'Mumbai', 'Delhi', 'Hyderabad', 'Coimbatore', 'Erlangen']
  const lower = place.toLowerCase()
  return cities.find(c => lower.includes(c.toLowerCase())) || 'Chennai'
}

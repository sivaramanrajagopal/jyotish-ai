/**
 * ForecastPanel.jsx
 * Calls POST /forecast and renders the AI-narrated daily reading.
 * Shown after the natal chart is calculated.
 */

import { useState } from 'react'
import api from '../api/client'

const SECTIONS = [
  { key: 'career',        label: 'Career & Status',   icon: '💼' },
  { key: 'love',          label: 'Love & Relations',  icon: '💞' },
  { key: 'health',        label: 'Health & Vitality', icon: '🌿' },
  { key: 'finance',       label: 'Finance & Wealth',  icon: '💰' },
  { key: 'spiritual',     label: 'Spiritual Growth',  icon: '🕉️' },
  { key: 'timing_advice', label: 'Timing & Actions',  icon: '⏳' },
  { key: 'dasha_context', label: 'Dasha Insight',     icon: '🔮' },
]

export default function ForecastPanel({ chart, placeOfBirth }) {
  const [forecast, setForecast] = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')

  // Derive a location guess from place_of_birth for panchangam
  const guessLocation = (place) => {
    if (!place) return 'Chennai'
    const cities = ['Chennai','Bangalore','Mumbai','Delhi','Hyderabad','Coimbatore','Erlangen']
    const lower = place.toLowerCase()
    return cities.find(c => lower.includes(c.toLowerCase())) || 'Chennai'
  }

  const handleGenerate = async () => {
    setLoading(true)
    setError('')
    setForecast(null)
    try {
      const { data } = await api.post('/forecast', {
        natal_chart: chart,
        location: guessLocation(placeOfBirth),
      })
      setForecast(data)
    } catch (err) {
      const detail = err.response?.data?.detail || ''
      if (detail.includes('OPENAI_API_KEY')) {
        setError('Add your OpenAI API key to backend/.env to enable AI forecasts. Get one at platform.openai.com/api-keys')
      } else {
        setError(detail || 'Could not generate forecast. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const cardStyle = { background: 'rgba(251,191,36,0.05)', border: '1px solid rgba(251,191,36,0.18)', borderRadius: '12px' }

  return (
    <div className="mb-8">
      {!forecast && !loading && (
        <div className="text-center rounded-2xl p-8" style={{ background: 'rgba(251,191,36,0.07)', border: '1px solid rgba(251,191,36,0.25)' }}>
          <div className="text-3xl mb-3">🔮</div>
          <h3 className="text-xl font-bold mb-2" style={{ color: '#fef3c7' }}>Your Daily Vedic Forecast</h3>
          <p className="mb-5 text-sm" style={{ color: 'rgba(254,243,199,0.5)' }}>
            AI-narrated insights based on your exact chart, current Dasha, and today's Panchangam.
          </p>

          {error && (
            <div className="text-sm rounded-lg px-4 py-3 mb-4 text-left" style={{ color: '#fca5a5', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)' }}>
              {error}
            </div>
          )}

          <button
            onClick={handleGenerate}
            className="font-semibold px-8 py-3 rounded-xl transition-all"
            style={{ background: 'linear-gradient(135deg, #d97706, #f59e0b)', color: '#1a0e00' }}
          >
            Generate Today's Forecast ✦
          </button>
        </div>
      )}

      {loading && (
        <div className="text-center rounded-2xl p-10" style={{ background: 'rgba(251,191,36,0.05)', border: '1px solid rgba(251,191,36,0.15)' }}>
          <div className="text-3xl mb-4 animate-pulse" style={{ color: '#fbbf24' }}>✦</div>
          <p className="font-semibold" style={{ color: '#fbbf24' }}>Reading the cosmos…</p>
          <p className="text-sm mt-1" style={{ color: 'rgba(254,243,199,0.4)' }}>Consulting your Dasha, Panchangam, and natal chart</p>
        </div>
      )}

      {forecast && (
        <div>
          <div className="flex items-center justify-between mb-4 px-1">
            <h3 className="text-base font-semibold uppercase tracking-wide" style={{ color: 'rgba(254,243,199,0.7)' }}>
              ✦ Daily Forecast — {forecast.date}
            </h3>
            <button
              onClick={handleGenerate}
              className="text-xs transition-colors"
              style={{ color: '#f59e0b' }}
            >
              Regenerate
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {SECTIONS.map(({ key, label, icon }) => {
              const text = forecast[key]
              if (!text) return null
              return (
                <div key={key} className="p-4" style={cardStyle}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">{icon}</span>
                    <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'rgba(251,191,36,0.5)' }}>
                      {label}
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed" style={{ color: 'rgba(254,243,199,0.8)' }}>{text}</p>
                </div>
              )
            })}
          </div>

          <p className="text-xs text-right" style={{ color: 'rgba(254,243,199,0.2)' }}>
            Narrated by {forecast.model}
          </p>
        </div>
      )}
    </div>
  )
}

/**
 * ChatPanel.jsx
 * Multi-turn Vedic astrology chat — golden cosmic theme + topic tagging chips.
 */

import { useState, useRef, useEffect } from 'react'
import api from '../api/client'

// ── Topic chips ─────────────────────────────────────────────────────────────
const TOPICS = [
  {
    key: 'panchangam',
    label: '📅 Panchangam',
    color: '#60a5fa',
    bg: 'rgba(96,165,250,0.15)',
    border: 'rgba(96,165,250,0.35)',
    question: "What does today's Panchangam say for me?",
  },
  {
    key: 'tara',
    label: '⭐ Tara Balam',
    color: '#c084fc',
    bg: 'rgba(192,132,252,0.15)',
    border: 'rgba(192,132,252,0.35)',
    question: "What are my good and bad days this month based on Tara Balam?",
  },
  {
    key: 'dasha',
    label: '🔄 My Dasha',
    color: '#fbbf24',
    bg: 'rgba(251,191,36,0.15)',
    border: 'rgba(251,191,36,0.35)',
    question: "What does my current Mahadasha and Bhukti mean for me?",
  },
  {
    key: 'yoga',
    label: '✨ Yogas',
    color: '#34d399',
    bg: 'rgba(52,211,153,0.15)',
    border: 'rgba(52,211,153,0.35)',
    question: "What yogas do I have and how do they affect my life?",
  },
  {
    key: 'muhurta',
    label: '🕐 Muhurta',
    color: '#fb7185',
    bg: 'rgba(251,113,133,0.15)',
    border: 'rgba(251,113,133,0.35)',
    question: "When is a good time this week to start something important?",
  },
  {
    key: 'planets',
    label: '🪐 Planets',
    color: '#f97316',
    bg: 'rgba(249,115,22,0.15)',
    border: 'rgba(249,115,22,0.35)',
    question: "Which planet is most influential in my chart right now?",
  },
]

// Detect which topic tags fit an AI reply
function detectTopics(text) {
  const t = text.toLowerCase()
  const found = []
  if (/panchangam|vaaram|tithi|nakshatra|yogam|karanam|rahu kalam|sunrise/.test(t))    found.push('panchangam')
  if (/tara|mitra|param|janma|sampat|naidhana|kshema|sadhana|pratyak/.test(t))        found.push('tara')
  if (/mahadasha|bhukti|antardasha|dasha|antar/.test(t))                              found.push('dasha')
  if (/yoga|gajakesari|budha.aditya|vargottama|neecha|raja yoga/.test(t))             found.push('yoga')
  if (/muhurta|auspicious|good time|best time|avoid|wednesday|friday/.test(t))        found.push('muhurta')
  if (/saturn|jupiter|mars|venus|mercury|sun|moon|rahu|ketu|graha|planet/.test(t))    found.push('planets')
  return found
}

const TOPIC_MAP = Object.fromEntries(TOPICS.map(t => [t.key, t]))

// ── Markdown renderer ────────────────────────────────────────────────────────
function MarkdownText({ text }) {
  if (!text) return null
  const lines = text.split('\n')
  const elements = []
  let key = 0
  for (const line of lines) {
    const trimmed = line.trim()
    if (/^[-*]\s+/.test(trimmed)) {
      const content = trimmed.replace(/^[-*]\s+/, '')
      elements.push(
        <div key={key++} style={{ display: 'flex', gap: '6px', marginBottom: '2px' }}>
          <span style={{ color: '#fbbf24', flexShrink: 0, marginTop: '1px' }}>•</span>
          <span>{renderBoldSafe(content)}</span>
        </div>
      )
    } else if (trimmed === '') {
      elements.push(<div key={key++} style={{ height: '6px' }} />)
    } else {
      elements.push(
        <div key={key++} style={{ marginBottom: '2px' }}>
          {renderBoldSafe(trimmed)}
        </div>
      )
    }
  }
  return <div style={{ lineHeight: '1.6' }}>{elements}</div>
}

/**
 * Safe bold renderer — NO dangerouslySetInnerHTML.
 * Splits on **text** markers and returns React <strong> elements.
 * XSS-safe because React escapes all text nodes by default.
 */
function renderBoldSafe(text) {
  if (!text) return null
  const parts = text.split(/\*\*(.+?)\*\*/g)
  return parts.map((part, i) =>
    i % 2 === 1
      ? <strong key={i} style={{ color: '#fef3c7', fontWeight: 600 }}>{part}</strong>
      : part
  )
}

function guessLocation(place) {
  if (!place) return 'Chennai'
  const cities = ['Chennai','Bangalore','Mumbai','Delhi','Hyderabad','Coimbatore','Erlangen']
  const lower = place.toLowerCase()
  return cities.find(c => lower.includes(c.toLowerCase())) || 'Chennai'
}

// ── Component ────────────────────────────────────────────────────────────────
export default function ChatPanel({ chart, placeOfBirth }) {
  const [messages, setMessages]     = useState([])
  const [input, setInput]           = useState('')
  const [loading, setLoading]       = useState(false)
  const [activeTopics, setActive]   = useState([])   // highlighted chips after last AI reply
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = async (text) => {
    const userMsg = text || input.trim()
    if (!userMsg || loading) return

    const newMessages = [...messages, { role: 'user', content: userMsg }]
    setMessages(newMessages)
    setInput('')
    setActive([])
    setLoading(true)

    try {
      const { data } = await api.post('/chat', {
        natal_chart: chart,
        messages: newMessages,
        location: guessLocation(placeOfBirth),
      })
      const reply = data.reply || ''
      setMessages(prev => [...prev, { role: 'assistant', content: reply }])
      setActive(detectTopics(reply))
    } catch (err) {
      const detail = err.response?.data?.detail || 'Something went wrong.'
      setMessages(prev => [...prev, { role: 'assistant', content: `⚠️ ${detail}` }])
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const cardBg    = { background: 'rgba(251,191,36,0.05)', border: '1px solid rgba(251,191,36,0.18)' }
  const userBubble = { background: 'linear-gradient(135deg, #b45309, #d97706)', color: '#fef9ec', borderRadius: '14px 14px 2px 14px' }
  const aiBubble   = { background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.15)', color: 'rgba(254,243,199,0.85)', borderRadius: '2px 14px 14px 14px' }

  return (
    <div className="rounded-2xl overflow-hidden mb-8" style={cardBg}>

      {/* Header */}
      <div className="px-5 py-3 flex items-center gap-2" style={{ borderBottom: '1px solid rgba(251,191,36,0.15)' }}>
        <span className="text-base">🔮</span>
        <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: 'rgba(251,191,36,0.6)' }}>
          Ask Your Chart
        </h3>
        <span className="ml-auto text-xs" style={{ color: 'rgba(254,243,199,0.2)' }}>Powered by GPT-4o mini</span>
      </div>

      {/* Topic chips */}
      <div className="px-4 pt-3 pb-1 flex flex-wrap gap-2">
        {TOPICS.map(topic => {
          const isActive = activeTopics.includes(topic.key)
          return (
            <button
              key={topic.key}
              onClick={() => sendMessage(topic.question)}
              disabled={loading}
              className="text-xs px-3 py-1.5 rounded-full font-semibold transition-all disabled:opacity-40"
              style={{
                background: isActive ? topic.bg : 'rgba(255,255,255,0.04)',
                border: `1px solid ${isActive ? topic.border : 'rgba(255,255,255,0.1)'}`,
                color: isActive ? topic.color : 'rgba(254,243,199,0.45)',
                transform: isActive ? 'scale(1.04)' : 'scale(1)',
                boxShadow: isActive ? `0 0 8px ${topic.bg}` : 'none',
              }}
            >
              {topic.label}
            </button>
          )
        })}
      </div>
      <div className="px-5 pb-1 text-xs" style={{ color: 'rgba(254,243,199,0.2)' }}>
        Tap a topic to ask a suggested question, or type your own below
      </div>

      {/* Messages */}
      <div className="px-4 py-4 space-y-3 min-h-[120px] max-h-[480px] overflow-y-auto">

        {/* Empty state */}
        {messages.length === 0 && (
          <div className="text-center py-6">
            <p className="text-xs mb-1" style={{ color: 'rgba(254,243,199,0.25)' }}>
              Ask anything about your natal chart, Dasha, or life areas.
            </p>
          </div>
        )}

        {/* Conversation */}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className="max-w-[82%] px-4 py-2.5 text-sm leading-relaxed" style={msg.role === 'user' ? userBubble : aiBubble}>
              {msg.role === 'assistant'
                ? <MarkdownText text={msg.content} />
                : msg.content
              }
              {/* Auto-tag badges on AI replies */}
              {msg.role === 'assistant' && i === messages.length - 1 && activeTopics.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2 pt-2" style={{ borderTop: '1px solid rgba(251,191,36,0.1)' }}>
                  {activeTopics.map(key => {
                    const t = TOPIC_MAP[key]
                    if (!t) return null
                    return (
                      <span
                        key={key}
                        className="text-xs px-2 py-0.5 rounded-full cursor-pointer"
                        style={{ background: t.bg, border: `1px solid ${t.border}`, color: t.color }}
                        onClick={() => sendMessage(t.question)}
                        title={`Ask more about ${t.label}`}
                      >
                        {t.label}
                      </span>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="px-4 py-3 rounded-2xl rounded-bl-sm" style={aiBubble}>
              <div className="flex gap-1 items-center">
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#fbbf24', animationDelay:'0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#fbbf24', animationDelay:'150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#fbbf24', animationDelay:'300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 flex gap-2" style={{ borderTop: '1px solid rgba(251,191,36,0.15)' }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask about your chart…"
          disabled={loading}
          className="flex-1 px-4 py-2.5 text-sm rounded-xl focus:outline-none transition-colors disabled:opacity-40 placeholder-amber-100/20"
          style={{ background: 'rgba(251,191,36,0.07)', border: '1px solid rgba(251,191,36,0.2)', color: '#fef3c7' }}
        />
        <button
          onClick={() => sendMessage()}
          disabled={!input.trim() || loading}
          className="px-4 py-2.5 rounded-xl transition-all text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
          style={{ background: 'linear-gradient(135deg, #d97706, #f59e0b)', color: '#1a0e00' }}
        >
          ↑
        </button>
      </div>
    </div>
  )
}

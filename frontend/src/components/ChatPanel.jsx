/**
 * ChatPanel.jsx
 * Multi-turn Vedic astrology chat — golden cosmic theme + topic tagging chips.
 */

import { useState, useRef, useEffect } from 'react'
import api from '../api/client'
import LanguageToggle from './LanguageToggle'
import { chartPayload } from '../lib/chartPayload'
import { formatApiError } from '../lib/apiError'
import { resolvePanchangamLocation } from '../lib/resolveLocation'
import { loadChatMessages, saveChatMessages } from '../lib/chatStorage'
import QuotaHint from './QuotaHint'

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

const CHAT_TR = {
  english: {
    header:      'Ask Your Chart',
    chipHint:    'Tap a topic to ask a suggested question, or type your own below',
    emptyState:  'Ask anything about your natal chart, Dasha, or life areas.',
    placeholder: 'Ask about your chart…',
  },
  tamil: {
    header:      'உங்கள் ஜாதகம் கேளுங்கள்',
    chipHint:    'ஒரு தலைப்பை தட்டவும் அல்லது நீங்களே கேள்வி கேளுங்கள்',
    emptyState:  'உங்கள் ஜாதகம், தசை அல்லது வாழ்க்கைத் துறைகள் பற்றி கேளுங்கள்.',
    placeholder: 'உங்கள் ஜாதகம் பற்றி கேளுங்கள்…',
  },
}

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
          <span style={{ color: '#FF9900', flexShrink: 0, marginTop: '1px' }}>•</span>
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
      ? <strong key={i} style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{part}</strong>
      : part
  )
}

// ── Component ────────────────────────────────────────────────────────────────
export default function ChatPanel({ chart, placeOfBirth, userId }) {
  const [messages, setMessages]     = useState(() => loadChatMessages(chart))
  const [input, setInput]           = useState('')
  const [loading, setLoading]       = useState(false)
  const [activeTopics, setActive]   = useState([])
  const [language, setLanguage]     = useState('english')
  const [lastFailedText, setLastFailedText] = useState('')
  const bottomRef = useRef(null)

  const panchangamLocation = resolvePanchangamLocation(placeOfBirth, chart)

  useEffect(() => {
    if (chart) setMessages(loadChatMessages(chart))
  }, [chart])

  useEffect(() => {
    if (!chart) return
    const toSave = messages.filter(m => m.role === 'user' || m.role === 'assistant')
    if (toSave.length) saveChatMessages(chart, toSave)
  }, [chart, messages])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const runChat = async (msgs, failedText = '') => {
    setLoading(true)
    try {
      const { data } = await api.post('/chat', chartPayload(chart, userId, {
        messages: msgs,
        location: panchangamLocation,
        language,
      }))
      const reply = data.reply || ''
      setMessages(prev => [...prev, { role: 'assistant', content: reply }])
      setActive(detectTopics(reply))
      setLastFailedText('')
    } catch (err) {
      const detail = formatApiError(err, 'Could not get a reply. Please try again.')
      setLastFailedText(failedText || msgs[msgs.length - 1]?.content || '')
      setMessages(prev => [...prev, { role: 'error', content: detail }])
    } finally {
      setLoading(false)
    }
  }

  const sendMessage = async (text) => {
    const userMsg = text || input.trim()
    if (!userMsg || loading) return

    const newMessages = [...messages, { role: 'user', content: userMsg }]
    setMessages(newMessages)
    setInput('')
    setActive([])
    await runChat(newMessages, userMsg)
  }

  const retryLast = async () => {
    const withoutError = messages.filter(m => m.role !== 'error')
    setMessages(withoutError)
    if (withoutError.length) await runChat(withoutError, lastFailedText)
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const cardBg    = { background: 'var(--card-bg)', border: '1px solid var(--card-border)', boxShadow: 'var(--card-shadow)' }
  const userBubble = { background: 'var(--orange)', color: 'var(--accent-dark)', borderRadius: '14px 14px 2px 14px', fontWeight: 500 }
  const aiBubble   = { background: 'var(--bubble-ai-bg)', border: '1px solid var(--bubble-ai-border)', color: 'var(--text-primary)', borderRadius: '2px 14px 14px 14px' }
  const errBubble  = { background: 'var(--error-bg)', border: '1px solid var(--error-border)', color: 'var(--error-text)', borderRadius: '8px' }

  return (
    <div className="rounded-2xl overflow-hidden mb-8" style={cardBg}>

      {/* Header */}
      <div className="px-4 sm:px-5 py-3 flex items-center gap-2 flex-wrap" style={{ borderBottom: '1px solid var(--card-border)', background: 'var(--nav-bg)' }}>
        <span className="text-base">🔮</span>
        <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: 'var(--orange)' }}>
          {(CHAT_TR[language] || CHAT_TR.english).header}
        </h3>
        <div className="ml-auto flex items-center gap-3">
          <LanguageToggle language={language} onChange={setLanguage} />
          <span className="text-xs hidden sm:block" style={{ color: 'rgba(255,255,255,0.4)' }}>
            {panchangamLocation}
          </span>
        </div>
      </div>

      <p className="legal-inline-hint px-4 pb-1 text-xs" style={{ color: 'var(--text-muted)' }}>
        AI responses are for entertainment and informational purposes only — not professional advice.
      </p>

      <div className="px-4 pt-2">
        <QuotaHint userId={userId} />
      </div>

      {/* Topic chips */}
      <div className="chat-topic-chips px-4 pt-3 pb-1 flex flex-wrap sm:flex-wrap gap-2">
        {TOPICS.map(topic => {
          const isActive = activeTopics.includes(topic.key)
          return (
            <button
              key={topic.key}
              onClick={() => sendMessage(topic.question)}
              disabled={loading}
              className="text-xs px-3 py-1.5 rounded-full font-semibold transition-all disabled:opacity-40"
              style={{
                background: isActive ? topic.bg : 'var(--chip-bg)',
                border: `1px solid ${isActive ? topic.border : 'var(--chip-border)'}`,
                color: isActive ? topic.color : 'var(--text-secondary)',
                transform: isActive ? 'scale(1.04)' : 'scale(1)',
              }}
            >
              {topic.label}
            </button>
          )
        })}
      </div>
      <div className="px-5 pb-1 text-xs" style={{ color: 'var(--text-muted)' }}>
        {(CHAT_TR[language] || CHAT_TR.english).chipHint}
      </div>

      {/* Messages */}
      <div className="px-3 sm:px-4 py-4 space-y-3 min-h-[120px] max-h-[50vh] sm:max-h-[480px] overflow-y-auto" style={{ background: 'var(--surface-chat)' }}>

        {/* Empty state */}
        {messages.length === 0 && (
          <div className="text-center py-6">
            <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>
              {(CHAT_TR[language] || CHAT_TR.english).emptyState}
            </p>
          </div>
        )}

        {/* Conversation */}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className="max-w-[88%] sm:max-w-[82%] px-4 py-2.5 text-sm leading-relaxed"
              style={
                msg.role === 'user' ? userBubble
                  : msg.role === 'error' ? errBubble
                    : aiBubble
              }
              role={msg.role === 'error' ? 'alert' : undefined}
            >
              {msg.role === 'assistant'
                ? <MarkdownText text={msg.content} />
                : msg.content
              }
              {msg.role === 'error' && i === messages.length - 1 && (
                <button type="button" className="chat-retry-btn" onClick={retryLast}>
                  Retry
                </button>
              )}
              {/* Auto-tag badges on AI replies */}
              {msg.role === 'assistant' && i === messages.length - 1 && activeTopics.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2 pt-2" style={{ borderTop: '1px solid var(--card-border)' }}>
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
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#FF9900', animationDelay:'0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#FF9900', animationDelay:'150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#FF9900', animationDelay:'300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-3 sm:px-4 py-3 flex gap-2" style={{ borderTop: '1px solid var(--card-border)', background: 'var(--card-bg)' }}>
        <label htmlFor="chat-input" className="sr-only">Your question</label>
        <input
          id="chat-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder={(CHAT_TR[language] || CHAT_TR.english).placeholder}
          disabled={loading}
          className="flex-1 px-4 py-2.5 text-base sm:text-sm rounded-xl focus:outline-none transition-colors disabled:opacity-40"
          style={{ background: 'var(--input-bg)', border: '1px solid var(--input-border)', color: 'var(--input-text)' }}
        />
        <button
          type="button"
          onClick={() => sendMessage()}
          disabled={!input.trim() || loading}
          aria-label="Send message"
          className="chat-send-btn px-4 py-2.5 rounded-xl transition-all text-sm font-bold disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
          style={{ background: 'var(--orange)', color: 'var(--accent-dark)' }}
        >
          ↑
        </button>
      </div>
    </div>
  )
}

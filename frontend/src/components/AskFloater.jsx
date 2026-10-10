/**
 * Floating Ask box. Same generative chat as Ask AI, available on every other page.
 * The model writes the reply. Chart numbers come from the app's tools.
 */
import { useEffect, useRef, useState } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'
import { formatApiError } from '../lib/apiError'
import { resolvePanchangamLocation } from '../lib/resolveLocation'
import { loadChatMessages, saveChatMessages } from '../lib/chatStorage'
import ChartEvidence from './ChartEvidence'

function visibleThread(messages) {
  return messages.filter((message) => message.role === 'user' || message.role === 'assistant')
}

export default function AskFloater({ chart, userId, placeOfBirth, page }) {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState(() => visibleThread(loadChatMessages(chart)))
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)
  const location = resolvePanchangamLocation(placeOfBirth, chart)

  useEffect(() => {
    setMessages(visibleThread(loadChatMessages(chart)))
  }, [chart])

  useEffect(() => {
    if (!chart || !messages.length) return
    saveChatMessages(chart, messages)
  }, [chart, messages])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading, open])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    const next = [...messages, { role: 'user', content: text }]
    setMessages(next)
    setInput('')
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post('/chat', chartPayload(chart, userId, {
        messages: next,
        location,
        language: 'english',
        page,
      }))
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply || '' }])
    } catch (err) {
      setError(formatApiError(err, 'Could not get a reply. Please try again.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed z-40 right-3 bottom-20 sm:bottom-6" style={{ width: open ? 'min(22rem, calc(100vw - 1.5rem))' : 'auto' }}>
      {open && (
        <section
          className="mb-2 rounded-xl overflow-hidden flex flex-col"
          style={{
            height: 'min(28rem, 70vh)',
            background: 'var(--card-bg)',
            border: '1px solid var(--card-border)',
            boxShadow: 'var(--card-shadow)',
          }}
          aria-label="Ask about this chart"
        >
          <header className="px-3 py-2 flex items-center justify-between" style={{ borderBottom: '1px solid var(--card-border)' }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 800, color: 'var(--text-primary)' }}>Ask</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{page}</div>
            </div>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close ask" style={{ color: 'var(--text-secondary)', fontSize: 18 }}>
              ×
            </button>
          </header>
          <div className="flex-1 overflow-y-auto px-3 py-2" style={{ display: 'grid', gap: 8, alignContent: 'start' }}>
            {messages.length === 0 && (
              <p style={{ margin: 0, fontSize: 13, lineHeight: 1.45, color: 'var(--text-secondary)' }}>
                Ask about this page. The reply is written by the model from your chart. Strength, condition, the current period, and today’s sky come from this app.
              </p>
            )}
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`}>
                <p
                  style={{
                    margin: 0,
                    fontSize: 13,
                    lineHeight: 1.45,
                    whiteSpace: 'pre-wrap',
                    color: 'var(--text-primary)',
                    background: message.role === 'user' ? 'var(--highlight-bg)' : 'transparent',
                    borderRadius: 8,
                    padding: message.role === 'user' ? '6px 8px' : 0,
                  }}
                >
                  {message.content}
                </p>
                {message.role === 'assistant' && (
                  <ChartEvidence
                    chart={chart}
                    userId={userId}
                    question={messages[index - 1]?.role === 'user' ? messages[index - 1].content : ''}
                  />
                )}
              </div>
            ))}
            {loading && <p style={{ margin: 0, fontSize: 12, color: 'var(--text-muted)' }}>Reading the chart…</p>}
            {error && <p style={{ margin: 0, fontSize: 12, color: '#c0392b' }}>{error}</p>}
            <div ref={bottomRef} />
          </div>
          <form
            className="px-3 py-2 flex gap-2"
            style={{ borderTop: '1px solid var(--card-border)' }}
            onSubmit={(event) => { event.preventDefault(); send() }}
          >
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask about this chart"
              aria-label="Ask about this chart"
              className="flex-1 rounded-lg px-2 py-2 text-sm"
              style={{ border: '1px solid var(--card-border)', background: 'var(--highlight-bg)', color: 'var(--text-primary)' }}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="rounded-lg px-3 text-sm font-semibold"
              style={{ background: 'var(--orange)', color: 'var(--accent-dark)', opacity: loading || !input.trim() ? 0.5 : 1 }}
            >
              Send
            </button>
          </form>
        </section>
      )}
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="ml-auto block rounded-full px-4 py-2 text-sm font-bold"
        style={{ background: 'var(--orange)', color: 'var(--accent-dark)', boxShadow: 'var(--card-shadow)' }}
      >
        Ask
      </button>
    </div>
  )
}

import { useState } from 'react'
import { getNativeNote } from '../lib/nativeNote'
import { loadSitting, matchQuestion } from '../lib/chartEvidence'

export default function ChartEvidence({ chart, userId, question }) {
  const [open, setOpen] = useState(false)
  const [reading, setReading] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const show = async () => {
    if (open) {
      setOpen(false)
      return
    }
    setOpen(true)
    setLoading(true)
    setError('')
    try {
      setReading(await loadSitting(chart, userId))
    } catch {
      setError('The chart evidence could not be loaded.')
    } finally {
      setLoading(false)
    }
  }

  const note = getNativeNote()
  const questionId = matchQuestion(question, note)
  const row = (reading?.life || []).find((item) => item.id === questionId)
  const timeline = reading?.timeline

  return (
    <div className="mt-2 pt-2" style={{ borderTop: '1px solid var(--card-border)' }}>
      <button
        type="button"
        onClick={show}
        aria-expanded={open}
        className="text-xs font-semibold min-h-[44px] w-full text-left px-1"
        style={{ color: 'var(--text-secondary)', background: 'transparent' }}
      >
        {open ? 'Hide the evidence' : 'Show the evidence'}
      </button>
      {open && (
        <div className="space-y-1 pb-1" style={{ overflowWrap: 'anywhere' }}>
          {loading && <p className="text-xs m-0" style={{ color: 'var(--text-muted)' }}>Reading the chart…</p>}
          {error && <p className="text-xs m-0" style={{ color: 'var(--orange)' }}>{error}</p>}
          {timeline && (
            <>
              <p className="text-xs m-0" style={{ color: 'var(--text-primary)' }}>{timeline.past}</p>
              <p className="text-xs m-0" style={{ color: 'var(--text-primary)' }}>{timeline.today}</p>
              <p className="text-xs m-0" style={{ color: 'var(--text-primary)' }}>{timeline.next}</p>
            </>
          )}
          {row && (
            <div className="space-y-1 pt-1">
              <p className="text-xs font-semibold m-0" style={{ color: 'var(--text-primary)' }}>
                {row.label}. {row.season_status}
              </p>
              {(row.house?.lines || []).map((line) => (
                <p key={line} className="text-xs m-0" style={{ color: 'var(--text-secondary)' }}>{line}</p>
              ))}
            </div>
          )}
          {reading && !row && (
            <p className="text-xs m-0" style={{ color: 'var(--text-muted)' }}>
              This question does not name one house. The lines above are the period and the open seasons.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

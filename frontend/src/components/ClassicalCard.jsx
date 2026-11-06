/**
 * ClassicalCard — BPHS chapter 24 rules for this chart, one per house lord.
 */
import { useState } from 'react'

const TONE_STYLE = {
  favourable: { label: 'Favourable', color: 'var(--rag-green-text)', background: 'var(--rag-green-bg)', border: 'var(--rag-green-border)' },
  mixed: { label: 'Mixed', color: 'var(--rag-amber-text)', background: 'var(--rag-amber-bg)', border: 'var(--rag-amber-border)' },
  challenging: { label: 'Challenging', color: 'var(--rag-red-text)', background: 'var(--rag-red-bg)', border: 'var(--rag-red-border)' },
}

const TOPICS = [
  { id: '', label: 'All', match: null },
  { id: 'career', label: 'Career', match: ['career', 'status'] },
  { id: 'wealth', label: 'Wealth', match: ['wealth', 'gains', 'income'] },
  { id: 'marriage', label: 'Marriage', match: ['marriage', 'partnership'] },
  { id: 'children', label: 'Children', match: ['children', 'education'] },
  { id: 'health', label: 'Health', match: ['health'] },
  { id: 'foreign', label: 'Foreign', match: ['foreign'] },
  { id: 'home', label: 'Home', match: ['home', 'mother', 'property'] },
]

function ordinal(n) {
  const tail = n % 100 >= 11 && n % 100 <= 13 ? 'th' : { 1: 'st', 2: 'nd', 3: 'rd' }[n % 10] || 'th'
  return `${n}${tail}`
}

export function ToneBadge({ tone }) {
  const style = TONE_STYLE[tone] || TONE_STYLE.mixed
  return (
    <span
      className="inline-block rounded px-1.5 py-0.5 text-xs font-semibold whitespace-nowrap"
      style={{ color: style.color, background: style.background, border: `1px solid ${style.border}` }}
    >
      {style.label}
    </span>
  )
}

function Rule({ match }) {
  const [open, setOpen] = useState(false)
  return (
    <li>
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className="w-full text-left rounded-md px-2.5 py-2.5 min-h-[44px]"
        style={{ background: 'var(--surface-muted)', border: '1px solid var(--card-border)', color: 'var(--text-primary)' }}
      >
        <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <span className="text-sm font-semibold" style={{ overflowWrap: 'anywhere' }}>
            {ordinal(match.lord_of)} lord {match.lord} in the {ordinal(match.in_house)}
          </span>
          <ToneBadge tone={match.tone} />
          {match.strength_label && (
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{match.strength_label}</span>
          )}
        </span>
        <span className="block text-sm mt-1" style={{ overflowWrap: 'anywhere' }}>{match.summary}</span>
      </button>
      {open && (
        <div className="px-2 py-2 space-y-2 text-sm" style={{ color: 'var(--text-primary)', overflowWrap: 'anywhere' }}>
          <p className="m-0">
            <span className="font-semibold">Why it matched. </span>{match.why}
          </p>
          <div className="rounded-md px-2.5 py-2 space-y-1" style={{ border: '1px solid var(--card-border)' }}>
            <p className="m-0 text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>
              {match.source.cite} · original verse
            </p>
            <p className="m-0">{match.source.translation}</p>
            <p className="m-0" lang="sa" style={{ color: 'var(--text-secondary)' }}>{match.source.sanskrit}</p>
            <p className="m-0 italic whitespace-pre-line" style={{ color: 'var(--text-muted)' }}>
              {match.source.transliteration.replace(/\s*\.(?=\S)/g, '\n')}
            </p>
          </div>
        </div>
      )}
    </li>
  )
}

export default function ClassicalCard({ data, error }) {
  const [topic, setTopic] = useState('')
  if (error) {
    return <p className="text-sm" style={{ color: 'var(--orange)' }}>{error}</p>
  }
  if (!data?.matches?.length) return null

  const filter = TOPICS.find((item) => item.id === topic)
  const matches = filter?.match
    ? data.matches.filter((match) => match.topics.some((t) => filter.match.includes(t)))
    : data.matches
  const shownHouses = new Set(matches.map((match) => match.lord_of))
  const dual = (data.dual_lordship || []).filter((note) => note.houses.some((h) => shownHouses.has(h)))

  return (
    <section
      aria-labelledby="classical-heading"
      className="rounded-lg px-3 py-3 space-y-3"
      style={{ background: 'var(--card-bg)', border: '1px solid var(--card-border)' }}
    >
      <header>
        <h3 id="classical-heading" className="text-sm font-semibold m-0" style={{ color: 'var(--text-primary)' }}>
          Classical texts · BPHS chapter 24
        </h3>
        <p className="text-sm mt-1 mb-0" style={{ color: 'var(--text-muted)', overflowWrap: 'break-word' }}>
          Where each house lord sits, and what Parashara says of it. Tap a rule for the reason and the verse.
        </p>
      </header>

      <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by topic">
        {TOPICS.map((item) => {
          const selected = topic === item.id
          return (
            <button
              key={item.label}
              type="button"
              aria-pressed={selected}
              onClick={() => setTopic(item.id)}
              className="rounded-md px-3 text-sm font-semibold min-h-[44px]"
              style={{
                background: selected ? 'var(--orange)' : 'var(--surface-muted)',
                color: selected ? 'var(--accent-dark)' : 'var(--text-primary)',
                border: '1px solid var(--card-border)',
              }}
            >
              {item.label}
            </button>
          )
        })}
      </div>

      <ul className="space-y-2 list-none p-0 m-0">
        {matches.map((match) => <Rule key={match.id} match={match} />)}
      </ul>

      {dual.length > 0 && (
        <div className="space-y-1">
          <p className="text-sm font-semibold m-0" style={{ color: 'var(--text-primary)' }}>Planets ruling two houses</p>
          {dual.map((note) => (
            <p key={note.lord} className="text-sm m-0" style={{ color: 'var(--text-primary)', overflowWrap: 'anywhere' }}>
              {note.note}
            </p>
          ))}
        </div>
      )}

      <p className="text-xs m-0" style={{ color: 'var(--text-muted)', overflowWrap: 'anywhere' }}>
        Summaries are written for this app. Verse text: {data.source.attribution} ({data.source.license}).
      </p>
    </section>
  )
}

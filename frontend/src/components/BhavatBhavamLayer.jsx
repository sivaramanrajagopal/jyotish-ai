/**
 * BhavatBhavamLayer — collapsible D1 house-from-house links (Health / Career).
 */
const SIGNAL_CLASS = {
  support: 'bb-signal--support',
  watch: 'bb-signal--watch',
  neutral: 'bb-signal--neutral',
}

const SIGNAL_LABEL = {
  support: { en: 'Support path', ta: 'ஆதரவு வழி' },
  watch: { en: 'Watch', ta: 'கவனம்' },
  neutral: { en: 'Neutral', ta: 'நடுநிலை' },
}

function Bilingual({ en, ta, inline = false }) {
  if (inline) {
    return (
      <span>
        <span className="bb-bi__en">{en}</span>
        {ta && <span className="bb-bi__ta"> · {ta}</span>}
      </span>
    )
  }
  return (
    <span>
      <span className="bb-bi__en">{en}</span>
      {ta && <span className="bb-bi__ta">{ta}</span>}
    </span>
  )
}

function LinkCard({ link }) {
  const cls = SIGNAL_CLASS[link.signal] || SIGNAL_CLASS.neutral
  const label = SIGNAL_LABEL[link.signal] || SIGNAL_LABEL.neutral
  return (
    <article className={`bb-link ${cls}`}>
      <div className="bb-link__top">
        <span className="bb-link__houses">
          H{link.primary_house} → H{link.bb_house}
        </span>
        <span className={`bb-signal ${cls}`}>
          {label.en} / {label.ta}
        </span>
      </div>
      <p className="bb-link__theme">
        <Bilingual en={link.theme_en} ta={link.theme_ta} inline />
      </p>
      <p className="bb-link__lords">
        Lords: <strong>{link.primary_lord}</strong> → <strong>{link.bb_lord}</strong>
        {link.primary_planets?.length > 0 && (
          <span className="bb-link__meta">
            {' '}· H{link.primary_house}: {link.primary_planets.join(', ')}
          </span>
        )}
        {link.bb_planets?.length > 0 && (
          <span className="bb-link__meta">
            {' '}· H{link.bb_house}: {link.bb_planets.join(', ')}
          </span>
        )}
      </p>
      <p className="bb-link__insight">
        <Bilingual en={link.insight_en} ta={link.insight_ta} />
      </p>
      {link.lord_links?.length > 0 && (
        <p className="bb-link__meta">
          Lord links: {link.lord_links.join(' · ')}
        </p>
      )}
    </article>
  )
}

export default function BhavatBhavamLayer({ data, variant = 'health' }) {
  if (!data?.links?.length) return null

  const title = variant === 'career'
    ? { en: 'Bhavat Bhavam — career support', ta: 'பாவத்தின் பாவம் — தொழில் ஆதரவு' }
    : { en: 'Bhavat Bhavam — recovery paths', ta: 'பாவத்தின் பாவம் — குணமடைதல் வழி' }

  return (
    <details className="bb-layer" open={data.links.length <= 2}>
      <summary className="bb-layer__summary">
        <Bilingual en={title.en} ta={title.ta} inline />
        <span className="bb-layer__count">({data.active_count})</span>
      </summary>
      <div className="bb-layer__body">
        {data.disclaimer?.en && (
          <p className="bb-disclaimer">
            <Bilingual en={data.disclaimer.en} ta={data.disclaimer.ta} inline />
          </p>
        )}
        <div className="bb-links">
          {data.links.map(link => (
            <LinkCard key={`${link.primary_house}-${link.bb_house}`} link={link} />
          ))}
        </div>
      </div>
    </details>
  )
}

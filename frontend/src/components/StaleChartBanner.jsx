import { isChartLikelyStale } from '../lib/chartStale'

export default function StaleChartBanner({ chart, onRecalculate }) {
  if (!isChartLikelyStale(chart)) return null

  return (
    <div
      className="stale-chart-banner rounded-lg px-4 py-3 mb-6 text-sm"
      style={{
        background: 'var(--error-bg)',
        border: '1px solid var(--error-border)',
        color: 'var(--error-text)',
        lineHeight: 1.5,
      }}
    >
      <strong>Chart update recommended.</strong>{' '}
      Your saved chart may use outdated planetary positions (ayanamsa mismatch).
      Recalculate on the Home tab so Ashtakavarga, forecast scores, and chat use correct Lahiri positions.
      {onRecalculate && (
        <div className="stale-chart-banner__action">
          <button
            type="button"
            onClick={onRecalculate}
            className="stale-chart-banner__btn"
          >
            Go to Home →
          </button>
        </div>
      )}
    </div>
  )
}

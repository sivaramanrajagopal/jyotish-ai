import { useEffect, useState } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'

/**
 * BPHS chapter 24 rules matched to the chart. Returns null data when the
 * server has the classical rules switched off (404), so callers render nothing.
 * Each result is kept with the chart it was fetched for, so a new chart never
 * shows the previous chart's rules while its own request is in flight.
 */
export function useClassicalRules(chart, userId, enabled = true) {
  const [result, setResult] = useState({ chart: null, data: null, error: '' })

  useEffect(() => {
    if (!chart || !enabled) return undefined
    let cancel = false
    api.post('/classical/matches', chartPayload(chart, userId))
      .then((res) => {
        if (!cancel) setResult({ chart, data: res.data, error: '' })
      })
      .catch((err) => {
        if (cancel) return
        const error = err.response?.status === 404
          ? ''
          : err.response?.data?.detail || 'Could not load the classical rules.'
        setResult({ chart, data: null, error })
      })
    return () => { cancel = true }
  }, [chart, userId, enabled])

  const current = result.chart === chart
  return {
    data: current ? result.data : null,
    error: current ? result.error : '',
    loading: Boolean(chart && enabled && !current),
  }
}

export function classicalForHouse(data, house) {
  return (data?.matches || []).find((match) => match.lord_of === house) || null
}

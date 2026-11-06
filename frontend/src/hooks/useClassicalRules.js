import { useEffect, useState } from 'react'
import api from '../api/client'
import { chartPayload } from '../lib/chartPayload'

/**
 * BPHS chapter 24 rules matched to the chart. Returns null data when the
 * server has the classical rules switched off (404), so callers render nothing.
 */
export function useClassicalRules(chart, userId, enabled = true) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!chart || !enabled) return undefined
    let cancel = false
    api.post('/classical/matches', chartPayload(chart, userId))
      .then((res) => {
        if (cancel) return
        setData(res.data)
        setError('')
      })
      .catch((err) => {
        if (cancel) return
        setData(null)
        if (err.response?.status !== 404) {
          setError(err.response?.data?.detail || 'Could not load the classical rules.')
        }
      })
    return () => { cancel = true }
  }, [chart, userId, enabled])

  return { data, error }
}

export function classicalForHouse(data, house) {
  return (data?.matches || []).find((match) => match.lord_of === house) || null
}

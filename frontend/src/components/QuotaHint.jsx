import { useEffect, useState } from 'react'
import api from '../api/client'

export default function QuotaHint({ userId }) {
  const [usage, setUsage] = useState(null)

  useEffect(() => {
    const url = userId ? '/auth/usage' : '/auth/anon-usage'
    api.get(url)
      .then(r => setUsage(r.data))
      .catch(() => setUsage(null))
  }, [userId])

  if (!usage) return null

  const chatLeft = Math.max(0, usage.chat_limit - usage.chat_count)
  const forecastLeft = Math.max(0, usage.forecast_limit - usage.forecast_count)
  const guestNote = usage.is_guest ? ' (guest — sign in for more)' : ''

  return (
    <p className="quota-hint" role="status">
      AI today: {chatLeft} chat · {forecastLeft} forecast remaining{guestNote}
    </p>
  )
}

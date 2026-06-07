import { useEffect, useState } from 'react'
import api from '../api/client'

export default function QuotaHint({ userId }) {
  const [usage, setUsage] = useState(null)

  useEffect(() => {
    if (!userId) {
      setUsage(null)
      return
    }
    api.get('/auth/usage')
      .then(r => setUsage(r.data))
      .catch(() => setUsage(null))
  }, [userId])

  if (!usage) return null

  const chatLeft = Math.max(0, usage.chat_limit - usage.chat_count)
  const forecastLeft = Math.max(0, usage.forecast_limit - usage.forecast_count)

  return (
    <p className="quota-hint" role="status">
      AI today: {chatLeft} chat · {forecastLeft} forecast remaining
    </p>
  )
}

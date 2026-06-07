import axios from 'axios'
import { supabase } from '../lib/supabase'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Attach Supabase JWT when the user is signed in (Step 2; verified on backend in Step 3).
api.interceptors.request.use(async (config) => {
  if (!supabase) return config
  try {
    const { data: { session } } = await supabase.auth.getSession()
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`
    }
  } catch {
    // Proceed without auth header
  }
  return config
})

export default api

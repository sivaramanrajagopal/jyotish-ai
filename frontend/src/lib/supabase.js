import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL?.trim()
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY?.trim()

const PLACEHOLDER_MARKERS = ['your-project-id', 'your-anon-key', 'xxx.supabase.co']

function isRealValue(value) {
  if (!value) return false
  const lower = value.toLowerCase()
  return !PLACEHOLDER_MARKERS.some((m) => lower.includes(m))
}

/** True when Vercel/local env has Supabase public keys (Step 2). */
export function isSupabaseConfigured() {
  return isRealValue(url) && isRealValue(anonKey)
}

export const supabase = isSupabaseConfigured()
  ? createClient(url, anonKey, {
      auth: {
        persistSession: true,
        detectSessionInUrl: true,
        flowType: 'pkce',
      },
    })
  : null

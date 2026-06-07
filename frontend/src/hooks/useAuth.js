import { useState, useEffect, useCallback } from 'react'
import { supabase, isSupabaseConfigured } from '../lib/supabase'
import { getAuthRedirectUrl } from '../lib/authRedirect'

export function useAuth() {
  const configured = isSupabaseConfigured()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(configured)

  useEffect(() => {
    if (!supabase) {
      setLoading(false)
      return undefined
    }

    let mounted = true

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (mounted) {
        setUser(session?.user ?? null)
        setLoading(false)
      }
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => {
      mounted = false
      subscription.unsubscribe()
    }
  }, [])

  const signInWithMagicLink = useCallback(async (email) => {
    if (!supabase) {
      throw new Error('Sign-in is not configured yet.')
    }
    const redirectTo = getAuthRedirectUrl()
    if (!redirectTo) {
      throw new Error('Could not determine redirect URL.')
    }
    const { error } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: { emailRedirectTo: redirectTo },
    })
    if (error) throw error
  }, [])

  const signOut = useCallback(async () => {
    if (!supabase) return
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  }, [])

  return {
    configured,
    user,
    loading,
    userId: user?.id ?? null,
    email: user?.email ?? null,
    signInWithMagicLink,
    signOut,
  }
}

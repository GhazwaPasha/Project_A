'use client'

import { useEffect, useRef } from 'react'
import { createClient } from '@/lib/supabase'
import { useAuthStore } from '@/stores/auth-store'
import { User } from '@/types'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { setUser, setLoading, logout, loadUserData } = useAuthStore()
  const supabase = createClient()
  const hasLoadedRef = useRef(false)

  useEffect(() => {
    const getSession = async () => {
      setLoading(true)
      try {
        const { data: { session } } = await supabase.auth.getSession()
        
        if (session?.user) {
          const user: User = {
            id: session.user.id,
            email: session.user.email!,
            created_at: session.user.created_at,
            updated_at: session.user.updated_at,
            email_confirmed_at: session.user.email_confirmed_at,
            last_sign_in_at: session.user.last_sign_in_at,
          }
          setUser(user)
          // Load user profile and organizations only once on initial mount
          if (!hasLoadedRef.current) {
            await loadUserData()
            hasLoadedRef.current = true
          }
        } else {
          logout()
        }
      } catch (error) {
        console.error('Error getting session:', error)
        logout()
      } finally {
        setLoading(false)
      }
    }

    getSession()

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        // Only reload user data on actual auth events, not on token refresh
        if (event === 'SIGNED_IN' || event === 'USER_UPDATED') {
          if (session?.user) {
            const user: User = {
              id: session.user.id,
              email: session.user.email!,
              created_at: session.user.created_at,
              updated_at: session.user.updated_at,
              email_confirmed_at: session.user.email_confirmed_at,
              last_sign_in_at: session.user.last_sign_in_at,
            }
            setUser(user)
            // Load user profile and organizations
            await loadUserData()
            hasLoadedRef.current = true
          }
        } else if (event === 'SIGNED_OUT') {
          logout()
          hasLoadedRef.current = false
        }
      }
    )

    return () => subscription.unsubscribe()
  }, [setUser, setLoading, logout, loadUserData, supabase.auth])

  return <>{children}</>
}

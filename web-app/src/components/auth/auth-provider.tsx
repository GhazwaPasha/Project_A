'use client'

import { useEffect } from 'react'
import { createClient } from '@/lib/supabase'
import { useAuthStore } from '@/stores/auth-store'
import { User } from '@/types'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { setUser, setLoading, logout, loadUserData } = useAuthStore()
  const supabase = createClient()

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
          // Load user profile and organizations
          await loadUserData()
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
        } else {
          logout()
        }
      }
    )

    return () => subscription.unsubscribe()
  }, [setUser, setLoading, logout, loadUserData, supabase.auth])

  return <>{children}</>
}

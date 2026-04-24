'use client'

import { useEffect, useRef } from 'react'
import { authClient } from '@/lib/auth-client'
import { useAuthStore } from '@/stores/auth-store'
import { User } from '@/types'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { data, isPending } = authClient.useSession()
  const { setUser, setLoading, logout, loadUserData } = useAuthStore()
  const lastLoadedUserId = useRef<string | null>(null)

  useEffect(() => {
    if (isPending) {
      setLoading(true)
      return
    }
    setLoading(false)

    if (data?.user?.id && data.user.email) {
      const now = new Date().toISOString()
      const user: User = {
        id: data.user.id,
        email: data.user.email,
        created_at: now,
        updated_at: now,
      }
      setUser(user)

      if (lastLoadedUserId.current !== data.user.id) {
        lastLoadedUserId.current = data.user.id
        void loadUserData()
      }
      return
    }

    // `data === undefined` is common while the session is refetching. Do not logout
    // (avoids brief default theme + re-applying accent when the session result returns).
    if (data === undefined) {
      return
    }

    lastLoadedUserId.current = null
    logout()
  }, [data, isPending, setUser, setLoading, logout, loadUserData])

  return <>{children}</>
}

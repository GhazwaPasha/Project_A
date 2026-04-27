'use client'

import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { authClient } from '@/lib/auth-client'
import { useAuthStore } from '@/stores/auth-store'
import { User } from '@/types'

/** If session GET errored, keep the local app session for network / server hiccups (not 401/403). */
function isTransientSessionFetchError(error: { status?: number }): boolean {
  const s = error.status
  if (s === 401 || s === 403) return false
  if (s == null) return true
  if (s === 0 || s === 429 || s === 408) return true
  if (s >= 500) return true
  if (s >= 400) return true
  return false
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { data, isPending, isRefetching, error: sessionError } = authClient.useSession()
  const queryClient = useQueryClient()
  const { setUser, setLoading, logout, loadUserData, clearForAccountSwitch, reconcilePersistedForSessionUser } =
    useAuthStore()
  const lastLoadedUserId = useRef<string | null>(null)
  const sessionUserIdRef = useRef<string | null>(null)

  useEffect(() => {
    sessionUserIdRef.current = data?.user?.id ?? null
  }, [data?.user?.id])

  useEffect(() => {
    return useAuthStore.persist.onFinishHydration(() => {
      const id = sessionUserIdRef.current
      if (id) {
        const s = useAuthStore.getState()
        s.reconcilePersistedForSessionUser(id)
        s.syncOrgQueries(id)
      }
    })
  }, [])

  useEffect(() => {
    if (isPending) {
      setLoading(true)
      return
    }
    setLoading(false)

    if (data?.user?.id && data.user.email) {
      const prevSessionUserId = lastLoadedUserId.current
      const switchingAccount =
        prevSessionUserId !== null && prevSessionUserId !== data.user.id

      if (switchingAccount) {
        clearForAccountSwitch()
        queryClient.clear()
      }

      const now = new Date().toISOString()
      const user: User = {
        id: data.user.id,
        email: data.user.email,
        created_at: now,
        updated_at: now,
      }
      reconcilePersistedForSessionUser(data.user.id)
      setUser(user)
      if (prevSessionUserId !== data.user.id) {
        lastLoadedUserId.current = data.user.id
        useAuthStore.getState().syncOrgQueries(data.user.id)
        void loadUserData()
      }
      return
    }

    if (isRefetching) {
      return
    }

    // `data === undefined` is common while the session is refetching. Do not logout
    // (avoids brief default theme + re-applying accent when the session result returns).
    if (data === undefined) {
      return
    }

    if (lastLoadedUserId.current && sessionError && isTransientSessionFetchError(sessionError)) {
      return
    }

    lastLoadedUserId.current = null
    logout()
  }, [data, isPending, isRefetching, sessionError, setUser, setLoading, logout, loadUserData, clearForAccountSwitch, queryClient])

  return <>{children}</>
}

'use client'

import { useEffect, useRef } from 'react'
import { useAuthStore } from '@/stores/auth-store'
import type { AppShellServerBootstrap } from '@/types/app-shell'

type Props = { bootstrap: AppShellServerBootstrap | null | undefined }

/**
 * Applies RSC-fetched org list + profile into the auth store when the client is still
 * empty (e.g. cold without localStorage rehydration yet), so the shell is consistent
 * with the server and `HydrationBoundary` data.
 */
export function AppShellBootstrapSeed({ bootstrap }: Props) {
  const user = useAuthStore((s) => s.user)
  const orgCount = useAuthStore((s) => s.organizations.length)
  const doneRef = useRef(false)

  useEffect(() => {
    if (!bootstrap || !user || user.id !== bootstrap.userId) return
    if (doneRef.current) return
    if (orgCount > 0) return
    doneRef.current = true
    void useAuthStore.getState().applyAppShellServerSnapshot(bootstrap)
  }, [bootstrap, user, orgCount])

  return null
}

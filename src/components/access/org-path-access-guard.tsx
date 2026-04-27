'use client'

import { useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/auth-store'
import { canAccessPathname, getDefaultHomePath } from '@/lib/org-nav-access'

/**
 * Redirects when the current org role may not open this URL (e.g. member on /journal or /home).
 *
 * Role is read synchronously from the persisted Zustand store so there is no post-render flash.
 * The useEffect handles the actual navigation; the synchronous check suppresses the protected
 * page content while the redirect is in flight.
 */
export function OrgPathAccessGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()

  // Read directly from the persisted store — no loading state needed since Zustand rehydrates
  // from localStorage synchronously before the first render.
  const role = useAuthStore.getState().currentOrgMemberRole
  const resolved = useAuthStore.getState().orgMemberRoleResolved
  const isSuper = useAuthStore.getState().profile?.is_super_admin === true

  // Keep the redirect in an effect so Next.js router is ready.
  useEffect(() => {
    if (!resolved) return
    if (canAccessPathname(pathname, role, isSuper)) return
    router.replace(getDefaultHomePath(role, isSuper))
  }, [pathname, role, resolved, isSuper, router])

  // Synchronous guard: suppress content immediately (no "Redirecting…" flash frame)
  if (resolved && !canAccessPathname(pathname, role, isSuper)) {
    return null
  }

  return <>{children}</>
}

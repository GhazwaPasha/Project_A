'use client'

import { useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/auth-store'
import { canAccessPathname, getDefaultHomePath } from '@/lib/org-nav-access'

/**
 * Redirects when the current org role may not open this URL (e.g. member on /journal or /home).
 */
export function OrgPathAccessGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const role = useAuthStore((s) => s.currentOrgMemberRole)
  const resolved = useAuthStore((s) => s.orgMemberRoleResolved)
  const isSuper = useAuthStore((s) => s.profile?.is_super_admin) === true

  useEffect(() => {
    if (!resolved) return
    if (canAccessPathname(pathname, role, isSuper)) return
    router.replace(getDefaultHomePath(role, isSuper))
  }, [pathname, role, resolved, isSuper, router])

  if (resolved && !canAccessPathname(pathname, role, isSuper)) {
    return (
      <div
        className="flex min-h-[40vh] items-center justify-center p-6 text-on-surface-variant"
        style={{ backgroundColor: 'var(--md-sys-color-background)' }}
      >
        Redirecting…
      </div>
    )
  }

  return <>{children}</>
}

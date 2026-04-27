/**
 * What URL paths a role may open. APIs are enforced in `app-data-authorize`.
 * Authenticated app routes live at top level (e.g. `/home`, `/inventory`); the `app/(app)` group has no URL prefix.
 */

export function getDefaultHomePath(
  role: string | null | undefined,
  isPlatformSuper: boolean
): string {
  if (isPlatformSuper) return '/home'
  if (role === 'member' || role === 'observer') return '/inventory'
  return '/home'
}

/**
 * If false, client should `router.replace(getDefaultHomePath(...))`.
 * `role == null` → allow (role not loaded yet; avoid redirect flash).
 */
export function canAccessPathname(
  pathname: string,
  role: string | null | undefined,
  isPlatformSuper: boolean
): boolean {
  const path = pathname || '/'
  if (path.startsWith('/super-admin')) return isPlatformSuper
  if (isPlatformSuper) return true

  const isOwnerOnlyPath = path.startsWith('/organization') || path.startsWith('/users')
  if (isOwnerOnlyPath) {
    if (role == null) {
      // First workspace: /organization/new is allowed with no org context; /organization settings stay restricted.
      if (path === '/organization/new' || path.startsWith('/organization/new/')) {
        return true
      }
      return false
    }
    return role === 'organization_owner' || role === 'super_admin'
  }

  if (role == null) return true

  if (role === 'organization_owner' || role === 'accountant' || role === 'super_admin') {
    return true
  }

  if (role === 'member') {
    if (path.startsWith('/inventory')) return true
    if (path.startsWith('/approvals')) return true
    if (path.startsWith('/team')) return true
    if (path.startsWith('/suppliers')) return true
    return false
  }

  if (role === 'observer') {
    if (path.startsWith('/inventory')) return true
    if (path.startsWith('/approvals')) return true
    return false
  }

  return true
}

export function isObserverRole(role: string | null | undefined) {
  return role === 'observer'
}

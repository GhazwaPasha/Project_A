import { useAuthStore } from '@/stores/auth-store'
import { hasOrgDataPermission, type OrgDataPermission } from '@/lib/organization-permissions'

/**
 * true when the user may perform `perm` in the current org
 * (mirrors `authorizeAppDataCall` for `/api/app-data` — platform super admin is always allowed here).
 */
export function useOrgDataPermission(perm: OrgDataPermission): boolean {
  const role = useAuthStore((s) => s.currentOrgMemberRole)
  const isSuper = useAuthStore((s) => s.profile?.is_super_admin) === true
  const resolved = useAuthStore((s) => s.orgMemberRoleResolved)
  if (isSuper) return true
  if (!resolved) return true
  if (!role) return false
  return hasOrgDataPermission(role, perm, { isPlatformSuperAdmin: false })
}

export function useCurrentOrgMemberRole() {
  return useAuthStore((s) => s.currentOrgMemberRole)
}

export function useOrgMemberRoleResolved() {
  return useAuthStore((s) => s.orgMemberRoleResolved)
}

import { getSql } from '@/server/pg'

/** One DB round-trip: super-admin flag + active membership role for an org. */
export type OrgPermissionSnapshot = {
  isSuperAdmin: boolean
  memberRole: string | null
}

export async function getOrgPermissionSnapshot(
  userId: string,
  organizationId: string
): Promise<OrgPermissionSnapshot | null> {
  if (!organizationId || !userId) return null
  const sql = getSql()
  const rows = await sql<{ is_super_admin: boolean; role: string | null }[]>`
    SELECT
      COALESCE(up.is_super_admin, false) AS is_super_admin,
      om.role
    FROM public.user_profiles up
    LEFT JOIN public.organization_members om
      ON om.user_id = up.id
      AND om.organization_id = ${organizationId}::uuid
      AND om.is_active = true
    WHERE up.id = ${userId}::uuid
    LIMIT 1
  `
  if (rows.length === 0) return null
  return {
    isSuperAdmin: rows[0].is_super_admin === true,
    memberRole: rows[0].role,
  }
}

export async function getOrganizationMemberRole(
  organizationId: string,
  userId: string
): Promise<string | null> {
  if (!organizationId || !userId) return null
  const sql = getSql()
  const rows = await sql<{ role: string }[]>`
    SELECT role
    FROM public.organization_members
    WHERE organization_id = ${organizationId}::uuid
      AND user_id = ${userId}::uuid
      AND is_active = true
    LIMIT 1
  `
  return rows[0]?.role ?? null
}

export async function isUserProfileSuperAdmin(userId: string): Promise<boolean> {
  const sql = getSql()
  const rows = await sql<{ is_super_admin: boolean }[]>`
    SELECT is_super_admin FROM public.user_profiles WHERE id = ${userId}::uuid LIMIT 1
  `
  return rows[0]?.is_super_admin === true
}

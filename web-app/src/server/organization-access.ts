import { getSql } from '@/server/pg'

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

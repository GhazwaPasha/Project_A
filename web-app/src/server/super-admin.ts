import { authInApiRoute } from '@/auth'
import { getSql } from '@/server/pg'
import { isUserProfileSuperAdmin } from '@/server/organization-access'

export class SuperAdminHttpError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export type SuperAdminUserRow = {
  id: string
  email: string
  full_name: string | null
  is_super_admin: boolean
  created_at: string
  updated_at: string
  last_sign_in_at: string | null
  membership_count: number
}

export type SuperAdminOrganizationRow = {
  id: string
  name: string
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  member_count: number
  owner_emails: string[]
}

export type SuperAdminMembershipRow = {
  id: string
  organization_id: string
  organization_name: string
  user_id: string
  email: string
  full_name: string | null
  role: string
  joined_at: string | null
  is_active: boolean
}

export type SuperAdminOverview = {
  stats: {
    totalUsers: number
    totalOrganizations: number
    superAdmins: number
    activeMemberships: number
  }
  users: SuperAdminUserRow[]
  organizations: SuperAdminOrganizationRow[]
  memberships: SuperAdminMembershipRow[]
}

export async function requirePlatformSuperAdmin(): Promise<{ userId: string; email: string }> {
  const session = await authInApiRoute()
  if (!session?.user?.id) {
    throw new SuperAdminHttpError(401, 'Unauthorized')
  }
  if (!(await isUserProfileSuperAdmin(session.user.id))) {
    throw new SuperAdminHttpError(403, 'Platform super admin access required')
  }
  return { userId: session.user.id, email: session.user.email }
}

export async function getSuperAdminOverview(): Promise<SuperAdminOverview> {
  const sql = getSql()
  const [statsRows, users, organizations, memberships] = await Promise.all([
    sql<
      {
        total_users: string | number
        total_organizations: string | number
        super_admins: string | number
        active_memberships: string | number
      }[]
    >`
      SELECT
        (SELECT COUNT(*) FROM public.user_profiles) AS total_users,
        (SELECT COUNT(*) FROM public.organizations) AS total_organizations,
        (SELECT COUNT(*) FROM public.user_profiles WHERE is_super_admin = true) AS super_admins,
        (SELECT COUNT(*) FROM public.organization_members WHERE is_active = true) AS active_memberships
    `,
    sql<SuperAdminUserRow[]>`
      SELECT
        p.id::text,
        p.email,
        p.full_name,
        p.is_super_admin,
        p.created_at::text,
        p.updated_at::text,
        p.last_sign_in_at::text,
        COUNT(m.id)::int AS membership_count
      FROM public.user_profiles p
      LEFT JOIN public.organization_members m
        ON m.user_id = p.id AND m.is_active = true
      GROUP BY p.id
      ORDER BY p.is_super_admin DESC, p.email
      LIMIT 500
    `,
    sql<SuperAdminOrganizationRow[]>`
      SELECT
        o.id::text,
        o.name,
        o.description,
        o.is_active,
        o.created_at::text,
        o.updated_at::text,
        COUNT(m.id)::int AS member_count,
        COALESCE(
          ARRAY_REMOVE(
            ARRAY_AGG(p.email ORDER BY p.email)
              FILTER (WHERE m.role = 'organization_owner' AND m.is_active = true),
            NULL
          ),
          ARRAY[]::text[]
        ) AS owner_emails
      FROM public.organizations o
      LEFT JOIN public.organization_members m
        ON m.organization_id = o.id AND m.is_active = true
      LEFT JOIN public.user_profiles p ON p.id = m.user_id
      GROUP BY o.id
      ORDER BY o.created_at DESC
      LIMIT 500
    `,
    sql<SuperAdminMembershipRow[]>`
      SELECT
        m.id::text,
        m.organization_id::text,
        o.name AS organization_name,
        m.user_id::text,
        p.email,
        p.full_name,
        m.role,
        m.joined_at::text,
        m.is_active
      FROM public.organization_members m
      INNER JOIN public.organizations o ON o.id = m.organization_id
      INNER JOIN public.user_profiles p ON p.id = m.user_id
      WHERE m.is_active = true
      ORDER BY o.name, (m.role = 'organization_owner') DESC, p.email
      LIMIT 1000
    `,
  ])

  const stats = statsRows[0]
  return {
    stats: {
      totalUsers: Number(stats?.total_users ?? 0),
      totalOrganizations: Number(stats?.total_organizations ?? 0),
      superAdmins: Number(stats?.super_admins ?? 0),
      activeMemberships: Number(stats?.active_memberships ?? 0),
    },
    users,
    organizations,
    memberships,
  }
}

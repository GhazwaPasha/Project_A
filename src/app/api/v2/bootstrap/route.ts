import { NextResponse } from 'next/server'
import { authInApiRoute } from '@/auth'
import { DataServiceAdmin } from '@/server/data-service-admin'
import { getSql } from '@/server/pg'
import { buildOrganizationSettingsView, getOrganizationAccountingDisplay } from '@/lib/organization-settings-defaults'

/** Everything the web app needs to start, in one request. Scoped to the session's own user. */
export async function GET() {
  const session = await authInApiRoute()
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const userId = session.user.id
  const sql = getSql()
  const [profile, organizations, memberships] = await Promise.all([
    DataServiceAdmin.getUserProfile(userId),
    DataServiceAdmin.getUserOrganizations(userId),
    sql<{ organization_id: string; role: string }[]>`
      SELECT organization_id::text AS organization_id, role
      FROM public.organization_members
      WHERE user_id = ${userId}::uuid AND is_active = true
    `,
  ])
  const roles = new Map(memberships.map((m) => [m.organization_id, m.role]))

  return NextResponse.json({
    user: session.user,
    isSuperAdmin: profile?.is_super_admin === true,
    hasProfile: profile != null,
    profile: profile ? { full_name: profile.full_name ?? null, phone: profile.phone ?? null } : null,
    organizations: organizations.map((o) => {
      const display = getOrganizationAccountingDisplay(o)
      const view = buildOrganizationSettingsView(o)
      return {
        id: o.id,
        name: o.name,
        description: o.description,
        role: roles.get(o.id) ?? null,
        currency: display.reportingCurrency,
        decimals: display.decimalPlaces,
        settings: {
          companyInfo: view.companyInfo,
          accountingSettings: view.accountingSettings,
          notificationSettings: view.notificationSettings,
          securitySettings: view.securitySettings,
        },
      }
    }),
  })
}

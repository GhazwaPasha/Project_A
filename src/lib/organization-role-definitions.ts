import type { UserRole } from '@/types'

/** Role values the org owner (or super admin) may assign when adding someone. */
export type InvitableOrgRole = 'accountant' | 'member' | 'observer'

export const INVITABLE_ORG_ROLES: { value: InvitableOrgRole; label: string; hint: string }[] = [
  { value: 'accountant', label: 'Accountant', hint: 'books, reports, and approvals (not org admin)' },
  { value: 'member', label: 'Member', hint: 'inventory, suppliers, and vouchers in this org' },
  { value: 'observer', label: 'Observer', hint: 'view inventory only' },
]

type OrgRoleInfo = {
  id: string
  role: UserRole
  name: string
  description: string
  permissions: string[]
}

/**
 * How each app role is described in Team → Roles. Maps to `organization_members.role` values.
 * (The UI is informational; real enforcement is server-side and future RBAC.)
 */
export const ORGANIZATION_ROLE_CATALOG: OrgRoleInfo[] = [
  {
    id: 'organization_owner',
    role: 'organization_owner',
    name: 'Owner',
    description: 'Full control of this organization, including billing, members, and all financial data.',
    permissions: [
      'Manage members',
      'All journal & ledger',
      'Reports',
      'Organization settings',
    ],
  },
  {
    id: 'accountant',
    role: 'accountant',
    name: 'Accountant',
    description: 'Day-to-day books: chart of accounts, journal entries, posting, and core reports.',
    permissions: ['Chart of accounts', 'Journal & ledger', 'Financial reports (standard)'],
  },
  {
    id: 'member',
    role: 'member',
    name: 'Member',
    description: 'Inventory operations: stock, categories, movements, suppliers, and vouchers. No main dashboard or full books.',
    permissions: [
      'Inventory and related vouchers',
      'Suppliers (when used by inventory flows)',
      'Team directory',
    ],
  },
  {
    id: 'observer',
    role: 'observer',
    name: 'Observer',
    description: 'Read-only access to the inventory area: can view but cannot add, edit, or approve anything.',
    permissions: ['View inventory, vouchers, and history', 'No edits or posting'],
  },
  {
    id: 'super_admin',
    role: 'super_admin',
    name: 'Platform admin',
    description: 'Product-wide administration (rare; usually not an org member role in apps).',
    permissions: ['Cross-tenant (when applicable)'],
  },
]

export function orgRoleLabel(role: string): string {
  const row = ORGANIZATION_ROLE_CATALOG.find((r) => r.id === role || r.role === role)
  if (row) return row.name
  switch (role) {
    case 'organization_owner':
      return 'Owner'
    case 'accountant':
      return 'Accountant'
    case 'member':
      return 'Member'
    case 'observer':
      return 'Observer'
    case 'super_admin':
      return 'Platform admin'
    default:
      return role
  }
}

export function orgRolePermissionsForDisplay(role: string): string[] {
  const row = ORGANIZATION_ROLE_CATALOG.find((r) => r.id === role || r.role === role)
  return row?.permissions ?? []
}

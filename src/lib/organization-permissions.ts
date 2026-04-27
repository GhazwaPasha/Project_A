/**
 * org.read — organization metadata, role lookup (all members).
 * financial.read — dashboard, COA, journal, ledger, reports, account balances, voucher approvals, etc.
 * data.export — export chart, CSVs from books.
 * inventory.read — all inventory, voucher, and supplier read methods used by the inventory module.
 * (Members & observers: inventory-only; they do not get financial.read.)
 */
export type OrgDataPermission =
  | 'org.read'
  | 'financial.read'
  | 'data.export'
  | 'ledger.write'
  | 'chart.write'
  | 'inventory.read'
  | 'inventory.write'
  | 'voucher.write'
  | 'supplier.write'

const FULL: OrgDataPermission[] = [
  'org.read',
  'financial.read',
  'data.export',
  'ledger.write',
  'chart.write',
  'inventory.read',
  'inventory.write',
  'voucher.write',
  'supplier.write',
]

/** Member: inventory + supplier + voucher (operational) only — no `financial.read` (no ledgers, journal, reports, or full COA APIs). */
const MEMBER: OrgDataPermission[] = [
  'org.read',
  'inventory.read',
  'inventory.write',
  'voucher.write',
  'supplier.write',
]

/** Observer: org metadata + read-only inventory. */
const OBSERVER: OrgDataPermission[] = ['org.read', 'inventory.read']

const ROLE_SETS: Record<string, Set<OrgDataPermission>> = {
  organization_owner: new Set(FULL),
  super_admin: new Set(FULL),
  accountant: new Set(FULL),
  member: new Set(MEMBER),
  observer: new Set(OBSERVER),
}

export function hasOrgDataPermission(
  memberRole: string | null | undefined,
  perm: OrgDataPermission,
  opts?: { isPlatformSuperAdmin?: boolean }
): boolean {
  if (opts?.isPlatformSuperAdmin) return true
  if (!memberRole) return false
  return ROLE_SETS[memberRole]?.has(perm) === true
}

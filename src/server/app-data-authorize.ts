import { getSql } from '@/server/pg'
import { getOrgPermissionSnapshot, isUserProfileSuperAdmin } from '@/server/organization-access'
import { hasOrgDataPermission, type OrgDataPermission } from '@/lib/organization-permissions'

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

const BOOKS_READ = new Set([
  'getBooksLock', 'getCloseChecklist', 'listUnpostedStock', 'listCustomers', 'listTaxRates', 'listDocuments', 'getDocument', 'previewDocument',
  'getAgedReport', 'getTaxSummary', 'listTaxReturns', 'getReconciliation', 'listBudgets', 'getBudgetReport', 'getForecast', 'getWorkSummary',
])
const BOOKS_WRITE = new Set([
  'reverseEntry', 'closeBooks', 'postStockMovement', 'recordStockMovement', 'saveCustomer', 'archiveCustomer', 'saveTaxRate', 'saveDocument', 'deleteDocument',
  'postDocument', 'recordPayment', 'voidDocument', 'recordTaxReturn', 'importStatement', 'matchStatementLine', 'unmatchStatementLine', 'ignoreStatementLine',
  'createEntryFromStatementLine', 'completeReconciliation', 'saveBudget', 'deleteBudget',
])

/** Membership + specific data permission (or platform super admin). */
async function requireDataPermission(
  userId: string,
  organizationId: string | null | undefined,
  perm: OrgDataPermission
): Promise<void> {
  if (!organizationId || !UUID_RE.test(organizationId)) {
    throw new Error('Forbidden')
  }
  const snap = await getOrgPermissionSnapshot(userId, organizationId)
  if (!snap) throw new Error('Forbidden')
  if (snap.isSuperAdmin) return
  const role = snap.memberRole
  if (!role) throw new Error('Forbidden')
  if (!hasOrgDataPermission(role, perm)) throw new Error('Forbidden')
}

/** Pass if the member has at least one of the permissions (e.g. accounts list for journal vs inventory). */
async function requireAnyDataPermission(
  userId: string,
  organizationId: string | null | undefined,
  perms: OrgDataPermission[]
): Promise<void> {
  if (!organizationId || !UUID_RE.test(organizationId)) {
    throw new Error('Forbidden')
  }
  const snap = await getOrgPermissionSnapshot(userId, organizationId)
  if (!snap) throw new Error('Forbidden')
  if (snap.isSuperAdmin) return
  const role = snap.memberRole
  if (!role) throw new Error('Forbidden')
  for (const p of perms) {
    if (hasOrgDataPermission(role, p)) return
  }
  throw new Error('Forbidden')
}

export async function assertOrgMembership(userId: string, organizationId: string) {
  const sql = getSql()
  const rows = await sql<{ ok: number }[]>`
    SELECT 1 AS ok
    FROM public.organization_members
    WHERE user_id = ${userId}
      AND organization_id = ${organizationId}
      AND is_active = true
    LIMIT 1
  `
  if (rows.length === 0) {
    throw new Error('Forbidden')
  }
}

function orgFromRecord(obj: unknown, key = 'organization_id'): string | null {
  if (obj && typeof obj === 'object' && key in obj) {
    const v = (obj as Record<string, unknown>)[key]
    return typeof v === 'string' ? v : null
  }
  return null
}

async function orgFromAccountId(id: number): Promise<string | null> {
  const sql = getSql()
  const rows = await sql<{ organization_id: string }[]>`
    SELECT organization_id::text AS organization_id
    FROM public.accounts
    WHERE id = ${id}
    LIMIT 1
  `
  return rows[0]?.organization_id ?? null
}

async function orgFromJournalEntryId(id: number): Promise<string | null> {
  const sql = getSql()
  const rows = await sql<{ organization_id: string }[]>`
    SELECT organization_id::text AS organization_id
    FROM public.journal_entries
    WHERE id = ${id}
    LIMIT 1
  `
  return rows[0]?.organization_id ?? null
}

async function orgFromVoucherId(id: number): Promise<string | null> {
  const sql = getSql()
  const rows = await sql<{ organization_id: string }[]>`
    SELECT organization_id::text AS organization_id
    FROM public.inventory_vouchers
    WHERE id = ${id}
    LIMIT 1
  `
  return rows[0]?.organization_id ?? null
}

async function orgFromSupplierId(id: number): Promise<string | null> {
  const sql = getSql()
  const rows = await sql<{ organization_id: string }[]>`
    SELECT organization_id::text AS organization_id
    FROM public.suppliers
    WHERE id = ${id}
    LIMIT 1
  `
  return rows[0]?.organization_id ?? null
}

async function orgFromInventoryCategoryId(id: number): Promise<string | null> {
  const sql = getSql()
  const rows = await sql<{ organization_id: string }[]>`
    SELECT organization_id::text AS organization_id
    FROM public.inventory_categories
    WHERE id = ${id}
    LIMIT 1
  `
  return rows[0]?.organization_id ?? null
}

async function orgFromInventoryItemId(id: number): Promise<string | null> {
  const sql = getSql()
  const rows = await sql<{ organization_id: string }[]>`
    SELECT organization_id::text AS organization_id
    FROM public.inventory_items
    WHERE id = ${id}
    LIMIT 1
  `
  return rows[0]?.organization_id ?? null
}

async function orgFromVoucherAttachmentId(id: number): Promise<string | null> {
  const sql = getSql()
  const rows = await sql<{ voucher_id: number }[]>`
    SELECT voucher_id
    FROM public.voucher_attachments
    WHERE id = ${id}
    LIMIT 1
  `
  if (!rows[0]?.voucher_id) return null
  return orgFromVoucherId(rows[0].voucher_id)
}

async function orgFromSupplierContactId(id: number): Promise<string | null> {
  const sql = getSql()
  const rows = await sql<{ supplier_id: number }[]>`
    SELECT supplier_id
    FROM public.supplier_contacts
    WHERE id = ${id}
    LIMIT 1
  `
  if (!rows[0]?.supplier_id) return null
  return orgFromSupplierId(rows[0].supplier_id)
}

/**
 * Ensures the session user may invoke `service.method` with `args`.
 * Throws Error('Forbidden') when not allowed.
 */
export async function authorizeAppDataCall(
  service: string,
  method: string,
  args: unknown[],
  userId: string
): Promise<void> {
  const key = `${service}.${method}`

  if (key === 'DataService.getCurrentUser') return
  if (key === 'DataService.getCurrentOrganizationId') return
  if (key === 'DataService.getCurrentOrganization') return

  if (method === 'getUserProfile' && service === 'DataService') {
    if (String(args[0]) !== userId) throw new Error('Forbidden')
    return
  }
  if (method === 'createUserProfile' && service === 'DataService') {
    if (String((args[0] as { id?: string })?.id) !== userId) throw new Error('Forbidden')
    return
  }
  if (method === 'getUserOrganizations' && service === 'DataService') {
    if (String(args[0]) !== userId) throw new Error('Forbidden')
    return
  }

  if (method === 'getOrganization' && service === 'DataService') {
    const orgId = String(args[0])
    if (UUID_RE.test(orgId)) {
      await requireDataPermission(userId, orgId, 'org.read')
    }
    return
  }

  if (key === 'DataService.getUserRoleInOrganization') {
    if (String(args[0]) !== userId) throw new Error('Forbidden')
    await requireDataPermission(userId, String(args[1]), 'org.read')
    return
  }

  if (key === 'DataService.updateUserPreferences') {
    if (String(args[0] ?? '') !== userId) throw new Error('Forbidden')
    return
  }

  if (key === 'DataService.updateUserProfile') {
    if (String(args[0] ?? '') !== userId) throw new Error('Forbidden')
    return
  }

  if (key === 'DataService.getAccounts') {
    await requireAnyDataPermission(userId, String(args[0]), ['financial.read', 'inventory.read'])
    return
  }

  const dataFinancial = new Set([
    'DataService.getJournalEntries',
    'DataService.getJournalEntriesWithLines',
    'DataService.getTrialBalance',
    'DataService.getFinancialMetrics',
    'DataService.getDashboardBundle',
    'DataService.getFinancialRatios',
    'DataService.generateBalanceSheet',
    'DataService.generateIncomeStatement',
    'DataService.generateTrialBalance',
    'DataService.generateAgedReceivables',
    'DataService.generateAgedPayables',
    'DataService.getAccountBalances',
  ])
  if (dataFinancial.has(key)) {
    await requireDataPermission(userId, String(args[0]), 'financial.read')
    return
  }

  const dataInventory = new Set([
    'DataService.getInventoryCategories',
    'DataService.getInventoryItems',
    'DataService.getInventoryTransactions',
    'DataService.getLowStockItems',
    'DataService.getInventoryValueByCategory',
  ])
  if (dataInventory.has(key)) {
    await requireDataPermission(userId, String(args[0]), 'inventory.read')
    return
  }

  if (key === 'DataService.getAccountBalance' || key === 'DataService.getAccountTransactions') {
    await requireDataPermission(userId, String(args[1]), 'financial.read')
    return
  }

  if (key === 'DataService.getJournalEntryWithLines') {
    const orgId = await orgFromJournalEntryId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'financial.read')
    return
  }

  if (key === 'DataService.createJournalEntry') {
    await requireDataPermission(userId, orgFromRecord(args[0]), 'ledger.write')
    return
  }

  if (key === 'DataService.createAccount') {
    await requireDataPermission(userId, orgFromRecord(args[0]), 'chart.write')
    return
  }

  if (key === 'DataService.updateAccount' || key === 'DataService.deleteAccount') {
    const orgId = await orgFromAccountId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'chart.write')
    return
  }

  if (key === 'DataService.getInventoryCategory') {
    const orgId = await orgFromInventoryCategoryId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'inventory.read')
    return
  }
  if (key === 'DataService.updateInventoryCategory' || key === 'DataService.deleteInventoryCategory') {
    const orgId = await orgFromInventoryCategoryId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'inventory.write')
    return
  }

  if (key === 'DataService.getInventoryItem') {
    const orgId = await orgFromInventoryItemId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'inventory.read')
    return
  }
  if (key === 'DataService.updateInventoryItem' || key === 'DataService.deleteInventoryItem') {
    const orgId = await orgFromInventoryItemId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'inventory.write')
    return
  }

  if (key === 'DataService.createInventoryCategory' || key === 'DataService.createInventoryItem') {
    await requireDataPermission(userId, orgFromRecord(args[0]), 'inventory.write')
    return
  }

  if (key === 'DataService.createInventoryTransaction') {
    await requireDataPermission(userId, orgFromRecord(args[0]), 'inventory.write')
    return
  }

  if (key === 'AccountService.exportChartOfAccounts') {
    await requireDataPermission(userId, String(args[0]), 'data.export')
    return
  }
  if (key === 'AccountService.importChartOfAccounts') {
    await requireDataPermission(userId, String(args[0]), 'chart.write')
    return
  }
  /* Full books / COA management — members (inventory-only) must not use these. */
  const acctReadFinancial = new Set([
    'AccountService.getAccountHierarchy',
    'AccountService.getParentAccounts',
    'AccountService.searchAccounts',
    'AccountService.getAccountsByType',
    'AccountService.getPostableAccounts',
    'AccountService.validateAccountCode',
    'AccountService.getAccountStats',
    'AccountService.getChartOfAccounts',
  ])
  if (acctReadFinancial.has(key)) {
    await requireDataPermission(userId, String(args[0]), 'financial.read')
    return
  }

  /* Flat list for account pickers (e.g. inventory GL links, suppliers) — inventory.read OR books. */
  if (key === 'AccountService.getAccounts') {
    await requireAnyDataPermission(userId, String(args[0]), ['financial.read', 'inventory.read'])
    return
  }

  if (key === 'AccountService.createAccount') {
    await requireDataPermission(userId, orgFromRecord(args[0]), 'chart.write')
    return
  }

  if (key === 'AccountService.getAccount' || key === 'AccountService.getChildAccounts' || key === 'AccountService.getAccountBalance') {
    const orgId = await orgFromAccountId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'financial.read')
    return
  }
  if (key === 'AccountService.updateAccount' || key === 'AccountService.deleteAccount') {
    const orgId = await orgFromAccountId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'chart.write')
    return
  }

  if (key === 'VoucherService.getVouchers' || key === 'VoucherService.getVoucherStats' || key === 'VoucherService.getExpiredVouchers') {
    await requireDataPermission(userId, String(args[0]), 'inventory.read')
    return
  }

  if (key === 'VoucherService.createVoucher') {
    await requireDataPermission(userId, String(args[1]), 'voucher.write')
    return
  }

  if (key === 'VoucherService.submitForApproval') {
    await requireDataPermission(userId, String(args[1]), 'voucher.write')
    return
  }

  if (key === 'VoucherService.getApprovalStats') {
    await requireDataPermission(userId, String(args[0]), 'financial.read')
    if (String(args[1]) !== userId) throw new Error('Forbidden')
    return
  }

  if (key === 'VoucherService.expireOverdueVouchers') {
    if (!(await isUserProfileSuperAdmin(userId))) throw new Error('Forbidden')
    return
  }

  if (key === 'VoucherService.getVoucher') {
    const orgId = await orgFromVoucherId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'inventory.read')
    return
  }
  if (service === 'BooksService') {
    const org = String(args[0] ?? '')
    if (BOOKS_READ.has(method)) return requireDataPermission(userId, org, 'financial.read')
    if (BOOKS_WRITE.has(method)) return requireDataPermission(userId, org, 'ledger.write')
    // Reopening changes figures people may rely on, so it's the owner's call.
    if (method === 'reopenBooks') {
      if (!UUID_RE.test(org)) throw new Error('Forbidden')
      const snap = await getOrgPermissionSnapshot(userId, org)
      if (!snap) throw new Error('Forbidden')
      if (snap.isSuperAdmin || snap.memberRole === 'organization_owner' || snap.memberRole === 'super_admin') return
    }
    throw new Error('Forbidden')
  }

  if (key === 'VoucherService.postVoucher' || key === 'VoucherService.previewVoucherPosting') {
    const orgId = await orgFromVoucherId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'ledger.write')
    return
  }

  const voucherByIdWrite = new Set([
    'VoucherService.updateVoucher',
    'VoucherService.deleteVoucher',
    'VoucherService.approveVoucher',
    'VoucherService.rejectVoucher',
    'VoucherService.renewExpiredVoucher',
    'VoucherService.executeVoucher',
    'VoucherService.completeVoucher',
  ])
  if (voucherByIdWrite.has(key)) {
    const orgId = await orgFromVoucherId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'voucher.write')
    return
  }

  if (key === 'VoucherService.uploadAttachment') {
    throw new Error('Forbidden')
  }

  if (key === 'VoucherService.deleteAttachment') {
    const orgId = await orgFromVoucherAttachmentId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'voucher.write')
    return
  }

  if (key === 'SupplierService.getSuppliers' || key === 'SupplierService.getSupplierStats' || key === 'SupplierService.getSuppliersForVoucher') {
    await requireDataPermission(userId, String(args[0]), 'inventory.read')
    return
  }

  if (key === 'SupplierService.createSupplier') {
    await requireDataPermission(userId, String(args[1]), 'supplier.write')
    return
  }

  if (key === 'SupplierService.getSupplier') {
    const orgId = await orgFromSupplierId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'inventory.read')
    return
  }
  if (key === 'SupplierService.updateSupplier' || key === 'SupplierService.deleteSupplier') {
    const orgId = await orgFromSupplierId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'supplier.write')
    return
  }

  if (key === 'SupplierService.getSupplierAccountMappings' || key === 'SupplierService.getSupplierContacts' || key === 'SupplierService.getSupplierForVoucher') {
    const orgId = await orgFromSupplierId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'inventory.read')
    return
  }
  if (key === 'SupplierService.updateSupplierAccountMappings') {
    const orgId = await orgFromSupplierId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'supplier.write')
    return
  }

  if (key === 'SupplierService.addSupplierContact') {
    const sid = (args[0] as { supplier_id?: number })?.supplier_id
    if (typeof sid !== 'number') throw new Error('Forbidden')
    const orgId = await orgFromSupplierId(sid)
    await requireDataPermission(userId, orgId, 'supplier.write')
    return
  }

  if (key === 'SupplierService.updateSupplierContact' || key === 'SupplierService.deleteSupplierContact') {
    const orgId = await orgFromSupplierContactId(Number(args[0]))
    await requireDataPermission(userId, orgId, 'supplier.write')
    return
  }

  throw new Error('Forbidden')
}

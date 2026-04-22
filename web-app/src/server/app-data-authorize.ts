import { getSql } from '@/server/pg'

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

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

async function requireOrg(userId: string, organizationId: string | null | undefined) {
  if (!organizationId || !UUID_RE.test(organizationId)) {
    throw new Error('Forbidden')
  }
  await assertOrgMembership(userId, organizationId)
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
      await assertOrgMembership(userId, orgId)
    }
    return
  }

  if (key === 'DataService.getUserRoleInOrganization') {
    if (String(args[0]) !== userId) throw new Error('Forbidden')
    await requireOrg(userId, String(args[1]))
    return
  }

  const dataOrgFirst = new Set([
    'DataService.getAccounts',
    'DataService.getJournalEntries',
    'DataService.getJournalEntriesWithLines',
    'DataService.getTrialBalance',
    'DataService.getFinancialMetrics',
    'DataService.getFinancialRatios',
    'DataService.generateBalanceSheet',
    'DataService.generateIncomeStatement',
    'DataService.generateTrialBalance',
    'DataService.generateAgedReceivables',
    'DataService.generateAgedPayables',
    'DataService.getAccountBalances',
    'DataService.getInventoryCategories',
    'DataService.getInventoryItems',
    'DataService.getInventoryTransactions',
    'DataService.getLowStockItems',
    'DataService.getInventoryValueByCategory',
  ])
  if (dataOrgFirst.has(key)) {
    await requireOrg(userId, String(args[0]))
    return
  }

  if (key === 'DataService.getAccountBalance' || key === 'DataService.getAccountTransactions') {
    await requireOrg(userId, String(args[1]))
    return
  }

  if (key === 'DataService.getJournalEntryWithLines') {
    const orgId = await orgFromJournalEntryId(Number(args[0]))
    await requireOrg(userId, orgId)
    return
  }

  if (key === 'DataService.createJournalEntry') {
    await requireOrg(userId, orgFromRecord(args[0]))
    return
  }

  if (key === 'DataService.createAccount') {
    await requireOrg(userId, orgFromRecord(args[0]))
    return
  }

  if (key === 'DataService.updateAccount' || key === 'DataService.deleteAccount') {
    const orgId = await orgFromAccountId(Number(args[0]))
    await requireOrg(userId, orgId)
    return
  }

  if (
    key === 'DataService.getInventoryCategory' ||
    key === 'DataService.updateInventoryCategory' ||
    key === 'DataService.deleteInventoryCategory'
  ) {
    const orgId = await orgFromInventoryCategoryId(Number(args[0]))
    await requireOrg(userId, orgId)
    return
  }

  if (
    key === 'DataService.getInventoryItem' ||
    key === 'DataService.updateInventoryItem' ||
    key === 'DataService.deleteInventoryItem'
  ) {
    const orgId = await orgFromInventoryItemId(Number(args[0]))
    await requireOrg(userId, orgId)
    return
  }

  if (key === 'DataService.createInventoryCategory' || key === 'DataService.createInventoryItem') {
    await requireOrg(userId, orgFromRecord(args[0]))
    return
  }

  if (key === 'DataService.createInventoryTransaction') {
    await requireOrg(userId, orgFromRecord(args[0]))
    return
  }

  const acctOrgFirst = new Set([
    'AccountService.getAccounts',
    'AccountService.getAccountHierarchy',
    'AccountService.getParentAccounts',
    'AccountService.searchAccounts',
    'AccountService.getAccountsByType',
    'AccountService.getPostableAccounts',
    'AccountService.validateAccountCode',
    'AccountService.getAccountStats',
    'AccountService.getChartOfAccounts',
    'AccountService.exportChartOfAccounts',
    'AccountService.importChartOfAccounts',
  ])
  if (acctOrgFirst.has(key)) {
    await requireOrg(userId, String(args[0]))
    return
  }

  if (key === 'AccountService.createAccount') {
    await requireOrg(userId, orgFromRecord(args[0]))
    return
  }

  if (key === 'AccountService.getAccount' || key === 'AccountService.updateAccount' || key === 'AccountService.deleteAccount') {
    const orgId = await orgFromAccountId(Number(args[0]))
    await requireOrg(userId, orgId)
    return
  }

  if (key === 'AccountService.getChildAccounts') {
    const orgId = await orgFromAccountId(Number(args[0]))
    await requireOrg(userId, orgId)
    return
  }

  if (key === 'AccountService.getAccountBalance') {
    const orgId = await orgFromAccountId(Number(args[0]))
    await requireOrg(userId, orgId)
    return
  }

  if (key === 'VoucherService.getVouchers' || key === 'VoucherService.getVoucherStats' || key === 'VoucherService.getExpiredVouchers') {
    await requireOrg(userId, String(args[0]))
    return
  }

  if (key === 'VoucherService.createVoucher') {
    await requireOrg(userId, String(args[1]))
    return
  }

  if (key === 'VoucherService.submitForApproval') {
    await requireOrg(userId, String(args[1]))
    return
  }

  if (key === 'VoucherService.getApprovalStats') {
    await requireOrg(userId, String(args[0]))
    if (String(args[1]) !== userId) throw new Error('Forbidden')
    return
  }

  if (key === 'VoucherService.expireOverdueVouchers') {
    return
  }

  const voucherById = new Set([
    'VoucherService.getVoucher',
    'VoucherService.updateVoucher',
    'VoucherService.deleteVoucher',
    'VoucherService.approveVoucher',
    'VoucherService.rejectVoucher',
    'VoucherService.renewExpiredVoucher',
    'VoucherService.executeVoucher',
    'VoucherService.postVoucher',
    'VoucherService.completeVoucher',
  ])
  if (voucherById.has(key)) {
    const orgId = await orgFromVoucherId(Number(args[0]))
    await requireOrg(userId, orgId)
    return
  }

  if (key === 'VoucherService.uploadAttachment') {
    throw new Error('Forbidden')
  }

  if (key === 'VoucherService.deleteAttachment') {
    const orgId = await orgFromVoucherAttachmentId(Number(args[0]))
    await requireOrg(userId, orgId)
    return
  }

  if (key === 'SupplierService.getSuppliers' || key === 'SupplierService.getSupplierStats' || key === 'SupplierService.getSuppliersForVoucher') {
    await requireOrg(userId, String(args[0]))
    return
  }

  if (key === 'SupplierService.createSupplier') {
    await requireOrg(userId, String(args[1]))
    return
  }

  if (key === 'SupplierService.getSupplier' || key === 'SupplierService.updateSupplier' || key === 'SupplierService.deleteSupplier') {
    const orgId = await orgFromSupplierId(Number(args[0]))
    await requireOrg(userId, orgId)
    return
  }

  if (
    key === 'SupplierService.getSupplierAccountMappings' ||
    key === 'SupplierService.updateSupplierAccountMappings' ||
    key === 'SupplierService.getSupplierContacts' ||
    key === 'SupplierService.getSupplierForVoucher'
  ) {
    const orgId = await orgFromSupplierId(Number(args[0]))
    await requireOrg(userId, orgId)
    return
  }

  if (key === 'SupplierService.addSupplierContact') {
    const sid = (args[0] as { supplier_id?: number })?.supplier_id
    if (typeof sid !== 'number') throw new Error('Forbidden')
    const orgId = await orgFromSupplierId(sid)
    await requireOrg(userId, orgId)
    return
  }

  if (key === 'SupplierService.updateSupplierContact' || key === 'SupplierService.deleteSupplierContact') {
    const orgId = await orgFromSupplierContactId(Number(args[0]))
    await requireOrg(userId, orgId)
    return
  }

  throw new Error('Forbidden')
}

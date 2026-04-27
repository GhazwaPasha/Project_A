import type { JSONValue } from 'postgres'
import { getSql } from '@/server/pg'
import {
  attachCategoryAccounts,
  attachItemCategory,
  attachItemsCategories,
  attachTransactionItem,
} from '@/server/data/inventory-helpers'
import { validateJournalLinesForSave } from '@/lib/journal-validation'
import {
  fetchAccountNetBalance,
  fetchJournalLineAggregatesByOrg,
  fetchTrialBalanceSums,
  netAmountForAccountType,
  trialRowToDebitsCredits,
} from '@/server/data/ledger-sql'
import { 
  User, 
  UserProfile, 
  Organization, 
  OrganizationMember, 
  Account,
  AccountCreatePayload, 
  JournalEntry, 
  JournalEntryLine,
  UserRole,
  AccountType,
  AccountReportCategory,
  InventoryCategory,
  InventoryItem,
  InventoryTransaction,
} from '@/types'
import { parseOrganizationSettingsValue } from '@/lib/organization-settings-defaults'
import {
  assertReportCategoryCompatible,
  balanceSheetSubsectionSortOrder,
  formatReportCategoryLabel,
  resolveBalanceSheetSubsectionKey,
  resolveExpenseBucket,
} from '@/lib/account-report-category'
import { allocateStructuredAccountCode } from '@/server/account-code'
import { isUndefinedColumnError } from '@/server/pg-undefined-column'

function organizationRowWithParsedSettings<T extends { settings: unknown }>(row: T): T {
  return { ...row, settings: parseOrganizationSettingsValue(row.settings) as T['settings'] }
}
import { isValidHex6 } from '@/lib/org-accent-color'
import { parseUserPreferences } from '@/lib/user-preferences'

export class DataServiceAdmin {
  // ================================
  // AUTHENTICATION & USER MANAGEMENT
  // ================================

  /** Not used on server; client resolves session via NextAuth. */
  static async getCurrentUser(): Promise<User | null> {
    return null
  }

  static async getUserProfile(userId: string): Promise<UserProfile | null> {
    const sql = getSql()
    const rows = await sql<UserProfile[]>`
      SELECT * FROM public.user_profiles WHERE id = ${userId}::uuid LIMIT 1
    `
    const row = rows[0] ?? null
    if (!row) return null
    return { ...row, preferences: parseUserPreferences(row.preferences) }
  }

  /**
   * Merges into `user_profiles.preferences` (e.g. `accentColor`, `theme`). Call only for the same user.
   */
  static async updateUserPreferences(
    userId: string,
    patch: { accentColor?: string | null; theme?: 'light' | 'dark' | 'system' | null }
  ): Promise<UserProfile | null> {
    if (patch.accentColor != null && patch.accentColor !== '' && !isValidHex6(patch.accentColor)) {
      throw new Error('Invalid accent color (use #RRGGBB)')
    }
    if (patch.theme != null && patch.theme !== 'light' && patch.theme !== 'dark' && patch.theme !== 'system') {
      throw new Error('Invalid theme')
    }
    const sql = getSql()
    const prof = await this.getUserProfile(userId)
    if (!prof) return null
    const cur = parseUserPreferences(prof.preferences) as Record<string, unknown>
    const next: Record<string, unknown> = { ...cur }
    if (patch.accentColor === null || patch.accentColor === '') {
      // Keep the key with `null` so the client can tell "user chose default" from
      // a row where the key was never present (use localStorage / avoid theme flash).
      next.accentColor = null
    } else if (patch.accentColor !== undefined) {
      next.accentColor = patch.accentColor
    }
    if (patch.theme === null) {
      delete next.theme
    } else if (patch.theme !== undefined) {
      next.theme = patch.theme
    }
    const rows = await sql<UserProfile[]>`
      UPDATE public.user_profiles
      SET
        preferences = ${JSON.stringify(next)}::jsonb,
        updated_at = now()
      WHERE id = ${userId}::uuid
      RETURNING *
    `
    const out = rows[0] ?? null
    if (!out) return null
    return { ...out, preferences: parseUserPreferences(out.preferences) }
  }

  static async updateUserProfile(
    userId: string,
    patch: { full_name?: string | null; phone?: string | null; avatar_url?: string | null }
  ): Promise<UserProfile | null> {
    const sql = getSql()
    const prof = await this.getUserProfile(userId)
    if (!prof) return null

    const trimOrNull = (v: string | null | undefined): string | null => {
      if (v == null) return null
      const t = v.trim()
      return t.length === 0 ? null : t
    }

    let full_name = prof.full_name
    if (patch.full_name !== undefined) {
      const t = trimOrNull(patch.full_name)
      if (t != null && t.length > 200) throw new Error('Full name is too long (max 200 characters)')
      full_name = t
    }

    let phone = prof.phone
    if (patch.phone !== undefined) {
      const t = trimOrNull(patch.phone)
      if (t != null && t.length > 50) throw new Error('Phone is too long (max 50 characters)')
      phone = t
    }

    let avatar_url = prof.avatar_url
    if (patch.avatar_url !== undefined) {
      const t = trimOrNull(patch.avatar_url)
      if (t != null) {
        try {
          const u = new URL(t)
          if (u.protocol !== 'http:' && u.protocol !== 'https:') {
            throw new Error('Avatar URL must start with http:// or https://')
          }
        } catch (e) {
          if (e instanceof TypeError) throw new Error('Invalid avatar URL')
          throw e
        }
        if (t.length > 2000) throw new Error('Avatar URL is too long')
      }
      avatar_url = t
    }

    const rows = await sql<UserProfile[]>`
      UPDATE public.user_profiles
      SET
        full_name = ${full_name},
        phone = ${phone},
        avatar_url = ${avatar_url},
        updated_at = now()
      WHERE id = ${userId}::uuid
      RETURNING *
    `
    const out = rows[0] ?? null
    if (!out) return null
    return { ...out, preferences: parseUserPreferences(out.preferences) }
  }

  static async createUserProfile(profile: Omit<UserProfile, 'created_at' | 'updated_at'>): Promise<UserProfile | null> {
    const sql = getSql()
    const pref = (profile.preferences ?? {}) as JSONValue
    const rows = await sql<UserProfile[]>`
      INSERT INTO public.user_profiles (
        id, email, full_name, avatar_url, phone, is_super_admin, preferences, last_sign_in_at
      )
      VALUES (
        ${profile.id}::uuid,
        ${profile.email},
        ${profile.full_name},
        ${profile.avatar_url},
        ${profile.phone},
        ${profile.is_super_admin},
        ${sql.json(pref)}::jsonb,
        ${profile.last_sign_in_at}
      )
      RETURNING *
    `
    const out = rows[0] ?? null
    if (!out) return null
    return { ...out, preferences: parseUserPreferences(out.preferences) }
  }

  // ================================
  // ORGANIZATION MANAGEMENT
  // ================================

  static async getUserOrganizations(userId: string): Promise<Organization[]> {
    const sql = getSql()
    const rows = await sql<Organization[]>`
      SELECT
        o.id, o.name, o.description, o.settings, o.created_at, o.updated_at, o.is_active
      FROM public.organization_members m
      INNER JOIN public.organizations o ON o.id = m.organization_id
      WHERE m.user_id = ${userId}::uuid
        AND m.is_active = true
      ORDER BY o.name
    `
    return rows.map((o) => organizationRowWithParsedSettings(o))
  }

  static async getOrganization(organizationId: string): Promise<Organization | null> {
    const sql = getSql()
    const rows = await sql<Organization[]>`
      SELECT * FROM public.organizations WHERE id = ${organizationId}::uuid LIMIT 1
    `
    const r = rows[0] ?? null
    return r ? organizationRowWithParsedSettings(r) : null
  }

  static getCurrentOrganizationId(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('selectedOrganizationId')
  }

  static async getCurrentOrganization(): Promise<Organization | null> {
    const orgId = this.getCurrentOrganizationId()
    if (!orgId) return null
    return this.getOrganization(orgId)
  }

  static async getUserRoleInOrganization(userId: string, organizationId: string): Promise<UserRole | null> {
    const sql = getSql()
    const rows = await sql<{ role: UserRole }[]>`
      SELECT role FROM public.organization_members
      WHERE user_id = ${userId}::uuid
        AND organization_id = ${organizationId}::uuid
        AND is_active = true
      LIMIT 1
    `
    return rows[0]?.role ?? null
  }

  // ================================
  // ACCOUNTS MANAGEMENT
  // ================================

  static async getAccounts(organizationId: string, activeOnly: boolean = true): Promise<Account[]> {
    const sql = getSql()
    if (activeOnly) {
      return (await sql<Account[]>`
        SELECT * FROM public.accounts
        WHERE organization_id = ${organizationId}::uuid AND is_active = true
        ORDER BY code
      `) as Account[]
    }
    return (await sql<Account[]>`
      SELECT * FROM public.accounts
      WHERE organization_id = ${organizationId}::uuid
      ORDER BY code
    `) as Account[]
  }

  static async createAccount(account: AccountCreatePayload): Promise<Account | null> {
    assertReportCategoryCompatible(account.account_type, account.report_category ?? null)
    const sql = getSql()
    if (account.parent_id != null) {
      const parents = await sql<{ account_type: string; organization_id: string }[]>`
        SELECT account_type::text AS account_type, organization_id::text AS organization_id
        FROM public.accounts WHERE id = ${account.parent_id} LIMIT 1
      `
      const p = parents[0]
      if (!p || p.organization_id !== account.organization_id) {
        throw new Error('Parent account must belong to the same organization.')
      }
      if (p.account_type !== account.account_type) {
        throw new Error('Child account must have the same account type as its parent.')
      }
    }

    let generatedCode = await allocateStructuredAccountCode(
      sql,
      account.organization_id,
      account.account_type,
      account.parent_id ?? null
    )
    const insertRow = async (includeReportCategory: boolean): Promise<Account | null> => {
      if (includeReportCategory) {
        const rows = await sql<Account[]>`
          INSERT INTO public.accounts (
            organization_id, code, name, account_type, parent_id, description, is_active,
            "group", report_category, is_postable, created_by
          ) VALUES (
            ${account.organization_id}::uuid,
            ${generatedCode},
            ${account.name},
            ${account.account_type}::public.account_type,
            ${account.parent_id},
            ${account.description},
            ${account.is_active},
            ${account.group},
            ${account.report_category ?? null}::public.account_report_category,
            ${account.is_postable ?? true},
            ${account.created_by}::uuid
          )
          RETURNING *
        `
        return (rows[0] as Account) ?? null
      }
      const rows = await sql<Account[]>`
        INSERT INTO public.accounts (
          organization_id, code, name, account_type, parent_id, description, is_active,
          "group", is_postable, created_by
        ) VALUES (
          ${account.organization_id}::uuid,
          ${generatedCode},
          ${account.name},
          ${account.account_type}::public.account_type,
          ${account.parent_id},
          ${account.description},
          ${account.is_active},
          ${account.group},
          ${account.is_postable ?? true},
          ${account.created_by}::uuid
        )
        RETURNING *
      `
      return (rows[0] as Account) ?? null
    }

    for (let attempt = 0; attempt < 8; attempt++) {
      try {
        try {
          return await insertRow(true)
        } catch (e) {
          if (isUndefinedColumnError(e, 'report_category')) {
            return await insertRow(false)
          }
          throw e
        }
      } catch (e) {
        const code =
          e && typeof e === 'object' && 'code' in e ? String((e as { code: unknown }).code) : ''
        if (code === '23505' && attempt < 7) {
          generatedCode = await allocateStructuredAccountCode(
            sql,
            account.organization_id,
            account.account_type,
            account.parent_id ?? null
          )
          continue
        }
        throw e
      }
    }
    return null
  }

  static async updateAccount(id: number, updates: Partial<Account>): Promise<Account | null> {
    const sql = getSql()
    const existingRows = (await sql<Account[]>`
      SELECT * FROM public.accounts WHERE id = ${id} LIMIT 1
    `) as Account[]
    const existing = existingRows[0]
    if (!existing) return null

    const mergedType = updates.account_type ?? existing.account_type
    const mergedParent =
      updates.parent_id !== undefined ? updates.parent_id : existing.parent_id
    const mergedReport =
      updates.report_category !== undefined ? updates.report_category : existing.report_category

    assertReportCategoryCompatible(mergedType, mergedReport ?? null)

    if (mergedParent != null) {
      const parents = await sql<{ account_type: string; organization_id: string }[]>`
        SELECT account_type::text AS account_type, organization_id::text AS organization_id
        FROM public.accounts WHERE id = ${mergedParent} LIMIT 1
      `
      const p = parents[0]
      if (!p || p.organization_id !== existing.organization_id) {
        throw new Error('Parent account must belong to the same organization.')
      }
      if (p.account_type !== mergedType) {
        throw new Error('Child account must have the same account type as its parent.')
      }
    }

    const u = { ...updates }
    delete (u as { code?: unknown }).code
    try {
      const rows = await sql<Account[]>`
        UPDATE public.accounts
        SET
          name = COALESCE(${u.name ?? null}, name),
          account_type = COALESCE(${u.account_type ?? null}::public.account_type, account_type),
          parent_id = ${mergedParent},
          description = ${u.description === undefined ? null : u.description},
          is_active = COALESCE(${u.is_active ?? null}, is_active),
          "group" = COALESCE(${u.group ?? null}, "group"),
          report_category = ${mergedReport}::public.account_report_category,
          is_postable = COALESCE(${u.is_postable ?? null}, is_postable)
        WHERE id = ${id}
        RETURNING *
      `
      return (rows[0] as Account) ?? null
    } catch (e) {
      if (!isUndefinedColumnError(e, 'report_category')) throw e
      const rows = await sql<Account[]>`
        UPDATE public.accounts
        SET
          name = COALESCE(${u.name ?? null}, name),
          account_type = COALESCE(${u.account_type ?? null}::public.account_type, account_type),
          parent_id = ${mergedParent},
          description = ${u.description === undefined ? null : u.description},
          is_active = COALESCE(${u.is_active ?? null}, is_active),
          "group" = COALESCE(${u.group ?? null}, "group"),
          is_postable = COALESCE(${u.is_postable ?? null}, is_postable)
        WHERE id = ${id}
        RETURNING *
      `
      return (rows[0] as Account) ?? null
    }
  }

  static async deleteAccount(id: number): Promise<boolean> {
    const sql = getSql()
    const r = await sql`DELETE FROM public.accounts WHERE id = ${id}`
    const c = (r as { count?: number })?.count
    return c === undefined ? true : c > 0
  }

  // ================================
  // JOURNAL ENTRIES MANAGEMENT
  // ================================

  static async getJournalEntries(organizationId: string, limit: number = 50): Promise<JournalEntry[]> {
    const sql = getSql()
    return (await sql<JournalEntry[]>`
      SELECT * FROM public.journal_entries
      WHERE organization_id = ${organizationId}::uuid
      ORDER BY entry_date DESC, id DESC
      LIMIT ${limit}
    `) as JournalEntry[]
  }

  static async getJournalEntriesWithLines(
    organizationId: string,
    limit: number = 50
  ): Promise<(JournalEntry & { lines: JournalEntryLine[] })[]> {
    const sql = getSql()
    const entries = (await sql<JournalEntry[]>`
      SELECT * FROM public.journal_entries
      WHERE organization_id = ${organizationId}::uuid
      ORDER BY entry_date DESC, id DESC
      LIMIT ${limit}
    `) as JournalEntry[]
    if (entries.length === 0) return []
    const ids = entries.map((e) => e.id)
    const allLines = (await sql<JournalEntryLine[]>`
      SELECT * FROM public.journal_entry_lines
      WHERE journal_entry_id IN ${sql(ids)}
      ORDER BY journal_entry_id, line_order
    `) as JournalEntryLine[]
    const byEntry = new Map<number, JournalEntryLine[]>()
    for (const line of allLines) {
      const j = line.journal_entry_id
      if (!byEntry.has(j)) byEntry.set(j, [])
      byEntry.get(j)!.push(line)
    }
    return entries.map((e) => ({ ...e, lines: byEntry.get(e.id) ?? [] }))
  }

  static async getJournalEntryWithLines(
    entryId: number
  ): Promise<(JournalEntry & { lines: JournalEntryLine[] }) | null> {
    const sql = getSql()
    const rows = (await sql<JournalEntry[]>`
      SELECT * FROM public.journal_entries WHERE id = ${entryId} LIMIT 1
    `) as JournalEntry[]
    const entry = rows[0]
    if (!entry) return null
    const lineRows = (await sql<JournalEntryLine[]>`
      SELECT * FROM public.journal_entry_lines
      WHERE journal_entry_id = ${entryId}
      ORDER BY line_order
    `) as JournalEntryLine[]
    return { ...entry, lines: lineRows }
  }

  /**
   * Ensures each line posts to a postable account in the same org (bypass-safe vs UI-only checks).
   */
  /** Same tagged-template API as pooled `Sql`; transaction clients from `sql.begin` match at runtime. */
  private static async assertJournalLineAccountsPostable(
    sqlExec: ReturnType<typeof getSql>,
    organizationId: string,
    lines: Array<{ account_id: number }>
  ): Promise<void> {
    const ids = Array.from(new Set(lines.map((l) => l.account_id).filter((id) => id > 0)))
    if (ids.length === 0) return
    const rows = (await sqlExec<
      { id: number; organization_id: string; is_postable: boolean }[]
    >`
      SELECT id, organization_id::text AS organization_id, is_postable
      FROM public.accounts
      WHERE id = ANY(${ids}::bigint[])
    `) as { id: number; organization_id: string; is_postable: boolean }[]
    const byId = new Map(rows.map((r) => [r.id, r]))
    for (const id of ids) {
      const a = byId.get(id)
      if (!a) {
        throw new Error(`Account ${id} was not found.`)
      }
      if (a.organization_id !== organizationId) {
        throw new Error(`Account ${id} does not belong to this organization.`)
      }
      if (!a.is_postable) {
        throw new Error(
          `Cannot post to account ${id}: it is a header (non-postable) account.`
        )
      }
    }
  }

  static async createJournalEntry(
    entry: Omit<JournalEntry, 'id' | 'created_at' | 'updated_at'>,
    lines: Omit<JournalEntryLine, 'id' | 'journal_entry_id'>[]
  ): Promise<JournalEntry | null> {
    const { totalDebits, normalized } = validateJournalLinesForSave(lines)
    const sql = getSql()
    return await sql.begin(async (tx) => {
      await this.assertJournalLineAccountsPostable(
        tx as unknown as ReturnType<typeof getSql>,
        entry.organization_id,
        normalized
      )
      const e = { ...entry, total_amount: totalDebits }
      const inserted = (await tx<JournalEntry[]>`
        INSERT INTO public.journal_entries (
          organization_id, entry_number, entry_date, description, reference,
          total_amount, is_posted, created_by, posted_by, posted_at
        )
        VALUES (
          ${e.organization_id}::uuid,
          ${e.entry_number},
          ${e.entry_date}::date,
          ${e.description},
          ${e.reference},
          ${e.total_amount},
          ${e.is_posted},
          ${e.created_by}::uuid,
          ${e.posted_by}::uuid,
          ${e.posted_at}
        )
        RETURNING *
      `) as JournalEntry[]
      const newEntry = inserted[0]
      if (!newEntry) {
        throw new Error('Failed to create journal entry')
      }
      for (const line of normalized) {
        await tx`
          INSERT INTO public.journal_entry_lines (
            journal_entry_id, account_id, description, debit_amount, credit_amount, line_order
          ) VALUES (
            ${newEntry.id},
            ${line.account_id},
            ${line.description},
            ${line.debit_amount},
            ${line.credit_amount},
            ${line.line_order}
          )
        `
      }
      return newEntry
    })
  }

  // ================================
  // FINANCIAL CALCULATIONS
  // ================================

  static async getAccountBalance(accountId: number, organizationId: string): Promise<number> {
    return fetchAccountNetBalance(accountId, organizationId)
  }

  static async getTrialBalance(organizationId: string, asOfDate?: string): Promise<Array<{
    account_id: number
    account_code: string
    account_name: string
    account_type: AccountType
    debit_balance: number
    credit_balance: number
  }>> {
    const rows = await fetchTrialBalanceSums(organizationId, asOfDate ?? null)
    return rows
      .map((row) => {
        const { debit_balance, credit_balance } = trialRowToDebitsCredits(row)
        return {
          account_id: row.id,
          account_code: row.code || '',
          account_name: row.name,
          account_type: row.account_type,
          debit_balance,
          credit_balance,
        }
      })
      .filter(
        (r) => r.debit_balance >= 0.01 || r.credit_balance >= 0.01
      )
  }

  static async getFinancialMetrics(
    organizationId: string,
    fromDate?: string | null,
    toDate?: string | null
  ): Promise<{
    totalRevenue: number
    totalExpenses: number
    netIncome: number
    totalAssets: number
    totalLiabilities: number
    totalEquity: number
  }> {
    const fd = typeof fromDate === 'string' && fromDate.trim() !== '' ? fromDate : undefined
    const td = typeof toDate === 'string' && toDate.trim() !== '' ? toDate : undefined
    const rows = await fetchTrialBalanceSums(organizationId, { fromDate: fd, toDate: td })
    let totalRevenue = 0
    let totalExpenses = 0
    let totalAssets = 0
    let totalLiabilities = 0
    let totalEquity = 0
    for (const row of rows) {
      const dr = row.dr != null ? Number(row.dr) : 0
      const cr = row.cr != null ? Number(row.cr) : 0
      const net = netAmountForAccountType(dr, cr, String(row.account_type))
      const t = String(row.account_type).toLowerCase()
      if (t === 'revenue') totalRevenue += net
      else if (t === 'expense') totalExpenses += net
      else if (t === 'asset') totalAssets += net
      else if (t === 'liability') totalLiabilities += net
      else if (t === 'equity') totalEquity += net
    }
    return {
      totalRevenue: Math.abs(totalRevenue) || 0,
      totalExpenses: Math.abs(totalExpenses) || 0,
      netIncome: (Math.abs(totalRevenue) - Math.abs(totalExpenses)) || 0,
      totalAssets: Math.max(0, totalAssets),
      totalLiabilities: Math.max(0, totalLiabilities),
      totalEquity: Math.max(0, totalEquity),
    }
  }

  static async getFinancialRatios(
    organizationId: string,
    _fromDate?: string,
    _toDate?: string
  ): Promise<{
    liquidity: {
      current_ratio: number
      quick_ratio: number
      working_capital: number
    }
    profitability: {
      gross_profit_margin: number
      net_profit_margin: number
      roa: number
    }
  }> {
    const m = await this.getFinancialMetrics(organizationId, _fromDate, _toDate)
    const working_capital = m.totalAssets - m.totalLiabilities
    const roa = m.totalAssets > 0 ? m.netIncome / m.totalAssets : 0
    return {
      liquidity: {
        current_ratio: 0,
        quick_ratio: 0,
        working_capital: Math.max(0, working_capital),
      },
      profitability: {
        gross_profit_margin: 0,
        net_profit_margin: m.netIncome !== 0 && m.totalRevenue ? m.netIncome / m.totalRevenue : 0,
        roa,
      },
    }
  }

  // ================================
  // REPORTS GENERATION
  // ================================

  static async generateBalanceSheet(organizationId: string, asOfDate?: string): Promise<{
    isGroupBased: boolean
    assetSections: Array<{
      name: string
      group: string
      accounts: Array<{
        id: number
        code: string
        name: string
        account_type: string
        balance: number
        parent_id: number | null
      }>
      total: number
    }>
    liabilitySections: Array<{
      name: string
      group: string
      accounts: Array<{
        id: number
        code: string
        name: string
        account_type: string
        balance: number
        parent_id: number | null
      }>
      total: number
    }>
    equitySections: Array<{
      name: string
      group: string
      accounts: Array<{
        id: number
        code: string
        name: string
        account_type: string
        balance: number
        parent_id: number | null
      }>
      total: number
    }>
    totalAssets: number
    totalLiabilities: number
    totalEquity: number
    isBalanced: boolean
    generatedAt: string
  }> {
    const currentDate = asOfDate || new Date().toISOString().split('T')[0]

    try {
      const sql = getSql()
      const accounts = (await sql<
        {
          id: number
          code: string
          name: string
          account_type: string
          group: string | null
          report_category: AccountReportCategory | null
          parent_id: number | null
          is_active: boolean
        }[]
      >`
        SELECT id, code, name, account_type::text AS account_type, "group" AS "group",
               report_category::text AS report_category, parent_id, is_active
        FROM public.accounts
        WHERE organization_id = ${organizationId}::uuid AND is_active = true
      `) as {
        id: number
        code: string
        name: string
        account_type: AccountType
        group: string | null
        report_category: AccountReportCategory | null
        parent_id: number | null
        is_active: boolean
      }[]

      if (!accounts || accounts.length === 0) {
        return {
          isGroupBased: true,
          assetSections: [],
          liabilitySections: [],
          equitySections: [],
          totalAssets: 0,
          totalLiabilities: 0,
          totalEquity: 0,
          isBalanced: false,
          generatedAt: new Date().toISOString()
        }
      }

      const accountIds = accounts.map((acc) => acc.id)
      const balances = (await sql<
        { account_id: number; debit_amount: string; credit_amount: string }[]
      >`
        SELECT
          jel.account_id,
          jel.debit_amount::text AS debit_amount,
          jel.credit_amount::text AS credit_amount
        FROM public.journal_entry_lines jel
        INNER JOIN public.journal_entries je ON je.id = jel.journal_entry_id
        WHERE je.organization_id = ${organizationId}::uuid
          AND jel.account_id = ANY(${accountIds}::bigint[])
          AND je.entry_date <= ${currentDate}::date
      `) as { account_id: number; debit_amount: string; credit_amount: string }[]

      const accountBalances = new Map<number, number>()
      for (const b of balances) {
        const dr = parseFloat(b.debit_amount) || 0
        const cr = parseFloat(b.credit_amount) || 0
        const currentBalance = accountBalances.get(b.account_id) || 0
        accountBalances.set(b.account_id, currentBalance + (dr - cr))
      }

      // Add balances to accounts
      const accountsWithBalances = accounts.map(account => ({
        ...account,
        balance: accountBalances.get(account.id) || 0
      }))

      const assetAccounts = accountsWithBalances.filter((acc) => acc.account_type === 'asset')
      const liabilityAccounts = accountsWithBalances.filter((acc) => acc.account_type === 'liability')
      const equityAccounts = accountsWithBalances.filter((acc) => acc.account_type === 'equity')

      // Create sections
      const assetSections = this.createAccountSections(assetAccounts, 'Assets')
      const liabilitySections = this.createAccountSections(liabilityAccounts, 'Liabilities')
      const equitySections = this.createAccountSections(equityAccounts, 'Equity')

      // Calculate totals
      const totalAssets = assetSections.reduce((sum, section) => sum + section.total, 0)
      const totalLiabilities = liabilitySections.reduce((sum, section) => sum + section.total, 0)
      const totalEquity = equitySections.reduce((sum, section) => sum + section.total, 0)
      const isBalanced = totalAssets === (totalLiabilities + totalEquity)

      return {
        isGroupBased: true,
        assetSections,
        liabilitySections,
        equitySections,
        totalAssets,
        totalLiabilities,
        totalEquity,
        isBalanced,
        generatedAt: new Date().toISOString()
      }

    } catch (error) {
      console.error('Error generating balance sheet:', error)
      return {
        isGroupBased: true,
        assetSections: [],
        liabilitySections: [],
        equitySections: [],
        totalAssets: 0,
        totalLiabilities: 0,
        totalEquity: 0,
        isBalanced: false,
        generatedAt: new Date().toISOString()
      }
    }
  }

  private static createAccountSections(
    accounts: Array<{
      id: number
      code: string
      name: string
      account_type: AccountType
      group: string | null
      report_category: AccountReportCategory | null
      parent_id: number | null
      balance: number
    }>,
    categoryName: string
  ) {
    const sections = new Map<string, typeof accounts>()

    accounts.forEach((account) => {
      const key = resolveBalanceSheetSubsectionKey({
        account_type: account.account_type,
        group: account.group,
        report_category: account.report_category,
      })
      if (!sections.has(key)) {
        sections.set(key, [])
      }
      sections.get(key)!.push(account)
    })

    const sorted = Array.from(sections.entries()).sort(
      ([a], [b]) => balanceSheetSubsectionSortOrder(a) - balanceSheetSubsectionSortOrder(b)
    )

    return sorted.map(([group, sectionAccounts]) => {
      const treeAccounts = this.buildAccountTree(sectionAccounts)

      const total = sectionAccounts.reduce((sum, acc) => {
        if (categoryName === 'Liabilities') {
          return sum + Math.abs(acc.balance)
        }
        return sum + acc.balance
      }, 0)

      return {
        name: formatReportCategoryLabel(group),
        group,
        accounts: treeAccounts,
        total,
      }
    })
  }

  private static buildAccountTree(accounts: any[]): any[] {
    // Create a map for quick lookup
    const accountMap = new Map<number, any>()
    const rootAccounts: any[] = []

    // First pass: create account objects with children arrays
    accounts.forEach(account => {
      accountMap.set(account.id, {
        id: account.id,
        code: account.code,
        name: account.name,
        account_type: account.account_type,
        balance: account.balance,
        parent_id: account.parent_id,
        children: []
      })
    })

    // Second pass: build the tree structure
    accounts.forEach(account => {
      const accountObj = accountMap.get(account.id)!
      
      if (account.parent_id && accountMap.has(account.parent_id)) {
        // This account has a parent, add it to parent's children
        const parent = accountMap.get(account.parent_id)!
        parent.children.push(accountObj)
      } else {
        // This is a root account
        rootAccounts.push(accountObj)
      }
    })

    // Sort accounts by code
    const sortAccounts = (accs: any[]) => {
      accs.sort((a, b) => a.code.localeCompare(b.code))
      accs.forEach(acc => {
        if (acc.children.length > 0) {
          sortAccounts(acc.children)
        }
      })
    }

    sortAccounts(rootAccounts)
    return rootAccounts
  }

  static async generateIncomeStatement(organizationId: string, fromDate?: string, toDate?: string): Promise<{
    revenue: { total: number; breakdown: Array<{ account: string; amount: number }> }
    costOfSales: { total: number; breakdown: Array<{ account: string; amount: number }> }
    operatingExpenses: { total: number; breakdown: Array<{ account: string; amount: number }> }
    otherExpenses: { total: number; breakdown: Array<{ account: string; amount: number }> }
    expenses: { total: number; breakdown: Array<{ account: string; amount: number }> }
    netIncome: number
    grossProfit: number
    operatingIncome: number
    generatedAt: string
  }> {
    const currentDate = new Date().toISOString().split('T')[0]
    const startDate = fromDate || currentDate
    const endDate = toDate || currentDate

    try {
      const sql = getSql()
      const accounts = (await sql<
        {
          id: number
          code: string
          name: string
          account_type: string
          report_category: AccountReportCategory | null
          is_active: boolean
        }[]
      >`
        SELECT id, code, name, account_type::text AS account_type,
               report_category::text AS report_category, is_active
        FROM public.accounts
        WHERE organization_id = ${organizationId}::uuid AND is_active = true
      `) as {
        id: number
        code: string
        name: string
        account_type: AccountType
        report_category: AccountReportCategory | null
        is_active: boolean
      }[]

      const emptyIs = () => ({
        revenue: { total: 0, breakdown: [] as Array<{ account: string; amount: number }> },
        costOfSales: { total: 0, breakdown: [] as Array<{ account: string; amount: number }> },
        operatingExpenses: { total: 0, breakdown: [] as Array<{ account: string; amount: number }> },
        otherExpenses: { total: 0, breakdown: [] as Array<{ account: string; amount: number }> },
        expenses: { total: 0, breakdown: [] as Array<{ account: string; amount: number }> },
        netIncome: 0,
        grossProfit: 0,
        operatingIncome: 0,
        generatedAt: new Date().toISOString(),
      })

      if (!accounts || accounts.length === 0) {
        return emptyIs()
      }

      const journalRows = (await sql<
        { account_id: number; debit_amount: string; credit_amount: string }[]
      >`
        SELECT
          jel.account_id,
          jel.debit_amount::text,
          jel.credit_amount::text
        FROM public.journal_entry_lines jel
        INNER JOIN public.journal_entries je ON je.id = jel.journal_entry_id
        WHERE je.organization_id = ${organizationId}::uuid
          AND je.entry_date >= ${startDate}::date
          AND je.entry_date <= ${endDate}::date
      `) as { account_id: number; debit_amount: string; credit_amount: string }[]

      const accountBalances = new Map<number, number>()
      for (const entry of journalRows) {
        const currentBalance = accountBalances.get(entry.account_id) || 0
        const dr = parseFloat(entry.debit_amount) || 0
        const cr = parseFloat(entry.credit_amount) || 0
        accountBalances.set(entry.account_id, currentBalance + (dr - cr))
      }

      const revenueAccounts = accounts.filter((acc) => acc.account_type === 'revenue')
      const expenseAccounts = accounts.filter((acc) => acc.account_type === 'expense')

      const lineAmount = (accountId: number) => Math.abs(accountBalances.get(accountId) || 0)

      const revenueBreakdown = revenueAccounts
        .map((account) => ({
          account: account.name,
          amount: lineAmount(account.id),
        }))
        .filter((item) => item.amount > 0)
        .sort((a, b) => b.amount - a.amount)

      const totalRevenue = revenueBreakdown.reduce((sum, item) => sum + item.amount, 0)

      const cogsBreakdown = expenseAccounts
        .filter((acc) => resolveExpenseBucket(acc.report_category) === 'cost_of_sales')
        .map((account) => ({ account: account.name, amount: lineAmount(account.id) }))
        .filter((item) => item.amount > 0)
        .sort((a, b) => b.amount - a.amount)

      const operatingBreakdown = expenseAccounts
        .filter((acc) => resolveExpenseBucket(acc.report_category) === 'operating_expense')
        .map((account) => ({ account: account.name, amount: lineAmount(account.id) }))
        .filter((item) => item.amount > 0)
        .sort((a, b) => b.amount - a.amount)

      const otherExpenseBreakdown = expenseAccounts
        .filter((acc) => resolveExpenseBucket(acc.report_category) === 'other_expense')
        .map((account) => ({ account: account.name, amount: lineAmount(account.id) }))
        .filter((item) => item.amount > 0)
        .sort((a, b) => b.amount - a.amount)

      const totalCogs = cogsBreakdown.reduce((s, i) => s + i.amount, 0)
      const totalOperatingExp = operatingBreakdown.reduce((s, i) => s + i.amount, 0)
      const totalOtherExp = otherExpenseBreakdown.reduce((s, i) => s + i.amount, 0)

      const combinedExpenseBreakdown = [...cogsBreakdown, ...operatingBreakdown, ...otherExpenseBreakdown]
      const totalExpenses = totalCogs + totalOperatingExp + totalOtherExp

      const grossProfit = totalRevenue - totalCogs
      const operatingIncome = grossProfit - totalOperatingExp
      const netIncome = operatingIncome - totalOtherExp

      return {
        revenue: {
          total: totalRevenue,
          breakdown: revenueBreakdown.map(({ account, amount }) => ({ account, amount })),
        },
        costOfSales: { total: totalCogs, breakdown: cogsBreakdown },
        operatingExpenses: { total: totalOperatingExp, breakdown: operatingBreakdown },
        otherExpenses: { total: totalOtherExp, breakdown: otherExpenseBreakdown },
        expenses: { total: totalExpenses, breakdown: combinedExpenseBreakdown },
        netIncome,
        grossProfit,
        operatingIncome,
        generatedAt: new Date().toISOString(),
      }

    } catch (error) {
      console.error('Error generating income statement:', error)
      return {
        revenue: { total: 0, breakdown: [] },
        costOfSales: { total: 0, breakdown: [] },
        operatingExpenses: { total: 0, breakdown: [] },
        otherExpenses: { total: 0, breakdown: [] },
        expenses: { total: 0, breakdown: [] },
        netIncome: 0,
        grossProfit: 0,
        operatingIncome: 0,
        generatedAt: new Date().toISOString(),
      }
    }
  }

  static async generateTrialBalance(organizationId: string, asOfDate?: string): Promise<{
    accounts: Array<{
      accountId: number
      accountName: string
      accountType: string
      debitBalance: number
      creditBalance: number
    }>
    totalDebits: number
    totalCredits: number
    isBalanced: boolean
    generatedAt: string
  }> {
    const rows = await fetchTrialBalanceSums(organizationId, asOfDate ?? null)
    const accounts = rows.map((r) => {
      const { debit_balance, credit_balance } = trialRowToDebitsCredits(r)
      return {
        accountId: r.id,
        accountName: r.name,
        accountType: String(r.account_type),
        debitBalance: debit_balance,
        creditBalance: credit_balance,
      }
    })
    const totalDebits = accounts.reduce((s, a) => s + a.debitBalance, 0)
    const totalCredits = accounts.reduce((s, a) => s + a.creditBalance, 0)
    return {
      accounts,
      totalDebits,
      totalCredits,
      isBalanced: Math.abs(totalDebits - totalCredits) < 0.02,
      generatedAt: new Date().toISOString(),
    }
  }

  static async generateAgedReceivables(organizationId: string, asOfDate?: string): Promise<{
    receivables: Array<{
      customerName: string
      current: number
      days30: number
      days60: number
      days90: number
      total: number
    }>
    totals: {
      current: number
      days30: number
      days60: number
      days90: number
      total: number
    }
    generatedAt: string
  }> {
    void organizationId
    void asOfDate
    return {
      receivables: [],
      totals: { current: 0, days30: 0, days60: 0, days90: 0, total: 0 },
      generatedAt: new Date().toISOString(),
    }
  }

  static async generateAgedPayables(organizationId: string, asOfDate?: string): Promise<{
    payables: Array<{
      vendorName: string
      current: number
      days30: number
      days60: number
      days90: number
      total: number
    }>
    totals: {
      current: number
      days30: number
      days60: number
      days90: number
      total: number
    }
    generatedAt: string
  }> {
    void organizationId
    void asOfDate
    return {
      payables: [],
      totals: { current: 0, days30: 0, days60: 0, days90: 0, total: 0 },
      generatedAt: new Date().toISOString(),
    }
  }

  // ================================
  // LEDGER MANAGEMENT
  // ================================

  static async getAccountBalances(organizationId: string, fromDate?: string, toDate?: string): Promise<Array<{
    id: number
    code: string
    name: string
    account_type: AccountType
    balance: number
    debit_balance: number
    credit_balance: number
    transaction_count: number
    last_transaction_date: string | null
    last_transaction_at: string | null
    level: number
    is_postable: boolean
    parent_id: number | null
    description: string
    group: string
  }>> {
    const sql = getSql()
    const [accounts, aggRows] = await Promise.all([
      sql<Account[]>`
        SELECT * FROM public.accounts
        WHERE organization_id = ${organizationId}::uuid
          AND is_active = true
        ORDER BY code
      `,
      fetchJournalLineAggregatesByOrg(organizationId, fromDate, toDate),
    ])

    if (!accounts || accounts.length === 0) {
      return []
    }

    const calculateLevel = (account: Account, allAccounts: Account[], visited = new Set<number>()): number => {
      const accId = account.id
      if (visited.has(accId)) {
        return 1
      }
      visited.add(accId)
      const parentId = account.parent_id
      if (!parentId) {
        return 1
      }
      const parentAccount = allAccounts.find((acc) => acc.id === parentId)
      if (!parentAccount) {
        return 1
      }
      return calculateLevel(parentAccount, allAccounts, visited) + 1
    }

    const calculateIsPostable = (account: Account, allAccounts: Account[]): boolean => {
      const accId = account.id
      return !allAccounts.some((acc) => acc.parent_id === accId)
    }

    const accountBalances = new Map<
      number,
      {
        debitTotal: number
        creditTotal: number
        transactionCount: number
        lastTransactionDate: string | null
        lastTransactionAt: string | null
      }
    >()
    for (const row of aggRows) {
      accountBalances.set(row.account_id, {
        debitTotal: parseFloat(row.dr) || 0,
        creditTotal: parseFloat(row.cr) || 0,
        transactionCount: Number(row.txn_count) || 0,
        lastTransactionDate: row.last_entry,
        lastTransactionAt: row.last_activity_at,
      })
    }

    return accounts.map((account) => {
      const balance = accountBalances.get(account.id) || {
        debitTotal: 0,
        creditTotal: 0,
        transactionCount: 0,
        lastTransactionDate: null,
        lastTransactionAt: null,
      }

      const accountType = String(account.account_type).toLowerCase()
      let netBalance = 0
      if (accountType === 'asset' || accountType === 'expense') {
        netBalance = balance.debitTotal - balance.creditTotal
      } else {
        netBalance = balance.creditTotal - balance.debitTotal
      }

      return {
        id: account.id,
        code: account.code || '',
        name: account.name,
        account_type: account.account_type,
        balance: netBalance,
        debit_balance: balance.debitTotal,
        credit_balance: balance.creditTotal,
        transaction_count: balance.transactionCount,
        last_transaction_date: balance.lastTransactionDate,
        last_transaction_at: balance.lastTransactionAt,
        level: calculateLevel(account, accounts),
        is_postable: (account as Account).is_postable ?? calculateIsPostable(account, accounts),
        parent_id: account.parent_id || null,
        description: account.description || '',
        group: account.group || '',
      }
    })
  }

  /** Single round-trip through `/api/app-data`: runs metrics + balances in parallel on the server. */
  static async getDashboardBundle(
    organizationId: string,
    fromDate?: string,
    toDate?: string
  ): Promise<{
    financialMetrics: Awaited<ReturnType<typeof DataServiceAdmin.getFinancialMetrics>>
    accountBalances: Awaited<ReturnType<typeof DataServiceAdmin.getAccountBalances>>
  }> {
    const [financialMetrics, accountBalances] = await Promise.all([
      this.getFinancialMetrics(organizationId, fromDate, toDate),
      this.getAccountBalances(organizationId, fromDate, toDate),
    ])
    return { financialMetrics, accountBalances }
  }

  static async getAccountTransactions(
    accountId: number,
    organizationId: string,
    fromDate?: string,
    toDate?: string
  ): Promise<
    Array<{
      id: number
      entry_id: number
      entry_number: string
      entry_date: string
      created_at: string
      description: string
      reference: string | null
      debit_amount: number
      credit_amount: number
      balance: number
    }>
  > {
    const sql = getSql()
    type R = {
      id: number
      debit_amount: string
      credit_amount: string
      entry_id: number
      entry_number: string
      entry_date: string
      created_at: string
      description: string
      reference: string | null
    }
    let rows: R[] = []
    if (fromDate && toDate) {
      rows = (await sql<R[]>`
        SELECT
          jel.id,
          jel.debit_amount::text,
          jel.credit_amount::text,
          je.id AS entry_id,
          je.entry_number,
          je.entry_date::text AS entry_date,
          je.created_at::text AS created_at,
          je.description,
          je.reference
        FROM public.journal_entry_lines jel
        INNER JOIN public.journal_entries je ON je.id = jel.journal_entry_id
        WHERE jel.account_id = ${accountId}
          AND je.organization_id = ${organizationId}::uuid
          AND je.entry_date >= ${fromDate}::date
          AND je.entry_date <= ${toDate}::date
        ORDER BY je.entry_date ASC, je.created_at ASC, jel.id ASC
      `) as R[]
    } else if (fromDate) {
      rows = (await sql<R[]>`
        SELECT
          jel.id,
          jel.debit_amount::text,
          jel.credit_amount::text,
          je.id AS entry_id,
          je.entry_number,
          je.entry_date::text AS entry_date,
          je.created_at::text AS created_at,
          je.description,
          je.reference
        FROM public.journal_entry_lines jel
        INNER JOIN public.journal_entries je ON je.id = jel.journal_entry_id
        WHERE jel.account_id = ${accountId}
          AND je.organization_id = ${organizationId}::uuid
          AND je.entry_date >= ${fromDate}::date
        ORDER BY je.entry_date ASC, je.created_at ASC, jel.id ASC
      `) as R[]
    } else if (toDate) {
      rows = (await sql<R[]>`
        SELECT
          jel.id,
          jel.debit_amount::text,
          jel.credit_amount::text,
          je.id AS entry_id,
          je.entry_number,
          je.entry_date::text AS entry_date,
          je.created_at::text AS created_at,
          je.description,
          je.reference
        FROM public.journal_entry_lines jel
        INNER JOIN public.journal_entries je ON je.id = jel.journal_entry_id
        WHERE jel.account_id = ${accountId}
          AND je.organization_id = ${organizationId}::uuid
          AND je.entry_date <= ${toDate}::date
        ORDER BY je.entry_date ASC, je.created_at ASC, jel.id ASC
      `) as R[]
    } else {
      rows = (await sql<R[]>`
        SELECT
          jel.id,
          jel.debit_amount::text,
          jel.credit_amount::text,
          je.id AS entry_id,
          je.entry_number,
          je.entry_date::text AS entry_date,
          je.created_at::text AS created_at,
          je.description,
          je.reference
        FROM public.journal_entry_lines jel
        INNER JOIN public.journal_entries je ON je.id = jel.journal_entry_id
        WHERE jel.account_id = ${accountId}
          AND je.organization_id = ${organizationId}::uuid
        ORDER BY je.entry_date ASC, je.created_at ASC, jel.id ASC
      `) as R[]
    }

    let runningBalance = 0
    return rows.map((line) => {
      const dr = parseFloat(line.debit_amount) || 0
      const cr = parseFloat(line.credit_amount) || 0
      runningBalance += dr - cr
      return {
        id: line.id,
        entry_id: line.entry_id,
        entry_number: line.entry_number,
        entry_date: line.entry_date,
        created_at: line.created_at,
        description: line.description,
        reference: line.reference,
        debit_amount: dr,
        credit_amount: cr,
        balance: runningBalance,
      }
    })
  }

  // ================================
  // INVENTORY MANAGEMENT
  // ================================

  // Inventory Categories
  static async getInventoryCategories(organizationId: string, activeOnly: boolean = false): Promise<InventoryCategory[]> {
    const sql = getSql()
    const rows = activeOnly
      ? ((await sql<InventoryCategory[]>`
        SELECT * FROM public.inventory_categories
        WHERE organization_id = ${organizationId}::uuid AND is_active = true
        ORDER BY name
      `) as InventoryCategory[])
      : ((await sql<InventoryCategory[]>`
        SELECT * FROM public.inventory_categories
        WHERE organization_id = ${organizationId}::uuid
        ORDER BY name
      `) as InventoryCategory[])
    return attachCategoryAccounts(sql, rows)
  }

  static async getInventoryCategory(categoryId: number): Promise<InventoryCategory | null> {
    const sql = getSql()
    const rows = (await sql<InventoryCategory[]>`
      SELECT * FROM public.inventory_categories
      WHERE id = ${categoryId}
      LIMIT 1
    `) as InventoryCategory[]
    const c = rows[0]
    if (!c) return null
    const withAcc = await attachCategoryAccounts(sql, [c])
    return withAcc[0] ?? null
  }

  static async createInventoryCategory(
    category: Omit<InventoryCategory, 'id' | 'created_at' | 'updated_at'>
  ): Promise<InventoryCategory | null> {
    const sql = getSql()
    const c = category
    const ins = (await sql<InventoryCategory[]>`
      INSERT INTO public.inventory_categories (
        organization_id, name, description, inventory_account_id, expense_account_id, parent_id, is_active, created_by
      )
      VALUES (
        ${c.organization_id}::uuid,
        ${c.name},
        ${c.description},
        ${c.inventory_account_id},
        ${c.expense_account_id},
        ${c.parent_id},
        ${c.is_active},
        ${c.created_by}::uuid
      )
      RETURNING *
    `) as InventoryCategory[]
    const row = ins[0]
    if (!row) return null
    const withAcc = await attachCategoryAccounts(sql, [row])
    return withAcc[0] ?? null
  }

  static async updateInventoryCategory(
    categoryId: number,
    updates: Partial<InventoryCategory>
  ): Promise<InventoryCategory | null> {
    const sql = getSql()
    const u = updates
    const rows = (await sql<InventoryCategory[]>`
      UPDATE public.inventory_categories
      SET
        name = COALESCE(${u.name ?? null}, name),
        description = ${u.description === undefined ? null : u.description},
        inventory_account_id = COALESCE(${u.inventory_account_id ?? null}, inventory_account_id),
        expense_account_id = COALESCE(${u.expense_account_id ?? null}, expense_account_id),
        parent_id = ${u.parent_id === undefined ? null : u.parent_id},
        is_active = COALESCE(${u.is_active ?? null}, is_active)
      WHERE id = ${categoryId}
      RETURNING *
    `) as InventoryCategory[]
    const row = rows[0]
    if (!row) return null
    const withAcc = await attachCategoryAccounts(sql, [row])
    return withAcc[0] ?? null
  }

  static async deleteInventoryCategory(categoryId: number): Promise<boolean> {
    const sql = getSql()
    const r = await sql`DELETE FROM public.inventory_categories WHERE id = ${categoryId}`
    return ((r as { count?: number }).count ?? 1) > 0
  }

  // Inventory Items
  static async getInventoryItems(organizationId: string, activeOnly: boolean = false): Promise<InventoryItem[]> {
    const sql = getSql()
    const base = activeOnly
      ? ((await sql<InventoryItem[]>`
        SELECT * FROM public.inventory_items
        WHERE organization_id = ${organizationId}::uuid AND is_active = true
        ORDER BY sku
      `) as InventoryItem[])
      : ((await sql<InventoryItem[]>`
        SELECT * FROM public.inventory_items
        WHERE organization_id = ${organizationId}::uuid
        ORDER BY sku
      `) as InventoryItem[])
    return attachItemsCategories(sql, base)
  }

  static async getInventoryItem(itemId: number): Promise<InventoryItem | null> {
    const sql = getSql()
    const rows = (await sql<InventoryItem[]>`
      SELECT * FROM public.inventory_items
      WHERE id = ${itemId}
      LIMIT 1
    `) as InventoryItem[]
    return attachItemCategory(sql, rows[0] ?? null)
  }

  static async createInventoryItem(
    item: Omit<InventoryItem, 'id' | 'created_at' | 'updated_at' | 'quantity_available' | 'total_value'>
  ): Promise<InventoryItem | null> {
    const sql = getSql()
    const i = item
    const ins = (await sql<InventoryItem[]>`
      INSERT INTO public.inventory_items (
        organization_id, category_id, sku, name, description, unit_of_measure, quantity_in, quantity_out, average_unit_cost, reorder_point, reorder_quantity, is_active, created_by
      ) VALUES (
        ${i.organization_id}::uuid,
        ${i.category_id},
        ${i.sku},
        ${i.name},
        ${i.description},
        ${i.unit_of_measure},
        ${i.quantity_in},
        ${i.quantity_out},
        ${i.average_unit_cost},
        ${i.reorder_point},
        ${i.reorder_quantity},
        ${i.is_active},
        ${i.created_by}::uuid
      )
      RETURNING *
    `) as InventoryItem[]
    return ins[0] ? this.getInventoryItem(ins[0].id) : null
  }

  static async updateInventoryItem(
    itemId: number,
    updates: Partial<InventoryItem>
  ): Promise<InventoryItem | null> {
    const sql = getSql()
    const u = updates
    await sql`
      UPDATE public.inventory_items
      SET
        category_id = COALESCE(${u.category_id ?? null}, category_id),
        sku = COALESCE(${u.sku ?? null}, sku),
        name = COALESCE(${u.name ?? null}, name),
        description = ${u.description === undefined ? null : u.description},
        unit_of_measure = COALESCE(${u.unit_of_measure ?? null}, unit_of_measure),
        quantity_in = COALESCE(${u.quantity_in ?? null}, quantity_in),
        quantity_out = COALESCE(${u.quantity_out ?? null}, quantity_out),
        quantity_available = COALESCE(${u.quantity_available ?? null}, quantity_available),
        average_unit_cost = COALESCE(${u.average_unit_cost ?? null}, average_unit_cost),
        total_value = COALESCE(${u.total_value ?? null}, total_value),
        reorder_point = COALESCE(${u.reorder_point ?? null}, reorder_point),
        reorder_quantity = COALESCE(${u.reorder_quantity ?? null}, reorder_quantity),
        is_active = COALESCE(${u.is_active ?? null}, is_active)
      WHERE id = ${itemId}
    `
    return this.getInventoryItem(itemId)
  }

  static async deleteInventoryItem(itemId: number): Promise<boolean> {
    const sql = getSql()
    const r = await sql`DELETE FROM public.inventory_items WHERE id = ${itemId}`
    return ((r as { count?: number }).count ?? 1) > 0
  }

  // Inventory Transactions
  static async getInventoryTransactions(
    organizationId: string,
    itemId?: number,
    limit?: number
  ): Promise<InventoryTransaction[]> {
    const sql = getSql()
    let base: InventoryTransaction[] = []
    if (itemId) {
      base = limit
        ? ((await sql<InventoryTransaction[]>`
          SELECT * FROM public.inventory_transactions
          WHERE organization_id = ${organizationId}::uuid AND item_id = ${itemId}
          ORDER BY transaction_date DESC, created_at DESC
          LIMIT ${limit}
        `) as InventoryTransaction[])
        : ((await sql<InventoryTransaction[]>`
          SELECT * FROM public.inventory_transactions
          WHERE organization_id = ${organizationId}::uuid AND item_id = ${itemId}
          ORDER BY transaction_date DESC, created_at DESC
        `) as InventoryTransaction[])
    } else {
      base = limit
        ? ((await sql<InventoryTransaction[]>`
          SELECT * FROM public.inventory_transactions
          WHERE organization_id = ${organizationId}::uuid
          ORDER BY transaction_date DESC, created_at DESC
          LIMIT ${limit}
        `) as InventoryTransaction[])
        : ((await sql<InventoryTransaction[]>`
          SELECT * FROM public.inventory_transactions
          WHERE organization_id = ${organizationId}::uuid
          ORDER BY transaction_date DESC, created_at DESC
        `) as InventoryTransaction[])
    }
    return attachTransactionItem(sql, base)
  }

  static async createInventoryTransaction(
    transaction: Omit<InventoryTransaction, 'id' | 'created_at'>
  ): Promise<InventoryTransaction | null> {
    const sql = getSql()
    const t = transaction
    const row = await sql.begin(async (tx) => {
      const ins = (await tx<InventoryTransaction[]>`
        INSERT INTO public.inventory_transactions (
          organization_id, item_id, transaction_type, quantity, unit_cost, total_cost, journal_entry_id, reference, description, transaction_date, created_by
        ) VALUES (
          ${t.organization_id}::uuid,
          ${t.item_id},
          ${t.transaction_type},
          ${t.quantity},
          ${t.unit_cost},
          ${t.total_cost},
          ${t.journal_entry_id},
          ${t.reference},
          ${t.description},
          ${t.transaction_date}::date,
          ${t.created_by}::uuid
        )
        RETURNING *
      `) as InventoryTransaction[]
      const tr = ins[0]
      if (!tr) return null

      const locked = (await tx<InventoryItem[]>`
        SELECT * FROM public.inventory_items
        WHERE id = ${t.item_id} AND organization_id = ${t.organization_id}::uuid
        FOR UPDATE
      `) as InventoryItem[]
      const item = locked[0]
      if (!item) {
        throw new Error('Inventory item not found for this organization')
      }

      const qty = Number(tr.quantity)
      const qIn = Math.abs(qty)
      let quantityIn = Number(item.quantity_in)
      let quantityOut = Number(item.quantity_out)
      const avail = Number(item.quantity_available)
      const avg = Number(item.average_unit_cost)
      let val = Number(item.total_value)
      const kind = t.transaction_type

      if (kind === 'in') {
        const addQty = qIn
        quantityIn += addQty
        let addValue = 0
        if (t.total_cost != null && Number(t.total_cost) > 0) {
          addValue = Number(t.total_cost)
        } else if (t.unit_cost != null && Number(t.unit_cost) > 0) {
          addValue = addQty * Number(t.unit_cost)
        } else {
          addValue = addQty * avg
        }
        const newAvail = avail + addQty
        const newTotal = val + addValue
        const newAvg = newAvail > 0 ? newTotal / newAvail : 0
        await tx`
          UPDATE public.inventory_items
          SET
            quantity_in = ${quantityIn},
            quantity_available = ${newAvail},
            total_value = ${newTotal},
            average_unit_cost = ${newAvg}
          WHERE id = ${item.id} AND organization_id = ${t.organization_id}::uuid
        `
      } else if (kind === 'out') {
        const outQty = qIn
        if (avail + 1e-9 < outQty) {
          throw new Error('Insufficient quantity on hand for this issue')
        }
        quantityOut += outQty
        const newAvail = avail - outQty
        const cogs = outQty * avg
        const newTotal = Math.max(0, val - cogs)
        await tx`
          UPDATE public.inventory_items
          SET
            quantity_out = ${quantityOut},
            quantity_available = ${newAvail},
            total_value = ${newTotal}
          WHERE id = ${item.id} AND organization_id = ${t.organization_id}::uuid
        `
      } else {
        // adjustment: signed delta on available; value at current average
        const newAvail = avail + qty
        if (newAvail < -1e-9) {
          throw new Error('Adjustment would make quantity negative')
        }
        const newTotal = newAvail * avg
        await tx`
          UPDATE public.inventory_items
          SET
            quantity_available = ${newAvail},
            total_value = ${newTotal < 0 ? 0 : newTotal}
          WHERE id = ${item.id} AND organization_id = ${t.organization_id}::uuid
        `
      }

      return tr
    })

    if (!row) return null
    const [enriched] = await attachTransactionItem(sql, [row])
    return enriched ?? null
  }

  // Get low stock items
  static async getLowStockItems(organizationId: string): Promise<InventoryItem[]> {
    const items = await this.getInventoryItems(organizationId, true)
    return items.filter(
      (item) => item.reorder_point > 0 && item.quantity_available <= item.reorder_point
    )
  }

  // Get inventory value by category
  static async getInventoryValueByCategory(organizationId: string): Promise<Array<{category: string, value: number}>> {
    const items = await this.getInventoryItems(organizationId, true)
    
    const categoryMap = new Map<string, number>()
    
    items.forEach(item => {
      const categoryName = item.category?.name || 'Uncategorized'
      const currentValue = categoryMap.get(categoryName) || 0
      categoryMap.set(categoryName, currentValue + item.total_value)
    })

    return Array.from(categoryMap.entries()).map(([category, value]) => ({
      category,
      value
    }))
  }
}

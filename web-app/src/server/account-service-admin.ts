import { getSql } from '@/server/pg'
import { fetchAccountNetBalance } from '@/server/data/ledger-sql'
import { getActingUserId } from '@/server/request-context'
import { Account, AccountType } from '@/types'

export class AccountServiceAdmin {
  static async getAccounts(
    organizationId: string,
    accountType?: AccountType,
    isActive: boolean = true
  ): Promise<Account[]> {
    const sql = getSql()
    if (isActive && accountType) {
      return (await sql<Account[]>`
        SELECT * FROM public.accounts
        WHERE organization_id = ${organizationId}::uuid
          AND is_active = true
          AND account_type = ${accountType}::public.account_type
        ORDER BY code
      `) as Account[]
    }
    if (isActive) {
      return (await sql<Account[]>`
        SELECT * FROM public.accounts
        WHERE organization_id = ${organizationId}::uuid AND is_active = true
        ORDER BY code
      `) as Account[]
    }
    if (accountType) {
      return (await sql<Account[]>`
        SELECT * FROM public.accounts
        WHERE organization_id = ${organizationId}::uuid
          AND account_type = ${accountType}::public.account_type
        ORDER BY code
      `) as Account[]
    }
    return (await sql<Account[]>`
      SELECT * FROM public.accounts
      WHERE organization_id = ${organizationId}::uuid
      ORDER BY code
    `) as Account[]
  }

  static async getAccount(id: number): Promise<Account | null> {
    const sql = getSql()
    const rows = (await sql<Account[]>`
      SELECT * FROM public.accounts WHERE id = ${id} LIMIT 1
    `) as Account[]
    return rows[0] ?? null
  }

  static async createAccount(accountData: {
    organization_id: string
    code: string
    name: string
    account_type: AccountType
    parent_id?: number
    description?: string
    group?: string
    is_postable?: boolean
  }): Promise<Account> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')
    const sql = getSql()
    const a = { ...accountData, created_by: acting, is_postable: accountData.is_postable ?? true, is_active: true }
    const rows = (await sql<Account[]>`
      INSERT INTO public.accounts (
        organization_id, code, name, account_type, parent_id, description, "group", is_postable, is_active, created_by
      ) VALUES (
        ${a.organization_id}::uuid,
        ${a.code},
        ${a.name},
        ${a.account_type}::public.account_type,
        ${a.parent_id ?? null},
        ${a.description ?? null},
        ${a.group ?? null},
        ${a.is_postable},
        true,
        ${a.created_by}::uuid
      )
      RETURNING *
    `) as Account[]
    if (!rows[0]) {
      throw new Error('Failed to create account')
    }
    return rows[0] as Account
  }

  static async updateAccount(id: number, accountData: Partial<Account>): Promise<Account> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')
    const sql = getSql()
    const u = accountData
    const rows = (await sql<Account[]>`
      UPDATE public.accounts
      SET
        code = COALESCE(${u.code ?? null}, code),
        name = COALESCE(${u.name ?? null}, name),
        account_type = COALESCE(${u.account_type ?? null}::public.account_type, account_type),
        parent_id = ${u.parent_id === undefined ? null : u.parent_id},
        description = ${u.description === undefined ? null : u.description},
        is_active = COALESCE(${u.is_active ?? null}, is_active),
        "group" = COALESCE(${u.group ?? null}, "group"),
        is_postable = COALESCE(${u.is_postable ?? null}, is_postable),
        updated_at = now()
      WHERE id = ${id}
      RETURNING *
    `) as Account[]
    if (!rows[0]) {
      throw new Error('Failed to update account')
    }
    return rows[0] as Account
  }

  static async deleteAccount(id: number): Promise<void> {
    const sql = getSql()
    await sql`DELETE FROM public.accounts WHERE id = ${id}`
  }

  static async getAccountHierarchy(organizationId: string): Promise<Account[]> {
    return this.getAccounts(organizationId, undefined, true)
  }

  static async getChildAccounts(parentId: number): Promise<Account[]> {
    const sql = getSql()
    return (await sql<Account[]>`
      SELECT * FROM public.accounts
      WHERE parent_id = ${parentId} AND is_active = true
      ORDER BY code
    `) as Account[]
  }

  static async getParentAccounts(organizationId: string): Promise<Account[]> {
    const sql = getSql()
    return (await sql<Account[]>`
      SELECT * FROM public.accounts
      WHERE organization_id = ${organizationId}::uuid
        AND parent_id IS NULL
        AND is_active = true
      ORDER BY code
    `) as Account[]
  }

  static async searchAccounts(
    organizationId: string,
    searchTerm: string,
    accountType?: AccountType,
    limit: number = 50
  ): Promise<Account[]> {
    const sql = getSql()
    const term = `%${searchTerm.replace(/[%_\\]/g, (c) => '\\' + c)}%`
    if (accountType) {
      return (await sql<Account[]>`
        SELECT * FROM public.accounts
        WHERE organization_id = ${organizationId}::uuid
          AND is_active = true
          AND account_type = ${accountType}::public.account_type
          AND (code ILIKE ${term} OR name ILIKE ${term})
        ORDER BY code
        LIMIT ${limit}
      `) as Account[]
    }
    return (await sql<Account[]>`
      SELECT * FROM public.accounts
      WHERE organization_id = ${organizationId}::uuid
        AND is_active = true
        AND (code ILIKE ${term} OR name ILIKE ${term})
      ORDER BY code
      LIMIT ${limit}
    `) as Account[]
  }

  static async getAccountsByType(organizationId: string, accountType: AccountType): Promise<Account[]> {
    return this.getAccounts(organizationId, accountType)
  }

  static async getPostableAccounts(organizationId: string): Promise<Account[]> {
    const sql = getSql()
    return (await sql<Account[]>`
      SELECT * FROM public.accounts
      WHERE organization_id = ${organizationId}::uuid
        AND is_active = true
        AND is_postable = true
      ORDER BY code
    `) as Account[]
  }

  static async validateAccountCode(organizationId: string, code: string, excludeId?: number): Promise<boolean> {
    const sql = getSql()
    const rows = excludeId
      ? await sql<{ c: string }[]>`
        SELECT 1::text AS c
        FROM public.accounts
        WHERE organization_id = ${organizationId}::uuid AND code = ${code} AND id <> ${excludeId}
        LIMIT 1
      `
      : await sql<{ c: string }[]>`
        SELECT 1::text AS c
        FROM public.accounts
        WHERE organization_id = ${organizationId}::uuid AND code = ${code}
        LIMIT 1
      `
    return rows.length === 0
  }

  static async getAccountBalance(_accountId: number, _asOfDate?: string): Promise<number> {
    const sql = getSql()
    const o = (await sql<{ organization_id: string }[]>`
      SELECT organization_id::text AS organization_id FROM public.accounts
      WHERE id = ${_accountId} LIMIT 1
    `)[0]
    if (!o) return 0
    return fetchAccountNetBalance(_accountId, o.organization_id)
  }

  static async getAccountStats(organizationId: string): Promise<{
    total_accounts: number
    accounts_by_type: Record<AccountType, number>
    active_accounts: number
    inactive_accounts: number
    postable_accounts: number
  }> {
    const sql = getSql()
    const data = (await sql<Pick<Account, 'account_type' | 'is_active' | 'is_postable'>[]>`
      SELECT account_type::text AS account_type, is_active, is_postable
      FROM public.accounts
      WHERE organization_id = ${organizationId}::uuid
    `) as Pick<Account, 'account_type' | 'is_active' | 'is_postable'>[]

    const rows = (data ?? []) as Pick<Account, 'account_type' | 'is_active' | 'is_postable'>[]

    const stats = {
      total_accounts: rows.length,
      accounts_by_type: {
        asset: 0,
        liability: 0,
        equity: 0,
        revenue: 0,
        expense: 0,
      } as Record<AccountType, number>,
      active_accounts: 0,
      inactive_accounts: 0,
      postable_accounts: 0,
    }

    rows.forEach((account) => {
      stats.accounts_by_type[account.account_type]++
      if (account.is_active) {
        stats.active_accounts++
      } else {
        stats.inactive_accounts++
      }
      if (account.is_postable) {
        stats.postable_accounts++
      }
    })

    return stats
  }

  static async getChartOfAccounts(organizationId: string): Promise<Account[]> {
    return this.getAccountHierarchy(organizationId)
  }

  static async exportChartOfAccounts(organizationId: string): Promise<Account[]> {
    const sql = getSql()
    return (await sql<Account[]>`
      SELECT * FROM public.accounts
      WHERE organization_id = ${organizationId}::uuid
      ORDER BY code
    `) as Account[]
  }

  static async importChartOfAccounts(
    organizationId: string,
    accounts: Omit<Account, 'id' | 'organization_id' | 'created_at' | 'updated_at' | 'created_by'>[]
  ): Promise<Account[]> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')
    const sql = getSql()
    const out: Account[] = []
    await sql.begin(async (tx) => {
      for (const a of accounts) {
        const rows = (await tx<Account[]>`
          INSERT INTO public.accounts (
            organization_id, code, name, account_type, parent_id, description, "group", is_postable, is_active, created_by
          ) VALUES (
            ${organizationId}::uuid,
            ${a.code},
            ${a.name},
            ${a.account_type}::public.account_type,
            ${a.parent_id},
            ${a.description},
            ${a.group},
            ${a.is_postable ?? true},
            ${a.is_active},
            ${acting}::uuid
          )
          RETURNING *
        `) as Account[]
        if (rows[0]) {
          out.push(rows[0] as Account)
        }
      }
    })
    return out
  }
}

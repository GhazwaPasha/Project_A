import { getSupabaseAdmin } from '@/server/supabase-admin'
import { getActingUserId } from '@/server/request-context'
import { Account, AccountType } from '@/types'

export class AccountServiceAdmin {
  // ===============================================
  // ACCOUNT CRUD OPERATIONS
  // ===============================================

  static async getAccounts(
    organizationId: string,
    accountType?: AccountType,
    isActive: boolean = true
  ): Promise<Account[]> {
    let query = getSupabaseAdmin()
      .from('accounts')
      .select('*')
      .eq('organization_id', organizationId)
      .order('code', { ascending: true })

    if (isActive) {
      query = query.eq('is_active', true)
    }

    if (accountType) {
      query = query.eq('account_type', accountType)
    }

    const { data, error } = await query

    if (error) {
      console.error('Error fetching accounts:', error)
      throw new Error('Failed to fetch accounts')
    }

    return data || []
  }

  static async getAccount(id: number): Promise<Account | null> {
    const { data, error } = await getSupabaseAdmin()
      .from('accounts')
      .select('*')
      .eq('id', id)
      .single()

    if (error) {
      console.error('Error fetching account:', error)
      throw new Error('Failed to fetch account')
    }

    return data
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

    const { data, error } = await getSupabaseAdmin()
      .from('accounts')
      .insert({
        ...accountData,
        is_active: true,
        created_by: acting,
      })
      .select()
      .single()

    if (error) {
      console.error('Error creating account:', error)
      throw new Error(`Failed to create account: ${error.message}`)
    }

    return data
  }

  static async updateAccount(id: number, accountData: Partial<Account>): Promise<Account> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')

    const { data, error } = await getSupabaseAdmin()
      .from('accounts')
      .update({
        ...accountData,
        updated_at: new Date().toISOString()
      })
      .eq('id', id)
      .select()
      .single()

    if (error) {
      console.error('Error updating account:', error)
      throw new Error(`Failed to update account: ${error.message}`)
    }

    return data
  }

  static async deleteAccount(id: number): Promise<void> {
    const { error } = await getSupabaseAdmin()
      .from('accounts')
      .delete()
      .eq('id', id)

    if (error) {
      console.error('Error deleting account:', error)
      throw new Error('Failed to delete account')
    }
  }

  // ===============================================
  // ACCOUNT HIERARCHY OPERATIONS
  // ===============================================

  static async getAccountHierarchy(organizationId: string): Promise<Account[]> {
    const { data, error } = await getSupabaseAdmin()
      .from('accounts')
      .select('*')
      .eq('organization_id', organizationId)
      .eq('is_active', true)
      .order('code', { ascending: true })

    if (error) {
      console.error('Error fetching account hierarchy:', error)
      throw new Error('Failed to fetch account hierarchy')
    }

    return data || []
  }

  static async getChildAccounts(parentId: number): Promise<Account[]> {
    const { data, error } = await getSupabaseAdmin()
      .from('accounts')
      .select('*')
      .eq('parent_id', parentId)
      .eq('is_active', true)
      .order('code', { ascending: true })

    if (error) {
      console.error('Error fetching child accounts:', error)
      throw new Error('Failed to fetch child accounts')
    }

    return data || []
  }

  static async getParentAccounts(organizationId: string): Promise<Account[]> {
    const { data, error } = await getSupabaseAdmin()
      .from('accounts')
      .select('*')
      .eq('organization_id', organizationId)
      .is('parent_id', null)
      .eq('is_active', true)
      .order('code', { ascending: true })

    if (error) {
      console.error('Error fetching parent accounts:', error)
      throw new Error('Failed to fetch parent accounts')
    }

    return data || []
  }

  // ===============================================
  // ACCOUNT SEARCH AND FILTERING
  // ===============================================

  static async searchAccounts(
    organizationId: string,
    searchTerm: string,
    accountType?: AccountType,
    limit: number = 50
  ): Promise<Account[]> {
    let query = getSupabaseAdmin()
      .from('accounts')
      .select('*')
      .eq('organization_id', organizationId)
      .eq('is_active', true)
      .or(`code.ilike.%${searchTerm}%,name.ilike.%${searchTerm}%`)
      .order('code', { ascending: true })
      .limit(limit)

    if (accountType) {
      query = query.eq('account_type', accountType)
    }

    const { data, error } = await query

    if (error) {
      console.error('Error searching accounts:', error)
      throw new Error('Failed to search accounts')
    }

    return data || []
  }

  static async getAccountsByType(
    organizationId: string,
    accountType: AccountType
  ): Promise<Account[]> {
    return this.getAccounts(organizationId, accountType)
  }

  static async getPostableAccounts(organizationId: string): Promise<Account[]> {
    const { data, error } = await getSupabaseAdmin()
      .from('accounts')
      .select('*')
      .eq('organization_id', organizationId)
      .eq('is_active', true)
      .eq('is_postable', true)
      .order('code', { ascending: true })

    if (error) {
      console.error('Error fetching postable accounts:', error)
      throw new Error('Failed to fetch postable accounts')
    }

    return data || []
  }

  // ===============================================
  // ACCOUNT VALIDATION
  // ===============================================

  static async validateAccountCode(
    organizationId: string,
    code: string,
    excludeId?: number
  ): Promise<boolean> {
    let query = getSupabaseAdmin()
      .from('accounts')
      .select('id')
      .eq('organization_id', organizationId)
      .eq('code', code)

    if (excludeId) {
      query = query.neq('id', excludeId)
    }

    const { data, error } = await query

    if (error) {
      console.error('Error validating account code:', error)
      throw new Error('Failed to validate account code')
    }

    return data.length === 0
  }

  static async getAccountBalance(
    accountId: number,
    asOfDate?: string
  ): Promise<number> {
    // This would typically involve calculating from journal entries
    // For now, return 0 as a placeholder
    // In a real implementation, you'd query the journal_entries and journal_entry_lines tables
    return 0
  }

  // ===============================================
  // ACCOUNT STATISTICS
  // ===============================================

  static async getAccountStats(organizationId: string): Promise<{
    total_accounts: number
    accounts_by_type: Record<AccountType, number>
    active_accounts: number
    inactive_accounts: number
    postable_accounts: number
  }> {
    const { data, error } = await getSupabaseAdmin()
      .from('accounts')
      .select('account_type, is_active, is_postable')
      .eq('organization_id', organizationId)

    if (error) {
      console.error('Error fetching account stats:', error)
      throw new Error('Failed to fetch account stats')
    }

    const rows = (data ?? []) as Pick<Account, 'account_type' | 'is_active' | 'is_postable'>[]

    const stats = {
      total_accounts: rows.length,
      accounts_by_type: {
        asset: 0,
        liability: 0,
        equity: 0,
        revenue: 0,
        expense: 0
      } as Record<AccountType, number>,
      active_accounts: 0,
      inactive_accounts: 0,
      postable_accounts: 0
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

  // ===============================================
  // CHART OF ACCOUNTS OPERATIONS
  // ===============================================

  static async getChartOfAccounts(organizationId: string): Promise<Account[]> {
    return this.getAccountHierarchy(organizationId)
  }

  static async exportChartOfAccounts(organizationId: string): Promise<Account[]> {
    const { data, error } = await getSupabaseAdmin()
      .from('accounts')
      .select('*')
      .eq('organization_id', organizationId)
      .order('code', { ascending: true })

    if (error) {
      console.error('Error exporting chart of accounts:', error)
      throw new Error('Failed to export chart of accounts')
    }

    return data || []
  }

  static async importChartOfAccounts(
    organizationId: string,
    accounts: Omit<Account, 'id' | 'organization_id' | 'created_at' | 'updated_at' | 'created_by'>[]
  ): Promise<Account[]> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')

    const accountsWithOrg = accounts.map(account => ({
      ...account,
      organization_id: organizationId,
      created_by: acting
    }))

    const { data, error } = await getSupabaseAdmin()
      .from('accounts')
      .insert(accountsWithOrg)
      .select()

    if (error) {
      console.error('Error importing chart of accounts:', error)
      throw new Error(`Failed to import chart of accounts: ${error.message}`)
    }

    return data || []
  }
}

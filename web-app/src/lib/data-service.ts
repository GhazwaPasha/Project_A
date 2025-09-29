import { createClient } from './supabase'
import { Database } from './supabase'
import { 
  User, 
  UserProfile, 
  Organization, 
  OrganizationMember, 
  Account, 
  JournalEntry, 
  JournalEntryLine,
  UserRole,
  AccountType 
} from '@/types'

const supabase = createClient()

export class DataService {
  // ================================
  // AUTHENTICATION & USER MANAGEMENT
  // ================================

  static async getCurrentUser(): Promise<User | null> {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return null

    return {
      id: user.id,
      email: user.email!,
      created_at: user.created_at,
      updated_at: user.updated_at,
      email_confirmed_at: user.email_confirmed_at,
      last_sign_in_at: user.last_sign_in_at,
    }
  }

  static async getUserProfile(userId: string): Promise<UserProfile | null> {
    const { data, error } = await supabase
      .from('user_profiles')
      .select('*')
      .eq('id', userId)
      .single()

    if (error) {
      console.error('Error fetching user profile:', error)
      return null
    }

    return data
  }

  static async createUserProfile(profile: Omit<UserProfile, 'created_at' | 'updated_at'>): Promise<UserProfile | null> {
    const { data, error } = await supabase
      .from('user_profiles')
      .insert(profile)
      .select()
      .single()

    if (error) {
      console.error('Error creating user profile:', error)
      return null
    }

    return data
  }

  // ================================
  // ORGANIZATION MANAGEMENT
  // ================================

  static async getUserOrganizations(userId: string): Promise<Organization[]> {
    const { data, error } = await supabase
      .from('organization_members')
      .select(`
        organization_id,
        role,
        organizations (
          id,
          name,
          description,
          settings,
          created_at,
          updated_at,
          is_active
        )
      `)
      .eq('user_id', userId)
      .eq('is_active', true)

    if (error) {
      console.error('Error fetching user organizations:', error)
      return []
    }

    return data.map(item => item.organizations).filter(Boolean) as Organization[]
  }

  static async getOrganization(organizationId: string): Promise<Organization | null> {
    const { data, error } = await supabase
      .from('organizations')
      .select('*')
      .eq('id', organizationId)
      .single()

    if (error) {
      console.error('Error fetching organization:', error)
      return null
    }

    return data
  }

  static async getUserRoleInOrganization(userId: string, organizationId: string): Promise<UserRole | null> {
    const { data, error } = await supabase
      .from('organization_members')
      .select('role')
      .eq('user_id', userId)
      .eq('organization_id', organizationId)
      .eq('is_active', true)
      .single()

    if (error) {
      console.error('Error fetching user role:', error)
      return null
    }

    return data.role
  }

  // ================================
  // ACCOUNTS MANAGEMENT
  // ================================

  static async getAccounts(organizationId: string, activeOnly: boolean = true): Promise<Account[]> {
    let query = supabase
      .from('accounts')
      .select('*')
      .eq('organization_id', organizationId)
      .order('code')

    if (activeOnly) {
      query = query.eq('is_active', true)
    }

    const { data, error } = await query

    if (error) {
      console.error('Error fetching accounts:', error)
      return []
    }

    return data || []
  }

  static async createAccount(account: Omit<Account, 'id' | 'created_at' | 'updated_at'>): Promise<Account | null> {
    const { data, error } = await supabase
      .from('accounts')
      .insert(account)
      .select()
      .single()

    if (error) {
      console.error('Error creating account:', error)
      return null
    }

    return data
  }

  static async updateAccount(id: number, updates: Partial<Account>): Promise<Account | null> {
    const { data, error } = await supabase
      .from('accounts')
      .update(updates)
      .eq('id', id)
      .select()
      .single()

    if (error) {
      console.error('Error updating account:', error)
      return null
    }

    return data
  }

  // ================================
  // JOURNAL ENTRIES MANAGEMENT
  // ================================

  static async getJournalEntries(organizationId: string, limit: number = 50): Promise<JournalEntry[]> {
    const { data, error } = await supabase
      .from('journal_entries')
      .select('*')
      .eq('organization_id', organizationId)
      .order('entry_date', { ascending: false })
      .limit(limit)

    if (error) {
      console.error('Error fetching journal entries:', error)
      return []
    }

    return data || []
  }

  static async getJournalEntryWithLines(entryId: number): Promise<(JournalEntry & { lines: JournalEntryLine[] }) | null> {
    const { data: entry, error: entryError } = await supabase
      .from('journal_entries')
      .select('*')
      .eq('id', entryId)
      .single()

    if (entryError) {
      console.error('Error fetching journal entry:', entryError)
      return null
    }

    const { data: lines, error: linesError } = await supabase
      .from('journal_entry_lines')
      .select('*')
      .eq('journal_entry_id', entryId)
      .order('line_order')

    if (linesError) {
      console.error('Error fetching journal entry lines:', linesError)
      return null
    }

    return {
      ...entry,
      lines: lines || []
    }
  }

  static async createJournalEntry(
    entry: Omit<JournalEntry, 'id' | 'created_at' | 'updated_at'>,
    lines: Omit<JournalEntryLine, 'id' | 'journal_entry_id'>[]
  ): Promise<JournalEntry | null> {
    const { data: newEntry, error: entryError } = await supabase
      .from('journal_entries')
      .insert(entry)
      .select()
      .single()

    if (entryError) {
      console.error('Error creating journal entry:', entryError)
      return null
    }

    // Create the journal entry lines
    const linesWithEntryId = lines.map(line => ({
      ...line,
      journal_entry_id: newEntry.id
    }))

    const { error: linesError } = await supabase
      .from('journal_entry_lines')
      .insert(linesWithEntryId)

    if (linesError) {
      console.error('Error creating journal entry lines:', linesError)
      // Rollback the journal entry
      await supabase.from('journal_entries').delete().eq('id', newEntry.id)
      return null
    }

    return newEntry
  }

  // ================================
  // FINANCIAL CALCULATIONS
  // ================================

  static async getAccountBalance(accountId: number, organizationId: string): Promise<number> {
    const { data, error } = await supabase
      .rpc('get_account_balance', {
        p_account_id: accountId,
        p_organization_id: organizationId
      })

    if (error) {
      console.error('Error calculating account balance:', error)
      return 0
    }

    return data || 0
  }

  static async getTrialBalance(organizationId: string): Promise<Array<{
    account_id: number
    account_code: string
    account_name: string
    account_type: AccountType
    debit_balance: number
    credit_balance: number
  }>> {
    const { data, error } = await supabase
      .rpc('get_trial_balance', {
        p_organization_id: organizationId
      })

    if (error) {
      console.error('Error fetching trial balance:', error)
      return []
    }

    return data || []
  }

  static async getFinancialMetrics(organizationId: string): Promise<{
    totalRevenue: number
    totalExpenses: number
    netIncome: number
    totalAssets: number
    totalLiabilities: number
    totalEquity: number
  }> {
    const { data, error } = await supabase
      .rpc('get_financial_metrics', {
        p_organization_id: organizationId
      })

    if (error) {
      console.error('Error fetching financial metrics:', error)
      return {
        totalRevenue: 0,
        totalExpenses: 0,
        netIncome: 0,
        totalAssets: 0,
        totalLiabilities: 0,
        totalEquity: 0
      }
    }

    return data || {
      totalRevenue: 0,
      totalExpenses: 0,
      netIncome: 0,
      totalAssets: 0,
      totalLiabilities: 0,
      totalEquity: 0
    }
  }
}

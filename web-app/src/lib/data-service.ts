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
  AccountType,
  InventoryCategory,
  InventoryItem,
  InventoryTransaction,
  InventoryTransactionType
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

  static async getUserOrganizations(userId: string): Promise<Organization[]> {
    const { data, error } = await supabase
      .from('organization_members')
      .select(`
        organizations:organization_id (
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

    return data?.map(item => item.organizations).filter(Boolean) || []
  }

  // ================================
  // ACCOUNTS MANAGEMENT
  // ================================

  static async getAccounts(organizationId: string, activeOnly: boolean = true): Promise<Account[]> {
    try {
      // Try with explicit .returns<Account[]>() to bypass type inference
      const query = supabase
        .from('accounts')
        .select('*')
        .eq('organization_id', organizationId)
        .order('code')
      
      const finalQuery = activeOnly ? query.eq('is_active', true) : query
      
      const { data, error } = await finalQuery

      if (error) {
        console.error('Error fetching accounts:', error)
        console.error('Full error object:', JSON.stringify(error, null, 2))
        return []
      }

      console.log('Data service - raw data from Supabase:', data?.[0])
      console.log('Data service - all fields:', data?.[0] ? Object.keys(data[0]) : 'no data')
      console.log('Data service - total records:', data?.length)

      return (data as any[]) || []
    } catch (err) {
      console.error('Exception in getAccounts:', err)
      return []
    }
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

  static async deleteAccount(id: number): Promise<boolean> {
    const { error } = await supabase
      .from('accounts')
      .delete()
      .eq('id', id)

    if (error) {
      console.error('Error deleting account:', error)
      return false
    }

    return true
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

  static async getJournalEntriesWithLines(organizationId: string, limit: number = 50): Promise<(JournalEntry & { lines: JournalEntryLine[] })[]> {
    const { data: entries, error: entriesError } = await supabase
      .from('journal_entries')
      .select(`
        *,
        journal_entry_lines (
          id,
          account_id,
          description,
          debit_amount,
          credit_amount,
          line_order
        )
      `)
      .eq('organization_id', organizationId)
      .order('entry_date', { ascending: false })
      .limit(limit)

    if (entriesError) {
      console.error('Error fetching journal entries with lines:', entriesError)
      return []
    }

    return (entries || []).map(entry => ({
      ...entry,
      lines: entry.journal_entry_lines || []
    }))
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

  static async getTrialBalance(organizationId: string, asOfDate?: string): Promise<Array<{
    account_id: number
    account_code: string
    account_name: string
    account_type: AccountType
    debit_balance: number
    credit_balance: number
  }>> {
    try {
      console.log('Getting trial balance for organization:', organizationId)
      
      // Get all active accounts
      const { data: accounts, error: accountsError } = await supabase
        .from('accounts')
        .select('*')
        .eq('organization_id', organizationId)
        .eq('is_active', true)
        .order('code')

      if (accountsError) {
        console.error('Error fetching accounts:', accountsError)
        return []
      }

      if (!accounts || accounts.length === 0) {
        console.log('No accounts found in database')
        return []
      }

      console.log('Found accounts:', accounts.length)

      // Calculate trial balance for each account
      const trialBalanceData = await Promise.all(
        accounts.map(async (account: any) => {
          // Get journal entry lines for this account
          const { data: journalLines, error: linesError } = await supabase
            .from('journal_entry_lines')
            .select(`
              debit_amount,
              credit_amount,
              journal_entries!inner(
                entry_date,
                organization_id
              )
            `)
            .eq('account_id', account.id)
            .eq('journal_entries.organization_id', organizationId)

          if (linesError) {
            console.error(`Error fetching journal lines for account ${account.id}:`, linesError)
            return null
          }

          // Calculate debit and credit totals
          let debitTotal = 0
          let creditTotal = 0

          if (journalLines) {
            for (const line of journalLines) {
              debitTotal += line.debit_amount || 0
              creditTotal += line.credit_amount || 0
            }
          }

          // Calculate net balance based on account type
          const accountType = account.account_type?.toLowerCase()
          let netBalance = 0
          
          if (accountType === 'asset' || accountType === 'expense') {
            // Assets and expenses increase with debits
            netBalance = debitTotal - creditTotal
          } else {
            // Liabilities, equity, and revenue increase with credits
            netBalance = creditTotal - debitTotal
          }

          // Only include accounts with activity or significant balances
          if (Math.abs(netBalance) >= 0.01 || debitTotal > 0 || creditTotal > 0) {
            // Determine debit and credit balances for display
            let debitBalance = 0
            let creditBalance = 0
            
            if (accountType === 'asset' || accountType === 'expense') {
              if (netBalance > 0) {
                debitBalance = netBalance
              } else if (netBalance < 0) {
                creditBalance = Math.abs(netBalance)
              }
            } else {
              if (netBalance > 0) {
                creditBalance = netBalance
              } else if (netBalance < 0) {
                debitBalance = Math.abs(netBalance)
              }
            }

            return {
              account_id: account.id,
              account_code: account.code || '',
              account_name: account.name,
              account_type: account.account_type,
              debit_balance: debitBalance,
              credit_balance: creditBalance
            }
          }

          return null
        })
      )

      // Filter out null values and return
      const result = trialBalanceData.filter(account => account !== null)
      console.log('Trial balance result:', result)
      console.log('Number of accounts with balances:', result.length)
      
      return result
    } catch (error) {
      console.error('Error calculating trial balance:', error)
      return []
    }
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
    level: number
    is_postable: boolean
    parent_id: number | null
    description: string
    group: string
  }>> {
    // Get all accounts first
    const { data: accounts, error: accountsError } = await supabase
      .from('accounts')
      .select('*')
      .eq('organization_id', organizationId)
      .eq('is_active', true)
      .order('code')
    
    if (accountsError) {
      console.error('Error fetching accounts:', accountsError)
      return []
    }

    if (!accounts || accounts.length === 0) {
      console.log('No accounts found in database')
      return []
    }

    // Calculate hierarchy levels for all accounts first
    const calculateLevel = (account: any, allAccounts: any[], visited = new Set()): number => {
      const accId = account.id
      if (visited.has(accId)) {
        return 1 // Prevent infinite loops
      }
      visited.add(accId)
      
      const parentId = account.parent_id
      if (!parentId) {
        return 1 // Root level
      }
      
      const parentAccount = allAccounts.find(acc => acc.id === parentId)
      if (!parentAccount) {
        return 1
      }
      
      return calculateLevel(parentAccount, allAccounts, visited) + 1
    }

    // Calculate is_postable for all accounts
    const calculateIsPostable = (account: any, allAccounts: any[]): boolean => {
      const accId = account.id
      // Check if this account has any children
      const hasChildren = allAccounts.some(acc => acc.parent_id === accId)
      // If it has no children, it's a leaf account and is postable
      return !hasChildren
    }

    // Get all journal entry lines for all accounts in a single query
    let journalQuery = supabase
      .from('journal_entry_lines')
      .select(`
        account_id,
        debit_amount,
        credit_amount,
        journal_entries!inner(
          entry_date,
          organization_id
        )
      `)
      .eq('journal_entries.organization_id', organizationId)

    // Apply date filtering if provided
    if (fromDate || toDate) {
      // First get journal entry IDs that match the date range
      let journalEntryQuery = supabase
        .from('journal_entries')
        .select('id')
        .eq('organization_id', organizationId)

      if (fromDate) {
        journalEntryQuery = journalEntryQuery.gte('entry_date', fromDate)
      }
      if (toDate) {
        journalEntryQuery = journalEntryQuery.lte('entry_date', toDate)
      }

      const { data: journalEntries, error: journalError } = await journalEntryQuery
      
      if (journalError) {
        console.error('Error fetching journal entries for date range:', journalError)
        return []
      }

      if (!journalEntries || journalEntries.length === 0) {
        // No journal entries in date range, return accounts with zero balances
        return accounts.map(account => ({
          id: account.id,
          code: account.code || '',
          name: account.name,
          account_type: account.account_type,
          balance: 0,
          debit_balance: 0,
          credit_balance: 0,
          transaction_count: 0,
          last_transaction_date: null,
          level: calculateLevel(account, accounts),
          is_postable: calculateIsPostable(account, accounts),
          parent_id: account.parent_id || null,
          description: account.description || '',
          group: account.group || ''
        }))
      }

      const journalIds = journalEntries.map(entry => entry.id)
      journalQuery = journalQuery.in('journal_entry_id', journalIds)
    }

    const { data: allJournalLines, error: linesError } = await journalQuery

    if (linesError) {
      console.error('Error fetching journal lines:', linesError)
      return []
    }

    // Group journal lines by account_id for efficient processing
    const accountBalances = new Map<number, {
      debitTotal: number
      creditTotal: number
      transactionCount: number
      lastTransactionDate: string | null
    }>()

    // Process all journal lines in memory
    if (allJournalLines) {
      for (const line of allJournalLines) {
        const accountId = line.account_id
        const debitAmount = line.debit_amount || 0
        const creditAmount = line.credit_amount || 0
        const entryDate = line.journal_entries?.entry_date

        if (!accountBalances.has(accountId)) {
          accountBalances.set(accountId, {
            debitTotal: 0,
            creditTotal: 0,
            transactionCount: 0,
            lastTransactionDate: null
          })
        }

        const balance = accountBalances.get(accountId)!
        balance.debitTotal += debitAmount
        balance.creditTotal += creditAmount
        balance.transactionCount++

        if (entryDate && (!balance.lastTransactionDate || entryDate > balance.lastTransactionDate)) {
          balance.lastTransactionDate = entryDate
        }
      }
    }

    // Calculate final account details
    const accountsWithDetails = accounts.map((account: any) => {
      const balance = accountBalances.get(account.id) || {
        debitTotal: 0,
        creditTotal: 0,
        transactionCount: 0,
        lastTransactionDate: null
      }

      // Calculate net balance based on account type
      const accountType = account.account_type?.toLowerCase()
      let netBalance = 0
      
      if (accountType === 'asset' || accountType === 'expense') {
        // Assets and expenses increase with debits
        netBalance = balance.debitTotal - balance.creditTotal
      } else {
        // Liabilities, equity, and revenue increase with credits
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
        level: calculateLevel(account, accounts),
        is_postable: calculateIsPostable(account, accounts),
        parent_id: account.parent_id || null,
        description: account.description || '',
        group: account.group || ''
      }
    })

    console.log('Final accounts with details:', accountsWithDetails.length)
    return accountsWithDetails
  }

  static async getAccountTransactions(
    accountId: number, 
    organizationId: string,
    fromDate?: string,
    toDate?: string
  ): Promise<Array<{
    id: number
    entry_id: number
    entry_number: string
    entry_date: string
    description: string
    reference: string | null
    debit_amount: number
    credit_amount: number
    balance: number
  }>> {
    // First, get the journal entry IDs that match our criteria
    let journalQuery = supabase
      .from('journal_entries')
      .select('id')
      .eq('organization_id', organizationId)
      .order('entry_date', { ascending: true })

    if (fromDate) {
      journalQuery = journalQuery.gte('entry_date', fromDate)
    }
    if (toDate) {
      journalQuery = journalQuery.lte('entry_date', toDate)
    }

    const { data: journalEntries, error: journalError } = await journalQuery

    if (journalError) {
      console.error('Error fetching journal entries:', journalError)
      return []
    }

    if (!journalEntries || journalEntries.length === 0) {
      return []
    }

    const journalIds = journalEntries.map(entry => entry.id)

    // Now get the journal entry lines for these entries and the specific account
    const { data, error } = await supabase
      .from('journal_entry_lines')
      .select(`
        id,
        debit_amount,
        credit_amount,
        journal_entries!inner(
          id,
          entry_number,
          entry_date,
          description,
          reference,
          organization_id
        )
      `)
      .eq('account_id', accountId)
      .in('journal_entry_id', journalIds)
      .order('journal_entries(entry_date)', { ascending: true })

    if (error) {
      console.error('Error fetching account transactions:', error)
      return []
    }

    // Calculate running balance
    let runningBalance = 0
    const transactions = (data || []).map((line: any) => {
      const entry = line.journal_entries
      runningBalance += line.debit_amount - line.credit_amount
      
      return {
        id: line.id,
        entry_id: entry.id,
        entry_number: entry.entry_number,
        entry_date: entry.entry_date,
        description: entry.description,
        reference: entry.reference,
        debit_amount: line.debit_amount,
        credit_amount: line.credit_amount,
        balance: runningBalance
      }
    })

    return transactions
  }

  static async getAccountBalance(accountId: number, organizationId: string): Promise<number> {
    const { data, error } = await supabase
      .from('journal_entry_lines')
      .select('debit_amount, credit_amount')
      .eq('account_id', accountId)
      .in('journal_entry_id', 
        supabase
          .from('journal_entries')
          .select('id')
          .eq('organization_id', organizationId)
      )

    if (error) {
      console.error('Error calculating account balance:', error)
      return 0
    }

    const balance = (data || []).reduce((sum, line) => {
      return sum + line.debit_amount - line.credit_amount
    }, 0)

    return balance
  }

  // ================================
  // INVENTORY MANAGEMENT
  // ================================

  // Inventory Categories
  static async getInventoryCategories(organizationId: string, activeOnly: boolean = false): Promise<InventoryCategory[]> {
    let query = supabase
      .from('inventory_categories')
      .select(`
        *,
        inventory_account:accounts!inventory_account_id(*),
        expense_account:accounts!expense_account_id(*)
      `)
      .eq('organization_id', organizationId)
      .order('name', { ascending: true })

    if (activeOnly) {
      query = query.eq('is_active', true)
    }

    const { data, error } = await query

    if (error) {
      console.error('Error fetching inventory categories:', error)
      return []
    }

    return data
  }

  static async getInventoryCategory(categoryId: number): Promise<InventoryCategory | null> {
    const { data, error } = await supabase
      .from('inventory_categories')
      .select(`
        *,
        inventory_account:accounts!inventory_account_id(*),
        expense_account:accounts!expense_account_id(*)
      `)
      .eq('id', categoryId)
      .single()

    if (error) {
      console.error('Error fetching inventory category:', error)
      return null
    }

    return data
  }

  static async createInventoryCategory(category: Omit<InventoryCategory, 'id' | 'created_at' | 'updated_at'>): Promise<InventoryCategory | null> {
    const { data, error } = await supabase
      .from('inventory_categories')
      .insert(category)
      .select(`
        *,
        inventory_account:accounts!inventory_account_id(*),
        expense_account:accounts!expense_account_id(*)
      `)
      .single()

    if (error) {
      console.error('Error creating inventory category:', error)
      return null
    }

    return data
  }

  static async updateInventoryCategory(categoryId: number, updates: Partial<InventoryCategory>): Promise<InventoryCategory | null> {
    const { data, error } = await supabase
      .from('inventory_categories')
      .update(updates)
      .eq('id', categoryId)
      .select(`
        *,
        inventory_account:accounts!inventory_account_id(*),
        expense_account:accounts!expense_account_id(*)
      `)
      .single()

    if (error) {
      console.error('Error updating inventory category:', error)
      return null
    }

    return data
  }

  static async deleteInventoryCategory(categoryId: number): Promise<boolean> {
    const { error } = await supabase
      .from('inventory_categories')
      .delete()
      .eq('id', categoryId)

    if (error) {
      console.error('Error deleting inventory category:', error)
      return false
    }

    return true
  }

  // Inventory Items
  static async getInventoryItems(organizationId: string, activeOnly: boolean = false): Promise<InventoryItem[]> {
    let query = supabase
      .from('inventory_items')
      .select(`
        *,
        category:inventory_categories(
          *,
          inventory_account:accounts!inventory_account_id(*),
          expense_account:accounts!expense_account_id(*)
        )
      `)
      .eq('organization_id', organizationId)
      .order('sku', { ascending: true })

    if (activeOnly) {
      query = query.eq('is_active', true)
    }

    const { data, error } = await query

    if (error) {
      console.error('Error fetching inventory items:', error)
      return []
    }

    return data
  }

  static async getInventoryItem(itemId: number): Promise<InventoryItem | null> {
    const { data, error } = await supabase
      .from('inventory_items')
      .select(`
        *,
        category:inventory_categories(
          *,
          inventory_account:accounts!inventory_account_id(*),
          expense_account:accounts!expense_account_id(*)
        )
      `)
      .eq('id', itemId)
      .single()

    if (error) {
      console.error('Error fetching inventory item:', error)
      return null
    }

    return data
  }

  static async createInventoryItem(item: Omit<InventoryItem, 'id' | 'created_at' | 'updated_at' | 'quantity_available' | 'total_value'>): Promise<InventoryItem | null> {
    const { data, error } = await supabase
      .from('inventory_items')
      .insert(item)
      .select(`
        *,
        category:inventory_categories(
          *,
          inventory_account:accounts!inventory_account_id(*),
          expense_account:accounts!expense_account_id(*)
        )
      `)
      .single()

    if (error) {
      console.error('Error creating inventory item:', error)
      return null
    }

    return data
  }

  static async updateInventoryItem(itemId: number, updates: Partial<InventoryItem>): Promise<InventoryItem | null> {
    const { data, error } = await supabase
      .from('inventory_items')
      .update(updates)
      .eq('id', itemId)
      .select(`
        *,
        category:inventory_categories(
          *,
          inventory_account:accounts!inventory_account_id(*),
          expense_account:accounts!expense_account_id(*)
        )
      `)
      .single()

    if (error) {
      console.error('Error updating inventory item:', error)
      return null
    }

    return data
  }

  static async deleteInventoryItem(itemId: number): Promise<boolean> {
    const { error } = await supabase
      .from('inventory_items')
      .delete()
      .eq('id', itemId)

    if (error) {
      console.error('Error deleting inventory item:', error)
      return false
    }

    return true
  }

  // Inventory Transactions
  static async getInventoryTransactions(organizationId: string, itemId?: number, limit?: number): Promise<InventoryTransaction[]> {
    let query = supabase
      .from('inventory_transactions')
      .select(`
        *,
        item:inventory_items(
          *,
          category:inventory_categories(*)
        )
      `)
      .eq('organization_id', organizationId)
      .order('transaction_date', { ascending: false })
      .order('created_at', { ascending: false })

    if (itemId) {
      query = query.eq('item_id', itemId)
    }

    if (limit) {
      query = query.limit(limit)
    }

    const { data, error } = await query

    if (error) {
      console.error('Error fetching inventory transactions:', error)
      return []
    }

    return data
  }

  static async createInventoryTransaction(
    transaction: Omit<InventoryTransaction, 'id' | 'created_at'>
  ): Promise<InventoryTransaction | null> {
    const { data, error } = await supabase
      .from('inventory_transactions')
      .insert(transaction)
      .select(`
        *,
        item:inventory_items(
          *,
          category:inventory_categories(*)
        )
      `)
      .single()

    if (error) {
      console.error('Error creating inventory transaction:', error)
      return null
    }

    return data
  }

  // Get low stock items
  static async getLowStockItems(organizationId: string): Promise<InventoryItem[]> {
    const { data, error } = await supabase
      .rpc('get_low_stock_items', { org_id: organizationId })

    if (error) {
      // Fallback if RPC doesn't exist yet
      const items = await this.getInventoryItems(organizationId, true)
      return items.filter(item => 
        item.reorder_point > 0 && item.quantity_available <= item.reorder_point
      )
    }

    return data || []
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

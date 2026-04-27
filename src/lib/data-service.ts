import { appDataRequest } from '@/lib/app-data-request'
import type {
  User,
  UserProfile,
  Organization,
  UserRole,
  AccountType,
  Account,
  AccountBalanceRow,
  AccountTransactionRow,
  AgedPayablesReportData,
  AgedReceivablesReportData,
  BalanceSheetReportData,
  FinancialMetricsData,
  IncomeStatementReportData,
  TrialBalanceReportData,
  JournalEntry,
  JournalEntryLine,
  InventoryCategory,
  InventoryItem,
  InventoryTransaction,
} from '@/types'

/** Browser client: calls secure `/api/app-data` (server uses service role + membership checks). */
export class DataService {
  static async getCurrentUser(): Promise<User | null> {
    if (typeof window === 'undefined') return null
    const { authClient } = await import('@/lib/auth-client')
    const { data } = await authClient.getSession()
    if (!data?.user?.id || !data.user.email) return null
    return {
      id: data.user.id,
      email: data.user.email,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      email_confirmed_at: undefined,
      last_sign_in_at: undefined,
    }
  }

  static async getUserProfile(userId: string): Promise<UserProfile | null> {
    return appDataRequest('DataService', 'getUserProfile', [userId])
  }

  static async createUserProfile(
    profile: Omit<UserProfile, 'created_at' | 'updated_at'>
  ): Promise<UserProfile | null> {
    return appDataRequest('DataService', 'createUserProfile', [profile])
  }

  static async getUserOrganizations(userId: string): Promise<Organization[]> {
    return appDataRequest('DataService', 'getUserOrganizations', [userId])
  }

  static async getOrganization(organizationId: string): Promise<Organization | null> {
    return appDataRequest('DataService', 'getOrganization', [organizationId])
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

  static async getUserRoleInOrganization(
    userId: string,
    organizationId: string
  ): Promise<UserRole | null> {
    return appDataRequest('DataService', 'getUserRoleInOrganization', [userId, organizationId])
  }

  static async updateUserPreferences(
    userId: string,
    patch: { accentColor?: string | null }
  ): Promise<UserProfile | null> {
    return appDataRequest('DataService', 'updateUserPreferences', [userId, patch])
  }

  static async getAccounts(organizationId: string, activeOnly: boolean = true): Promise<Account[]> {
    return appDataRequest('DataService', 'getAccounts', [organizationId, activeOnly])
  }

  static async createAccount(
    account: Omit<Account, 'id' | 'created_at' | 'updated_at'>
  ): Promise<Account | null> {
    return appDataRequest('DataService', 'createAccount', [account])
  }

  static async updateAccount(id: number, updates: Partial<Account>): Promise<Account | null> {
    return appDataRequest('DataService', 'updateAccount', [id, updates])
  }

  static async deleteAccount(id: number): Promise<boolean> {
    return appDataRequest('DataService', 'deleteAccount', [id])
  }

  static async getJournalEntries(organizationId: string, limit: number = 50): Promise<JournalEntry[]> {
    return appDataRequest('DataService', 'getJournalEntries', [organizationId, limit])
  }

  static async getJournalEntriesWithLines(
    organizationId: string,
    limit: number = 50
  ): Promise<(JournalEntry & { lines: JournalEntryLine[] })[]> {
    return appDataRequest('DataService', 'getJournalEntriesWithLines', [organizationId, limit])
  }

  static async getJournalEntryWithLines(
    entryId: number
  ): Promise<(JournalEntry & { lines: JournalEntryLine[] }) | null> {
    return appDataRequest('DataService', 'getJournalEntryWithLines', [entryId])
  }

  static async createJournalEntry(
    entry: Omit<JournalEntry, 'id' | 'created_at' | 'updated_at'>,
    lines: Omit<JournalEntryLine, 'id' | 'journal_entry_id'>[]
  ): Promise<JournalEntry | null> {
    return appDataRequest('DataService', 'createJournalEntry', [entry, lines])
  }

  static async getAccountBalance(accountId: number, organizationId: string): Promise<number> {
    return appDataRequest('DataService', 'getAccountBalance', [accountId, organizationId])
  }

  static async getTrialBalance(
    organizationId: string,
    asOfDate?: string
  ): Promise<
    Array<{
      account_id: number
      account_code: string
      account_name: string
      account_type: AccountType
      debit_balance: number
      credit_balance: number
    }>
  > {
    return appDataRequest('DataService', 'getTrialBalance', [organizationId, asOfDate])
  }

  static async getFinancialMetrics(
    organizationId: string,
    fromDate?: string,
    toDate?: string
  ): Promise<FinancialMetricsData> {
    return appDataRequest<FinancialMetricsData>('DataService', 'getFinancialMetrics', [
      organizationId,
      fromDate,
      toDate,
    ])
  }

  /** One `/api/app-data` call: financial metrics + account balances (server runs them in parallel). */
  static async getDashboardBundle(
    organizationId: string,
    fromDate?: string,
    toDate?: string
  ): Promise<{ financialMetrics: FinancialMetricsData; accountBalances: AccountBalanceRow[] }> {
    return appDataRequest('DataService', 'getDashboardBundle', [organizationId, fromDate, toDate])
  }

  static async getFinancialRatios(
    organizationId: string,
    fromDate?: string,
    toDate?: string
  ): Promise<{
    liquidity: { current_ratio: number; quick_ratio: number; working_capital: number }
    profitability: { gross_profit_margin: number; net_profit_margin: number; roa: number }
  }> {
    return appDataRequest('DataService', 'getFinancialRatios', [organizationId, fromDate, toDate])
  }

  static async generateBalanceSheet(organizationId: string, asOfDate?: string): Promise<BalanceSheetReportData> {
    return appDataRequest<BalanceSheetReportData>('DataService', 'generateBalanceSheet', [organizationId, asOfDate])
  }

  static async generateIncomeStatement(
    organizationId: string,
    fromDate?: string,
    toDate?: string
  ): Promise<IncomeStatementReportData> {
    return appDataRequest<IncomeStatementReportData>('DataService', 'generateIncomeStatement', [
      organizationId,
      fromDate,
      toDate,
    ])
  }

  static async generateTrialBalance(organizationId: string, asOfDate?: string): Promise<TrialBalanceReportData> {
    return appDataRequest<TrialBalanceReportData>('DataService', 'generateTrialBalance', [
      organizationId,
      asOfDate,
    ])
  }

  static async generateAgedReceivables(
    organizationId: string,
    asOfDate?: string
  ): Promise<AgedReceivablesReportData> {
    return appDataRequest<AgedReceivablesReportData>('DataService', 'generateAgedReceivables', [
      organizationId,
      asOfDate,
    ])
  }

  static async generateAgedPayables(organizationId: string, asOfDate?: string): Promise<AgedPayablesReportData> {
    return appDataRequest<AgedPayablesReportData>('DataService', 'generateAgedPayables', [organizationId, asOfDate])
  }

  static async getAccountBalances(
    organizationId: string,
    fromDate?: string,
    toDate?: string
  ): Promise<AccountBalanceRow[]> {
    return appDataRequest<AccountBalanceRow[]>('DataService', 'getAccountBalances', [
      organizationId,
      fromDate,
      toDate,
    ])
  }

  static async getAccountTransactions(
    accountId: number,
    organizationId: string,
    fromDate?: string,
    toDate?: string
  ): Promise<AccountTransactionRow[]> {
    return appDataRequest<AccountTransactionRow[]>('DataService', 'getAccountTransactions', [
      accountId,
      organizationId,
      fromDate,
      toDate,
    ])
  }

  static async getInventoryCategories(organizationId: string, activeOnly: boolean = false): Promise<InventoryCategory[]> {
    return appDataRequest<InventoryCategory[]>('DataService', 'getInventoryCategories', [organizationId, activeOnly])
  }

  static async getInventoryCategory(categoryId: number): Promise<InventoryCategory | null> {
    return appDataRequest('DataService', 'getInventoryCategory', [categoryId])
  }

  static async createInventoryCategory(
    category: Omit<InventoryCategory, 'id' | 'created_at' | 'updated_at'>
  ): Promise<InventoryCategory | null> {
    return appDataRequest('DataService', 'createInventoryCategory', [category])
  }

  static async updateInventoryCategory(
    categoryId: number,
    updates: Partial<InventoryCategory>
  ): Promise<InventoryCategory | null> {
    return appDataRequest('DataService', 'updateInventoryCategory', [categoryId, updates])
  }

  static async deleteInventoryCategory(categoryId: number): Promise<boolean> {
    return appDataRequest('DataService', 'deleteInventoryCategory', [categoryId])
  }

  static async getInventoryItems(organizationId: string, activeOnly: boolean = false): Promise<InventoryItem[]> {
    return appDataRequest<InventoryItem[]>('DataService', 'getInventoryItems', [organizationId, activeOnly])
  }

  static async getInventoryItem(itemId: number): Promise<InventoryItem | null> {
    return appDataRequest('DataService', 'getInventoryItem', [itemId])
  }

  static async createInventoryItem(
    item: Omit<InventoryItem, 'id' | 'created_at' | 'updated_at' | 'quantity_available' | 'total_value'>
  ): Promise<InventoryItem | null> {
    return appDataRequest('DataService', 'createInventoryItem', [item])
  }

  static async updateInventoryItem(
    itemId: number,
    updates: Partial<InventoryItem>
  ): Promise<InventoryItem | null> {
    return appDataRequest('DataService', 'updateInventoryItem', [itemId, updates])
  }

  static async deleteInventoryItem(itemId: number): Promise<boolean> {
    return appDataRequest('DataService', 'deleteInventoryItem', [itemId])
  }

  static async getInventoryTransactions(
    organizationId: string,
    itemId?: number,
    limit?: number
  ): Promise<InventoryTransaction[]> {
    return appDataRequest<InventoryTransaction[]>('DataService', 'getInventoryTransactions', [
      organizationId,
      itemId,
      limit,
    ])
  }

  static async createInventoryTransaction(
    transaction: Omit<InventoryTransaction, 'id' | 'created_at'>
  ): Promise<InventoryTransaction | null> {
    return appDataRequest('DataService', 'createInventoryTransaction', [transaction])
  }

  static async getLowStockItems(organizationId: string): Promise<InventoryItem[]> {
    return appDataRequest('DataService', 'getLowStockItems', [organizationId])
  }

  static async getInventoryValueByCategory(organizationId: string) {
    return appDataRequest('DataService', 'getInventoryValueByCategory', [organizationId])
  }
}

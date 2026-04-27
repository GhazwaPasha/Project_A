/**
 * Centralized query key factory for consistent cache management
 * This ensures all query keys follow the same pattern and can be easily invalidated
 */

export const queryKeys = {
  // User and authentication
  user: ['user'] as const,
  userProfile: (userId: string) => ['user-profile', userId] as const,
  userOrganizations: (userId: string) => ['user-organizations', userId] as const,
  
  // Organization data
  currentOrganization: (orgId: string) => ['current-organization', orgId] as const,
  organization: (orgId: string) => ['organization', orgId] as const,
  
  // Financial data
  financialMetrics: (orgId: string, dateRange?: { fromDate?: string; toDate?: string }) => 
    ['financial-metrics', orgId, dateRange] as const,
  
  accountBalances: (orgId: string, dateRange?: { fromDate?: string; toDate?: string }) => 
    ['account-balances', orgId, dateRange] as const,

  /** Dashboard: metrics + balances in one request */
  dashboardBundle: (orgId: string, dateRange?: { fromDate?: string; toDate?: string }) =>
    ['dashboard-bundle', orgId, dateRange] as const,
  
  accounts: (orgId: string, activeOnly?: boolean) => 
    ['accounts', orgId, { activeOnly }] as const,
  
  accountsByType: (orgId: string, accountType: string) => 
    ['accounts-by-type', orgId, accountType] as const,
  
  // Journal entries
  journalEntries: (orgId: string, limit?: number) => 
    ['journal-entries', orgId, { limit }] as const,
  
  journalEntry: (entryId: number) => 
    ['journal-entry', entryId] as const,
  
  // Reports
  balanceSheet: (orgId: string, asOfDate?: string) => 
    ['balance-sheet', orgId, { asOfDate }] as const,
  
  incomeStatement: (orgId: string, fromDate?: string, toDate?: string) => 
    ['income-statement', orgId, { fromDate, toDate }] as const,
  
  trialBalance: (orgId: string, asOfDate?: string) => 
    ['trial-balance', orgId, { asOfDate }] as const,
  
  agedReceivables: (orgId: string, asOfDate?: string) => 
    ['aged-receivables', orgId, { asOfDate }] as const,
  
  agedPayables: (orgId: string, asOfDate?: string) => 
    ['aged-payables', orgId, { asOfDate }] as const,
  
  // Inventory
  inventoryCategories: (orgId: string, activeOnly?: boolean) => 
    ['inventory-categories', orgId, { activeOnly }] as const,
  
  inventoryCategory: (categoryId: number) => 
    ['inventory-category', categoryId] as const,
  
  inventoryItems: (orgId: string, activeOnly?: boolean) => 
    ['inventory-items', orgId, { activeOnly }] as const,
  
  inventoryItem: (itemId: number) => 
    ['inventory-item', itemId] as const,
  
  inventoryTransactions: (orgId: string, itemId?: number, limit?: number) => 
    ['inventory-transactions', orgId, { itemId, limit }] as const,
  
  lowStockItems: (orgId: string) => 
    ['low-stock-items', orgId] as const,
  
  inventoryValueByCategory: (orgId: string) => 
    ['inventory-value-by-category', orgId] as const,
  
  // Vouchers
  vouchers: (orgId: string, filters?: any, limit?: number, offset?: number) => 
    ['vouchers', orgId, { filters, limit, offset }] as const,
  
  voucher: (voucherId: number) => 
    ['voucher', voucherId] as const,
  
  voucherStats: (orgId: string) => 
    ['voucher-stats', orgId] as const,
  
  voucherApprovalStats: (orgId: string) => 
    ['voucher-approval-stats', orgId] as const,
  
  // Suppliers
  suppliers: (orgId: string, filters?: any, limit?: number, offset?: number) => 
    ['suppliers', orgId, { filters, limit, offset }] as const,
  
  supplier: (supplierId: number) => 
    ['supplier', supplierId] as const,
  
  // Utility functions for query invalidation
  // These return individual 2-element prefix keys that TanStack Query can correctly
  // prefix-match against full keys like ['financial-metrics', orgId, dateRange].
  allOrganizationQueries: (orgId: string) => 
    [orgId] as const,

  financialQueryPrefixes: (orgId: string) =>
    [
      ['dashboard-bundle', orgId] as const,
      ['financial-metrics', orgId] as const,
      ['account-balances', orgId] as const,
      ['accounts', orgId] as const,
    ],

  reportQueryPrefixes: (orgId: string) =>
    [
      ['balance-sheet', orgId] as const,
      ['income-statement', orgId] as const,
      ['trial-balance', orgId] as const,
      ['aged-receivables', orgId] as const,
      ['aged-payables', orgId] as const,
    ],

  inventoryQueryPrefixes: (orgId: string) =>
    [
      ['inventory-categories', orgId] as const,
      ['inventory-items', orgId] as const,
      ['inventory-transactions', orgId] as const,
      ['low-stock-items', orgId] as const,
      ['inventory-value-by-category', orgId] as const,
    ],

  voucherQueryPrefixes: (orgId: string) =>
    [
      ['vouchers', orgId] as const,
      ['voucher-stats', orgId] as const,
      ['voucher-approval-stats', orgId] as const,
      ['pending-approvals', orgId] as const,
      ['expired-vouchers', orgId] as const,
    ],

  supplierQueryPrefixes: (orgId: string) =>
    [
      ['suppliers', orgId] as const,
    ],
}

/**
 * Helper function to create query keys with consistent structure
 */
export function createQueryKey<T extends readonly unknown[]>(...args: T): T {
  return args
}

/**
 * Helper function to check if a query key matches a pattern
 */
export function matchesQueryKey(queryKey: unknown[], pattern: string[]): boolean {
  if (queryKey.length < pattern.length) return false
  
  for (let i = 0; i < pattern.length; i++) {
    if (pattern[i] !== queryKey[i]) return false
  }
  
  return true
}

/**
 * Helper function to extract organization ID from query key
 */
export function extractOrgIdFromQueryKey(queryKey: unknown[]): string | null {
  // Most query keys have orgId as the second element
  if (queryKey.length >= 2 && typeof queryKey[1] === 'string') {
    return queryKey[1]
  }
  
  // Some query keys have orgId as the first element
  if (queryKey.length >= 1 && typeof queryKey[0] === 'string') {
    return queryKey[0]
  }
  
  return null
}

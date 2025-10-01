export interface User {
  id: string
  email: string
  created_at: string
  updated_at: string
  email_confirmed_at?: string
  last_sign_in_at?: string
}

export interface UserProfile {
  id: string
  email: string
  full_name: string | null
  avatar_url: string | null
  phone: string | null
  is_super_admin: boolean
  preferences: any
  created_at: string
  updated_at: string
  last_sign_in_at: string | null
}

export interface Organization {
  id: string
  name: string
  description: string | null
  settings: any
  created_at: string
  updated_at: string
  is_active: boolean
}

export interface OrganizationMember {
  id: string
  organization_id: string
  user_id: string
  role: UserRole
  invited_by: string | null
  invited_at: string
  joined_at: string | null
  is_active: boolean
  permissions: any
}

export interface Account {
  id: number
  organization_id: string
  code: string
  name: string
  account_type: AccountType
  parent_id: number | null
  description: string | null
  is_active: boolean
  group: string | null
  is_postable: boolean
  created_at: string
  updated_at: string
  created_by: string | null
}

export interface JournalEntry {
  id: number
  organization_id: string
  entry_number: string
  entry_date: string
  description: string
  reference: string | null
  total_amount: number
  is_posted: boolean
  created_at: string
  updated_at: string
  created_by: string | null
  posted_by: string | null
  posted_at: string | null
}

export interface JournalEntryLine {
  id: number
  journal_entry_id: number
  account_id: number
  description: string | null
  debit_amount: number
  credit_amount: number
  line_order: number
}

export interface FinancialMetric {
  label: string
  value: number
  change?: number
  changeType?: 'increase' | 'decrease' | 'neutral'
  format?: 'currency' | 'percentage' | 'number'
}

export interface DashboardData {
  totalRevenue: number
  totalExpenses: number
  netIncome: number
  cashFlow: number
  recentTransactions: JournalEntry[]
  topAccounts: Array<{
    account: Account
    balance: number
  }>
}

export interface InventoryCategory {
  id: number
  organization_id: string
  name: string
  description: string | null
  
  // Separate account mappings for IN and OUT
  inventory_account_id: number    // For IN transactions (Asset account)
  expense_account_id: number      // For OUT transactions (COGS/Expense account)
  
  // Optional hierarchy
  parent_id: number | null
  
  // Metadata
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string | null
  
  // Relations
  inventory_account?: Account
  expense_account?: Account
  parent?: InventoryCategory
  children?: InventoryCategory[]
}

export interface InventoryItem {
  id: number
  organization_id: string
  category_id: number
  
  sku: string
  name: string
  description: string | null
  unit_of_measure: string
  
  // In/Out/Available
  quantity_in: number
  quantity_out: number
  quantity_available: number
  
  // Cost tracking
  average_unit_cost: number
  total_value: number
  
  // Reorder
  reorder_point: number
  reorder_quantity: number
  
  // Metadata
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string | null
  
  // Relations
  category?: InventoryCategory
}

export interface InventoryTransaction {
  id: number
  organization_id: string
  item_id: number
  transaction_type: 'in' | 'out' | 'adjustment'
  
  quantity: number              // Positive for IN, Negative for OUT
  unit_cost: number | null
  total_cost: number | null
  
  journal_entry_id: number | null
  reference: string | null
  description: string | null
  
  transaction_date: string
  created_at: string
  created_by: string | null
  
  // Relations
  item?: InventoryItem
}

export type UserRole = 'super_admin' | 'organization_owner' | 'accountant' | 'member'
export type AccountType = 'asset' | 'liability' | 'equity' | 'revenue' | 'expense'
export type EntryType = 'debit' | 'credit'
export type InventoryTransactionType = 'in' | 'out' | 'adjustment'

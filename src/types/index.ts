export interface User {
  id: string
  email: string
  created_at: string
  updated_at: string
  email_confirmed_at?: string
  last_sign_in_at?: string
}

/** Merged in `public.user_profiles.preferences` (JSON). */
export interface UserPreferences {
  /** UI accent; `#RRGGBB`. Personal to the signed-in user. */
  accentColor?: string
  /** Persisted next-themes value for cross-device sync. */
  theme?: 'light' | 'dark' | 'system'
  [key: string]: unknown
}

export interface UserProfile {
  id: string
  email: string
  full_name: string | null
  avatar_url: string | null
  phone: string | null
  is_super_admin: boolean
  preferences: UserPreferences
  created_at: string
  updated_at: string
  last_sign_in_at: string | null
}

/** Merged in `public.organizations.settings` (JSON). */
export interface OrganizationSettings {
  [key: string]: unknown
}

export interface Organization {
  id: string
  name: string
  description: string | null
  settings: OrganizationSettings
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

export type UserRole =
  | 'super_admin'
  | 'organization_owner'
  | 'accountant'
  | 'member'
  | 'observer'
export type AccountType = 'asset' | 'liability' | 'equity' | 'revenue' | 'expense'

/** Dashboard / ledger row from `getFinancialMetrics`. */
export type FinancialMetricsData = {
  totalRevenue: number
  totalExpenses: number
  netIncome: number
  totalAssets: number
  totalLiabilities: number
  totalEquity: number
}

/** Row from `DataService.getAccountBalances` (aggregated balances per account). */
export type AccountBalanceRow = {
  id: number
  code: string
  name: string
  account_type: AccountType
  balance: number
  debit_balance: number
  credit_balance: number
  transaction_count: number
  last_transaction_date: string | null
  /** Latest journal entry `created_at` for this account (ISO string); use with `last_transaction_date` for display. */
  last_transaction_at: string | null
  level: number
  is_postable: boolean
  parent_id: number | null
  description: string
  group: string
}

/** Ledger line from `DataService.getAccountTransactions`. */
export type AccountTransactionRow = {
  id: number
  entry_id: number
  entry_number: string
  entry_date: string
  /** When the journal entry row was stored (for time of day; `entry_date` is date-only). */
  created_at: string
  description: string
  reference: string | null
  debit_amount: number
  credit_amount: number
  balance: number
}

/** Payload from `generateAgedPayables` (UI shape). */
export type AgedPayablesReportData = {
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
}

/** Payload from `generateAgedReceivables` (UI shape). */
export type AgedReceivablesReportData = {
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
}

/** Payload from `generateTrialBalance` (UI shape). */
export type TrialBalanceReportData = {
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
}

/** Payload from `generateIncomeStatement` (UI shape). */
export type IncomeStatementReportData = {
  revenue: { total: number; breakdown: Array<{ account: string; amount: number }> }
  expenses: { total: number; breakdown: Array<{ account: string; amount: number }> }
  netIncome: number
  grossProfit: number
  operatingIncome: number
  generatedAt: string
}

/** Nested account node on balance sheet reports. */
export type BalanceSheetAccountNode = {
  id: number
  code: string
  name: string
  account_type: string
  balance: number
  parent_id: number | null
  children: BalanceSheetAccountNode[]
}

export type BalanceSheetSection = {
  name: string
  group: string
  accounts: BalanceSheetAccountNode[]
  total: number
}

/** Payload from `generateBalanceSheet` (UI shape). */
export type BalanceSheetReportData = {
  isGroupBased: boolean
  assetSections: BalanceSheetSection[]
  liabilitySections: BalanceSheetSection[]
  equitySections: BalanceSheetSection[]
  totalAssets: number
  totalLiabilities: number
  totalEquity: number
  isBalanced: boolean
  generatedAt: string
}

export type EntryType = 'debit' | 'credit'
export type InventoryTransactionType = 'in' | 'out' | 'adjustment'

// ===============================================
// VOUCHER SYSTEM TYPES
// ===============================================

export type VoucherType = 'purchase' | 'issuance'
export type VoucherStatus = 'draft' | 'pending_finance' | 'approved' | 'receiving' | 'issuing' | 'posted' | 'completed' | 'rejected' | 'expired' | 'cancelled'
export type PaymentType = 'credit' | 'cash' | 'check' | 'card' | 'bank_transfer' | 'partial'

// ===============================================
// SUPPLIER SYSTEM TYPES
// ===============================================

export type SupplierStatus = 'active' | 'inactive' | 'suspended'
export type PaymentTerms = 'net_15' | 'net_30' | 'net_45' | 'net_60' | 'due_on_receipt' | 'cash_on_delivery' | 'prepaid'

export interface Supplier {
  id: number
  organization_id: string
  supplier_code: string
  name: string
  description?: string
  
  // Contact information
  contact_person?: string
  email?: string
  phone?: string
  fax?: string
  
  // Address information
  billing_address_line1?: string
  billing_address_line2?: string
  billing_city?: string
  billing_state?: string
  billing_postal_code?: string
  billing_country?: string
  
  shipping_address_line1?: string
  shipping_address_line2?: string
  shipping_city?: string
  shipping_state?: string
  shipping_postal_code?: string
  shipping_country?: string
  
  // Business information
  tax_id?: string
  registration_number?: string
  currency: string
  credit_limit?: number
  current_balance?: number
  payment_terms?: PaymentTerms
  
  // Status and metadata
  status: SupplierStatus
  is_preferred: boolean
  notes?: string
  
  // Audit fields
  created_at: string
  updated_at: string
  created_by?: string
  updated_by?: string
  
  // Relations
  account_mappings?: SupplierAccountMappings
  contacts?: SupplierContact[]
}

export interface SupplierAccountMappings {
  id: number
  supplier_id: number
  organization_id: string

  // Account mappings (see supplier_account_mappings / SupplierServiceAdmin)
  payable_account_id: number
  cash_account_id?: number
  expense_account_id?: number
  inventory_account_id?: number
  freight_account_id?: number
  tax_account_id?: number
  discount_account_id?: number

  // Metadata
  created_at: string
  updated_at: string
  created_by?: string
  updated_by?: string

  // Relations
  payable_account?: Account
  cash_account?: Account
  expense_account?: Account
  inventory_account?: Account
  freight_account?: Account
  tax_account?: Account
  discount_account?: Account
}

export interface SupplierContact {
  id: number
  supplier_id: number
  
  // Contact details
  name: string
  title?: string
  email?: string
  phone?: string
  mobile?: string
  fax?: string
  
  // Contact type flags
  is_primary: boolean
  is_billing: boolean
  is_shipping: boolean
  is_technical: boolean
  
  // Metadata
  created_at: string
  updated_at: string
  created_by?: string
}

export interface SupplierFormData {
  // Basic information
  supplier_code: string
  name: string
  legal_name?: string
  description?: string
  
  // Contact information
  contact_person?: string
  email?: string
  phone?: string
  fax?: string
  website?: string
  
  // Address information
  billing_address_line1?: string
  billing_address_line2?: string
  billing_city?: string
  billing_state?: string
  billing_postal_code?: string
  billing_country?: string
  
  shipping_address_line1?: string
  shipping_address_line2?: string
  shipping_city?: string
  shipping_state?: string
  shipping_postal_code?: string
  shipping_country?: string
  
  // Business information
  tax_id?: string
  registration_number?: string
  currency: string
  
  // Payment terms
  payment_terms: PaymentTerms
  credit_limit: number
  
  // Status and metadata
  status: SupplierStatus
  is_preferred: boolean
  notes?: string
  
  // Account mappings
  account_mappings: {
    payable_account_id: number
    cash_account_id?: number
    expense_account_id?: number
    inventory_account_id?: number
    freight_account_id?: number
    tax_account_id?: number
    discount_account_id?: number
  }
  
  // Contacts
  contacts: Array<{
    name: string
    title?: string
    email?: string
    phone?: string
    mobile?: string
    fax?: string
    is_primary: boolean
    is_billing: boolean
    is_shipping: boolean
    is_technical: boolean
  }>
}

export interface SupplierFilters {
  status?: SupplierStatus[]
  search?: string
  is_preferred?: boolean
  payment_terms?: PaymentTerms[]
}

/** Minimal supplier row for voucher supplier dropdowns (`getSuppliersForVoucher`). */
export type SupplierVoucherPicker = {
  id: number
  supplier_code: string
  name: string
  payable_account_id: number
  cash_account_id?: number
  expense_account_id?: number
}

export interface InventoryVoucher {
  id: number
  organization_id: string
  voucher_number: string
  voucher_type: VoucherType
  status: VoucherStatus
  
  // Requester/creator
  requested_by: string
  requested_date: string
  
  // Purchase-specific fields
  vendor_name?: string
  vendor_contact?: string
  purchase_order_number?: string
  expected_delivery_date?: string
  
  // Issuance-specific fields
  purpose?: string
  destination?: string
  cost_center?: string
  project_code?: string
  destination_account_id?: number
  
  // Payment details
  payment_type: PaymentType
  payment_account_id?: number
  deposit_amount: number
  payment_reference?: string
  
  // Common fields
  description?: string
  notes?: string
  total_estimated_cost: number
  total_actual_cost?: number
  
  // Expiration tracking
  submitted_at?: string
  approval_deadline?: string
  expired_at?: string
  renewed_at?: string
  renewal_count: number
  renewal_reason?: string
  
  // Approval tracking
  finance_approved_by?: string
  finance_approved_at?: string
  finance_approval_notes?: string
  
  rejected_by?: string
  rejected_at?: string
  rejection_reason?: string
  
  // Execution tracking
  executed_by?: string
  executed_at?: string
  
  // Journal entry link
  journal_entry_id?: number
  
  // Metadata
  created_at: string
  updated_at: string
  
  // Relations
  lines?: InventoryVoucherLine[]
  attachments?: VoucherAttachment[]
  requested_by_user?: UserProfile
  finance_approved_by_user?: UserProfile
  rejected_by_user?: UserProfile
  executed_by_user?: UserProfile
  destination_account?: Account
  payment_account?: Account
  journal_entry?: JournalEntry
}

export interface InventoryVoucherLine {
  id: number
  voucher_id: number
  line_number: number
  
  // Item details
  item_id: number
  
  // Quantities
  quantity_requested: number
  quantity_approved?: number
  quantity_actual?: number
  
  // Cost details
  unit_cost_estimated?: number
  unit_cost_actual?: number
  total_cost: number
  
  // Line-specific notes
  notes?: string
  
  // Metadata
  created_at: string
  
  // Relations
  item?: InventoryItem
}

export interface VoucherApproval {
  id: number
  voucher_id: number
  approver_id: string
  action: 'approved' | 'rejected' | 'requested_changes'
  comments?: string
  created_at: string
  
  // Relations
  approver?: UserProfile
}

export interface VoucherExpirationLog {
  id: number
  voucher_id: number
  status_when_expired: VoucherStatus
  expired_at: string
  approval_deadline: string
  items_count: number
  total_value: number
  renewed_at?: string
  renewed_by?: string
  renewal_reason?: string
  created_at: string
  
  // Relations
  renewed_by_user?: UserProfile
}

export interface VoucherAttachment {
  id: number
  voucher_id: number
  file_name: string
  file_path: string
  file_type?: string
  file_size?: number
  description?: string
  uploaded_by?: string
  uploaded_at: string
  
  // Relations
  uploaded_by_user?: UserProfile
}

// ===============================================
// VOUCHER FORM TYPES
// ===============================================

export interface VoucherFormData {
  voucher_type: VoucherType
  description: string
  notes?: string
  
  // Purchase fields
  vendor_name?: string
  vendor_contact?: string
  purchase_order_number?: string
  expected_delivery_date?: string
  supplier_id?: number  // New field for supplier integration
  payment_type: PaymentType
  payment_account_id?: number
  deposit_amount?: number
  payment_reference?: string
  
  // Issuance fields
  purpose?: string
  destination?: string
  cost_center?: string
  project_code?: string
  destination_account_id?: number
  
  // Line items
  lines: VoucherLineFormData[]
}

export interface VoucherLineFormData {
  item_id: number
  quantity_requested: number
  unit_cost_estimated?: number
  notes?: string
}

// ===============================================
// VOUCHER FILTER TYPES
// ===============================================

export interface VoucherFilters {
  status?: VoucherStatus[]
  voucher_type?: VoucherType[]
  requested_by?: string[]
  date_from?: string
  date_to?: string
  amount_min?: number
  amount_max?: number
  search?: string
}

// ===============================================
// VOUCHER STATISTICS TYPES
// ===============================================

export interface VoucherStats {
  total_vouchers: number
  pending_approval: number
  approved: number
  rejected: number
  expired: number
  completed: number
  total_value: number
  average_approval_time_hours: number
  approval_rate_percent: number
}

export interface VoucherApprovalStats {
  total_approved: number
  total_rejected: number
  average_time_hours: number
  total_value: number
  pending: number
  fastest_approval_minutes: number
  large_amounts_count: number
  average_large_amount: number
}
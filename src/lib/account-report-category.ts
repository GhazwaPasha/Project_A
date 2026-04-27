import type { AccountReportCategory, AccountType } from '@/types'

export type { AccountReportCategory }

export const ACCOUNT_REPORT_CATEGORIES: readonly AccountReportCategory[] = [
  'current_asset',
  'fixed_asset',
  'other_asset',
  'current_liability',
  'long_term_liability',
  'other_liability',
  'owners_equity',
  'retained_earnings',
  'other_equity',
  'operating_revenue',
  'other_revenue',
  'cost_of_sales',
  'operating_expense',
  'other_expense',
] as const

const BS_ASSET: readonly AccountReportCategory[] = ['current_asset', 'fixed_asset', 'other_asset']
const BS_LIABILITY: readonly AccountReportCategory[] = [
  'current_liability',
  'long_term_liability',
  'other_liability',
]
const BS_EQUITY: readonly AccountReportCategory[] = ['owners_equity', 'retained_earnings', 'other_equity']
const PL_REVENUE: readonly AccountReportCategory[] = ['operating_revenue', 'other_revenue']
const PL_EXPENSE: readonly AccountReportCategory[] = ['cost_of_sales', 'operating_expense', 'other_expense']

const SET_BS_ASSET = new Set<string>(BS_ASSET)
const SET_BS_LIABILITY = new Set<string>(BS_LIABILITY)
const SET_BS_EQUITY = new Set<string>(BS_EQUITY)

/** Allowed report_category values per account_type. */
export function allowedReportCategoriesForAccountType(accountType: AccountType): AccountReportCategory[] {
  switch (accountType) {
    case 'asset':
      return [...BS_ASSET]
    case 'liability':
      return [...BS_LIABILITY]
    case 'equity':
      return [...BS_EQUITY]
    case 'revenue':
      return [...PL_REVENUE]
    case 'expense':
      return [...PL_EXPENSE]
    default:
      return []
  }
}

export function reportCategoryMatchesAccountType(
  category: AccountReportCategory | null | undefined,
  accountType: AccountType
): boolean {
  if (category == null || category === undefined) return true
  return allowedReportCategoriesForAccountType(accountType).includes(category)
}

export function assertReportCategoryCompatible(accountType: AccountType, category: AccountReportCategory | null): void {
  if (category != null && !reportCategoryMatchesAccountType(category, accountType)) {
    throw new Error(
      `report_category "${category}" is not valid for account_type "${accountType}".`
    )
  }
}

/** Known legacy subsection keys stored in `group` (snake_case). */
const LEGACY_BS_KEYS = new Set([
  'current_asset',
  'fixed_asset',
  'other_asset',
  'current_liability',
  'long_term_liability',
  'other_liability',
  'owners_equity',
  'retained_earnings',
  'other_equity',
])

export function defaultBalanceSheetSubsection(accountType: AccountType): string {
  if (accountType === 'asset') return 'other_asset'
  if (accountType === 'liability') return 'other_liability'
  if (accountType === 'equity') return 'other_equity'
  return 'other'
}

/**
 * Pick balance-sheet subsection key for grouping (after filtering by account_type).
 * Prefers `report_category`, then legacy `group` when it matches known keys, else type defaults.
 */
export function resolveBalanceSheetSubsectionKey(account: {
  account_type: AccountType
  group: string | null
  report_category: AccountReportCategory | null
}): string {
  const rc = account.report_category
  if (account.account_type === 'asset' && rc && SET_BS_ASSET.has(rc)) return rc
  if (account.account_type === 'liability' && rc && SET_BS_LIABILITY.has(rc)) return rc
  if (account.account_type === 'equity' && rc && SET_BS_EQUITY.has(rc)) return rc

  const g = account.group?.trim()
  if (g && LEGACY_BS_KEYS.has(g)) {
    if (account.account_type === 'asset' && SET_BS_ASSET.has(g)) return g
    if (account.account_type === 'liability' && SET_BS_LIABILITY.has(g)) return g
    if (account.account_type === 'equity' && SET_BS_EQUITY.has(g)) return g
  }

  return defaultBalanceSheetSubsection(account.account_type)
}

/** Stable ordering for balance-sheet subsections within Assets / Liabilities / Equity. */
export function balanceSheetSubsectionSortOrder(key: string): number {
  const order: Record<string, number> = {
    current_asset: 1,
    fixed_asset: 2,
    other_asset: 3,
    current_liability: 10,
    long_term_liability: 11,
    other_liability: 12,
    owners_equity: 20,
    retained_earnings: 21,
    other_equity: 22,
    other: 99,
  }
  return order[key] ?? 50
}

/** Income statement: classify revenue rows (account_type revenue). */
export function resolveRevenueBucket(
  report_category: AccountReportCategory | null
): 'operating_revenue' | 'other_revenue' {
  if (report_category === 'other_revenue') return 'other_revenue'
  return 'operating_revenue'
}

/** Income statement: classify expense rows (account_type expense). */
export function resolveExpenseBucket(
  report_category: AccountReportCategory | null
): 'cost_of_sales' | 'operating_expense' | 'other_expense' {
  if (report_category === 'cost_of_sales') return 'cost_of_sales'
  if (report_category === 'other_expense') return 'other_expense'
  return 'operating_expense'
}

export function formatReportCategoryLabel(category: string): string {
  const nameMap: Record<string, string> = {
    current_asset: 'Current Assets',
    fixed_asset: 'Fixed Assets',
    other_asset: 'Other Assets',
    current_liability: 'Current Liabilities',
    long_term_liability: 'Long-term Liabilities',
    other_liability: 'Other Liabilities',
    owners_equity: "Owner's Equity",
    retained_earnings: 'Retained Earnings',
    other_equity: 'Other Equity',
    operating_revenue: 'Operating Revenue',
    other_revenue: 'Other Revenue',
    cost_of_sales: 'Cost of Sales',
    operating_expense: 'Operating Expenses',
    other_expense: 'Other Expenses',
  }
  return (
    nameMap[category] ||
    category.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
  )
}

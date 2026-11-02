import { QueryClient, queryOptions } from '@tanstack/react-query'
import { ApiError, call, getConnections, getMonthly, getProposals } from './api'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 30 * 60_000,
      refetchOnMount: true,
      refetchOnWindowFocus: true,
      // A permission or validation error won't change on retry, so show it right away.
      retry: (count, error) => !(error instanceof ApiError && error.status < 500) && count < 2,
    },
  },
})

/** Everything that changes when an entry is recorded. One place, so no screen shows stale numbers. */
export function refreshBooks() {
  for (const key of ['journal', 'dashboard', 'balance-sheet', 'income-statement', 'trial-balance', 'balances', 'account-txns', 'monthly']) {
    void queryClient.invalidateQueries({ queryKey: [key] })
  }
}

export type Money = number | string
export type Id = number | string
export const num = (v: Money | null | undefined) => Number(v ?? 0) || 0

export type AccountType = 'asset' | 'liability' | 'equity' | 'revenue' | 'expense'
export type AccountBalance = { id: Id; code: string; name: string; account_type: AccountType; balance: Money; transaction_count: Money; last_transaction_date: string | null; is_postable: boolean }
export type DashboardBundle = { financialMetrics: { totalRevenue: Money; totalExpenses: Money }; accountBalances: AccountBalance[] }
export type Section = { name: string; total: Money; accounts: { id: Id; code: string; name: string; balance: Money }[] }
export type BalanceSheet = { assetSections: Section[]; liabilitySections: Section[]; equitySections: Section[]; totalAssets: Money; totalLiabilities: Money; totalEquity: Money; isBalanced: boolean }
type Breakdown = { total: Money; breakdown: { account: string; amount: Money }[] }
export type IncomeStatement = { revenue: Breakdown; costOfSales: Breakdown; operatingExpenses: Breakdown; otherExpenses: Breakdown; grossProfit: Money; netIncome: Money }
export type TrialRow = { account_id: Id; account_code: string; account_name: string; account_type: string; debit_balance: Money; credit_balance: Money }
export type Line = { id: Id; account_id: Id; description: string | null; debit_amount: Money; credit_amount: Money }
export type Entry = { id: Id; entry_number: string; entry_date: string; description: string; reference: string | null; total_amount: Money; is_posted: boolean; lines: Line[] }
export type Account = { id: Id; code: string; name: string; is_postable?: boolean }
export type AccountTxn = { id: Id; entry_number: string; entry_date: string; description: string; debit_amount: Money; credit_amount: Money; balance: Money }
export type StockItem = { id: Id; sku: string; name: string; unit_of_measure: string; quantity_available: Money; average_unit_cost: Money; total_value: Money; reorder_point: Money }
export type VoucherStats = { pending_approval: Money }
export type MonthRow = { month: string; revenue: Money; expenses: Money }

const q = <T,>(key: unknown[], service: 'DataService' | 'VoucherService', method: string, args: unknown[]) =>
  queryOptions<T>({ queryKey: key, queryFn: () => call<T>(service, method, args) })

export const dashboard = (org: string, from: string, to: string) => q<DashboardBundle>(['dashboard', org, from, to], 'DataService', 'getDashboardBundle', [org, from, to])
export const balanceSheet = (org: string, asOf: string) => q<BalanceSheet>(['balance-sheet', org, asOf], 'DataService', 'generateBalanceSheet', [org, asOf])
export const incomeStatement = (org: string, from: string, to: string) => q<IncomeStatement>(['income-statement', org, from, to], 'DataService', 'generateIncomeStatement', [org, from, to])
export const trialBalance = (org: string) => q<TrialRow[]>(['trial-balance', org], 'DataService', 'getTrialBalance', [org])
export const journal = (org: string, limit = 200) => q<Entry[]>(['journal', org, limit], 'DataService', 'getJournalEntriesWithLines', [org, limit])
export const accounts = (org: string) => q<Account[]>(['accounts', org], 'DataService', 'getAccounts', [org, false])
export const balancesFor = (org: string, from?: string, to?: string) => q<AccountBalance[]>(['balances', org, from, to], 'DataService', 'getAccountBalances', [org, from, to])
export const accountTxns = (org: string, id: Id, from?: string, to?: string) => q<AccountTxn[]>(['account-txns', org, id, from, to], 'DataService', 'getAccountTransactions', [id, org, from, to])
export const lowStock = (org: string) => q<StockItem[]>(['low-stock', org], 'DataService', 'getLowStockItems', [org])
export const voucherStats = (org: string) => q<VoucherStats>(['voucher-stats', org], 'VoucherService', 'getVoucherStats', [org])
export const proposals = (org: string) => queryOptions({ queryKey: ['proposals', org], queryFn: () => getProposals(org), refetchInterval: 30_000 })
export const connections = (org: string) => queryOptions({ queryKey: ['connections', org], queryFn: () => getConnections(org) })
export const monthly = (org: string) => queryOptions<MonthRow[]>({ queryKey: ['monthly', org], queryFn: () => getMonthly(org) })

const pad = (n: number) => String(n).padStart(2, '0')
export const iso = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
export const today = () => iso(new Date())

export type Period = 'month' | 'quarter' | 'year'
export function periodRange(p: Period, now = new Date()) {
  const y = now.getFullYear()
  const m = now.getMonth()
  const start = p === 'year' ? new Date(y, 0, 1) : p === 'quarter' ? new Date(y, m - (m % 3), 1) : new Date(y, m, 1)
  return { from: iso(start), to: iso(now) }
}

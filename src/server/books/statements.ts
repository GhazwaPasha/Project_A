/**
 * The financial statements. Every figure comes from fetchReportBalances, in each account's natural direction, so
 * a contra account (sales returns, a gain booked to an expense) reduces its section instead of adding to it.
 */
import {
  balanceSheetSubsectionSortOrder,
  formatReportCategoryLabel,
  resolveBalanceSheetSubsectionKey,
  resolveExpenseBucket,
  resolveRevenueBucket,
} from '@/lib/account-report-category'
import type { AccountReportCategory } from '@/types'
import { fetchEarningsSplit, fetchReportBalances, type ReportAccount } from '@/server/data/ledger-sql'

import { roundMoney, sumMoney } from '@/lib/money'

const money = (n: number) => roundMoney(n)
const sum = (xs: number[]) => sumMoney(xs)
const today = () => new Date().toISOString().slice(0, 10)
const monthStart = (d: string) => `${d.slice(0, 7)}-01`

export type StatementAccount = { id: number | string; code: string; name: string; account_type: string; balance: number; parent_id: number | null; depth: number; is_computed?: boolean }
export type StatementSection = { name: string; group: string; accounts: StatementAccount[]; total: number }

/**
 * Accounts in tree order, each with its depth, for indenting. An account with no balance is left out unless
 * something under it has one, so headers still show above their children.
 */
function flattenTree(accounts: ReportAccount[]): StatementAccount[] {
  const ids = new Set(accounts.map((a) => a.id))
  const children = new Map<number | null, ReportAccount[]>()
  for (const a of accounts) {
    const parent = a.parent_id != null && ids.has(a.parent_id) ? a.parent_id : null
    if (!children.has(parent)) children.set(parent, [])
    children.get(parent)!.push(a)
  }
  const out: StatementAccount[] = []
  const hasAmount = (a: ReportAccount): boolean => a.balance !== 0 || (children.get(a.id) ?? []).some(hasAmount)
  const walk = (parent: number | null, depth: number) => {
    for (const a of (children.get(parent) ?? []).sort((x, y) => x.code.localeCompare(y.code))) {
      if (!hasAmount(a)) continue
      out.push({ id: a.id, code: a.code, name: a.name, account_type: a.account_type, balance: a.balance, parent_id: a.parent_id, depth })
      walk(a.id, depth + 1)
    }
  }
  walk(null, 0)
  return out
}

function sections(accounts: ReportAccount[]): StatementSection[] {
  const groups = new Map<string, ReportAccount[]>()
  for (const a of accounts) {
    const key = resolveBalanceSheetSubsectionKey({ account_type: a.account_type, group: a.group, report_category: a.report_category as AccountReportCategory | null })
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(a)
  }
  return Array.from(groups.entries())
    .sort(([a], [b]) => balanceSheetSubsectionSortOrder(a) - balanceSheetSubsectionSortOrder(b))
    .map(([group, list]) => ({ name: formatReportCategoryLabel(group), group, accounts: flattenTree(list), total: sum(list.map((a) => a.balance)) }))
    .filter((s) => s.accounts.length > 0)
}

/**
 * Assets = liabilities + equity, with profit carried into equity as it's earned: this year's so far, and every
 * earlier year's. No closing entry is needed, so the sheet balances on any date.
 */
export async function balanceSheet(org: string, asOfDate?: string) {
  const asOf = asOfDate || today()
  const [accounts, earnings] = await Promise.all([fetchReportBalances(org, asOf), fetchEarningsSplit(org, `${asOf.slice(0, 4)}-01-01`, asOf)])
  const assetSections = sections(accounts.filter((a) => a.account_type === 'asset'))
  const liabilitySections = sections(accounts.filter((a) => a.account_type === 'liability'))
  const equitySections = sections(accounts.filter((a) => a.account_type === 'equity'))

  const computed: StatementAccount[] = [
    { id: 'retained_earnings_prior', code: '', name: 'Retained earnings, prior years', account_type: 'equity', balance: earnings.prior, parent_id: null, depth: 0, is_computed: true },
    { id: 'current_year_earnings', code: '', name: 'Current year earnings', account_type: 'equity', balance: earnings.current, parent_id: null, depth: 0, is_computed: true },
  ].filter((a) => a.balance !== 0)
  if (computed.length) {
    let section = equitySections.find((s) => s.group === 'retained_earnings')
    if (!section) {
      section = { name: formatReportCategoryLabel('retained_earnings'), group: 'retained_earnings', accounts: [], total: 0 }
      equitySections.push(section)
      equitySections.sort((a, b) => balanceSheetSubsectionSortOrder(a.group) - balanceSheetSubsectionSortOrder(b.group))
    }
    section.accounts.push(...computed)
    section.total = sum([section.total, ...computed.map((a) => a.balance)])
  }

  const totalAssets = sum(assetSections.map((s) => s.total))
  const totalLiabilities = sum(liabilitySections.map((s) => s.total))
  const totalEquity = sum(equitySections.map((s) => s.total))
  return {
    isGroupBased: true,
    asOf,
    assetSections,
    liabilitySections,
    equitySections,
    totalAssets,
    totalLiabilities,
    totalEquity,
    currentYearEarnings: earnings.current,
    priorYearsEarnings: earnings.prior,
    difference: money(totalAssets - totalLiabilities - totalEquity),
    isBalanced: Math.abs(totalAssets - totalLiabilities - totalEquity) < 0.005,
    generatedAt: new Date().toISOString(),
  }
}

type Line = { account: string; account_id: number; code: string; amount: number }
const block = (accounts: ReportAccount[]) => {
  const breakdown: Line[] = accounts
    .filter((a) => a.balance !== 0)
    .map((a) => ({ account: a.name, account_id: a.id, code: a.code, amount: a.balance }))
    .sort((a, b) => b.amount - a.amount)
  return { total: sum(breakdown.map((l) => l.amount)), breakdown }
}

/**
 * Where an income or expense line sits. IFRS 18 categories (pl_category) decide finance and tax lines when set;
 * otherwise the account's report category does.
 */
export function incomeStatementBucket(a: Pick<ReportAccount, 'account_type' | 'report_category' | 'pl_category'>) {
  if (a.pl_category === 'income_tax' && a.account_type === 'expense') return 'incomeTax'
  if (a.pl_category === 'financing' || a.pl_category === 'investing') return a.account_type === 'revenue' ? 'financeIncome' : 'financeCosts'
  if (a.account_type === 'revenue') return resolveRevenueBucket(a.report_category as AccountReportCategory | null) === 'other_revenue' ? 'otherRevenue' : 'revenue'
  const e = resolveExpenseBucket(a.report_category as AccountReportCategory | null)
  return e === 'cost_of_sales' ? 'costOfSales' : e === 'other_expense' ? 'otherExpenses' : 'operatingExpenses'
}

/**
 * Revenue, less cost of sales for gross profit, less operating expenses, plus other income less other expenses for
 * operating profit; then finance income and costs, then income tax. With no dates it covers this month so far.
 */
export async function incomeStatement(org: string, fromDate?: string, toDate?: string) {
  const to = toDate || today()
  const from = fromDate || monthStart(to)
  const accounts = (await fetchReportBalances(org, { fromDate: from, toDate: to })).filter((a) => a.account_type === 'revenue' || a.account_type === 'expense')
  const pick = (bucket: string) => block(accounts.filter((a) => incomeStatementBucket(a) === bucket))
  const revenue = pick('revenue')
  const costOfSales = pick('costOfSales')
  const operatingExpenses = pick('operatingExpenses')
  const otherRevenue = pick('otherRevenue')
  const otherExpenses = pick('otherExpenses')
  const financeIncome = pick('financeIncome')
  const financeCosts = pick('financeCosts')
  const incomeTax = pick('incomeTax')
  const grossProfit = money(revenue.total - costOfSales.total)
  const operatingIncome = money(grossProfit - operatingExpenses.total + otherRevenue.total - otherExpenses.total)
  const profitBeforeTax = money(operatingIncome + financeIncome.total - financeCosts.total)
  const netIncome = money(profitBeforeTax - incomeTax.total)
  const expenseLines = [...costOfSales.breakdown, ...operatingExpenses.breakdown, ...otherExpenses.breakdown, ...financeCosts.breakdown, ...incomeTax.breakdown]
  return {
    from,
    to,
    revenue,
    costOfSales,
    operatingExpenses,
    otherRevenue,
    otherExpenses,
    financeIncome,
    financeCosts,
    incomeTax,
    expenses: { total: sum(expenseLines.map((l) => l.amount)), breakdown: expenseLines },
    grossProfit,
    operatingIncome,
    profitBeforeTax,
    netIncome,
    generatedAt: new Date().toISOString(),
  }
}

const isCurrentAsset = (a: ReportAccount) =>
  a.account_type === 'asset' && (a.report_category === 'current_asset' || ['cash', 'bank', 'receivable', 'inventory', 'input_tax'].includes(a.system_role ?? '') || a.cash_flow_category === 'cash')
const isCurrentLiability = (a: ReportAccount) =>
  a.account_type === 'liability' && (a.report_category === 'current_liability' || ['payable', 'grni', 'output_tax'].includes(a.system_role ?? ''))

/** The dashboard's headline figures: profit for the range, and position at its end, from the same numbers as the statements. */
export async function financialMetrics(org: string, fromDate?: string | null, toDate?: string | null) {
  const to = toDate || today()
  const from = fromDate || monthStart(to)
  const [range, position] = await Promise.all([fetchReportBalances(org, { fromDate: from, toDate: to }), fetchReportBalances(org, to)])
  const total = (rows: ReportAccount[], type: string) => sum(rows.filter((a) => a.account_type === type).map((a) => a.balance))
  const totalRevenue = total(range, 'revenue')
  const totalExpenses = total(range, 'expense')
  const totalAssets = total(position, 'asset')
  const totalLiabilities = total(position, 'liability')
  // Equity includes all profit to date, as on the balance sheet.
  const totalEquity = money(total(position, 'equity') + total(position, 'revenue') - total(position, 'expense'))
  const costOfSales = sum(range.filter((a) => a.account_type === 'expense' && incomeStatementBucket(a) === 'costOfSales').map((a) => a.balance))
  const currentAssets = sum(position.filter(isCurrentAsset).map((a) => a.balance))
  const inventory = sum(position.filter((a) => a.account_type === 'asset' && a.system_role === 'inventory').map((a) => a.balance))
  const currentLiabilities = sum(position.filter(isCurrentLiability).map((a) => a.balance))
  return {
    totalRevenue,
    totalExpenses,
    netIncome: money(totalRevenue - totalExpenses),
    totalAssets,
    totalLiabilities,
    totalEquity,
    costOfSales,
    currentAssets,
    currentLiabilities,
    inventory,
  }
}

/** Ratios from the same figures. A ratio with nothing to divide by is null, not zero. */
export async function financialRatios(org: string, fromDate?: string, toDate?: string) {
  const m = await financialMetrics(org, fromDate, toDate)
  const div = (a: number, b: number) => (b ? Math.round((a / b) * 10000) / 10000 : null)
  return {
    liquidity: {
      current_ratio: div(m.currentAssets, m.currentLiabilities),
      quick_ratio: div(m.currentAssets - m.inventory, m.currentLiabilities),
      working_capital: money(m.currentAssets - m.currentLiabilities),
    },
    profitability: {
      gross_profit_margin: div(m.totalRevenue - m.costOfSales, m.totalRevenue),
      net_profit_margin: div(m.netIncome, m.totalRevenue),
      roa: div(m.netIncome, m.totalAssets),
    },
  }
}

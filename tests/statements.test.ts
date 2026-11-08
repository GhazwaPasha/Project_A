import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { account, ORG, startDatabase, USER } from './helpers/db'
import { actingUserStore } from '../src/server/request-context'
import { BooksServiceAdmin as B } from '../src/server/books/service'
import { DataServiceAdmin as D } from '../src/server/data-service-admin'

/**
 * A worked example with answers done by hand:
 * capital 10,000; a bank loan 5,000; cash sales 3,000; a 500 refund to Sales returns; rent 1,000;
 * a 200 gain credited to an expense account against what's owed.
 * Revenue 2,500, expenses 800, net income 1,700. Assets 16,500 = liabilities 4,800 + equity 11,700.
 */
let db: Awaited<ReturnType<typeof startDatabase>>
const a: Record<string, number> = {}
const as = <T>(fn: () => Promise<T>) => actingUserStore.run(USER, fn)
const je = (date: string, lines: [number, number, number][]) => as(() => D.createJournalEntry(
  { organization_id: ORG, entry_number: '', entry_date: date, description: 'Example', reference: null, total_amount: 0, is_posted: true, created_by: USER, posted_by: USER, posted_at: new Date().toISOString() } as never,
  lines.map(([id, dr, cr], i) => ({ account_id: id, description: null, debit_amount: dr, credit_amount: cr, line_order: i + 1 })) as never,
))

before(async () => {
  db = await startDatabase()
  a.bank = await account('1010', 'Bank', 'asset')
  a.ap = await account('2000', 'Payable', 'liability')
  a.loan = await account('2100', 'Bank loan', 'liability')
  a.capital = await account('3000', 'Owner capital', 'equity')
  a.sales = await account('4000', 'Sales', 'revenue')
  a.returns = await account('4900', 'Sales returns', 'revenue')
  a.rent = await account('6200', 'Rent', 'expense')
  a.gain = await account('6900', 'Stock count gains', 'expense')
  await je('2025-06-01', [[a.bank, 10000, 0], [a.capital, 0, 10000]])
  await je('2026-01-05', [[a.bank, 5000, 0], [a.loan, 0, 5000]])
  await je('2026-01-10', [[a.bank, 3000, 0], [a.sales, 0, 3000]])
  await je('2026-01-11', [[a.returns, 500, 0], [a.bank, 0, 500]])
  await je('2026-01-12', [[a.rent, 1000, 0], [a.bank, 0, 1000]])
  await je('2026-01-13', [[a.ap, 200, 0], [a.gain, 0, 200]])
})
after(async () => { await db.stop() })

test('the income statement nets contra accounts instead of adding them', async () => {
  const r = await D.generateIncomeStatement(ORG, '2026-01-01', '2026-01-31')
  assert.equal(r.revenue.total, 2500)
  assert.equal(r.revenue.breakdown.find((l) => l.account === 'Sales returns')?.amount, -500)
  assert.equal(r.expenses.total, 800)
  assert.equal(r.netIncome, 1700)
})

test('the balance sheet balances, with profit carried into equity', async () => {
  const r = await D.generateBalanceSheet(ORG, '2026-01-31')
  assert.equal(r.totalAssets, 16500)
  assert.equal(r.totalLiabilities, 4800)
  assert.equal(r.totalEquity, 11700)
  assert.equal(r.currentYearEarnings, 1700)
  assert.ok(r.isBalanced)
  // A year later, January's profit has moved to prior years.
  const next = await D.generateBalanceSheet(ORG, '2027-02-01')
  assert.equal(next.priorYearsEarnings, 1700)
  assert.equal(next.currentYearEarnings, 0)
  assert.ok(next.isBalanced)
})

test('the dashboard agrees with the statements', async () => {
  const m = await D.getFinancialMetrics(ORG, '2026-01-01', '2026-01-31')
  assert.deepEqual([m.totalRevenue, m.totalExpenses, m.netIncome, m.totalAssets, m.totalLiabilities, m.totalEquity], [2500, 800, 1700, 16500, 4800, 11700])
})

test('child accounts are listed under their parent, and empty accounts are left out', async () => {
  const [parent] = await db.sql`INSERT INTO public.accounts (organization_id, code, name, account_type, is_postable) VALUES (${ORG}::uuid, '1100', 'Cash at bank', 'asset', false) RETURNING id`
  const [child] = await db.sql`INSERT INTO public.accounts (organization_id, code, name, account_type, parent_id) VALUES (${ORG}::uuid, '1101', 'Savings', 'asset', ${parent.id}) RETURNING id`
  await je('2026-01-20', [[Number(child.id), 300, 0], [a.bank, 0, 300]])
  const r = await D.generateBalanceSheet(ORG, '2026-01-31')
  const rows = r.assetSections.flatMap((s) => s.accounts)
  const at = rows.findIndex((x) => x.name === 'Cash at bank')
  assert.equal(rows[at + 1].name, 'Savings')
  assert.equal(rows[at + 1].depth, 1)
  assert.ok(r.isBalanced)
})

test('cash flow agrees with the change in cash', async () => {
  const r = await as(() => B.getCashFlow(ORG, '2026-01-01', '2026-01-31'))
  assert.ok(r.agrees)
})

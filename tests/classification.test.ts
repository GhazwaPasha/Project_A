import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { account, ORG, startDatabase, USER } from './helpers/db'
import { actingUserStore } from '../src/server/request-context'
import { BooksServiceAdmin as B } from '../src/server/books/service'
import { DataServiceAdmin as D } from '../src/server/data-service-admin'
import { AccountServiceAdmin as A } from '../src/server/account-service-admin'

let db: Awaited<ReturnType<typeof startDatabase>>
const a: Record<string, number> = {}
const as = <T>(fn: () => Promise<T>) => actingUserStore.run(USER, fn)
const je = (date: string, lines: [number, number, number][], extra: Record<string, unknown> = {}) => as(() => D.createJournalEntry(
  { organization_id: ORG, entry_number: '', entry_date: date, description: 'Test', reference: null, total_amount: 0, is_posted: true, created_by: USER, posted_by: USER, posted_at: null, ...extra } as never,
  lines.map(([id, dr, cr], i) => ({ account_id: id, description: null, debit_amount: dr, credit_amount: cr, line_order: i + 1 })) as never,
))
const role = async (id: number) => (await db.sql`SELECT system_role, is_control, cash_flow_category FROM public.accounts WHERE id = ${id}`)[0]

before(async () => {
  db = await startDatabase()
  a.bank = await account('1010', 'Current account', 'asset')
  a.ar = await account('1200', 'Trade debtors', 'asset')
  a.loan = await account('2150', 'Short-term facility', 'liability')
  a.capital = await account('3000', 'Owner capital', 'equity')
  a.sales = await account('4000', 'Sales', 'revenue')
  a.interest = await account('7000', 'Loan interest', 'expense')
  a.badDebt = await account('6800', 'Bad debts', 'expense')
})
after(async () => { await db.stop() })

test('an account takes its role when the system first uses it for one', async () => {
  await db.sql`INSERT INTO public.customers (organization_id, name, receivable_account_id) VALUES (${ORG}::uuid, 'Apex', ${a.ar})`
  assert.deepEqual({ ...(await role(a.ar)) }, { system_role: 'receivable', is_control: true, cash_flow_category: null })
})

test('a manual entry cannot post to a control account without a reason; with one it records why', async () => {
  await je('2026-01-02', [[a.bank, 1000, 0], [a.capital, 0, 1000]])
  await je('2026-01-03', [[a.ar, 400, 0], [a.sales, 0, 400]], { control_reason: 'Opening balance, Apex' })
  await assert.rejects(je('2026-01-04', [[a.badDebt, 100, 0], [a.ar, 0, 100]]), /control account/)
  const e = await je('2026-01-04', [[a.badDebt, 100, 0], [a.ar, 0, 100]], { control_reason: 'Bad debt written off' })
  assert.equal(e?.reference, 'Control account: Bad debt written off')
  assert.equal((e as unknown as { source: string }).source, 'manual_control')
  // An AI can never override.
  await assert.rejects(je('2026-01-05', [[a.badDebt, 1, 0], [a.ar, 0, 1]], { source: 'agent', control_reason: 'because' }), /control account/)
})

test('classification is checked against the account type', async () => {
  await assert.rejects(as(() => A.updateAccount(a.sales, { system_role: 'bank' } as never)), /asset accounts/)
  await assert.rejects(as(() => A.updateAccount(a.sales, { cash_flow_category: 'financing' } as never)), /balance sheet/)
  await as(() => A.updateAccount(a.bank, { system_role: 'bank' } as never))
  assert.equal((await role(a.bank)).is_control, false)
  await as(() => A.updateAccount(a.loan, { cash_flow_category: 'financing' } as never))
  await as(() => A.updateAccount(a.interest, { pl_category: 'financing' } as never))
})

test('cash flow finds cash by role, and a loan is financing even when short-term', async () => {
  await je('2026-01-10', [[a.bank, 5000, 0], [a.loan, 0, 5000]])
  await je('2026-01-20', [[a.interest, 50, 0], [a.bank, 0, 50]])
  const r = await as(() => B.getCashFlow(ORG, '2026-01-01', '2026-01-31'))
  assert.equal(r.cash_accounts_guessed, false)
  assert.deepEqual(r.cash_accounts.map((c) => c.name), ['Current account'])
  assert.equal(r.financing.net, 1000 + 5000 - 50)
  assert.ok(r.agrees)
})

test('the income statement shows interest below operating profit', async () => {
  const r = await D.generateIncomeStatement(ORG, '2026-01-01', '2026-01-31')
  assert.equal(r.financeCosts.total, 50)
  assert.equal(r.operatingIncome, 400 - 100)
  assert.equal(r.netIncome, 400 - 100 - 50)
})

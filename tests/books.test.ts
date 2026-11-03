import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { account, ORG, OTHER_ORG, startDatabase, USER } from './helpers/db'
import { actingUserStore } from '../src/server/request-context'
import { BooksServiceAdmin as B } from '../src/server/books/service'
import { DataServiceAdmin as D } from '../src/server/data-service-admin'
import { authorizeAppDataCall } from '../src/server/app-data-authorize'

type Doc = Record<string, unknown>
let db: Awaited<ReturnType<typeof startDatabase>>
const a: Record<string, number> = {}
let item = 0
const as = <T>(fn: () => Promise<T>) => actingUserStore.run(USER, fn)
const balances = async () => Object.fromEntries((await D.getAccountBalances(ORG)).map((x: { code: string; balance: number }) => [x.code, Number(x.balance)]))
const entries = async () => (await db.sql`SELECT COUNT(*)::int AS n FROM public.journal_entries`)[0].n as number
const bookBalanced = async () => {
  const tb = await D.getTrialBalance(ORG)
  const sum = (k: string) => tb.reduce((s: number, r: unknown) => s + Number((r as Record<string, number>)[k]), 0)
  assert.ok(Math.abs(sum('debit_balance') - sum('credit_balance')) < 0.005, 'books out of balance')
}
const invoice = (o = {}) => ({ kind: 'invoice' as const, party_name: 'Apex', issue_date: '2026-03-10', due_date: '2026-04-09', lines: [{ description: 'Goods', account_id: a.sales, quantity: 2, unit_price: 500 }], ...o })
const journal = (date: string, amount = 100) => D.createJournalEntry(
  { organization_id: ORG, entry_number: `T-${Date.now()}-${Math.random()}`, entry_date: date, description: 'Manual', reference: null, total_amount: amount, is_posted: true, created_by: USER, posted_by: USER, posted_at: new Date().toISOString() } as never,
  [{ account_id: a.bank, description: null, debit_amount: amount, credit_amount: 0, line_order: 1 }, { account_id: a.sales, description: null, debit_amount: 0, credit_amount: amount, line_order: 2 }] as never,
)

before(async () => {
  db = await startDatabase()
  a.bank = await account('1010', 'Bank', 'asset')
  a.ar = await account('1200', 'Receivable', 'asset')
  a.inv = await account('1300', 'Inventory', 'asset')
  a.inputTax = await account('1400', 'Input tax', 'asset')
  a.ap = await account('2000', 'Payable', 'liability')
  a.outputTax = await account('2200', 'Output tax', 'liability')
  a.sales = await account('4000', 'Sales', 'revenue')
  a.cogs = await account('5000', 'Cost of goods', 'expense')
  a.rent = await account('6200', 'Rent', 'expense')
  a.foreign = await account('9000', 'Theirs', 'asset', { org: OTHER_ORG })
  const [c] = await db.sql`INSERT INTO public.inventory_categories (organization_id, name, inventory_account_id, expense_account_id) VALUES (${ORG}::uuid, 'Packaging', ${a.inv}, ${a.cogs}) RETURNING id`
  const [i] = await db.sql`INSERT INTO public.inventory_items (organization_id, category_id, sku, name) VALUES (${ORG}::uuid, ${c.id}, 'CTN', 'Cartons') RETURNING id`
  item = Number(i.id)
})
after(async () => { await db.stop() })

test('journal entries save with number ids, as the app sends them', () => as(async () => {
  assert.ok(await journal('2026-01-05'))
  await bookBalanced()
}))

test('invoice: draft stays out of the books; posting records it; numbers run in order', () => as(async () => {
  const start = await entries()
  const { id } = await B.saveDocument(ORG, invoice())
  assert.equal(await entries(), start)
  const doc = await B.getDocument(ORG, id) as Doc
  assert.equal(doc.number, 'INV-0001'); assert.equal(doc.status, 'draft'); assert.equal(doc.total, 1000)
  const preview = await B.previewDocument(ORG, id)
  assert.ok(preview.problems.length, 'asks for the receivable account')
  assert.equal(await entries(), start)
  await assert.rejects(() => B.postDocument(ORG, id), /Choose the account/)
  assert.equal((await B.postDocument(ORG, id, { control_account_id: a.ar }) as Doc).status, 'posted')
  assert.equal(await entries(), start + 1)
  assert.equal((await balances())['1200'], 1000)
  await assert.rejects(() => B.postDocument(ORG, id, { control_account_id: a.ar }), /already been posted/)
  await assert.rejects(() => B.saveDocument(ORG, { ...invoice(), id }), /Only a draft/)
  await assert.rejects(() => B.deleteDocument(ORG, id), /Only a draft/)
  await bookBalanced()
}))

test('payments: partial, then full; never more than is owed; never on a draft', () => as(async () => {
  const { id } = await B.saveDocument(ORG, invoice({ party_name: 'Pay Co' }))
  await assert.rejects(() => B.recordPayment(ORG, id, { date: '2026-03-20', amount: 10, bank_account_id: a.bank }), /Post this/)
  await B.postDocument(ORG, id, { control_account_id: a.ar })
  await assert.rejects(() => B.recordPayment(ORG, id, { date: '2026-03-20', amount: 5000, bank_account_id: a.bank }), /more than/)
  assert.equal((await B.recordPayment(ORG, id, { date: '2026-03-20', amount: 400, bank_account_id: a.bank }) as Doc).status, 'partial')
  const paid = await B.recordPayment(ORG, id, { date: '2026-03-25', amount: 600, bank_account_id: a.bank }) as Doc
  assert.equal(paid.status, 'paid'); assert.equal(paid.balance, 0)
  await assert.rejects(() => B.recordPayment(ORG, id, { date: '2026-03-26', amount: 1, bank_account_id: a.bank }), /already fully paid/)
  await assert.rejects(() => B.voidDocument(ORG, id, { reason: 'x' }), /payments/)
  await bookBalanced()
}))

test('voiding reverses the entry and can only happen once', () => as(async () => {
  const start = (await balances())['1200']
  const { id } = await B.saveDocument(ORG, invoice({ party_name: 'Void Co' }))
  await B.postDocument(ORG, id, { control_account_id: a.ar })
  await assert.rejects(() => B.voidDocument(ORG, id, { reason: ' ' }), /Say why/)
  assert.equal((await B.voidDocument(ORG, id, { reason: 'Mistake', date: '2026-03-11' }) as Doc).status, 'void')
  assert.equal((await balances())['1200'], start)
  await assert.rejects(() => B.voidDocument(ORG, id, { reason: 'Again' }), /already void/)
  await bookBalanced()
}))

test('bills with tax: cost and input tax debited, tax summary nets against sales', () => as(async () => {
  const rate = await B.saveTaxRate(ORG, { name: 'GST', rate: 10, sales_account_id: a.outputTax, purchase_account_id: a.inputTax })
  const rateId = Number(rate.id)
  const bill = await B.saveDocument(ORG, { kind: 'bill', party_name: 'Landlord', issue_date: '2026-05-01', due_date: '2026-05-15', lines: [{ description: 'Rent', account_id: a.rent, quantity: 1, unit_price: 200, tax_rate_id: rateId }] })
  assert.equal((await B.postDocument(ORG, bill.id, { control_account_id: a.ap }) as Doc).total, 220)
  const sale = await B.saveDocument(ORG, invoice({ party_name: 'Taxed', issue_date: '2026-05-02', due_date: '2026-06-01', lines: [{ description: 'Goods', account_id: a.sales, quantity: 1, unit_price: 500, tax_rate_id: rateId }] }))
  await B.postDocument(ORG, sale.id, { control_account_id: a.ar })
  const s = await B.getTaxSummary(ORG, '2026-05-01', '2026-05-31')
  assert.deepEqual([s.output_tax, s.input_tax, s.net_tax], [50, 20, 30])
  const b = await balances()
  assert.equal(b['2200'], 50); assert.equal(b['1400'], 20)
  await B.recordTaxReturn(ORG, { from: '2026-05-01', to: '2026-05-31', reference: 'Q2' })
  await assert.rejects(() => B.recordTaxReturn(ORG, { from: '2026-05-15', to: '2026-06-30' }), /already recorded/)
  await assert.rejects(() => B.getTaxSummary(ORG, '2026-06-01', '2026-05-01'), /can't be before/)
  await bookBalanced()
}))

test('another organization cannot be reached by id', () => as(async () => {
  const { id } = await B.saveDocument(OTHER_ORG, { kind: 'invoice', party_name: 'X', issue_date: '2026-01-01', due_date: '2026-01-02', lines: [{ description: 'x', account_id: a.foreign, quantity: 1, unit_price: 1 }] })
  await assert.rejects(() => B.getDocument(ORG, id), /not found/)
  await assert.rejects(() => B.postDocument(ORG, id, { control_account_id: a.ar }), /not found/)
  await assert.rejects(() => B.saveDocument(ORG, invoice({ lines: [{ description: 'x', account_id: a.foreign, quantity: 1, unit_price: 1 }] })), /Choose an account/)
  const mine = await B.saveDocument(ORG, invoice({ party_name: 'Mine' }))
  await assert.rejects(() => B.postDocument(ORG, mine.id, { control_account_id: a.foreign }), /does not belong/)
  await B.deleteDocument(ORG, mine.id)
}))

test('aged report: payments after the as-of date still count as unpaid then', () => as(async () => {
  const { id } = await B.saveDocument(ORG, invoice({ party_name: 'Aged Co', issue_date: '2026-01-01', due_date: '2026-01-31' }))
  await B.postDocument(ORG, id, { control_account_id: a.ar })
  await B.recordPayment(ORG, id, { date: '2026-04-15', amount: 1000, bank_account_id: a.bank })
  const early = await B.getAgedReport(ORG, 'invoice', '2026-03-31')
  assert.equal(early.rows.find((r) => r.party_name === 'Aged Co')?.d31_60, 1000)
  const late = await B.getAgedReport(ORG, 'invoice', '2026-04-30')
  assert.equal(late.rows.find((r) => r.party_name === 'Aged Co'), undefined)
}))

test('reversal: opposite entry, once only, and source-linked entries are refused', () => as(async () => {
  const start = (await balances())['1010']
  const id = Number((await journal('2026-06-01', 75))?.id)
  await B.reverseEntry(ORG, id, { date: '2026-06-02', reason: 'Typo' })
  assert.equal((await balances())['1010'], start)
  await assert.rejects(() => B.reverseEntry(ORG, id), /already been reversed/)
  const [rev] = await db.sql`SELECT id FROM public.journal_entries WHERE reverses_entry_id = ${id}`
  await assert.rejects(() => B.reverseEntry(ORG, Number(rev.id)), /itself a reversal/)
  const doc = await B.saveDocument(ORG, invoice({ party_name: 'Linked' }))
  const posted = await B.postDocument(ORG, doc.id, { control_account_id: a.ar }) as Doc
  await assert.rejects(() => B.reverseEntry(ORG, Number(posted.journal_entry_id)), /came from an invoice/)
  await bookBalanced()
}))

test('stock: moves and entries happen together, and failures leave nothing behind', () => as(async () => {
  const stock = async () => (await db.sql`SELECT quantity_available::float AS q, total_value::float AS v FROM public.inventory_items WHERE id = ${item}`)[0]
  const inv = async () => (await balances())['1300'] ?? 0
  const start = await inv()
  await assert.rejects(() => B.recordStockMovement(ORG, { item_id: item, transaction_type: 'in', quantity: 10, unit_cost: 20, transaction_date: '2026-06-10' }), /came from/)
  assert.equal((await stock()).q, 0, 'a refused movement moves nothing')
  await B.recordStockMovement(ORG, { item_id: item, transaction_type: 'in', quantity: 10, unit_cost: 20, transaction_date: '2026-06-10', offset_account_id: a.ap })
  assert.equal(await inv(), start + 200)
  assert.ok((await B.recordStockMovement(ORG, { item_id: item, transaction_type: 'out', quantity: 3, transaction_date: '2026-06-11' })).entry_id)
  assert.equal(await inv(), start + 140)
  await B.recordStockMovement(ORG, { item_id: item, transaction_type: 'adjustment', quantity: -2, transaction_date: '2026-06-12' })
  assert.equal(await inv(), start + 100)
  const s = await stock()
  assert.deepEqual([s.q, s.v], [5, 100])
  await assert.rejects(() => B.recordStockMovement(ORG, { item_id: item, transaction_type: 'out', quantity: 99, transaction_date: '2026-06-12' }), /Insufficient/)
  // Recorded by someone without books access, then posted later.
  const staff = await D.createInventoryTransaction({ organization_id: ORG, item_id: item, transaction_type: 'out', quantity: -1, unit_cost: null, total_cost: null, journal_entry_id: null, reference: null, description: null, transaction_date: '2026-06-13', created_by: USER } as never)
  const waiting = await B.listUnpostedStock(ORG)
  assert.ok(waiting.some((w) => Number(w.id) === Number(staff?.id)))
  assert.equal(await inv(), start + 100, 'not in the books yet')
  await B.postStockMovement(ORG, Number(staff?.id))
  assert.equal(await inv(), start + 80)
  await assert.rejects(() => B.postStockMovement(ORG, Number(staff?.id)), /already in your books/)
  assert.equal(await inv(), start + (await stock()).v, 'stock value matches the books')
  await bookBalanced()
}))

test('bank: imports once, matches exact amounts, records fees, reconciles to zero', () => as(async () => {
  await journal('2026-07-02', 500)
  await journal('2026-07-20', 40)
  const rows = [
    { date: '2026-07-03', description: 'Deposit', amount: '500.00' },
    { date: '2026-07-05', description: 'Bank fee', amount: '(25.00)' },
    { date: '2026-07-06', description: 'Same', amount: '10' },
    { date: '2026-07-06', description: 'Same', amount: '10' },
  ]
  assert.deepEqual(await B.importStatement(ORG, a.bank, rows), { added: 4, skipped: 0 })
  assert.deepEqual(await B.importStatement(ORG, a.bank, rows), { added: 0, skipped: 4 })
  await assert.rejects(() => B.importStatement(ORG, a.bank, [{ date: 'yesterday', description: 'x', amount: '1' }]), /date/)
  let r = await B.getReconciliation(ORG, a.bank, { as_of: '2026-07-31' })
  const deposit = r.lines.find((l) => l.description === 'Deposit')
  const fee = r.lines.find((l) => l.description === 'Bank fee')
  assert.ok(deposit && fee)
  assert.equal(deposit.candidates.length, 1)
  await assert.rejects(() => B.matchStatementLine(ORG, fee.id, deposit.candidates[0].id), /amounts don't match/)
  await B.matchStatementLine(ORG, deposit.id, deposit.candidates[0].id)
  await assert.rejects(() => B.matchStatementLine(ORG, deposit.id, deposit.candidates[0].id), /already dealt with/)
  const bookBefore = r.book_balance
  await B.createEntryFromStatementLine(ORG, fee.id, { offset_account_id: a.rent })
  r = await B.getReconciliation(ORG, a.bank, { as_of: '2026-07-31' })
  assert.equal(r.book_balance, bookBefore - 25)
  for (const l of r.lines.filter((x) => x.description === 'Same')) await B.ignoreStatementLine(ORG, l.id)
  assert.equal(r.outstanding.reduce((s, l) => s + l.amount, 0), 40, 'the 40 the bank has not shown yet')
  const statement = r.book_balance - 40
  await assert.rejects(() => B.completeReconciliation(ORG, a.bank, { as_of: '2026-07-31', statement_balance: statement + 1 }), /difference/)
  await B.completeReconciliation(ORG, a.bank, { as_of: '2026-07-31', statement_balance: statement })
  await bookBalanced()
}))

test('budgets compare to actuals, income and expense only', () => as(async () => {
  await assert.rejects(() => B.saveBudget(ORG, { name: 'Bad', year: 2026, lines: [{ account_id: a.bank, month: 1, amount: 5 }] }), /income and expense/)
  const { id } = await B.saveBudget(ORG, { name: 'Plan', year: 2026, lines: [{ account_id: a.sales, month: 3, amount: 900 }, { account_id: a.rent, month: 5, amount: 150 }] })
  const r = await B.getBudgetReport(ORG, id)
  const rent = r.accounts.find((x) => x.code === '6200')
  const sales = r.accounts.find((x) => x.code === '4000')
  assert.ok(rent && sales)
  assert.equal(rent.budget[4], 150); assert.equal(rent.actual[4], 200); assert.equal(rent.variance, rent.actual_total - 150)
  assert.ok(sales.actual[2] >= 1000, 'sales are positive, in their natural direction')
  await assert.rejects(() => B.getBudgetReport(OTHER_ORG, id), /not found/)
  await B.saveBudget(ORG, { id, name: 'Plan', year: 2026, lines: [] })
  assert.equal((await B.getBudgetReport(ORG, id)).accounts.every((x) => x.budget_total === 0), true)
}))

test('forecast says how much history it rests on', () => as(async () => {
  const f = await B.getForecast(ORG, 3)
  assert.equal(f.rows.length, 3); assert.equal(f.history.length, 12)
  assert.ok(['reasonable', 'low', 'very low'].includes(f.confidence))
  assert.ok(f.rows.every((r) => r.revenue >= 0 && r.expenses >= 0))
}))

test('closing: blocks every kind of entry in the period; only later dates work; reopening needs a reason', () => as(async () => {
  assert.equal((await B.getCloseChecklist(ORG, '2026-03-31')).balanced, true)
  await assert.rejects(() => B.closeBooks(ORG, { through: '2099-12-31' }), /hasn't finished/)
  await B.closeBooks(ORG, { through: '2026-03-31', notes: 'Q1' })
  await assert.rejects(() => B.closeBooks(ORG, { through: '2026-02-28' }), /already closed/)
  const closed = /closed through 2026-03-31/
  await assert.rejects(() => journal('2026-03-31'), closed)
  assert.ok(await journal('2026-04-01'))
  const d = await B.saveDocument(ORG, invoice({ party_name: 'Late' }))
  await assert.rejects(() => B.postDocument(ORG, d.id, { control_account_id: a.ar }), closed)
  assert.equal((await B.getDocument(ORG, d.id) as Doc).status, 'draft', 'a refused post leaves the draft')
  await assert.rejects(() => B.recordStockMovement(ORG, { item_id: item, transaction_type: 'out', quantity: 1, transaction_date: '2026-03-15' }), closed)
  const e = await journal('2026-04-02')
  await assert.rejects(() => B.reverseEntry(ORG, Number(e?.id), { date: '2026-03-01' }), closed)
  await assert.rejects(() => B.reopenBooks(ORG, { reason: '' }), /Say why/)
  await B.reopenBooks(ORG, { reason: 'Found an error' })
  assert.ok(await journal('2026-03-31'))
  assert.equal((await B.getBooksLock(ORG)).closed_through, null)
}))

test('roles: each role can only do what it should', async () => {
  const roles: Record<string, string> = { accountant: '00000000-0000-4000-8000-000000000002', member: '00000000-0000-4000-8000-000000000003', observer: '00000000-0000-4000-8000-000000000004', organization_owner: '00000000-0000-4000-8000-000000000005' }
  for (const [role, id] of Object.entries(roles)) {
    await db.sql`INSERT INTO public.user_profiles (id, email, full_name) VALUES (${id}::uuid, ${`${role}@example.com`}, ${role})`
    await db.sql`INSERT INTO public.organization_members (id, organization_id, user_id, role, is_active) VALUES (gen_random_uuid(), ${ORG}::uuid, ${id}::uuid, ${role}, true)`
  }
  const can = (role: string, method: string, args: unknown[] = [ORG]) => authorizeAppDataCall('BooksService', method, args, roles[role]).then(() => true, () => false)
  assert.equal(await can('accountant', 'postDocument'), true)
  assert.equal(await can('accountant', 'closeBooks'), true)
  assert.equal(await can('accountant', 'reopenBooks'), false)
  assert.equal(await can('organization_owner', 'reopenBooks'), true)
  for (const role of ['member', 'observer']) {
    assert.equal(await can(role, 'postDocument'), false, `${role} can't post`)
    assert.equal(await can(role, 'listDocuments'), false, `${role} can't read`)
    assert.equal(await can(role, 'recordStockMovement'), false, `${role} can't post stock`)
    assert.equal(await can(role, 'reopenBooks'), false)
  }
  assert.equal(await can('accountant', 'post'), false, 'internal helpers are not callable')
  assert.equal(await can('organization_owner', 'getDocument', [OTHER_ORG]), false, 'other organizations are off limits')
})

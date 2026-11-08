import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { account, ORG, startDatabase, USER } from './helpers/db'
import { actingUserStore } from '../src/server/request-context'
import { BooksServiceAdmin as B } from '../src/server/books/service'
import { DataServiceAdmin as D } from '../src/server/data-service-admin'

let db: Awaited<ReturnType<typeof startDatabase>>
const a: Record<string, number> = {}
let invoice = 0
const as = <T>(fn: () => Promise<T>) => actingUserStore.run(USER, fn)

before(async () => {
  db = await startDatabase()
  a.bank = await account('1010', 'Bank', 'asset')
  a.ar = await account('1200', 'Receivable', 'asset')
  a.sales = await account('4000', 'Sales', 'revenue')
  a.badDebt = await account('6800', 'Bad debts', 'expense')
  const { id } = await as(() => B.saveDocument(ORG, { kind: 'invoice', party_name: 'Apex', issue_date: '2026-03-10', due_date: '2026-04-09', lines: [{ description: 'Goods', account_id: a.sales, quantity: 2, unit_price: 500 }] }))
  invoice = id
  await as(() => B.postDocument(ORG, id, { control_account_id: a.ar }))
})
after(async () => { await db.stop() })

test('posting an invoice makes its receivable account a control account', async () => {
  const [r] = await db.sql`SELECT system_role, is_control FROM public.accounts WHERE id = ${a.ar}`
  assert.deepEqual({ ...r }, { system_role: 'receivable', is_control: true })
})

test('a payment must go to a bank or cash account, dated on or after the invoice', async () => {
  await assert.rejects(as(() => B.recordPayment(ORG, invoice, { date: '2026-03-01', amount: 100, bank_account_id: a.bank })), /before the invoice/)
  await assert.rejects(as(() => B.recordPayment(ORG, invoice, { date: '2026-03-15', amount: 100, bank_account_id: a.sales })), /bank or cash/)
  await as(() => B.recordPayment(ORG, invoice, { date: '2026-03-15', amount: 400, bank_account_id: a.bank }))
})

test('receivables agree with open invoices, until something reaches the account without an invoice', async () => {
  const before = await as(() => B.getControlCheck(ORG, '2026-03-31'))
  assert.ok(before.in_step)
  assert.deepEqual(before.rows.map((r) => [r.ledger, r.subledger]), [[600, 600]])
  await as(() => D.createJournalEntry(
    { organization_id: ORG, entry_number: '', entry_date: '2026-03-20', description: 'Write-off', reference: null, total_amount: 0, is_posted: true, created_by: USER, posted_by: USER, posted_at: null, control_reason: 'Disputed, written off' } as never,
    [{ account_id: a.badDebt, description: null, debit_amount: 100, credit_amount: 0, line_order: 1 }, { account_id: a.ar, description: null, debit_amount: 0, credit_amount: 100, line_order: 2 }] as never,
  ))
  const afterWriteOff = await as(() => B.getControlCheck(ORG, '2026-03-31'))
  assert.equal(afterWriteOff.rows[0].difference, -100)
  const checklist = await as(() => B.getCloseChecklist(ORG, '2026-03-31'))
  assert.equal(checklist.control_differences, 1)
  // As of a date before the invoice, there's nothing open and nothing in the account.
  assert.ok((await as(() => B.getControlCheck(ORG, '2026-03-01'))).in_step)
})

test('open documents can be found by party and amount', async () => {
  const found = await as(() => B.findOpenDocuments(ORG, { kind: 'invoice', party: 'apex', amount: 600 }))
  assert.equal(found[0].id, invoice)
  assert.equal(found[0].balance, 600)
})

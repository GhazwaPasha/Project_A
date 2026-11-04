import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { account, ORG, OTHER_ORG, startDatabase, USER } from './helpers/db'
import { actingUserStore } from '../src/server/request-context'
import { BooksServiceAdmin as B } from '../src/server/books/service'
import { DataServiceAdmin as D } from '../src/server/data-service-admin'
import { InventoryServiceAdmin as I } from '../src/server/inventory/service'
import { authorizeAppDataCall, orgForCall } from '../src/server/app-data-authorize'
import { actionLabel, isWrite, listAuditLog, recordAudit, safeDetails } from '../src/server/audit'
import { acceptInvite, createInvite, listInvites, revokeInvite } from '../src/server/invites'
import { cashFlowSummary, cashSection, creditNoteEntry } from '../src/server/books/rules'

type Doc = Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any
let db: Awaited<ReturnType<typeof startDatabase>>
const as = <T>(fn: () => Promise<T>) => actingUserStore.run(USER, fn)
const a: Record<string, number> = {}
const DAY = '2026-03-10'
const dated = { issue_date: DAY, due_date: '2026-04-09' }
let cat = 0
let counter = 0
const INVITED = '00000000-0000-4000-8000-000000000021'
const STRANGER = '00000000-0000-4000-8000-000000000022'

const balance = async (id: number) => Number((await db.sql`SELECT COALESCE(SUM(debit_amount - credit_amount), 0)::float AS b FROM public.journal_entry_lines WHERE account_id = ${id}`)[0].b)
const item = async (o: Doc = {}) => {
  counter += 1
  const id = Number((await D.createInventoryItem({ organization_id: ORG, category_id: cat, sku: `C-${counter}`, name: `Item ${counter}`, description: null, unit_of_measure: 'Each', quantity_in: 0, quantity_out: 0, average_unit_cost: 0, reorder_point: 0, reorder_quantity: 0, is_active: true, created_by: USER, ...o } as never))!.id)
  if (o.costing_method) await I.setItemCosting(ORG, id, o.costing_method)
  return id
}
const stockIn = (id: number, q: number, cost: number, o: Doc = {}) => B.recordStockMovement(ORG, { item_id: id, transaction_type: 'in', quantity: q, unit_cost: cost, transaction_date: DAY, offset_account_id: a.ap, ...o })
const row = async (id: number) => (await db.sql`SELECT quantity_available::float AS q, total_value::float AS v FROM public.inventory_items WHERE id = ${id}`)[0] as Doc
const booksAgree = async () => { const c = await I.getBooksCheck(ORG); assert.ok(c.agrees, JSON.stringify(c.rows)) }
const invoice = async (lines: Doc[]) => {
  const { id } = await B.saveDocument(ORG, { kind: 'invoice', party_name: 'Apex', ...dated, lines: lines as never })
  return B.postDocument(ORG, id, { control_account_id: a.ar }) as Promise<Doc>
}

before(async () => {
  db = await startDatabase()
  a.bank = await account('1010', 'Bank', 'asset'); a.ar = await account('1200', 'Receivable', 'asset'); a.inv = await account('1300', 'Inventory', 'asset'); a.tax = await account('2200', 'Tax', 'liability')
  a.ap = await account('2000', 'Payable', 'liability'); a.sales = await account('4000', 'Sales', 'revenue'); a.cogs = await account('5000', 'Cost', 'expense')
  cat = Number((await db.sql`INSERT INTO public.inventory_categories (organization_id, name, inventory_account_id, expense_account_id) VALUES (${ORG}::uuid, 'Goods', ${a.inv}, ${a.cogs}) RETURNING id`)[0].id)
  for (const [id, email] of [[INVITED, 'new.person@example.com'], [STRANGER, 'someone.else@example.com']]) await db.sql`INSERT INTO public.user_profiles (id, email, full_name) VALUES (${id}::uuid, ${email}, 'x')`
})
after(async () => { await db.stop() })

// ---- Invites

test('an invite works once, for the right email, and only its hash is stored', async () => {
  const invite = await createInvite(ORG, 'New.Person@example.com', 'member', USER)
  const [stored] = await db.sql`SELECT token_hash FROM public.organization_invites WHERE id = ${invite.id}`
  assert.notEqual(stored.token_hash, invite.token)
  assert.equal((await listInvites(ORG) as Doc[]).length, 1)
  await assert.rejects(() => acceptInvite(invite.token, { id: STRANGER, email: 'someone.else@example.com' }), /This invite is for new.person/)
  await assert.rejects(() => acceptInvite('not-a-real-token-at-all-1234', { id: INVITED, email: 'new.person@example.com' }), /no longer valid/)
  const joined = await acceptInvite(invite.token, { id: INVITED, email: 'NEW.person@example.com' })
  assert.equal(joined.role, 'member')
  const [m] = await db.sql`SELECT role, is_active FROM public.organization_members WHERE organization_id = ${ORG}::uuid AND user_id = ${INVITED}::uuid`
  assert.equal(m.role, 'member')
  await assert.rejects(() => acceptInvite(invite.token, { id: INVITED, email: 'new.person@example.com' }), /already been used/)
  assert.equal((await listInvites(ORG) as Doc[]).length, 0)
})

test('invites can be replaced, revoked, and they expire', async () => {
  const first = await createInvite(ORG, 'later@example.com', 'observer', USER)
  const second = await createInvite(ORG, 'later@example.com', 'accountant', USER)
  await assert.rejects(() => acceptInvite(first.token, { id: STRANGER, email: 'later@example.com' }), /no longer valid/)
  await assert.rejects(() => revokeInvite(OTHER_ORG, second.id), /no longer open/)
  await revokeInvite(ORG, second.id)
  await assert.rejects(() => acceptInvite(second.token, { id: STRANGER, email: 'later@example.com' }), /no longer valid/)
  const old = await createInvite(ORG, 'old@example.com', 'member', USER)
  await db.sql`UPDATE public.organization_invites SET expires_at = now() - interval '1 day' WHERE id = ${old.id}`
  await assert.rejects(() => acceptInvite(old.token, { id: STRANGER, email: 'old@example.com' }), /expired/)
})

// ---- Audit log

test('audit: labels and which calls count as changes', () => {
  assert.equal(actionLabel('postDocument'), 'Post document')
  for (const m of ['getDocument', 'listWarehouses', 'previewDocument', 'findSerial', 'generateBalanceSheet']) assert.equal(isWrite(m), false, m)
  for (const m of ['postDocument', 'saveItemDetails', 'deleteBudget', 'createCreditNote', 'updateAccount']) assert.equal(isWrite(m), true, m)
})

test('audit: secrets are hidden and big imports are trimmed', () => {
  const clean = safeDetails({ password: 'p', api_key: 'k', accessToken: 't', nested: { client_secret: 's', name: 'ok' }, rows: Array.from({ length: 80 }, (_v, i) => i) }) as Doc
  assert.equal(clean.password, '[hidden]'); assert.equal(clean.api_key, '[hidden]'); assert.equal(clean.accessToken, '[hidden]'); assert.equal(clean.nested.client_secret, '[hidden]'); assert.equal(clean.nested.name, 'ok')
  assert.equal(clean.rows.length, 51)
  const huge = safeDetails({ rows: Array.from({ length: 50 }, () => 'x'.repeat(300)) }) as Doc
  assert.ok(String(huge.truncated).length <= 2000)
})

test('audit: entries are stored per organization and can’t be changed or deleted', async () => {
  await recordAudit({ org: ORG, userId: USER, action: 'Post document', targetType: 'books', targetId: 7, details: [{ total: 10, password: 'p' }] })
  await recordAudit({ org: OTHER_ORG, userId: USER, action: 'Other org', details: { a: 1 } })
  const rows = await listAuditLog(ORG) as Doc[]
  assert.equal(rows[0].action, 'Post document'); assert.equal(rows[0].target_id, '7'); assert.equal(rows[0].email, 't@example.com')
  assert.equal(rows[0].details[0].password, '[hidden]')
  assert.ok(!rows.some((r) => r.action === 'Other org'))
  await assert.rejects(() => db.sql`UPDATE public.audit_log SET action = 'x' WHERE organization_id = ${ORG}::uuid`, /cannot be changed/)
  await assert.rejects(() => db.sql`DELETE FROM public.audit_log WHERE organization_id = ${ORG}::uuid`, /cannot be changed/)
})

test('audit: a logging failure never fails the work', async () => {
  await recordAudit({ org: 'not-a-uuid', userId: USER, action: 'x' })
})

test('audit: finds the organization for calls that only name a record', async () => {
  assert.equal(await orgForCall('BooksService', 'postDocument', [ORG, 5]), ORG)
  assert.equal(await orgForCall('DataService', 'createInventoryItem', [{ organization_id: OTHER_ORG }]), OTHER_ORG)
  assert.equal(await orgForCall('DataService', 'updateAccount', [a.bank, { name: 'x' }]), ORG)
  assert.equal(await orgForCall('VoucherService', 'createVoucher', [{ description: 'x' }, ORG]), ORG)
  assert.equal(await orgForCall('DataService', 'createInventoryItem', [{ name: 'x' }]), null)
  assert.equal(await orgForCall('DataService', 'updateAccount', [987654321]), null)
  // A person's own profile belongs to no organization, even though the first argument looks like one.
  assert.equal(await orgForCall('DataService', 'updateUserProfile', [USER, { full_name: 'x' }]), null)
  // Ids repeat across tables, so the method decides which table is asked.
  const theirAccount = await account('9100', 'Theirs', 'asset', { org: OTHER_ORG })
  const mine = await item()
  await db.sql`INSERT INTO public.inventory_items (id, organization_id, category_id, sku, name) OVERRIDING SYSTEM VALUE VALUES (${theirAccount}, ${ORG}::uuid, ${cat}, 'SAME-ID', 'Same id') ON CONFLICT DO NOTHING`
  assert.equal(await orgForCall('DataService', 'deleteAccount', [theirAccount]), OTHER_ORG)
  assert.equal(await orgForCall('DataService', 'updateInventoryItem', [mine]), ORG)
})

test('audit and cash flow readers need access to the books', async () => {
  const id = '00000000-0000-4000-8000-000000000023'
  await db.sql`INSERT INTO public.user_profiles (id, email, full_name) VALUES (${id}::uuid, 'staff@example.com', 'x')`
  await db.sql`INSERT INTO public.organization_members (id, user_id, organization_id, role, is_active) VALUES (gen_random_uuid(), ${id}::uuid, ${ORG}::uuid, 'member', true)`
  for (const m of ['listAuditLog', 'getCashFlow', 'createCreditNote']) await assert.rejects(() => authorizeAppDataCall('BooksService', m, [ORG], id), /Forbidden/, m)
})

// ---- Credit notes

test('credit rule: reverses the document for both kinds and balances', () => {
  const lines = [{ account_id: 1, amount: 100, tax_amount: 10, tax_account_id: 2 }]
  for (const kind of ['invoice', 'bill'] as const) {
    const e = creditNoteEntry(kind, 3, 4, lines, 60, 50)
    assert.equal(e.reduce((s, l) => s + l.debit, 0), 110)
    assert.equal(e.reduce((s, l) => s + l.credit, 0), 110)
  }
  assert.equal(creditNoteEntry('invoice', 3, 4, lines, 110, 0).find((l) => l.account_id === 3)?.credit, 110)
  assert.equal(creditNoteEntry('bill', 3, 4, lines, 110, 0).find((l) => l.account_id === 3)?.debit, 110)
})

test('a credit note on an unpaid invoice reduces what’s owed, and stock goes back at its cost', () => as(async () => {
  const i = await item()
  await stockIn(i, 10, 10)
  const doc = await invoice([{ description: 'Goods', account_id: a.sales, quantity: 4, unit_price: 25, item_id: i }])
  const ar = await balance(a.ar), sales = await balance(a.sales), cogs = await balance(a.cogs)
  const { document } = await B.createCreditNote(ORG, doc.id, { date: DAY, reason: 'Damaged', lines: [{ line_id: doc.lines[0].id, quantity: 1 }] }) as { document: Doc }
  assert.equal(document.number, doc.number); assert.equal(document.balance, 75); assert.equal(document.status, 'partial')
  assert.equal(document.credit_notes[0].number, 'CN-0001'); assert.equal(document.lines[0].credited_quantity, 1)
  assert.equal(await balance(a.ar), ar - 25); assert.equal(await balance(a.sales), sales + 25); assert.equal(await balance(a.cogs), cogs - 10)
  assert.equal((await row(i)).q, 7); assert.equal((await row(i)).v, 70)
  await booksAgree()
  await assert.rejects(() => B.createCreditNote(ORG, doc.id, { date: DAY, reason: 'Too many', lines: [{ line_id: doc.lines[0].id, quantity: 4 }] }), /Only 3 of/)
  const rest = await B.createCreditNote(ORG, doc.id, { date: DAY, reason: 'All of it', lines: [{ line_id: doc.lines[0].id, quantity: 3 }] }) as { document: Doc }
  assert.equal(rest.document.balance, 0); assert.equal(rest.document.status, 'paid')
  assert.equal((await row(i)).q, 10); assert.equal((await row(i)).v, 100)
  await booksAgree()
}))

test('a paid invoice can be credited, with the rest refunded from the bank', () => as(async () => {
  const doc = await invoice([{ description: 'Service', account_id: a.sales, quantity: 1, unit_price: 100 }])
  await B.recordPayment(ORG, doc.id, { date: DAY, amount: 80, bank_account_id: a.bank })
  const bank = await balance(a.bank)
  const line = { line_id: doc.lines[0].id, quantity: 1 }
  await assert.rejects(() => B.createCreditNote(ORG, doc.id, { date: DAY, reason: 'Refund', lines: [line] }), /already been paid/)
  await assert.rejects(() => B.createCreditNote(ORG, doc.id, { date: DAY, reason: ' ', lines: [line], refund_account_id: a.bank }), /Say why/)
  const { document } = await B.createCreditNote(ORG, doc.id, { date: DAY, reason: 'Refund', lines: [line], refund_account_id: a.bank }) as { document: Doc }
  assert.equal(document.credit_notes[0].applied, 20); assert.equal(document.credit_notes[0].refund, 80)
  assert.equal(await balance(a.bank), bank - 80)
  assert.equal(document.balance, 0)
  const aged = await B.getAgedReport(ORG, 'invoice', '2026-12-31') as Doc
  assert.ok(!aged.documents.some((d: Doc) => d.number === doc.number))
}))

test('tax falls by the credited amount, in the credit note’s period', () => as(async () => {
  const [r] = await db.sql`INSERT INTO public.tax_rates (organization_id, name, rate, sales_account_id, purchase_account_id) VALUES (${ORG}::uuid, 'VAT', 10, ${a.tax}, ${a.tax}) RETURNING id`
  const { id } = await B.saveDocument(ORG, { kind: 'invoice', party_name: 'T', issue_date: '2026-05-10', due_date: '2026-05-20', lines: [{ description: 'x', account_id: a.sales, quantity: 3, unit_price: 100, tax_rate_id: Number(r.id) }] })
  const doc = await B.postDocument(ORG, id, { control_account_id: a.ar }) as Doc
  const tax = await balance(a.tax)
  await B.createCreditNote(ORG, id, { date: '2026-06-10', reason: 'x', lines: [{ line_id: doc.lines[0].id, quantity: 1 }] })
  assert.equal(await balance(a.tax), tax + 10)
  assert.equal((await B.getTaxSummary(ORG, '2026-05-01', '2026-05-31') as Doc).output_tax, 30)
  assert.equal((await B.getTaxSummary(ORG, '2026-06-01', '2026-06-30') as Doc).output_tax, -10)
}))

test('awkward cents: the last credit on a line takes exactly what’s left', () => as(async () => {
  const doc = await invoice([{ description: 'Thirds', account_id: a.sales, quantity: 3, unit_price: 33.33 }])
  const ar = await balance(a.ar)
  for (let n = 0; n < 3; n++) await B.createCreditNote(ORG, doc.id, { date: DAY, reason: 'x', lines: [{ line_id: doc.lines[0].id, quantity: 1 }] })
  assert.equal(await balance(a.ar), ar - 99.99)
  assert.equal((await B.getDocument(ORG, doc.id) as Doc).balance, 0)
}))

test('no restock: damaged goods stay out of stock, and their cost stays a cost', () => as(async () => {
  const i = await item()
  await stockIn(i, 5, 10)
  const doc = await invoice([{ description: 'Goods', account_id: a.sales, quantity: 2, unit_price: 25, item_id: i }])
  const cogs = await balance(a.cogs)
  await B.createCreditNote(ORG, doc.id, { date: DAY, reason: 'Broken', lines: [{ line_id: doc.lines[0].id, quantity: 2, restock: false }] })
  assert.equal((await row(i)).q, 3); assert.equal(await balance(a.cogs), cogs)
  await booksAgree()
}))

test('FIFO returns go back into their own layer, partial returns never over-restore', () => as(async () => {
  const i = await item({ costing_method: 'fifo' })
  await stockIn(i, 2, 10)
  await stockIn(i, 2, 30)
  const doc = await invoice([{ description: 'Goods', account_id: a.sales, quantity: 3, unit_price: 50, item_id: i }])
  assert.equal(doc.lines[0].cost_amount, 50)
  await B.createCreditNote(ORG, doc.id, { date: DAY, reason: 'x', lines: [{ line_id: doc.lines[0].id, quantity: 1 }] })
  let r = await row(i)
  const layers = async () => (await db.sql`SELECT SUM(quantity)::float q, SUM(value)::float v FROM public.stock_cost_layers WHERE item_id = ${i}`)[0]
  assert.equal(r.q, 2); assert.equal((await layers()).q, 2)
  await B.createCreditNote(ORG, doc.id, { date: DAY, reason: 'x', lines: [{ line_id: doc.lines[0].id, quantity: 2 }] })
  r = await row(i)
  assert.equal(r.q, 4); assert.equal(r.v, 80); assert.equal((await layers()).q, 4); assert.equal((await layers()).v, 80)
  await booksAgree()
}))

test('serial returns: a partial return must say which units, and they come back', () => as(async () => {
  const i = await item({ track_serials: true })
  await stockIn(i, 3, 10, { serial_numbers: 'R1,R2,R3' })
  const doc = await invoice([{ description: 'Units', account_id: a.sales, quantity: 2, unit_price: 25, item_id: i, serial_numbers: 'R1,R2' }])
  await assert.rejects(() => B.createCreditNote(ORG, doc.id, { date: DAY, reason: 'x', lines: [{ line_id: doc.lines[0].id, quantity: 1 }] }), /which serial numbers/)
  await B.createCreditNote(ORG, doc.id, { date: DAY, reason: 'x', lines: [{ line_id: doc.lines[0].id, quantity: 1, serial_numbers: 'R2' }] })
  const here = (await db.sql`SELECT serial_number FROM public.stock_serials WHERE item_id = ${i} AND in_stock ORDER BY serial_number`).map((s) => s.serial_number)
  assert.deepEqual(here, ['R2', 'R3'])
  await booksAgree()
}))

test('a bill credit takes the stock back out and reduces what you owe', () => as(async () => {
  const i = await item()
  const { id } = await B.saveDocument(ORG, { kind: 'bill', party_name: 'Acme', ...dated, lines: [{ description: 'Stock', quantity: 4, unit_price: 10, item_id: i }] })
  const doc = await B.postDocument(ORG, id, { control_account_id: a.ap }) as Doc
  const ap = await balance(a.ap)
  const { document } = await B.createCreditNote(ORG, id, { date: DAY, reason: 'Sent back', lines: [{ line_id: doc.lines[0].id, quantity: 1 }] }) as { document: Doc }
  assert.equal(document.credit_notes[0].number, 'DN-0001')
  assert.equal(await balance(a.ap), ap + 10)
  assert.equal((await row(i)).q, 3); assert.equal((await row(i)).v, 30)
  await booksAgree()
}))

test('credit notes respect closed periods and organizations, and drafts can’t be credited', () => as(async () => {
  const doc = await invoice([{ description: 'x', account_id: a.sales, quantity: 1, unit_price: 10 }])
  const line = { line_id: doc.lines[0].id, quantity: 1 }
  await assert.rejects(() => B.createCreditNote(OTHER_ORG, doc.id, { date: DAY, reason: 'x', lines: [line] }), /not found/)
  await db.sql`INSERT INTO public.period_closes (organization_id, through_date, closed_by) VALUES (${ORG}::uuid, '2026-01-31', ${USER}::uuid)`
  await assert.rejects(() => B.createCreditNote(ORG, doc.id, { date: '2026-01-15', reason: 'x', lines: [line] }), /closed through/)
  await db.sql`UPDATE public.period_closes SET reopened_at = now(), reopen_reason = 't' WHERE organization_id = ${ORG}::uuid`
  const { id } = await B.saveDocument(ORG, { kind: 'invoice', party_name: 'D', ...dated, lines: [{ description: 'x', account_id: a.sales, quantity: 1, unit_price: 10 }] })
  await assert.rejects(() => B.createCreditNote(ORG, id, { date: DAY, reason: 'x', lines: [{ line_id: 1, quantity: 1 }] }), /Only a posted/)
  const made = await B.createCreditNote(ORG, doc.id, { date: DAY, reason: 'x', lines: [line] }) as { document: Doc }
  const [je] = await db.sql`SELECT journal_entry_id FROM public.credit_notes WHERE document_id = ${doc.id}`
  await assert.rejects(() => B.reverseEntry(ORG, Number(je.journal_entry_id)), /came from a/)
  assert.ok(made.document)
}))

// ---- Cash flow

test('cash flow rule: sections, splitting and transfers between cash accounts', () => {
  const l = (account_id: number, is_cash: boolean, debit: number, credit: number, account_type = 'revenue', report_category: string | null = null) => ({ account_id, code: String(account_id), name: `A${account_id}`, is_cash, debit, credit, account_type, report_category })
  assert.equal(cashSection({ account_type: 'asset', report_category: 'fixed_asset' }), 'investing')
  assert.equal(cashSection({ account_type: 'liability', report_category: 'long_term_liability' }), 'financing')
  assert.equal(cashSection({ account_type: 'equity', report_category: null }), 'financing')
  assert.equal(cashSection({ account_type: 'expense', report_category: null }), 'operating')
  const s = cashFlowSummary([
    [l(1, true, 100, 0), l(2, false, 0, 100)],
    [l(1, true, 0, 30), l(3, false, 30, 0, 'expense')],
    [l(1, true, 0, 500), l(4, false, 500, 0, 'asset', 'fixed_asset')],
    [l(1, true, 1000, 0), l(5, false, 0, 1000, 'liability', 'long_term_liability')],
    [l(1, true, 50, 0), l(6, true, 0, 50, 'asset')],
    [l(1, true, 99.99, 0), l(2, false, 0, 33.33), l(7, false, 0, 66.66, 'equity')],
  ])
  assert.equal(s.operating.net, 103.33); assert.equal(s.operating.in, 133.33); assert.equal(s.operating.out, -30)
  assert.equal(s.investing.net, -500); assert.equal(s.financing.net, 1066.66)
  assert.equal(s.net, 669.99)
})

test('the cash flow report agrees with the books, and stays inside the organization', () => as(async () => {
  const from = '2027-01-01', to = '2027-01-31'
  const opening = (await B.getCashFlow(ORG, from, to) as Doc).opening
  const doc = await (async () => {
    const { id } = await B.saveDocument(ORG, { kind: 'invoice', party_name: 'Cash', issue_date: from, due_date: to, lines: [{ description: 'x', account_id: a.sales, quantity: 1, unit_price: 200 }] })
    return B.postDocument(ORG, id, { control_account_id: a.ar }) as Promise<Doc>
  })()
  await B.recordPayment(ORG, doc.id, { date: '2027-01-15', amount: 200, bank_account_id: a.bank })
  const r = await B.getCashFlow(ORG, from, to) as Doc
  assert.equal(r.operating.net, 200); assert.equal(r.closing, opening + 200); assert.equal(r.agrees, true)
  assert.deepEqual(r.cash_accounts.map((c: Doc) => c.name), ['Bank'])
  const other = await B.getCashFlow(OTHER_ORG, from, to) as Doc
  assert.equal(other.net, 0); assert.equal(other.closing, 0)
  await assert.rejects(() => B.getCashFlow(ORG, to, from), /before the start/)
}))

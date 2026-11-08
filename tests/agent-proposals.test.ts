import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { account, ORG, startDatabase, USER } from './helpers/db'
import { actingUserStore } from '../src/server/request-context'
import { BooksServiceAdmin as B } from '../src/server/books/service'
import { approveProposal, createPaymentProposal, createPostDocumentProposal, createProposal, recordDirectly } from '../src/server/agent/proposals'

let db: Awaited<ReturnType<typeof startDatabase>>
const a: Record<string, number> = {}
let invoice = 0
const as = <T>(fn: () => Promise<T>) => actingUserStore.run(USER, fn)
const why = { explanation: 'Test', confidence: 'high' as const }

before(async () => {
  db = await startDatabase()
  await db.sql`INSERT INTO public.organization_members (id, organization_id, user_id, role, is_active) VALUES (gen_random_uuid(), ${ORG}::uuid, ${USER}::uuid, 'organization_owner', true)`
  a.bank = await account('1010', 'Bank', 'asset')
  a.ar = await account('1200', 'Receivable', 'asset')
  a.capital = await account('3000', 'Owner capital', 'equity')
  a.sales = await account('4000', 'Sales', 'revenue')
  a.rent = await account('6200', 'Rent', 'expense')
  const { id } = await as(() => B.saveDocument(ORG, { kind: 'invoice', party_name: 'Apex', issue_date: '2026-03-10', due_date: '2026-04-09', lines: [{ description: 'Goods', account_id: a.sales, quantity: 2, unit_price: 500 }] }))
  invoice = id
})
after(async () => { await db.stop() })

test('posting a draft goes through the document, not a raw entry', async () => {
  const p = await createPostDocumentProposal(USER, ORG, 'app', null, { document_id: invoice, control_account_id: a.ar, ...why })
  assert.equal(p.kind, 'post_document')
  const entry = await approveProposal(USER, ORG, p.id)
  const doc = (await B.getDocument(ORG, invoice)) as { status: string; journal_entry_id: number }
  assert.equal(doc.status, 'posted')
  assert.equal(Number(doc.journal_entry_id), Number(entry.id))
})

test('a payment proposal records the payment on the invoice when approved', async () => {
  const p = await createPaymentProposal(USER, ORG, 'app', null, { document_id: invoice, date: '2026-03-20', amount: 600, bank_account_id: a.bank, ...why })
  assert.match(p.warnings[0], /400.00 will still be open/)
  // A second one that would overpay is refused while the first waits.
  await assert.rejects(createPaymentProposal(USER, ORG, 'app', null, { document_id: invoice, date: '2026-03-21', amount: 600, bank_account_id: a.bank, ...why }), /already waiting/)
  await approveProposal(USER, ORG, p.id)
  const doc = (await B.getDocument(ORG, invoice)) as { status: string; balance: number }
  assert.deepEqual([doc.status, doc.balance], ['partial', 400])
  assert.ok((await as(() => B.getControlCheck(ORG, '2026-03-31'))).in_step)
})

test('a journal proposal cannot touch a control account', async () => {
  await assert.rejects(createProposal(USER, ORG, 'app', null, { date: '2026-03-25', description: 'Cash from Apex', lines: [{ account_id: a.bank, debit: 400, credit: 0 }, { account_id: a.ar, debit: 0, credit: 400 }], ...why }), /control account/)
})

test('a duplicate is refused unless the person confirms it is separate, and unusual lines carry a warning', async () => {
  const lines = [{ account_id: a.rent, debit: 900, credit: 0 }, { account_id: a.bank, debit: 0, credit: 900 }]
  const first = await createProposal(USER, ORG, 'app', null, { date: '2026-03-01', description: 'Rent', lines, ...why })
  await assert.rejects(createProposal(USER, ORG, 'app', null, { date: '2026-03-03', description: 'Rent', lines, ...why }), /already waiting/)
  const entry = await approveProposal(USER, ORG, first.id)
  assert.match(entry.entry_number, /^JNL-/)
  const [row] = await db.sql`SELECT source, source_id FROM public.journal_entries WHERE id = ${entry.id}`
  assert.deepEqual({ ...row }, { source: 'agent', source_id: first.id })
  await assert.rejects(createProposal(USER, ORG, 'app', null, { date: '2026-03-04', description: 'Rent', lines, ...why }), /looks the same as JNL-/)
  await createProposal(USER, ORG, 'app', null, { date: '2026-03-04', description: 'Rent, second unit', lines, not_a_duplicate: true, ...why })
  const odd = await createProposal(USER, ORG, 'app', null, { date: '2026-03-05', description: 'Odd', lines: [{ account_id: a.sales, debit: 50, credit: 0 }, { account_id: a.bank, debit: 0, credit: 50 }], ...why })
  assert.match(odd.warnings[0], /income account/)
})

test('a direct MCP recording is traced like any AI entry', async () => {
  const entry = await recordDirectly(USER, ORG, { date: '2026-03-06', description: 'Owner put money in', lines: [{ account_id: a.bank, debit: 2000, credit: 0 }, { account_id: a.capital, debit: 0, credit: 2000 }], ...why }, 'Claude')
  const [p] = await db.sql`SELECT status, source, source_name FROM public.agent_proposals WHERE journal_entry_id = ${entry.id}`
  assert.deepEqual({ ...p }, { status: 'recorded', source: 'mcp', source_name: 'Claude' })
})

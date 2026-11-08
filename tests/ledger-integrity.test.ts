import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { account, ORG, startDatabase, USER } from './helpers/db'
import { actingUserStore } from '../src/server/request-context'
import { DataServiceAdmin as D } from '../src/server/data-service-admin'
import { AccountServiceAdmin as A } from '../src/server/account-service-admin'

let db: Awaited<ReturnType<typeof startDatabase>>
const a: Record<string, number> = {}
const as = <T>(fn: () => Promise<T>) => actingUserStore.run(USER, fn)
const je = (lines: [number, number, number][], extra: Record<string, unknown> = {}) => as(() => D.createJournalEntry(
  { organization_id: ORG, entry_number: 'JE-1700000000000', entry_date: '2026-02-01', description: 'Test', reference: null, total_amount: 0, is_posted: false, created_by: USER, posted_by: null, posted_at: null, ...extra } as never,
  lines.map(([id, dr, cr], i) => ({ account_id: id, description: null, debit_amount: dr, credit_amount: cr, line_order: i + 1 })) as never,
))

before(async () => {
  db = await startDatabase()
  a.bank = await account('1010', 'Bank', 'asset')
  a.sales = await account('4000', 'Sales', 'revenue')
  a.rent = await account('6200', 'Rent', 'expense')
})
after(async () => { await db.stop() })

test('the server numbers manual entries in order and posts them, whatever the caller sent', async () => {
  const first = await je([[a.bank, 100, 0], [a.sales, 0, 100]])
  const second = await je([[a.bank, 50, 0], [a.sales, 0, 50]])
  assert.equal(first?.entry_number, 'JNL-0001')
  assert.equal(second?.entry_number, 'JNL-0002')
  assert.equal(first?.is_posted, true)
  assert.equal((first as unknown as { source: string }).source, 'manual')
})

test('negative amounts are refused, in code and in the database', async () => {
  await assert.rejects(je([[a.bank, -50, 0], [a.rent, 0, -50]]), /negative/)
  const [e] = await db.sql`SELECT id FROM public.journal_entries LIMIT 1`
  await assert.rejects(db.sql`INSERT INTO public.journal_entry_lines (journal_entry_id, account_id, debit_amount, credit_amount) VALUES (${e.id}, ${a.bank}, -5, 0)`)
})

test('the database refuses an entry that does not balance', async () => {
  await assert.rejects(db.sql.begin(async (tx) => {
    const [e] = await tx`INSERT INTO public.journal_entries (organization_id, entry_number, entry_date) VALUES (${ORG}::uuid, 'X-1', '2026-02-02') RETURNING id`
    await tx`INSERT INTO public.journal_entry_lines (journal_entry_id, account_id, debit_amount) VALUES (${e.id}, ${a.bank}, 100)`
    await tx`INSERT INTO public.journal_entry_lines (journal_entry_id, account_id, credit_amount) VALUES (${e.id}, ${a.sales}, 90)`
  }), /does not balance/)
})

test('posted entries cannot be edited or deleted', async () => {
  const [e] = await db.sql`SELECT id FROM public.journal_entries WHERE entry_number = 'JNL-0001'`
  await assert.rejects(db.sql`UPDATE public.journal_entries SET entry_date = '2026-03-01' WHERE id = ${e.id}`, /cannot be changed/)
  await assert.rejects(db.sql`UPDATE public.journal_entry_lines SET debit_amount = 1 WHERE journal_entry_id = ${e.id}`, /cannot be changed/)
  await assert.rejects(db.sql`DELETE FROM public.journal_entries WHERE id = ${e.id}`, /cannot be deleted/)
})

test('an account with entries cannot change type, and one with a balance cannot be made inactive', async () => {
  await assert.rejects(as(() => D.updateAccount(a.sales, { account_type: 'expense' } as never)), /type can't change/)
  await assert.rejects(as(() => A.updateAccount(a.bank, { is_active: false } as never)), /still has a balance/)
  const spare = await account('6300', 'Spare', 'expense')
  await as(() => D.updateAccount(spare, { account_type: 'asset' } as never))
  await as(() => D.updateAccount(spare, { is_active: false } as never))
})

test('the trial balance stays balanced and includes inactive accounts that hold a balance', async () => {
  await je([[a.rent, 30, 0], [a.bank, 0, 30]])
  await db.sql`UPDATE public.accounts SET is_active = false WHERE id = ${a.rent}`
  const tb = await D.generateTrialBalance(ORG)
  assert.ok(tb.isBalanced)
  assert.ok(tb.accounts.some((r) => r.accountName === 'Rent'))
})

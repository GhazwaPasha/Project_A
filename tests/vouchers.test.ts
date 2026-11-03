import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { account, ORG, OTHER_ORG, startDatabase, USER } from './helpers/db'
import { actingUserStore } from '../src/server/request-context'
import { VoucherServiceAdmin as V } from '../src/server/voucher-service-admin'
import { DataServiceAdmin as D } from '../src/server/data-service-admin'

let db: Awaited<ReturnType<typeof startDatabase>>
const a: Record<string, number> = {}
let ITEM = 0
const form = (o = {}) => ({ voucher_type: 'purchase', description: 'Test', vendor_name: 'Noor', payment_type: 'credit', lines: [{ item_id: ITEM, quantity_requested: 10, unit_cost_estimated: 100 }], ...o }) as never
const stock = async () => (await db.sql`SELECT quantity_available::float AS q, total_value::float AS v, average_unit_cost::float AS a FROM public.inventory_items WHERE id = ${ITEM}`)[0]
const counts = async () => ({ j: (await db.sql`SELECT COUNT(*)::int AS n FROM public.journal_entries`)[0].n, t: (await db.sql`SELECT COUNT(*)::int AS n FROM public.inventory_transactions`)[0].n })
const balances = async () => Object.fromEntries((await D.getAccountBalances(ORG)).map((x: { code: string; balance: number }) => [x.code, Number(x.balance)]))
const executed = async (o = {}, qty = 10, cost?: number) => {
  const v = await V.createVoucher(form(o), ORG)
  await V.submitForApproval(v.id, ORG)
  await V.approveVoucher(v.id)
  const [l] = await db.sql`SELECT id FROM public.inventory_voucher_lines WHERE voucher_id = ${v.id} ORDER BY line_number`
  await V.executeVoucher(v.id, { [Number(l.id)]: qty }, cost ? { [Number(l.id)]: cost } : undefined)
  return Number(v.id)
}
const as = <T>(fn: () => Promise<T>) => actingUserStore.run(USER, fn)

before(async () => {
  db = await startDatabase()
  a.inv = await account('1300', 'Inventory', 'asset')
  a.ap = await account('2000', 'Payable', 'liability')
  a.ap2 = await account('2010', 'Other payable', 'liability')
  a.header = await account('2999', 'Header', 'liability', { postable: false })
  a.cogs = await account('5000', 'Cost of goods', 'expense')
  a.foreign = await account('2000', 'Theirs', 'liability', { org: OTHER_ORG })
  const [c] = await db.sql`INSERT INTO public.inventory_categories (organization_id, name, inventory_account_id, expense_account_id) VALUES (${ORG}::uuid, 'Packaging', ${a.inv}, ${a.cogs}) RETURNING id`
  const [i] = await db.sql`INSERT INTO public.inventory_items (organization_id, category_id, sku, name) VALUES (${ORG}::uuid, ${c.id}, 'CTN', 'Cartons') RETURNING id`
  ITEM = Number(i.id)
})
after(async () => { await db.stop() })

test('steps cannot be skipped', () => as(async () => {
  const v = await V.createVoucher(form(), ORG)
  await assert.rejects(() => V.postVoucher(v.id, { payable_account_id: a.ap }), /can't be posted/)
  await assert.rejects(() => V.completeVoucher(v.id), /can't be completed/)
  await assert.rejects(() => V.approveVoucher(v.id), /can't be approved/)
}))
test('a purchase moves stock and records one linked entry, once', () => as(async () => {
  const id = await executed({}, 8, 110)
  const start = await counts()
  assert.equal((await V.previewVoucherPosting(id)).needs_payable, true)
  assert.deepEqual(await counts(), start)
  assert.equal((await V.postVoucher(id, { payable_account_id: a.ap, date: '2026-10-15' }) as unknown as Record<string, unknown>).status, 'posted')
  const s = await stock()
  assert.deepEqual([s.q, s.v, s.a], [8, 880, 110])
  assert.deepEqual(await counts(), { j: start.j + 1, t: start.t + 1 })
  assert.equal((await balances())['2000'], 880)
  await assert.rejects(() => V.postVoucher(id, { payable_account_id: a.ap }), /can't be posted/)
  await assert.rejects(() => V.deleteVoucher(id), /can't be deleted/)
}))
test('supplier payable is found by name, and average cost blends', () => as(async () => {
  const [s] = await db.sql`INSERT INTO public.suppliers (organization_id, supplier_code, name) VALUES (${ORG}::uuid, 'S1', 'Noor') RETURNING id`
  await db.sql`INSERT INTO public.supplier_account_mappings (supplier_id, organization_id, payable_account_id) VALUES (${s.id}, ${ORG}::uuid, ${a.ap2})`
  await V.postVoucher(await executed({}, 1, 50))
  assert.equal((await balances())['2010'], 50)
  const st = await stock()
  assert.equal(st.q, 9); assert.equal(st.v, 930)
}))
test('issuing books the cost at average; too many is refused and nothing changes', () => as(async () => {
  const s0 = await stock()
  await V.postVoucher(await executed({ voucher_type: 'issuance', purpose: 'Packing', vendor_name: undefined, lines: [{ item_id: ITEM, quantity_requested: 3 }] }, 3))
  assert.equal((await stock()).q, s0.q - 3)
  assert.ok(Math.abs((await balances())['5000'] - 3 * s0.a) < 0.02)
  const c0 = await counts(); const s1 = await stock()
  const big = await executed({ voucher_type: 'issuance', purpose: 'Too many', lines: [{ item_id: ITEM, quantity_requested: 500 }] }, 500)
  await assert.rejects(() => V.postVoucher(big), /on hand/)
  assert.deepEqual(await counts(), c0); assert.deepEqual(await stock(), s1)
}))
test('any failure mid-post rolls everything back', () => as(async () => {
  const s0 = await stock(); const c0 = await counts()
  const id = await executed({}, 1, 10)
  await assert.rejects(() => V.postVoucher(id, { payable_account_id: a.header }), /header/)
  await assert.rejects(() => V.postVoucher(id, { payable_account_id: a.foreign }), /does not belong/)
  const original = D.applyInventoryTransaction
  D.applyInventoryTransaction = (async () => { throw new Error('boom') }) as never
  try { await assert.rejects(() => V.postVoucher(id, { payable_account_id: a.ap }), /boom/) } finally { D.applyInventoryTransaction = original }
  assert.deepEqual(await counts(), c0); assert.deepEqual(await stock(), s0)
  assert.equal((await db.sql`SELECT status FROM public.inventory_vouchers WHERE id = ${id}`)[0].status, 'receiving')
}))
test('stock value matches the books', () => as(async () => {
  assert.ok(Math.abs((await stock()).v - (await balances())['1300']) < 0.02)
}))

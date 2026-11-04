import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { account, ORG, OTHER_ORG, startDatabase, USER } from './helpers/db'
import { actingUserStore } from '../src/server/request-context'
import { InventoryServiceAdmin as I } from '../src/server/inventory/service'
import { BooksServiceAdmin as B } from '../src/server/books/service'
import { DataServiceAdmin as D } from '../src/server/data-service-admin'
import { VoucherServiceAdmin as V } from '../src/server/voucher-service-admin'

type Doc = Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any
let db: Awaited<ReturnType<typeof startDatabase>>
const as = <T>(fn: () => Promise<T>) => actingUserStore.run(USER, fn)
const a: Record<string, number> = {}
const b: Record<string, number> = {}
const DAY = '2026-03-10'
let counter = 0
const item = async (org: string, cat: number, o: Doc = {}) => {
  counter += 1
  return Number((await D.createInventoryItem({ organization_id: org, category_id: cat, sku: `S-${counter}`, name: `Item ${counter}`, description: null, unit_of_measure: 'Each', quantity_in: 0, quantity_out: 0, average_unit_cost: 0, reorder_point: 0, reorder_quantity: 0, is_active: true, created_by: USER, ...o } as never))!.id)
}
/** What a browser could send to the plain movement call. */
const raw = (itemId: number, o: Doc = {}) => D.createInventoryTransaction({ organization_id: ORG, item_id: itemId, transaction_type: 'in', quantity: 1, unit_cost: 5, total_cost: 5, journal_entry_id: null, reference: null, description: null, transaction_date: DAY, created_by: USER, ...o } as never) as Promise<Doc>
const row = async (id: number) => (await db.sql`SELECT quantity_available::float AS q, total_value::float AS v, quantity_in::float AS qi, average_unit_cost::float AS avg FROM public.inventory_items WHERE id = ${id}`)[0] as Doc

before(async () => {
  db = await startDatabase()
  a.inv = await account('1300', 'Inv', 'asset'); a.cogs = await account('5000', 'Cogs', 'expense'); a.ap = await account('2000', 'AP', 'liability'); a.sales = await account('4000', 'Sales', 'revenue')
  a.header = await account('1000', 'Assets', 'asset', { postable: false })
  b.inv = await account('1300', 'Inv', 'asset', { org: OTHER_ORG }); b.cogs = await account('5000', 'Cogs', 'expense', { org: OTHER_ORG }); b.ap = await account('2000', 'AP', 'liability', { org: OTHER_ORG })
  a.cat = Number((await db.sql`INSERT INTO public.inventory_categories (organization_id, name, inventory_account_id, expense_account_id) VALUES (${ORG}::uuid, 'A', ${a.inv}, ${a.cogs}) RETURNING id`)[0].id)
  b.cat = Number((await db.sql`INSERT INTO public.inventory_categories (organization_id, name, inventory_account_id, expense_account_id) VALUES (${OTHER_ORG}::uuid, 'B', ${b.inv}, ${b.cogs}) RETURNING id`)[0].id)
  await db.sql`INSERT INTO public.user_profiles (id, email, full_name) VALUES ('00000000-0000-4000-8000-000000000099'::uuid, 'x@example.com', 'x')`
})
after(async () => { await db.stop() })

test('the browser call can no longer undo another organization’s movements', () => as(async () => {
  const theirs = await item(OTHER_ORG, b.cat, { track_serials: true })
  await I.setItemCosting(OTHER_ORG, theirs, 'fifo')
  await B.recordStockMovement(OTHER_ORG, { item_id: theirs, transaction_type: 'in', quantity: 2, unit_cost: 100, transaction_date: DAY, offset_account_id: b.ap, serial_numbers: 'SECRET-1,SECRET-2' })
  const out = await B.recordStockMovement(OTHER_ORG, { item_id: theirs, transaction_type: 'out', quantity: 1, transaction_date: DAY, serial_numbers: 'SECRET-1' })
  const layers = async () => (await db.sql`SELECT SUM(quantity)::float q, SUM(value)::float v FROM public.stock_cost_layers WHERE item_id = ${theirs}`)[0]
  const before = await layers()
  const mine = await item(ORG, a.cat, { track_serials: true })
  await I.setItemCosting(ORG, mine, 'fifo')
  const made = await raw(mine, { from_transaction_ids: [out.id] })
  assert.deepEqual(await layers(), before, 'their cost layers are untouched')
  assert.ok(!(made.serials as string[]).includes('SECRET-1'), 'their serial numbers do not leak')
  assert.equal((await db.sql`SELECT COUNT(*)::int AS n FROM public.stock_serials WHERE item_id = ${mine} AND serial_number LIKE 'SECRET%'`)[0].n, 0)
}))

test('even internal movements refuse to undo a movement that is not this item’s own', () => as(async () => {
  const mine = await item(ORG, a.cat), other = await item(ORG, a.cat), theirs = await item(OTHER_ORG, b.cat)
  await B.recordStockMovement(OTHER_ORG, { item_id: theirs, transaction_type: 'in', quantity: 2, unit_cost: 1, transaction_date: DAY, offset_account_id: b.ap })
  const foreign = await B.recordStockMovement(OTHER_ORG, { item_id: theirs, transaction_type: 'out', quantity: 1, transaction_date: DAY })
  const sibling = await B.recordStockMovement(ORG, { item_id: other, transaction_type: 'in', quantity: 2, unit_cost: 1, transaction_date: DAY, offset_account_id: a.ap })
  const call = (from: number) => db.sql.begin((tx) => D.applyInventoryTransaction(tx as never, { organization_id: ORG, item_id: mine, transaction_type: 'in', quantity: 1, unit_cost: 1, total_cost: 1, journal_entry_id: null, reference: null, description: null, transaction_date: DAY, created_by: USER, from_transaction_ids: [from] } as never))
  await assert.rejects(() => call(foreign.id), /Stock movement not found/)
  await assert.rejects(() => call(sibling.id), /Stock movement not found/)
}))

test('the browser call sets its own journal link, author and value rules', () => as(async () => {
  const [je] = await db.sql`SELECT id FROM public.journal_entries WHERE organization_id = ${OTHER_ORG}::uuid LIMIT 1`
  const i = await item(ORG, a.cat)
  const r = await raw(i, { journal_entry_id: Number(je.id), created_by: '00000000-0000-4000-8000-000000000099', source_type: 'document', source_id: 1 })
  assert.equal(r.journal_entry_id, null)
  assert.equal(r.created_by, USER)
  assert.equal(r.source_type, null)
  // A person can't set what stock leaving is worth.
  await raw(i, { quantity: 1, unit_cost: 5, total_cost: 5 })
  const before = await row(i)
  await raw(i, { transaction_type: 'out', quantity: -1, unit_cost: 9999, total_cost: 9999 })
  assert.equal((await row(i)).v, before.v - 5)
  await assert.rejects(() => raw(i, { transaction_type: 'transfer_in' }), /Unknown kind/)
}))

test('internal movements can only link to this organization’s entries', () => as(async () => {
  const [je] = await db.sql`SELECT id FROM public.journal_entries WHERE organization_id = ${OTHER_ORG}::uuid LIMIT 1`
  const i = await item(ORG, a.cat)
  await assert.rejects(() => db.sql.begin((tx) => D.applyInventoryTransaction(tx as never, { organization_id: ORG, item_id: i, transaction_type: 'in', quantity: 1, unit_cost: 1, total_cost: 1, journal_entry_id: Number(je.id), reference: null, description: null, transaction_date: DAY, created_by: USER } as never)), /Journal entry not found/)
}))

test('new items start empty, whatever the browser says', () => as(async () => {
  const i = await item(ORG, a.cat, { quantity_in: 500, quantity_out: 3, average_unit_cost: 77 })
  const r = await row(i)
  assert.equal(r.qi, 0); assert.equal(r.avg, 0)
}))

test('items and categories stay inside their organization', () => as(async () => {
  await assert.rejects(() => item(ORG, b.cat), /Category not found/)
  const i = await item(ORG, a.cat, { description: 'Keep me' })
  await assert.rejects(() => D.updateInventoryItem(i, { category_id: b.cat } as never), /Category not found/)
  const category = (o: Doc) => D.createInventoryCategory({ organization_id: ORG, name: `C${++counter}`, description: null, inventory_account_id: a.inv, expense_account_id: a.cogs, parent_id: null, is_active: true, created_by: USER, ...o } as never)
  await assert.rejects(() => category({ inventory_account_id: b.inv }), /Account not found/)
  await assert.rejects(() => category({ expense_account_id: b.cogs }), /Account not found/)
  await assert.rejects(() => category({ inventory_account_id: a.sales }), /must be an asset/)
  await assert.rejects(() => category({ expense_account_id: a.ap }), /must be an expense/)
  await assert.rejects(() => category({ inventory_account_id: a.header }), /can be posted/)
  await assert.rejects(() => category({ parent_id: b.cat }), /Category not found/)
  const made = await category({}) as Doc
  await assert.rejects(() => D.updateInventoryCategory(Number(made.id), { inventory_account_id: b.inv } as never), /Account not found/)
  await assert.rejects(() => D.updateInventoryCategory(Number(made.id), { parent_id: b.cat } as never), /Category not found/)
}))

test('a partial edit keeps what it was not told to change', () => as(async () => {
  const i = await item(ORG, a.cat, { description: 'Keep me' })
  await D.updateInventoryItem(i, { name: 'Renamed' } as never)
  const [r] = await db.sql`SELECT name, description FROM public.inventory_items WHERE id = ${i}`
  assert.equal(r.name, 'Renamed'); assert.equal(r.description, 'Keep me')
  const c = await D.createInventoryCategory({ organization_id: ORG, name: `Kept${++counter}`, description: 'Keep me', inventory_account_id: a.inv, expense_account_id: a.cogs, parent_id: a.cat, is_active: true, created_by: USER } as never) as Doc
  await D.updateInventoryCategory(Number(c.id), { name: `Renamed${counter}` } as never)
  const [k] = await db.sql`SELECT description, parent_id FROM public.inventory_categories WHERE id = ${c.id}`
  assert.equal(k.description, 'Keep me'); assert.equal(Number(k.parent_id), a.cat)
}))

test('vouchers can’t use another organization’s items or suppliers', () => as(async () => {
  const theirs = await item(OTHER_ORG, b.cat, { name: 'Their secret product' })
  const [s] = await db.sql`INSERT INTO public.suppliers (organization_id, supplier_code, name, created_by) VALUES (${OTHER_ORG}::uuid, 'S1', 'Their supplier', ${USER}::uuid) RETURNING id`
  const form = { voucher_type: 'purchase', description: 'x', vendor_name: 'x', payment_type: 'credit', lines: [{ item_id: theirs, quantity_requested: 1, unit_cost_estimated: 1 }] }
  await assert.rejects(() => V.createVoucher(form as never, ORG), /Item not found/)
  const mine = await item(ORG, a.cat)
  await assert.rejects(() => V.createVoucher({ ...form, supplier_id: Number(s.id), lines: [{ item_id: mine, quantity_requested: 1, unit_cost_estimated: 1 }] } as never, ORG), /Supplier not found/)
  const made = await V.createVoucher({ ...form, lines: [{ item_id: mine, quantity_requested: 1, unit_cost_estimated: 1 }] } as never, ORG) as Doc
  await assert.rejects(() => V.updateVoucher(Number(made.id), { lines: [{ item_id: theirs, quantity_requested: 1 }] } as never), /Item not found/)
}))

test('purchase orders can’t use another organization’s tax rates', () => as(async () => {
  const [r] = await db.sql`INSERT INTO public.tax_rates (organization_id, name, rate, sales_account_id, purchase_account_id) VALUES (${OTHER_ORG}::uuid, 'Their tax', 5, ${b.ap}, ${b.inv}) RETURNING id`
  const mine = await item(ORG, a.cat)
  await assert.rejects(() => I.savePurchaseOrder(ORG, { supplier_name: 'x', order_date: DAY, lines: [{ item_id: mine, quantity: 1, unit_cost: 1, tax_rate_id: Number(r.id) }] }), /tax rate is not available/)
}))

test('a closed period is closed to every stock movement', () => as(async () => {
  const i = await item(ORG, a.cat)
  await B.recordStockMovement(ORG, { item_id: i, transaction_type: 'in', quantity: 5, unit_cost: 2, transaction_date: DAY, offset_account_id: a.ap })
  const north = (await I.saveWarehouse(ORG, { name: 'North' })).id
  const main = Number((await db.sql`SELECT id FROM public.warehouses WHERE organization_id = ${ORG}::uuid AND is_default`)[0].id)
  await db.sql`INSERT INTO public.period_closes (organization_id, through_date, closed_by) VALUES (${ORG}::uuid, '2026-01-31', ${USER}::uuid)`
  const before = await row(i)
  await assert.rejects(() => raw(i, { transaction_date: '2026-01-15' }), /closed through/)
  await assert.rejects(() => I.transferStock(ORG, { from_warehouse_id: main, to_warehouse_id: north, date: '2026-01-15', lines: [{ item_id: i, quantity: 1 }] }), /closed through/)
  await assert.rejects(() => raw(i, { transaction_type: 'adjustment', quantity: -1, transaction_date: '2026-01-31' }), /closed through/)
  assert.deepEqual(await row(i), before)
  assert.ok(await raw(i, { transaction_date: '2026-02-01' }), 'the day after is open')
  await db.sql`UPDATE public.period_closes SET reopened_at = now(), reopen_reason = 't' WHERE organization_id = ${ORG}::uuid`
}))

test('movements with values that make no sense are refused, and change nothing', () => as(async () => {
  const i = await item(ORG, a.cat)
  await assert.rejects(() => raw(i, { quantity: -5 }), /positive quantity/)
  await assert.rejects(() => raw(i, { quantity: 0 }), /must not be zero/)
  await assert.rejects(() => raw(i, { transaction_type: 'adjustment', quantity: 0 }), /must not be zero/)
  await assert.rejects(() => raw(i, { quantity: 'lots' }), /must not be zero/)
  await assert.rejects(() => raw(i, { unit_cost: -1, total_cost: null }), /can't be negative/)
  await assert.rejects(() => raw(i, { unit_cost: 1, total_cost: -5 }), /can't be negative/)
  await assert.rejects(() => raw(i, { transaction_date: 'soon' }), /real date/)
  const r = await row(i)
  assert.equal(r.q, 0); assert.equal(r.v, 0)
}))

import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { account, ORG, OTHER_ORG, startDatabase, USER } from './helpers/db'
import { actingUserStore } from '../src/server/request-context'
import { InventoryServiceAdmin as I } from '../src/server/inventory/service'
import { BooksServiceAdmin as B } from '../src/server/books/service'
import { DataServiceAdmin as D } from '../src/server/data-service-admin'
import { authorizeAppDataCall } from '../src/server/app-data-authorize'
import { allocateLots, abcAnalysis, countAdjustments, reorderLine } from '../src/server/inventory/rules'

type Doc = Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any
let db: Awaited<ReturnType<typeof startDatabase>>
const a: Record<string, number> = {}
let category = 0
let main = 0
let north = 0
let counter = 0
const as = <T>(fn: () => Promise<T>) => actingUserStore.run(USER, fn)
const DAY = '2026-03-10'

const newItem = async (o: Doc = {}) => {
  counter += 1
  const made = await D.createInventoryItem({ organization_id: ORG, category_id: category, sku: `T-${counter}`, name: `Item ${counter}`, description: null, unit_of_measure: 'pcs', quantity_in: 0, quantity_out: 0, average_unit_cost: 0, reorder_point: 0, reorder_quantity: 0, is_active: true, created_by: USER, ...o } as never)
  return Number(made!.id)
}
const move = (item: number, type: 'in' | 'out' | 'adjustment', quantity: number, o: Doc = {}) => B.recordStockMovement(ORG, { item_id: item, transaction_type: type, quantity, transaction_date: DAY, offset_account_id: a.ap, ...o })
const stock = async (item: number, cost?: number, quantity = 10, o: Doc = {}) => move(item, 'in', quantity, { unit_cost: cost ?? 10, ...o })
const itemRow = async (id: number) => (await db.sql`SELECT quantity_available::float AS q, total_value::float AS v, average_unit_cost::float AS avg FROM public.inventory_items WHERE id = ${id}`)[0] as Doc
const level = async (item: number, wh: number) => Number((await db.sql`SELECT quantity::float AS q FROM public.stock_levels WHERE item_id = ${item} AND warehouse_id = ${wh}`)[0]?.q ?? 0)
/** The rule everything rests on: warehouses add up to the item, and batches add up to the warehouses. */
const invariant = async () => {
  const off = await db.sql`
    SELECT i.id FROM public.inventory_items i
    LEFT JOIN (SELECT item_id, SUM(quantity) AS q FROM public.stock_levels GROUP BY 1) l ON l.item_id = i.id
    LEFT JOIN (SELECT item_id, SUM(quantity) AS q FROM public.stock_lots GROUP BY 1) s ON s.item_id = i.id
    WHERE ABS(i.quantity_available - COALESCE(l.q, 0)) > 0.0001 OR (i.track_lots AND ABS(COALESCE(l.q, 0) - COALESCE(s.q, 0)) > 0.0001)
  `
  assert.equal(off.length, 0, `stock totals disagree on items ${off.map((r) => r.id).join(',')}`)
}
const booksAgree = async () => {
  const check = await I.getBooksCheck(ORG)
  assert.ok(check.agrees, `stock and books differ: ${JSON.stringify(check.rows)}`)
}

before(async () => {
  db = await startDatabase()
  a.bank = await account('1010', 'Bank', 'asset')
  a.ar = await account('1200', 'Receivable', 'asset')
  a.inv = await account('1300', 'Inventory', 'asset')
  a.ap = await account('2000', 'Payable', 'liability')
  a.grni = await account('2100', 'Received not billed', 'liability')
  a.sales = await account('4000', 'Sales', 'revenue')
  a.cogs = await account('5000', 'Cost of goods', 'expense')
  const [c] = await db.sql`INSERT INTO public.inventory_categories (organization_id, name, inventory_account_id, expense_account_id) VALUES (${ORG}::uuid, 'Packaging', ${a.inv}, ${a.cogs}) RETURNING id`
  category = Number(c.id)
  await as(async () => {
    north = (await I.saveWarehouse(ORG, { name: 'North' })).id
    main = (await I.saveWarehouse(ORG, { name: 'Main', is_default: true })).id
    await I.saveSettings(ORG, { grni_account_id: a.grni })
  })
})
after(async () => { await db.stop() })

// ---- Rules ----

test('batches: first to expire goes first, no expiry goes last, and a shortfall is reported', () => {
  const lots = [{ id: 1, quantity: 5, expiry_date: null }, { id: 2, quantity: 5, expiry_date: '2026-06-01' }, { id: 3, quantity: 5, expiry_date: '2026-05-01' }]
  assert.deepEqual(allocateLots(lots, 7).picks.map((p) => [p.lot.id, p.quantity]), [[3, 5], [2, 2]])
  assert.equal(allocateLots(lots, 20).short, 5)
})

test('reorder: covers lead time, counts what is on order, and leaves unused items alone', () => {
  const base = { item_id: 1, on_hand: 10, on_order: 0, used_90_days: 90, reorder_point: 0, reorder_quantity: 0, lead_time_days: 14 }
  const low = reorderLine(base)
  assert.equal(low.suggested, 34); assert.equal(low.days_of_cover, 10); assert.equal(low.stockout_risk, true)
  assert.equal(reorderLine({ ...base, on_order: 50 }).suggested, 0)
  assert.equal(reorderLine({ ...base, used_90_days: 0 }).suggested, 0)
  assert.equal(reorderLine({ ...base, used_90_days: 0, reorder_point: 20, reorder_quantity: 5 }).suggested, 5)
})

test('ABC splits value used at 80 and 95 percent', () => {
  const r = abcAnalysis([{ item_id: 1, usage_value: 80 }, { item_id: 2, usage_value: 15 }, { item_id: 3, usage_value: 5 }, { item_id: 4, usage_value: 0 }])
  assert.deepEqual(r.map((x) => x.class), ['A', 'B', 'C', 'C'])
})

test('count entry balances and only moves what differs', () => {
  const r = countAdjustments([
    { item_id: 1, counted: 8, current: 10, average_unit_cost: 5, inventory_account_id: 1, adjustment_account_id: 2 },
    { item_id: 2, counted: 12, current: 10, average_unit_cost: 5, inventory_account_id: 1, adjustment_account_id: 2 },
    { item_id: 3, counted: null, current: 10, average_unit_cost: 5, inventory_account_id: 1, adjustment_account_id: 2 },
    { item_id: 4, counted: 10, current: 10, average_unit_cost: 5, inventory_account_id: 1, adjustment_account_id: 2 },
  ])
  assert.deepEqual(r.moves.map((m) => m.item_id), [1, 2])
  assert.deepEqual(r.entry, [], 'a gain and a loss of the same value net to nothing')
})

// ---- Items and SKUs ----

test('a blank SKU gets the next number; duplicates and repeated barcodes are refused', () => as(async () => {
  const first = await D.createInventoryItem({ organization_id: ORG, category_id: category, sku: '', name: 'Auto', description: null, unit_of_measure: 'pcs', quantity_in: 0, quantity_out: 0, average_unit_cost: 0, reorder_point: 0, reorder_quantity: 0, is_active: true, created_by: USER, barcode: '8901234' } as never)
  assert.equal(first!.sku, 'SKU-0001')
  await db.sql`DELETE FROM public.inventory_items WHERE id = ${first!.id}`
  const again = await newItem({ sku: null, name: 'Auto 2', barcode: '8901234' })
  const row = await D.getInventoryItem(again) as Doc
  assert.equal(row.sku, 'SKU-0001', 'free again only because nothing holds it')
  await assert.rejects(() => newItem({ sku: 'SKU-0001' }), /SKU-0001 is already on/)
  await assert.rejects(() => newItem({ barcode: '8901234' }), /barcode is already on/)
  const other = await newItem()
  await assert.rejects(() => I.saveItemDetails(ORG, other, { barcode: '8901234' }), /barcode is already on/)
}))

test('item details: another organization can not be referenced, and lead time stays sensible', () => as(async () => {
  const item = await newItem()
  const foreign = await account('9001', 'Theirs', 'revenue', { org: OTHER_ORG })
  await assert.rejects(() => I.saveItemDetails(ORG, item, { income_account_id: foreign }), /Account not found/)
  await assert.rejects(() => I.saveItemDetails(ORG, item, { lead_time_days: 9999 }), /Lead time/)
  await assert.rejects(() => I.saveItemDetails(OTHER_ORG, item, { barcode: 'x' }), /Item not found/)
  await I.saveItemDetails(ORG, item, { barcode: 'B-1', selling_price: 25, income_account_id: a.sales, lead_time_days: 7 })
  const d = await I.getItemDetail(ORG, item) as Doc
  assert.equal(d.barcode, 'B-1'); assert.equal(d.selling_price, 25); assert.equal(d.lead_time_days, 7)
}))

test('import adds and updates by SKU, leaves quantities alone, and reports bad lines', () => as(async () => {
  assert.deepEqual(await I.importItems(ORG, [{ sku: 'IMP-1', name: 'Imported', category: 'packaging', barcode: 'IMP', selling_price: '12.50' }]), { added: 1, updated: 0 })
  assert.deepEqual(await I.importItems(ORG, [{ sku: 'IMP-1', name: 'Renamed', category: 'Packaging' }]), { added: 0, updated: 1 })
  const [row] = await db.sql`SELECT name, barcode, quantity_available::float AS q FROM public.inventory_items WHERE sku = 'IMP-1'`
  assert.equal(row.name, 'Renamed'); assert.equal(row.barcode, 'IMP'); assert.equal(row.q, 0)
  await assert.rejects(() => I.importItems(ORG, [{ sku: 'X', name: 'Y', category: 'Nope' }]), /no category called/)
}))

// ---- Warehouses and transfers ----

test('movements land in a warehouse, and going below zero there is refused even with stock elsewhere', () => as(async () => {
  const item = await newItem()
  await stock(item, 10, 10, { warehouse_id: north })
  assert.equal(await level(item, north), 10)
  await assert.rejects(() => move(item, 'out', 1, { warehouse_id: main }), /Insufficient quantity: only 0/)
  assert.equal((await itemRow(item)).q, 10, 'nothing changed')
  await move(item, 'out', 4, { warehouse_id: north })
  assert.equal(await level(item, north), 6)
  await invariant(); await booksAgree()
}))

test('a transfer moves stock, not value, and adds nothing to the books', () => as(async () => {
  const item = await newItem()
  await stock(item, 7, 10)
  const before = await itemRow(item)
  const [{ n }] = await db.sql`SELECT COUNT(*)::int AS n FROM public.journal_entries`
  const { reference } = await I.transferStock(ORG, { from_warehouse_id: main, to_warehouse_id: north, date: DAY, lines: [{ item_id: item, quantity: 4 }] })
  assert.match(reference, /^TR-\d{4}$/)
  assert.equal(await level(item, main), 6); assert.equal(await level(item, north), 4)
  assert.deepEqual(await itemRow(item), before)
  assert.equal((await db.sql`SELECT COUNT(*)::int AS n FROM public.journal_entries`)[0].n, n)
  await assert.rejects(() => I.transferStock(ORG, { from_warehouse_id: main, to_warehouse_id: north, date: DAY, lines: [{ item_id: item, quantity: 99 }] }), /Insufficient/)
  await assert.rejects(() => I.transferStock(ORG, { from_warehouse_id: main, to_warehouse_id: main, date: DAY, lines: [{ item_id: item, quantity: 1 }] }), /two different/)
  assert.equal(await level(item, main), 6, 'a refused transfer changes nothing')
  await invariant(); await booksAgree()
}))

test('a warehouse holding stock can not be closed, and there is only one default', () => as(async () => {
  const item = await newItem()
  const temp = (await I.saveWarehouse(ORG, { name: 'Temp' })).id
  await stock(item, 5, 1, { warehouse_id: temp })
  await assert.rejects(() => I.saveWarehouse(ORG, { id: temp, name: 'Temp', is_active: false }), /still holds stock/)
  await assert.rejects(() => I.saveWarehouse(ORG, { id: main, name: 'Main', is_active: false }), /another default/)
  const [{ n }] = await db.sql`SELECT COUNT(*)::int AS n FROM public.warehouses WHERE organization_id = ${ORG}::uuid AND is_default`
  assert.equal(n, 1)
}))

// ---- Batches ----

test('batches: sold first-to-expire, keep their expiry across a transfer, and add up', () => as(async () => {
  const item = await newItem({ track_lots: true })
  await stock(item, 10, 5, { lot_number: 'LATE', expiry_date: '2027-01-01' })
  await stock(item, 10, 5, { lot_number: 'SOON', expiry_date: '2026-12-01' })
  await move(item, 'out', 6)
  const lots = (await I.getItemDetail(ORG, item) as Doc).lots as Doc[]
  assert.deepEqual(lots.map((l) => [l.lot_number, l.quantity]), [['LATE', 4]])
  await I.transferStock(ORG, { from_warehouse_id: main, to_warehouse_id: north, date: DAY, lines: [{ item_id: item, quantity: 3 }] })
  const moved = ((await I.getItemDetail(ORG, item) as Doc).lots as Doc[]).find((l) => Number(l.warehouse_id) === north)!
  assert.equal(moved.lot_number, 'LATE'); assert.equal(moved.expiry_date, '2027-01-01'); assert.equal(moved.quantity, 3)
  await invariant(); await booksAgree()
}))

test('turning batches on gives existing stock an opening batch, and they stay on while stock is in batches', () => as(async () => {
  const item = await newItem()
  await stock(item, 10, 5)
  await I.saveItemDetails(ORG, item, { track_lots: true })
  const lots = (await I.getItemDetail(ORG, item) as Doc).lots as Doc[]
  assert.deepEqual(lots.map((l) => [l.lot_number, l.quantity]), [['OPENING', 5]])
  await invariant()
  await assert.rejects(() => I.saveItemDetails(ORG, item, { track_lots: false }), /batch tracking stays on/)
}))

test('stock card shows each movement with a running balance', () => as(async () => {
  const item = await newItem()
  await stock(item, 10, 10)
  await move(item, 'out', 3)
  const card = await I.getStockCard(ORG, item) as Doc[]
  assert.deepEqual(card.map((c) => c.balance), [7, 10], 'newest first')
  assert.equal((await I.getStockCard(OTHER_ORG, item) as Doc[]).length, 0)
}))

// ---- Purchase orders ----

const draftOrder = async (item: number, quantity = 10, unit_cost = 5) => (await I.savePurchaseOrder(ORG, { supplier_name: 'Acme', warehouse_id: main, order_date: DAY, lines: [{ item_id: item, quantity, unit_cost }] })).id

test('purchase order: a draft moves nothing; goods need approval; part and over receipts behave', () => as(async () => {
  const item = await newItem()
  const id = await draftOrder(item)
  const line = (await I.getPurchaseOrder(ORG, id) as Doc).lines[0]
  await assert.rejects(() => I.receivePurchaseOrder(ORG, id, { date: DAY, lines: [{ line_id: line.id, quantity: 1 }] }), /has to be approved/)
  assert.equal((await itemRow(item)).q, 0)
  await I.approvePurchaseOrder(ORG, id)
  await assert.rejects(() => I.savePurchaseOrder(ORG, { id, supplier_name: 'Acme', order_date: DAY, lines: [{ item_id: item, quantity: 1, unit_cost: 1 }] }), /Only a draft/)
  const part = await I.receivePurchaseOrder(ORG, id, { date: DAY, lines: [{ line_id: line.id, quantity: 4 }] }) as Doc
  assert.equal(part.status, 'partial'); assert.equal((await itemRow(item)).q, 4); assert.equal((await itemRow(item)).v, 20)
  await assert.rejects(() => I.receivePurchaseOrder(ORG, id, { date: DAY, lines: [{ line_id: line.id, quantity: 7 }] }), /Only 6 of/)
  const full = await I.receivePurchaseOrder(ORG, id, { date: DAY, lines: [{ line_id: line.id, quantity: 6 }] }) as Doc
  assert.equal(full.status, 'received')
  await assert.rejects(() => I.receivePurchaseOrder(ORG, id, { date: DAY, lines: [{ line_id: line.id, quantity: 1 }] }), /already finished/)
  await invariant(); await booksAgree()
}))

test('bill from receipts clears received-not-billed into what is owed, once; voiding frees it to bill again', () => as(async () => {
  const before = await grni()
  const item = await newItem()
  const id = await draftOrder(item, 10, 5)
  await I.approvePurchaseOrder(ORG, id)
  const line = (await I.getPurchaseOrder(ORG, id) as Doc).lines[0]
  await I.receivePurchaseOrder(ORG, id, { date: DAY, lines: [{ line_id: line.id, quantity: 10 }] })
  assert.equal(await grni(), before + 50)
  const bill = await I.createBillFromReceipts(ORG, id)
  await assert.rejects(() => I.createBillFromReceipts(ORG, id), /already been billed/)
  const onHand = (await itemRow(item)).q
  await B.postDocument(ORG, bill.id, { control_account_id: a.ap })
  assert.equal(await grni(), before, 'cleared')
  assert.equal((await itemRow(item)).q, onHand, 'the bill does not count the goods twice')
  await B.voidDocument(ORG, bill.id, { reason: 'Wrong price' })
  assert.equal(await grni(), before + 50, 'back to waiting')
  assert.ok(await I.createBillFromReceipts(ORG, id), 'can be billed again')
  await invariant(); await booksAgree()
}))
async function grni() {
  const [r] = await db.sql`SELECT COALESCE(SUM(credit_amount - debit_amount), 0)::float AS b FROM public.journal_entry_lines WHERE account_id = ${a.grni}`
  return Number(r.b)
}

test('cancelling: an untouched order is cancelled, one with receipts stays received', () => as(async () => {
  const item = await newItem()
  const empty = await draftOrder(item)
  assert.equal((await I.cancelPurchaseOrder(ORG, empty) as Doc).status, 'cancelled')
  const id = await draftOrder(item)
  await I.approvePurchaseOrder(ORG, id)
  const line = (await I.getPurchaseOrder(ORG, id) as Doc).lines[0]
  await I.receivePurchaseOrder(ORG, id, { date: DAY, lines: [{ line_id: line.id, quantity: 1 }] })
  assert.equal((await I.cancelPurchaseOrder(ORG, id) as Doc).status, 'received')
  await assert.rejects(() => I.cancelPurchaseOrder(ORG, id), /already finished/)
}))

test('a free receipt adds stock with no value and no entry, and receiving needs the account set up', () => as(async () => {
  const item = await newItem()
  await stock(item, 10, 10)
  const id = await draftOrder(item, 10, 0)
  await I.approvePurchaseOrder(ORG, id)
  const line = (await I.getPurchaseOrder(ORG, id) as Doc).lines[0]
  await I.receivePurchaseOrder(ORG, id, { date: DAY, lines: [{ line_id: line.id, quantity: 10 }] })
  const row = await itemRow(item)
  assert.equal(row.q, 20); assert.equal(row.v, 100); assert.equal(row.avg, 5)
  await booksAgree()
  await I.saveSettings(ORG, { grni_account_id: null })
  await assert.rejects(() => I.receivePurchaseOrder(ORG, id, { date: DAY, lines: [{ line_id: line.id, quantity: 1 }] }), /set up/)
  await assert.rejects(() => I.saveSettings(ORG, { grni_account_id: a.bank }), /liability/)
  await I.saveSettings(ORG, { grni_account_id: a.grni })
}))

// ---- Invoices and bills ----

const dated = { issue_date: DAY, due_date: '2026-04-09' }

test('selling an item takes stock and records cost of sales in the same entry; voiding puts both back', () => as(async () => {
  const item = await newItem()
  await stock(item, 10, 10)
  const { id } = await B.saveDocument(ORG, { kind: 'invoice', party_name: 'Apex', ...dated, lines: [{ description: 'Cartons', account_id: a.sales, quantity: 3, unit_price: 25, item_id: item }] })
  const preview = await B.previewDocument(ORG, id, { control_account_id: a.ar })
  assert.ok(preview.lines.some((l) => l.account_id === a.cogs && l.debit === 30), 'preview shows the cost')
  assert.equal((await itemRow(item)).q, 10, 'a preview changes nothing')
  const doc = await B.postDocument(ORG, id, { control_account_id: a.ar }) as Doc
  assert.equal((await itemRow(item)).q, 7); assert.equal((await itemRow(item)).v, 70)
  const lines = await db.sql`SELECT account_id, debit_amount::float AS dr, credit_amount::float AS cr FROM public.journal_entry_lines WHERE journal_entry_id = ${doc.journal_entry_id}`
  assert.ok(lines.some((l) => Number(l.account_id) === a.cogs && l.dr === 30))
  assert.ok(lines.some((l) => Number(l.account_id) === a.inv && l.cr === 30))
  assert.equal(doc.lines[0].cost_amount, 30)
  await invariant(); await booksAgree()
  await B.voidDocument(ORG, id, { reason: 'Returned' })
  assert.equal((await itemRow(item)).q, 10); assert.equal((await itemRow(item)).v, 100)
  await invariant(); await booksAgree()
}))

test('selling more than a warehouse holds is refused, and the preview warns first', () => as(async () => {
  const item = await newItem()
  await stock(item, 10, 2)
  const { id } = await B.saveDocument(ORG, { kind: 'invoice', party_name: 'Apex', ...dated, lines: [{ description: 'Too many', account_id: a.sales, quantity: 3, unit_price: 25, item_id: item }] })
  assert.ok((await B.previewDocument(ORG, id, { control_account_id: a.ar })).problems.some((p) => /Only 2 of/.test(p)))
  await assert.rejects(() => B.postDocument(ORG, id, { control_account_id: a.ar }), /Insufficient/)
  assert.equal(((await B.getDocument(ORG, id)) as Doc).status, 'draft'); assert.equal((await itemRow(item)).q, 2)
  await booksAgree()
}))

test('two lines of one item clear its whole value, with awkward cents', () => as(async () => {
  const item = await newItem()
  await stock(item, 3.33, 3)
  const { id } = await B.saveDocument(ORG, { kind: 'invoice', party_name: 'Apex', ...dated, lines: [
    { description: 'One', account_id: a.sales, quantity: 1, unit_price: 9, item_id: item },
    { description: 'Two', account_id: a.sales, quantity: 2, unit_price: 9, item_id: item },
  ] })
  await B.postDocument(ORG, id, { control_account_id: a.ar })
  const row = await itemRow(item)
  assert.equal(row.q, 0); assert.equal(row.v, 0)
  await booksAgree()
}))

test('a bill for an item goes to its stock account and adds stock; voiding takes it out at that cost', () => as(async () => {
  const item = await newItem()
  const { id } = await B.saveDocument(ORG, { kind: 'bill', party_name: 'Acme', ...dated, lines: [{ description: 'Stock', account_id: a.cogs, quantity: 4, unit_price: 12.5, item_id: item, warehouse_id: north }] })
  const saved = await B.getDocument(ORG, id) as Doc
  assert.equal(Number(saved.lines[0].account_id), a.inv, 'the stock account wins over what was chosen')
  await B.postDocument(ORG, id, { control_account_id: a.ap })
  assert.equal(await level(item, north), 4); assert.equal((await itemRow(item)).v, 50)
  await booksAgree()
  await B.voidDocument(ORG, id, { reason: 'Duplicate' })
  assert.equal((await itemRow(item)).q, 0); assert.equal((await itemRow(item)).v, 0)
  await invariant(); await booksAgree()
}))

test('a voided bill whose goods were sold is refused, with nothing changed', () => as(async () => {
  const item = await newItem()
  const { id } = await B.saveDocument(ORG, { kind: 'bill', party_name: 'Acme', ...dated, lines: [{ description: 'Stock', quantity: 2, unit_price: 10, item_id: item }] })
  await B.postDocument(ORG, id, { control_account_id: a.ap })
  await move(item, 'out', 2)
  await assert.rejects(() => B.voidDocument(ORG, id, { reason: 'Oops' }), /Insufficient/)
  assert.equal(((await B.getDocument(ORG, id)) as Doc).status, 'posted')
  await booksAgree()
}))

test('a closed period refuses stock posted into it', () => as(async () => {
  const item = await newItem()
  await stock(item, 10, 2)
  const id = await draftOrder(item)
  await I.approvePurchaseOrder(ORG, id)
  const line = (await I.getPurchaseOrder(ORG, id) as Doc).lines[0]
  await db.sql`INSERT INTO public.period_closes (organization_id, through_date, closed_by) VALUES (${ORG}::uuid, '2026-01-31', ${USER}::uuid)`
  await assert.rejects(() => I.receivePurchaseOrder(ORG, id, { date: '2026-01-15', lines: [{ line_id: line.id, quantity: 1 }] }), /closed/)
  await db.sql`UPDATE public.period_closes SET reopened_at = now(), reopen_reason = 'test' WHERE organization_id = ${ORG}::uuid`
  assert.equal((await itemRow(item)).q, 2)
}))

test('document numbers are not reused after a draft is deleted', () => as(async () => {
  const one = await B.saveDocument(ORG, { kind: 'invoice', party_name: 'A', ...dated, lines: [{ description: 'x', account_id: a.sales, quantity: 1, unit_price: 1 }] })
  const two = await B.saveDocument(ORG, { kind: 'invoice', party_name: 'B', ...dated, lines: [{ description: 'x', account_id: a.sales, quantity: 1, unit_price: 1 }] })
  await B.deleteDocument(ORG, one.id)
  const three = await B.saveDocument(ORG, { kind: 'invoice', party_name: 'C', ...dated, lines: [{ description: 'x', account_id: a.sales, quantity: 1, unit_price: 1 }] })
  const n = async (id: number) => Number(String(((await B.getDocument(ORG, id)) as Doc).number).split('-')[1])
  assert.equal(await n(three.id), (await n(two.id)) + 1)
}))

// ---- Counts ----

test('a count corrects stock and the books together, ignores uncounted items, and respects stock that moved meanwhile', () => as(async () => {
  const short = await newItem(), extra = await newItem(), moved = await newItem(), skipped = await newItem()
  for (const i of [short, extra, moved, skipped]) await stock(i, 10, 10)
  const { id } = await I.createStockCount(ORG, { warehouse_id: main, count_date: DAY })
  const count = await I.getStockCount(ORG, id) as Doc
  const lineOf = (item: number) => count.lines.find((l: Doc) => Number(l.item_id) === item).id
  await I.saveStockCountLines(ORG, id, [{ line_id: lineOf(short), counted: 8 }, { line_id: lineOf(extra), counted: 11 }, { line_id: lineOf(moved), counted: 7 }])
  await move(moved, 'out', 3)
  const posted = await I.postStockCount(ORG, id) as Doc
  assert.equal(posted.status, 'posted')
  assert.equal((await itemRow(short)).q, 8); assert.equal((await itemRow(short)).v, 80)
  assert.equal((await itemRow(extra)).q, 11); assert.equal((await itemRow(extra)).v, 110)
  assert.equal((await itemRow(moved)).q, 7, 'the sale during the count is not a loss')
  assert.equal((await itemRow(skipped)).q, 10)
  await assert.rejects(() => I.postStockCount(ORG, id), /finished/)
  await assert.rejects(() => I.saveStockCountLines(ORG, id, [{ line_id: lineOf(short), counted: 1 }]), /finished/)
  await invariant(); await booksAgree()
}))

test('a count on a batch item keeps batches in step', () => as(async () => {
  const item = await newItem({ track_lots: true })
  await stock(item, 10, 5, { lot_number: 'A1' })
  const { id } = await I.createStockCount(ORG, { warehouse_id: main, count_date: DAY })
  const count = await I.getStockCount(ORG, id) as Doc
  const line = count.lines.find((l: Doc) => Number(l.item_id) === item)
  const others = count.lines.filter((l: Doc) => Number(l.item_id) !== item).map((l: Doc) => ({ line_id: l.id, counted: null }))
  await I.saveStockCountLines(ORG, id, [{ line_id: line.id, counted: 7 }, ...others])
  await I.postStockCount(ORG, id)
  const lots = (await I.getItemDetail(ORG, item) as Doc).lots as Doc[]
  assert.equal(lots.reduce((s, l) => s + Number(l.quantity), 0), 7)
  await invariant(); await booksAgree()
}))

// ---- Planning and reports ----

test('plan drafts one order per supplier, for a person to approve', () => as(async () => {
  const [s] = await db.sql`INSERT INTO public.suppliers (organization_id, supplier_code, name, created_by) VALUES (${ORG}::uuid, 'S1', 'Acme Supply', ${USER}::uuid) RETURNING id`
  const withSupplier = await newItem({ preferred_supplier_id: Number(s.id), reorder_point: 5, reorder_quantity: 20 })
  const without = await newItem({ reorder_point: 5, reorder_quantity: 10 })
  const plan = await I.getReorderPlan(ORG) as Doc[]
  assert.equal(plan.find((p) => Number(p.item_id) === withSupplier)!.suggested, 20)
  const { orders } = await I.createOrdersFromPlan(ORG, { lines: [{ item_id: withSupplier, quantity: 20 }, { item_id: without, quantity: 10 }] })
  assert.equal(orders.length, 2)
  const made = await Promise.all(orders.map((o) => I.getPurchaseOrder(ORG, o))) as Doc[]
  assert.deepEqual(made.map((m) => m.status), ['draft', 'draft'])
  assert.deepEqual(made.map((m) => m.supplier_name).sort(), ['Acme Supply', 'Supplier to confirm'])
}))

test('analysis totals match the items, and spot idle and expiring stock', () => as(async () => {
  const idle = await newItem()
  await stock(idle, 10, 1)
  const expiring = await newItem({ track_lots: true })
  await stock(expiring, 10, 1, { lot_number: 'OLD', expiry_date: new Date(Date.now() + 5 * 86400000).toISOString().slice(0, 10) })
  const r = await I.getAnalysis(ORG) as Doc
  const [{ v }] = await db.sql`SELECT COALESCE(SUM(total_value), 0)::float AS v FROM public.inventory_items WHERE organization_id = ${ORG}::uuid AND is_active`
  assert.ok(Math.abs(r.total_value - v) < 0.01)
  assert.ok(r.slow_moving.some((s: Doc) => Number(s.item_id) === idle))
  assert.ok(r.expiring.some((l: Doc) => l.lot_number === 'OLD' && l.status === 'soon'))
}))

test('books check flags a real gap', () => as(async () => {
  const item = await newItem()
  await stock(item, 10, 1)
  await db.sql`UPDATE public.inventory_items SET total_value = total_value + 5 WHERE id = ${item}`
  const check = await I.getBooksCheck(ORG)
  assert.equal(check.agrees, false)
  assert.equal(check.rows[0].difference, 5)
  await db.sql`UPDATE public.inventory_items SET total_value = total_value - 5 WHERE id = ${item}`
  await booksAgree()
}))

// ---- Other organizations and roles ----

test('another organization sees and touches none of it', () => as(async () => {
  const item = await newItem()
  const po = await draftOrder(item)
  await assert.rejects(() => I.getItemDetail(OTHER_ORG, item), /not found/)
  await assert.rejects(() => I.getPurchaseOrder(OTHER_ORG, po), /not found/)
  await assert.rejects(() => I.approvePurchaseOrder(OTHER_ORG, po), /Only a draft/)
  await assert.rejects(() => I.savePurchaseOrder(OTHER_ORG, { supplier_name: 'X', warehouse_id: main, order_date: DAY, lines: [{ item_id: item, quantity: 1, unit_cost: 1 }] }), /Warehouse not found/)
  await assert.rejects(() => I.savePurchaseOrder(OTHER_ORG, { supplier_name: 'X', order_date: DAY, lines: [{ item_id: item, quantity: 1, unit_cost: 1 }] }), /Choose an item/)
  await assert.rejects(() => I.transferStock(OTHER_ORG, { from_warehouse_id: main, to_warehouse_id: north, date: DAY, lines: [{ item_id: item, quantity: 1 }] }), /Warehouse not found/)
  await assert.rejects(() => move(item, 'in', 1, { warehouse_id: main, unit_cost: 1 }).then(() => D.applyInventoryTransaction(db.sql as never, { organization_id: ORG, item_id: item, transaction_type: 'in', quantity: 1, unit_cost: 1, total_cost: 1, journal_entry_id: null, reference: null, description: null, transaction_date: DAY, created_by: USER, warehouse_id: 999999 } as never)), /Warehouse not found/)
  assert.equal(((await I.listWarehouses(OTHER_ORG)) as Doc[]).some((w) => Number(w.id) === main), false)
}))

test('roles: members run stock, only those who keep the books commit money, observers only look', async () => {
  const ids: Record<string, string> = { member: '00000000-0000-4000-8000-000000000002', observer: '00000000-0000-4000-8000-000000000003', accountant: '00000000-0000-4000-8000-000000000004' }
  for (const [role, id] of Object.entries(ids)) {
    await db.sql`INSERT INTO public.user_profiles (id, email, full_name) VALUES (${id}::uuid, ${`${role}@example.com`}, ${role})`
    await db.sql`INSERT INTO public.organization_members (id, user_id, organization_id, role, is_active) VALUES (gen_random_uuid(), ${id}::uuid, ${ORG}::uuid, ${role}, true)`
  }
  const can = (who: string, method: string) => authorizeAppDataCall('InventoryService', method, [ORG], ids[who]).then(() => true, () => false)
  assert.equal(await can('observer', 'getReorderPlan'), true)
  assert.equal(await can('observer', 'transferStock'), false)
  assert.equal(await can('member', 'transferStock'), true)
  assert.equal(await can('member', 'receivePurchaseOrder'), true)
  assert.equal(await can('member', 'approvePurchaseOrder'), false)
  assert.equal(await can('member', 'postStockCount'), false)
  assert.equal(await can('member', 'getBooksCheck'), false)
  assert.equal(await can('accountant', 'approvePurchaseOrder'), true)
  assert.equal(await can('accountant', 'getBooksCheck'), true)
  assert.equal(await can('accountant', 'nothingLikeThis'), false)
  assert.equal(await authorizeAppDataCall('InventoryService', 'getAnalysis', [OTHER_ORG], ids.member).then(() => true, () => false), false)
})

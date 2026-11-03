import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { account, ORG, OTHER_ORG, startDatabase, USER } from './helpers/db'
import { actingUserStore } from '../src/server/request-context'
import { InventoryServiceAdmin as I } from '../src/server/inventory/service'
import { BooksServiceAdmin as B } from '../src/server/books/service'
import { DataServiceAdmin as D } from '../src/server/data-service-admin'
import { VoucherServiceAdmin as V } from '../src/server/voucher-service-admin'
import { authorizeAppDataCall } from '../src/server/app-data-authorize'
import { assemblyEntry, consumeLayers, findBomCycle, parseSerials } from '../src/server/inventory/rules'

type Doc = Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any
let db: Awaited<ReturnType<typeof startDatabase>>
const a: Record<string, number> = {}
let category = 0
let main = 0
let north = 0
let counter = 0
const as = <T>(fn: () => Promise<T>) => actingUserStore.run(USER, fn)
const DAY = '2026-03-10'
const dated = { issue_date: DAY, due_date: '2026-04-09' }

const newItem = async (o: Doc = {}) => {
  counter += 1
  const made = await D.createInventoryItem({ organization_id: ORG, category_id: category, sku: `D-${counter}`, name: `Item ${counter}`, description: null, unit_of_measure: 'Each', quantity_in: 0, quantity_out: 0, average_unit_cost: 0, reorder_point: 0, reorder_quantity: 0, is_active: true, created_by: USER, ...o } as never)
  const id = Number(made!.id)
  if (o.costing_method) await I.setItemCosting(ORG, id, o.costing_method)
  return id
}
const move = (item: number, type: 'in' | 'out' | 'adjustment', quantity: number, o: Doc = {}) => B.recordStockMovement(ORG, { item_id: item, transaction_type: type, quantity, transaction_date: DAY, offset_account_id: a.ap, ...o })
const row = async (id: number) => (await db.sql`SELECT quantity_available::float AS q, total_value::float AS v, average_unit_cost::float AS avg FROM public.inventory_items WHERE id = ${id}`)[0] as Doc
const lastCost = async (item: number) => Number((await db.sql`SELECT total_cost::float AS c FROM public.inventory_transactions WHERE item_id = ${item} ORDER BY id DESC LIMIT 1`)[0].c)
const inStock = async (item: number, wh?: number) => (await db.sql`SELECT serial_number FROM public.stock_serials WHERE item_id = ${item} AND in_stock AND (${wh ?? null}::bigint IS NULL OR warehouse_id = ${wh ?? null}::bigint) ORDER BY id`).map((r) => r.serial_number as string)
const layerSum = async (item: number) => (await db.sql`SELECT COALESCE(SUM(quantity), 0)::float AS q, COALESCE(SUM(value), 0)::float AS v FROM public.stock_cost_layers WHERE item_id = ${item}`)[0] as Doc
const agree = async (item?: number) => {
  const check = await I.getBooksCheck(ORG)
  assert.ok(check.agrees, `stock and books differ: ${JSON.stringify(check.rows)}`)
  const off = await db.sql`
    SELECT i.id FROM public.inventory_items i LEFT JOIN (SELECT item_id, SUM(quantity) AS q FROM public.stock_levels GROUP BY 1) l ON l.item_id = i.id
    WHERE ABS(i.quantity_available - COALESCE(l.q, 0)) > 0.0001
       OR (i.track_serials AND i.quantity_available <> (SELECT COUNT(*) FROM public.stock_serials s WHERE s.item_id = i.id AND s.in_stock))
       OR (i.costing_method = 'fifo' AND ABS(i.total_value - COALESCE((SELECT SUM(value) FROM public.stock_cost_layers c WHERE c.item_id = i.id), 0)) > 0.01)
  `
  assert.equal(off.length, 0, `totals disagree on items ${off.map((r) => r.id).join(',')}`)
  if (item) assert.ok(await row(item))
}

before(async () => {
  db = await startDatabase()
  a.bank = await account('1010', 'Bank', 'asset')
  a.ar = await account('1200', 'Receivable', 'asset')
  a.inv = await account('1300', 'Inventory', 'asset')
  a.inv2 = await account('1310', 'Finished goods', 'asset')
  a.ap = await account('2000', 'Payable', 'liability')
  a.grni = await account('2100', 'Received not billed', 'liability')
  a.sales = await account('4000', 'Sales', 'revenue')
  a.cogs = await account('5000', 'Cost of goods', 'expense')
  a.labour = await account('5100', 'Labour', 'expense')
  const [c] = await db.sql`INSERT INTO public.inventory_categories (organization_id, name, inventory_account_id, expense_account_id) VALUES (${ORG}::uuid, 'Parts', ${a.inv}, ${a.cogs}) RETURNING id`
  category = Number(c.id)
  await as(async () => {
    main = (await I.saveWarehouse(ORG, { name: 'Main', is_default: true })).id
    north = (await I.saveWarehouse(ORG, { name: 'North' })).id
    await I.saveSettings(ORG, { grni_account_id: a.grni })
  })
})
after(async () => { await db.stop() })

// ---- Rules ----

test('layers: oldest first, a whole layer takes its whole value, a shortfall is reported', () => {
  const layers = [{ id: 1, quantity: 3, value: 10 }, { id: 2, quantity: 5, value: 50 }]
  assert.equal(consumeLayers(layers, 3).cost, 10)
  assert.equal(consumeLayers(layers, 4).cost, 20)
  assert.equal(consumeLayers(layers, 1).cost, 3.33)
  assert.equal(consumeLayers(layers, 9).short, 1)
})

test('serial lists: lines or commas, blanks dropped, repeats refused', () => {
  assert.deepEqual(parseSerials('A1, A2\nA3;A4\n\n'), ['A1', 'A2', 'A3', 'A4'])
  assert.deepEqual(parseSerials(null), [])
  assert.throws(() => parseSerials('A1,A1'), /listed twice/)
})

test('a part that leads back to the item is found, at any depth', () => {
  const others = [{ item_id: 2, component_id: 3 }, { item_id: 3, component_id: 1 }]
  assert.equal(findBomCycle(1, [2], others), 2)
  assert.equal(findBomCycle(1, [1], []), 1)
  assert.equal(findBomCycle(1, [4], others), null)
})

test('build entry balances, with parts on two accounts and an extra cost', () => {
  const lines = assemblyEntry(9, [{ inventory_account_id: 1, amount: 30 }, { inventory_account_id: 1, amount: 10 }, { inventory_account_id: 2, amount: 5 }], 15, 7)
  assert.equal(lines.reduce((s, l) => s + l.debit, 0), 60)
  assert.equal(lines.reduce((s, l) => s + l.credit, 0), 60)
  assert.equal(lines.length, 4)
})

// ---- FIFO ----

test('FIFO: issues cost the oldest purchases, and the books follow', () => as(async () => {
  const item = await newItem({ costing_method: 'fifo' })
  await move(item, 'in', 10, { unit_cost: 10 })
  await move(item, 'in', 10, { unit_cost: 20 })
  await move(item, 'out', 12)
  assert.equal(await lastCost(item), 140, '10 at 10 and 2 at 20')
  const r = await row(item)
  assert.equal(r.q, 8); assert.equal(r.v, 160); assert.equal(r.avg, 20)
  assert.deepEqual(await layerSum(item), { q: 8, v: 160 })
  await agree()
}))

test('the same stock on moving average costs differently, and stays that way by default', () => as(async () => {
  const item = await newItem()
  await move(item, 'in', 10, { unit_cost: 10 })
  await move(item, 'in', 10, { unit_cost: 20 })
  await move(item, 'out', 12)
  assert.equal(await lastCost(item), 180)
  assert.deepEqual(await layerSum(item), { q: 0, v: 0 })
  await agree()
}))

test('switching method keeps the value, both ways', () => as(async () => {
  const item = await newItem()
  await move(item, 'in', 3, { unit_cost: 3.33 })
  await move(item, 'in', 4, { unit_cost: 7 })
  const before = await row(item)
  await I.setItemCosting(ORG, item, 'fifo')
  assert.equal((await row(item)).v, before.v)
  assert.deepEqual(await layerSum(item), { q: 7, v: before.v })
  await move(item, 'out', 7)
  assert.equal((await row(item)).v, 0)
  await move(item, 'in', 2, { unit_cost: 5 })
  await I.setItemCosting(ORG, item, 'average')
  assert.deepEqual(await layerSum(item), { q: 0, v: 0 })
  assert.equal((await row(item)).avg, 5)
  await agree()
}))

test('FIFO invoice: preview, entry and stock all use the layer cost; voiding restores it', () => as(async () => {
  const item = await newItem({ costing_method: 'fifo' })
  await move(item, 'in', 2, { unit_cost: 10 })
  await move(item, 'in', 2, { unit_cost: 30 })
  const { id } = await B.saveDocument(ORG, { kind: 'invoice', party_name: 'Apex', ...dated, lines: [
    { description: 'One', account_id: a.sales, quantity: 1, unit_price: 50, item_id: item },
    { description: 'Two', account_id: a.sales, quantity: 2, unit_price: 50, item_id: item },
  ] })
  const preview = await B.previewDocument(ORG, id, { control_account_id: a.ar })
  assert.ok(preview.lines.some((l) => l.account_id === a.cogs && l.debit === 50), 'two lines cost 10 + (10 + 30)')
  const doc = await B.postDocument(ORG, id, { control_account_id: a.ar }) as Doc
  assert.equal(doc.lines[0].cost_amount + doc.lines[1].cost_amount, 50)
  assert.equal((await row(item)).v, 30)
  await agree()
  await B.voidDocument(ORG, id, { reason: 'Returned' })
  const r = await row(item)
  assert.equal(r.q, 4); assert.equal(r.v, 80)
  await move(item, 'out', 2)
  assert.equal(await lastCost(item), 20, 'restored stock goes back to the front of the queue')
  await agree()
}))

test('FIFO bill: void takes that bill’s own stock, and is refused once it has been used', () => as(async () => {
  const item = await newItem({ costing_method: 'fifo' })
  const save = (price: number) => B.saveDocument(ORG, { kind: 'bill', party_name: 'Acme', ...dated, lines: [{ description: 'Stock', quantity: 5, unit_price: price, item_id: item }] })
  const first = await save(10), second = await save(20)
  await B.postDocument(ORG, first.id, { control_account_id: a.ap })
  await B.postDocument(ORG, second.id, { control_account_id: a.ap })
  await move(item, 'out', 1)
  await assert.rejects(() => B.voidDocument(ORG, first.id, { reason: 'Oops' }), /already been used/)
  assert.equal(((await B.getDocument(ORG, first.id)) as Doc).status, 'posted')
  await B.voidDocument(ORG, second.id, { reason: 'Duplicate' })
  assert.equal((await row(item)).v, 40, 'the 20s left, not the 10s')
  await agree()
}))

test('FIFO count: a loss costs the oldest layers, in the entry and in stock', () => as(async () => {
  const item = await newItem({ costing_method: 'fifo' })
  await move(item, 'in', 5, { unit_cost: 2 })
  await move(item, 'in', 5, { unit_cost: 8 })
  const { id } = await I.createStockCount(ORG, { warehouse_id: main, count_date: DAY })
  const count = await I.getStockCount(ORG, id) as Doc
  const lines = count.lines.map((l: Doc) => ({ line_id: l.id, counted: Number(l.item_id) === item ? 4 : null }))
  await I.saveStockCountLines(ORG, id, lines)
  await I.postStockCount(ORG, id)
  const r = await row(item)
  assert.equal(r.q, 4); assert.equal(r.v, 32)
  await agree()
}))

test('FIFO voucher: issuing posts the layer cost', () => as(async () => {
  const item = await newItem({ costing_method: 'fifo' })
  await move(item, 'in', 5, { unit_cost: 2 })
  await move(item, 'in', 5, { unit_cost: 8 })
  const [v] = await db.sql`INSERT INTO public.inventory_vouchers (organization_id, voucher_number, voucher_type, status, requested_by, requested_date) VALUES (${ORG}::uuid, ${`IV-${counter}`}, 'issuance', 'issuing', ${USER}::uuid, ${DAY}::date) RETURNING id`
  await db.sql`INSERT INTO public.inventory_voucher_lines (voucher_id, line_number, item_id, quantity_requested) VALUES (${v.id}, 1, ${item}, 6)`
  await V.postVoucher(Number(v.id), { date: DAY })
  assert.equal(await lastCost(item), 18)
  assert.equal((await row(item)).v, 32)
  await agree()
}))

test('default method: new items follow it, and it can switch everything at once', () => as(async () => {
  await I.setDefaultCosting(ORG, { method: 'fifo' })
  const made = await newItem()
  assert.equal((await db.sql`SELECT costing_method FROM public.inventory_items WHERE id = ${made}`)[0].costing_method, 'fifo')
  await I.setDefaultCosting(ORG, { method: 'average', apply_to_all: true })
  assert.equal((await db.sql`SELECT COUNT(*)::int AS n FROM public.inventory_items WHERE organization_id = ${ORG}::uuid AND costing_method = 'fifo'`)[0].n, 0)
  await agree()
}))

// ---- Serial numbers ----

test('serials: named on the way in, created if blank, and the count has to match', () => as(async () => {
  const item = await newItem({ track_serials: true, sku: 'CAM' })
  await move(item, 'in', 2, { unit_cost: 100, serial_numbers: 'X1\nX2' })
  await move(item, 'in', 2, { unit_cost: 100 })
  assert.deepEqual(await inStock(item), ['X1', 'X2', 'CAM-S0003', 'CAM-S0004'])
  await assert.rejects(() => move(item, 'in', 2, { unit_cost: 100, serial_numbers: 'X9' }), /needs 2 serial numbers/)
  await assert.rejects(() => move(item, 'in', 1, { unit_cost: 100, serial_numbers: 'X1' }), /already in stock/)
  await assert.rejects(() => move(item, 'in', 1.5, { unit_cost: 100 }), /must be whole/)
  assert.equal((await row(item)).q, 4, 'refused movements change nothing')
  await agree()
}))

test('serials: going out by number or oldest first, and a unit that returns keeps its number', () => as(async () => {
  const item = await newItem({ track_serials: true })
  await move(item, 'in', 3, { unit_cost: 50, serial_numbers: 'A,B,C' })
  await move(item, 'out', 1, { serial_numbers: 'B' })
  assert.deepEqual(await inStock(item), ['A', 'C'])
  await assert.rejects(() => move(item, 'out', 1, { serial_numbers: 'B' }), /isn't in Main/)
  await move(item, 'out', 1)
  assert.deepEqual(await inStock(item), ['C'])
  await move(item, 'in', 1, { unit_cost: 50, serial_numbers: 'B' })
  assert.deepEqual(await inStock(item), ['B', 'C'])
  const [found] = await I.findSerial(ORG, 'b') as Doc[]
  assert.equal(found.in_stock, true)
  assert.equal(found.history.length, 3)
  assert.equal((await I.findSerial(OTHER_ORG, 'B') as Doc[]).length, 0)
  await agree()
}))

test('serials follow a transfer, and turning tracking on numbers existing stock', () => as(async () => {
  const item = await newItem({ track_serials: true })
  await move(item, 'in', 3, { unit_cost: 50, serial_numbers: 'T1,T2,T3' })
  await I.transferStock(ORG, { from_warehouse_id: main, to_warehouse_id: north, date: DAY, lines: [{ item_id: item, quantity: 2, serial_numbers: 'T1,T3' }] })
  assert.deepEqual(await inStock(item, north), ['T1', 'T3'])
  assert.deepEqual(await inStock(item, main), ['T2'])
  const later = await newItem({ sku: 'LATE' })
  await move(later, 'in', 2, { unit_cost: 5 })
  await I.saveItemDetails(ORG, later, { track_serials: true })
  assert.deepEqual(await inStock(later), ['LATE-S0001', 'LATE-S0002'])
  await assert.rejects(() => I.saveItemDetails(ORG, later, { track_serials: false }), /stays on/)
  await assert.rejects(() => I.saveItemDetails(ORG, later, { track_lots: true }), /not both/)
  await agree()
}))

test('serials on an invoice: the named units leave, and voiding brings those same units back', () => as(async () => {
  const item = await newItem({ track_serials: true })
  await move(item, 'in', 3, { unit_cost: 50, serial_numbers: 'I1,I2,I3' })
  const { id } = await B.saveDocument(ORG, { kind: 'invoice', party_name: 'Apex', ...dated, lines: [{ description: 'Camera', account_id: a.sales, quantity: 2, unit_price: 90, item_id: item, serial_numbers: 'I1,I3' }] })
  const doc = await B.postDocument(ORG, id, { control_account_id: a.ar }) as Doc
  assert.deepEqual(doc.lines[0].serial_numbers, ['I1', 'I3'])
  assert.deepEqual(await inStock(item), ['I2'])
  await B.voidDocument(ORG, id, { reason: 'Returned' })
  assert.deepEqual(await inStock(item), ['I1', 'I2', 'I3'])
  await agree()
}))

test('serials on a purchase order receipt', () => as(async () => {
  const item = await newItem({ track_serials: true })
  const { id } = await I.savePurchaseOrder(ORG, { supplier_name: 'Acme', warehouse_id: main, order_date: DAY, lines: [{ item_id: item, quantity: 2, unit_cost: 40 }] })
  await I.approvePurchaseOrder(ORG, id)
  const line = (await I.getPurchaseOrder(ORG, id) as Doc).lines[0]
  await assert.rejects(() => I.receivePurchaseOrder(ORG, id, { date: DAY, lines: [{ line_id: line.id, quantity: 2, serial_numbers: 'P1' }] }), /needs 2/)
  await I.receivePurchaseOrder(ORG, id, { date: DAY, lines: [{ line_id: line.id, quantity: 2, serial_numbers: 'P1,P2' }] })
  assert.deepEqual(await inStock(item), ['P1', 'P2'])
  await agree()
}))

test('batches come back as the same batch when a sale is voided', () => as(async () => {
  const item = await newItem({ track_lots: true })
  await move(item, 'in', 5, { unit_cost: 10, lot_number: 'L1', expiry_date: '2027-01-01' })
  const { id } = await B.saveDocument(ORG, { kind: 'invoice', party_name: 'Apex', ...dated, lines: [{ description: 'Goods', account_id: a.sales, quantity: 2, unit_price: 20, item_id: item }] })
  await B.postDocument(ORG, id, { control_account_id: a.ar })
  await B.voidDocument(ORG, id, { reason: 'Returned' })
  const lots = (await I.getItemDetail(ORG, item) as Doc).lots as Doc[]
  assert.deepEqual(lots.map((l) => [l.lot_number, l.quantity, l.expiry_date]), [['L1', 5, '2027-01-01']])
  await agree()
}))

// ---- Units ----

test('units: refused when they make no sense', () => as(async () => {
  const item = await newItem()
  await assert.rejects(() => I.saveUnit(ORG, { item_id: item, name: 'Each', factor: 2 }), /base unit/)
  await assert.rejects(() => I.saveUnit(ORG, { item_id: item, name: 'Box', factor: 0 }), /how many/)
  await I.saveUnit(ORG, { item_id: item, name: 'Box', factor: 12 })
  await assert.rejects(() => I.saveUnit(ORG, { item_id: item, name: 'box', factor: 6 }), /already has/)
  await assert.rejects(() => I.saveUnit(OTHER_ORG, { item_id: item, name: 'Crate', factor: 6 }), /Item not found/)
}))

test('units on an order: buy in boxes, stock counts in eaches, and what is on order follows', () => as(async () => {
  const item = await newItem()
  const { id: unit } = await I.saveUnit(ORG, { item_id: item, name: 'Box', factor: 12 })
  const { id } = await I.savePurchaseOrder(ORG, { supplier_name: 'Acme', warehouse_id: main, order_date: DAY, lines: [{ item_id: item, quantity: 5, unit_cost: 120, unit_id: unit }] })
  await I.approvePurchaseOrder(ORG, id)
  assert.equal((await I.getItemDetail(ORG, item) as Doc).on_order, 60)
  const line = (await I.getPurchaseOrder(ORG, id) as Doc).lines[0]
  assert.equal(line.unit_name, 'Box')
  await I.receivePurchaseOrder(ORG, id, { date: DAY, lines: [{ line_id: line.id, quantity: 2 }] })
  const r = await row(item)
  assert.equal(r.q, 24); assert.equal(r.v, 240); assert.equal(r.avg, 10)
  assert.equal((await I.getItemDetail(ORG, item) as Doc).on_order, 36)
  await assert.rejects(() => I.receivePurchaseOrder(ORG, id, { date: DAY, lines: [{ line_id: line.id, quantity: 4 }] }), /Only 3 of/)
  await agree()
}))

test('units on an invoice and bill: priced per unit, stock moves in the base unit, and voids undo it', () => as(async () => {
  const item = await newItem()
  const { id: unit } = await I.saveUnit(ORG, { item_id: item, name: 'Box', factor: 10 })
  const bill = await B.saveDocument(ORG, { kind: 'bill', party_name: 'Acme', ...dated, lines: [{ description: 'Boxes', quantity: 3, unit_price: 100, item_id: item, unit_id: unit }] })
  await B.postDocument(ORG, bill.id, { control_account_id: a.ap })
  assert.equal((await row(item)).q, 30); assert.equal((await row(item)).v, 300)
  const sale = await B.saveDocument(ORG, { kind: 'invoice', party_name: 'Apex', ...dated, lines: [{ description: 'A box', account_id: a.sales, quantity: 2, unit_price: 200, item_id: item, unit_id: unit }] })
  const doc = await B.postDocument(ORG, sale.id, { control_account_id: a.ar }) as Doc
  assert.equal(doc.total, 400)
  assert.equal(doc.lines[0].unit_name, 'Box')
  assert.equal((await row(item)).q, 10); assert.equal(doc.lines[0].cost_amount, 200)
  await agree()
  await B.voidDocument(ORG, sale.id, { reason: 'Returned' })
  assert.equal((await row(item)).q, 30)
  await I.deleteUnit(ORG, unit)
  assert.equal(((await B.getDocument(ORG, sale.id)) as Doc).lines[0].unit_name, 'Box', 'history keeps the unit')
  const other = await newItem()
  await assert.rejects(() => B.saveDocument(ORG, { kind: 'bill', party_name: 'Acme', ...dated, lines: [{ description: 'x', quantity: 1, unit_price: 1, item_id: other, unit_id: 999999 }] }), /not set up/)
  await agree()
}))

// ---- Bills of materials ----

test('a bill of materials refuses repeats, loops, and items from elsewhere', () => as(async () => {
  const kit = await newItem(), part = await newItem(), sub = await newItem()
  await assert.rejects(() => I.saveBom(ORG, { item_id: kit, lines: [{ item_id: kit, quantity: 1 }] }), /part of itself/)
  await assert.rejects(() => I.saveBom(ORG, { item_id: kit, lines: [{ item_id: part, quantity: 1 }, { item_id: part, quantity: 2 }] }), /only be listed once/)
  await I.saveBom(ORG, { item_id: sub, lines: [{ item_id: kit, quantity: 1 }] })
  await assert.rejects(() => I.saveBom(ORG, { item_id: kit, lines: [{ item_id: sub, quantity: 1 }] }), /made using/)
  await assert.rejects(() => I.saveBom(OTHER_ORG, { item_id: kit, lines: [{ item_id: part, quantity: 1 }] }), /Item not found/)
  await assert.rejects(() => I.buildAssembly(ORG, { item_id: part, quantity: 1, date: DAY }), /no list of parts/)
}))

test('a build uses parts, makes stock at their cost plus extra, and moves value between accounts', () => as(async () => {
  const [c] = await db.sql`INSERT INTO public.inventory_categories (organization_id, name, inventory_account_id, expense_account_id) VALUES (${ORG}::uuid, 'Finished', ${a.inv2}, ${a.cogs}) RETURNING id`
  const kit = await newItem({ category_id: Number(c.id) }), x = await newItem(), y = await newItem({ costing_method: 'fifo' })
  await move(x, 'in', 10, { unit_cost: 2 })
  await move(y, 'in', 2, { unit_cost: 5 })
  await move(y, 'in', 10, { unit_cost: 9 })
  await I.saveBom(ORG, { item_id: kit, output_quantity: 2, lines: [{ item_id: x, quantity: 4 }, { item_id: y, quantity: 6 }] })
  const listed = (await I.listBoms(ORG) as Doc[]).find((b) => Number(b.item_id) === kit)!
  assert.equal(listed.can_build, 4, 'x allows 5, y allows 4')
  const built = await I.buildAssembly(ORG, { item_id: kit, quantity: 2, date: DAY, extra_cost: 7, extra_account_id: a.labour })
  assert.equal(built.total, 8 + (10 + 36) + 7)
  assert.equal((await row(kit)).q, 2); assert.equal((await row(kit)).v, 61)
  assert.equal((await row(x)).q, 6); assert.equal((await row(y)).q, 6); assert.equal((await row(y)).v, 54)
  await agree()
  await assert.rejects(() => I.buildAssembly(ORG, { item_id: kit, quantity: 100, date: DAY }), /Insufficient/)
  assert.equal((await row(kit)).q, 2, 'a build that can not finish changes nothing')
  await assert.rejects(() => I.buildAssembly(ORG, { item_id: kit, quantity: 1, date: DAY, extra_cost: 5 }), /where the extra cost/)
  await I.reverseAssembly(ORG, built.id)
  assert.equal((await row(kit)).q, 0); assert.equal((await row(kit)).v, 0)
  assert.equal((await row(x)).v, 20); assert.equal((await row(y)).v, 100)
  await assert.rejects(() => I.reverseAssembly(ORG, built.id), /already been undone/)
  await agree()
  const [labour] = await db.sql`SELECT COALESCE(SUM(credit_amount - debit_amount), 0)::float AS b FROM public.journal_entry_lines WHERE account_id = ${a.labour}`
  assert.equal(labour.b, 0, 'the extra cost is reversed too')
}))

test('a build that has been sold can not be undone, and serial output is tracked', () => as(async () => {
  const kit = await newItem({ track_serials: true }), part = await newItem({ track_serials: true })
  await move(part, 'in', 2, { unit_cost: 10, serial_numbers: 'PT1,PT2' })
  await I.saveBom(ORG, { item_id: kit, lines: [{ item_id: part, quantity: 1 }] })
  const built = await I.buildAssembly(ORG, { item_id: kit, quantity: 2, date: DAY, serial_numbers: ['K1', 'K2'] })
  assert.deepEqual(await inStock(kit), ['K1', 'K2'])
  await move(kit, 'out', 1, { serial_numbers: 'K1' })
  await assert.rejects(() => I.reverseAssembly(ORG, built.id), /Insufficient|isn't in/)
  assert.deepEqual(await inStock(part), [])
  await move(kit, 'in', 1, { unit_cost: 10, serial_numbers: 'K1' })
  await I.reverseAssembly(ORG, built.id)
  assert.deepEqual(await inStock(part), ['PT1', 'PT2'])
  await agree()
}))

// ---- Roles ----

test('roles for the new actions', async () => {
  const ids: Record<string, string> = { member: '00000000-0000-4000-8000-000000000012', accountant: '00000000-0000-4000-8000-000000000014' }
  for (const [role, id] of Object.entries(ids)) {
    await db.sql`INSERT INTO public.user_profiles (id, email, full_name) VALUES (${id}::uuid, ${`${role}2@example.com`}, ${role})`
    await db.sql`INSERT INTO public.organization_members (id, user_id, organization_id, role, is_active) VALUES (gen_random_uuid(), ${id}::uuid, ${ORG}::uuid, ${role}, true)`
  }
  const can = (who: string, method: string, args: unknown[] = [ORG]) => authorizeAppDataCall('InventoryService', method, args, ids[who]).then(() => true, () => false)
  assert.equal(await can('member', 'findSerial'), true)
  assert.equal(await can('member', 'saveBom'), true)
  assert.equal(await can('member', 'buildAssembly', [ORG, { quantity: 1 }]), true)
  assert.equal(await can('member', 'buildAssembly', [ORG, { quantity: 1, extra_cost: 5 }]), false)
  assert.equal(await can('accountant', 'buildAssembly', [ORG, { quantity: 1, extra_cost: 5 }]), true)
  assert.equal(await can('member', 'reverseAssembly'), false)
  assert.equal(await can('member', 'setItemCosting'), false)
  assert.equal(await can('accountant', 'setDefaultCosting'), true)
})

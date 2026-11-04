import { getSql } from '@/server/pg'
import { DataServiceAdmin } from '@/server/data-service-admin'
import { BooksServiceAdmin } from '@/server/books/service'
import { nextNumber } from '@/server/numbering'
import { InventoryItems, acting, requireDate, text, today, type Pg, type Row } from '@/server/inventory/items'
import { money, quantity, receiptEntry } from '@/server/inventory/rules'

export type PurchaseOrderForm = { id?: number; supplier_id?: number | null; supplier_name?: string | null; warehouse_id?: number | null; order_date: string; expected_date?: string | null; notes?: string | null; lines: { item_id: number; quantity: number; unit_cost: number; tax_rate_id?: number | null; unit_id?: number | null }[] }
export type ReceiptForm = { date: string; lines: { line_id: number; quantity: number; lot_number?: string | null; expiry_date?: string | null; serial_numbers?: string[] | string | null }[] }

/** Purchase orders, partial receipts, and bills from what arrived. */
export class InventoryPurchasing extends InventoryItems {
  static listPurchaseOrders(org: string) {
    return getSql()`
      SELECT p.id, p.number, p.status, p.supplier_name, p.order_date::text AS order_date, p.expected_date::text AS expected_date, w.name AS warehouse_name,
        COALESCE(SUM(l.quantity * l.unit_cost), 0)::float AS total,
        COALESCE(SUM(l.quantity), 0)::float AS ordered, COALESCE(SUM(l.quantity_received), 0)::float AS received,
        EXISTS (SELECT 1 FROM public.goods_receipts g WHERE g.purchase_order_id = p.id AND g.bill_id IS NULL) AS has_unbilled
      FROM public.purchase_orders p
      JOIN public.warehouses w ON w.id = p.warehouse_id
      LEFT JOIN public.purchase_order_lines l ON l.purchase_order_id = p.id
      WHERE p.organization_id = ${org}::uuid
      GROUP BY p.id, w.name ORDER BY p.order_date DESC, p.id DESC LIMIT 500
    `
  }

  static async getPurchaseOrder(org: string, id: number) {
    const sql = getSql()
    const [p] = (await sql`
      SELECT p.*, p.order_date::text AS order_date, p.expected_date::text AS expected_date, w.name AS warehouse_name
      FROM public.purchase_orders p JOIN public.warehouses w ON w.id = p.warehouse_id
      WHERE p.id = ${id} AND p.organization_id = ${org}::uuid
    `) as Row[]
    if (!p) throw new Error('Purchase order not found.')
    const lines = await sql`
      SELECT l.id, l.item_id, l.quantity::float, l.quantity_received::float, l.unit_cost::float, l.tax_rate_id, l.unit_name, l.unit_factor::float, (SELECT u.id FROM public.item_units u WHERE u.item_id = l.item_id AND u.name = l.unit_name) AS unit_id, i.name AS item_name, i.sku, i.unit_of_measure, i.track_lots, i.track_serials
      FROM public.purchase_order_lines l JOIN public.inventory_items i ON i.id = l.item_id
      WHERE l.purchase_order_id = ${id} ORDER BY l.id
    `
    const receipts = await sql`
      SELECT g.id, g.number, g.receipt_date::text AS receipt_date, g.total::float, g.bill_id, d.number AS bill_number
      FROM public.goods_receipts g LEFT JOIN public.trade_documents d ON d.id = g.bill_id
      WHERE g.purchase_order_id = ${id} ORDER BY g.receipt_date, g.id
    `
    return { ...p, lines, receipts }
  }

  /** Saves a draft order. It doesn't touch stock or the books. */
  static async savePurchaseOrder(org: string, form: PurchaseOrderForm) {
    const date = requireDate(form.order_date, 'Order date')
    if (form.expected_date) requireDate(form.expected_date, 'Expected date')
    if (!form.lines?.length) throw new Error('Add at least one item.')
    return getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      let supplier = text(form.supplier_name)
      if (form.supplier_id) {
        const [s] = (await tx`SELECT name FROM public.suppliers WHERE id = ${form.supplier_id} AND organization_id = ${org}::uuid`) as Row[]
        if (!s) throw new Error('Supplier not found.')
        supplier = s.name
      }
      if (!supplier) throw new Error('Choose a supplier.')
      const warehouse = await this.requireWarehouse(tx, org, form.warehouse_id)
      const ids = form.lines.map((l) => Number(l.item_id))
      const known = (await tx`SELECT id FROM public.inventory_items WHERE organization_id = ${org}::uuid AND id = ANY(${ids}::bigint[])`) as Row[]
      if (form.lines.some((l) => !known.some((k) => Number(k.id) === Number(l.item_id)))) throw new Error('Choose an item for every line.')
      const rateIds = form.lines.map((l) => l.tax_rate_id).filter(Boolean).map(Number)
      const rates = rateIds.length ? ((await tx`SELECT id FROM public.tax_rates WHERE organization_id = ${org}::uuid AND id = ANY(${rateIds}::bigint[])`) as Row[]) : []
      if (rateIds.some((id) => !rates.some((r) => Number(r.id) === id))) throw new Error('That tax rate is not available.')
      form.lines.forEach((l) => {
        if (!(Number(l.quantity) > 0)) throw new Error('Quantities must be more than zero.')
        if (!(Number(l.unit_cost) >= 0)) throw new Error("A cost can't be negative.")
      })
      let id = Number(form.id ?? 0)
      if (id) {
        const [p] = (await tx`SELECT status FROM public.purchase_orders WHERE id = ${id} AND organization_id = ${org}::uuid FOR UPDATE`) as Row[]
        if (!p) throw new Error('Purchase order not found.')
        if (p.status !== 'draft') throw new Error('Only a draft order can be edited.')
        await tx`UPDATE public.purchase_orders SET supplier_id = ${form.supplier_id ?? null}, supplier_name = ${supplier}, warehouse_id = ${warehouse}, order_date = ${date}::date, expected_date = ${form.expected_date ?? null}::date, notes = ${text(form.notes)}, updated_at = now() WHERE id = ${id}`
        await tx`DELETE FROM public.purchase_order_lines WHERE purchase_order_id = ${id}`
      } else {
        const number = await nextNumber(tx, org, 'PO', 'public.purchase_orders', 'number')
        const [row] = (await tx`
          INSERT INTO public.purchase_orders (organization_id, number, supplier_id, supplier_name, warehouse_id, order_date, expected_date, notes, created_by)
          VALUES (${org}::uuid, ${number}, ${form.supplier_id ?? null}, ${supplier}, ${warehouse}, ${date}::date, ${form.expected_date ?? null}::date, ${text(form.notes)}, ${acting()}::uuid) RETURNING id
        `) as Row[]
        id = Number(row.id)
      }
      const unitIds = form.lines.map((l) => l.unit_id).filter(Boolean).map(Number)
      const units = unitIds.length ? ((await tx`SELECT id, item_id, name, factor::float AS factor FROM public.item_units WHERE id = ANY(${unitIds}::bigint[])`) as Row[]) : []
      for (const l of form.lines) {
        const unit = l.unit_id ? units.find((u) => Number(u.id) === Number(l.unit_id) && Number(u.item_id) === Number(l.item_id)) : null
        if (l.unit_id && !unit) throw new Error('That unit is not set up for this item.')
        await tx`INSERT INTO public.purchase_order_lines (purchase_order_id, item_id, quantity, unit_cost, tax_rate_id, unit_name, unit_factor) VALUES (${id}, ${Number(l.item_id)}, ${Number(l.quantity)}, ${Number(l.unit_cost)}, ${l.tax_rate_id ?? null}, ${unit?.name ?? null}, ${unit?.factor ?? 1})`
      }
      return { id }
    })
  }

  static async approvePurchaseOrder(org: string, id: number) {
    const rows = await getSql()`
      UPDATE public.purchase_orders SET status = 'approved', approved_by = ${acting()}::uuid, approved_at = now(), updated_at = now()
      WHERE id = ${id} AND organization_id = ${org}::uuid AND status = 'draft' RETURNING id
    `
    if (!rows.length) throw new Error('Only a draft order can be approved.')
    return this.getPurchaseOrder(org, id)
  }

  /** Cancels what's still to come. Anything already received stays received. */
  static async cancelPurchaseOrder(org: string, id: number) {
    const rows = await getSql()`
      UPDATE public.purchase_orders SET status = CASE WHEN EXISTS (SELECT 1 FROM public.goods_receipts g WHERE g.purchase_order_id = ${id}) THEN 'received' ELSE 'cancelled' END, updated_at = now()
      WHERE id = ${id} AND organization_id = ${org}::uuid AND status IN ('draft', 'approved', 'partial') RETURNING id
    `
    if (!rows.length) throw new Error('This order is already finished.')
    return this.getPurchaseOrder(org, id)
  }

  /** Goods arrive: stock goes up at the ordered cost, and what's owed waits in the "received, not billed" account. */
  static async receivePurchaseOrder(org: string, id: number, form: ReceiptForm) {
    const date = requireDate(form.date)
    const wanted = (form.lines ?? []).filter((l) => Number(l.quantity) > 0)
    if (!wanted.length) throw new Error('Enter at least one quantity received.')
    const user = acting()
    const settings = await this.getSettings(org)
    if (!settings.grni_account_id) throw new Error('An accountant needs to set up the "received, not billed" account first, under Inventory, Reports.')
    await getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const [p] = (await tx`SELECT * FROM public.purchase_orders WHERE id = ${id} AND organization_id = ${org}::uuid FOR UPDATE`) as Row[]
      if (!p) throw new Error('Purchase order not found.')
      if (p.status !== 'approved' && p.status !== 'partial') throw new Error(p.status === 'draft' ? 'This order has to be approved before goods can be received.' : 'This order is already finished.')
      const lines = (await tx`
        SELECT l.*, i.name AS item_name, c.inventory_account_id
        FROM public.purchase_order_lines l JOIN public.inventory_items i ON i.id = l.item_id JOIN public.inventory_categories c ON c.id = i.category_id
        WHERE l.purchase_order_id = ${id} FOR UPDATE OF l
      `) as Row[]
      const plan = wanted.map((w) => {
        const l = lines.find((x) => Number(x.id) === Number(w.line_id))
        if (!l) throw new Error('That line is not on this order.')
        const q = Number(w.quantity)
        const left = quantity(Number(l.quantity) - Number(l.quantity_received))
        if (q > left + 1e-9) throw new Error(`Only ${left} of ${l.item_name} still to come on this order.`)
        if (w.expiry_date) requireDate(w.expiry_date, 'Expiry date')
        return { line: l, q, amount: money(q * Number(l.unit_cost)), lot_number: text(w.lot_number), expiry_date: w.expiry_date ?? null, serial_numbers: w.serial_numbers ?? null }
      }).sort((a, b) => Number(a.line.item_id) - Number(b.line.item_id))
      const total = money(plan.reduce((s, x) => s + x.amount, 0))
      const number = await nextNumber(tx, org, 'GR', 'public.goods_receipts', 'number')
      let entry: number | null = null
      if (total > 0) {
        const created = await DataServiceAdmin.insertJournalEntry(tx,
          { organization_id: org, entry_number: `JE-${number}`, entry_date: date, description: `Goods received, ${p.number}, ${p.supplier_name}`, reference: p.number, total_amount: total, is_posted: true, created_by: user, posted_by: user, posted_at: new Date().toISOString() } as never,
          receiptEntry(plan.map((x) => ({ inventory_account_id: Number(x.line.inventory_account_id), amount: x.amount })), settings.grni_account_id as number).map((l, i) => ({ account_id: l.account_id, description: l.description, debit_amount: l.debit, credit_amount: l.credit, line_order: i + 1 })) as never)
        entry = Number(created?.id)
      }
      const [receipt] = (await tx`
        INSERT INTO public.goods_receipts (organization_id, purchase_order_id, number, receipt_date, warehouse_id, total, journal_entry_id, created_by)
        VALUES (${org}::uuid, ${id}, ${number}, ${date}::date, ${p.warehouse_id}, ${total}, ${entry}, ${user}::uuid) RETURNING id
      `) as Row[]
      for (const x of plan) {
        await DataServiceAdmin.applyInventoryTransaction(tx, {
          organization_id: org, item_id: Number(x.line.item_id), transaction_type: 'in', quantity: x.q * Number(x.line.unit_factor), unit_cost: Number(x.line.unit_cost) / Number(x.line.unit_factor), total_cost: x.amount, journal_entry_id: entry,
          reference: number, description: `${p.number}, ${p.supplier_name}`, transaction_date: date, created_by: user, warehouse_id: Number(p.warehouse_id), lot_number: x.lot_number, expiry_date: x.expiry_date, serial_numbers: x.serial_numbers, source_type: 'goods_receipt', source_id: Number(receipt.id),
        } as never)
        await tx`INSERT INTO public.goods_receipt_lines (goods_receipt_id, purchase_order_line_id, item_id, quantity, unit_cost, lot_number, expiry_date) VALUES (${receipt.id}, ${x.line.id}, ${x.line.item_id}, ${x.q}, ${x.line.unit_cost}, ${x.lot_number}, ${x.expiry_date}::date)`
        await tx`UPDATE public.purchase_order_lines SET quantity_received = quantity_received + ${x.q} WHERE id = ${x.line.id}`
      }
      const [{ left }] = (await tx`SELECT COALESCE(SUM(quantity - quantity_received), 0)::float AS left FROM public.purchase_order_lines WHERE purchase_order_id = ${id}`) as Row[]
      await tx`UPDATE public.purchase_orders SET status = ${Number(left) > 1e-9 ? 'partial' : 'received'}, updated_at = now() WHERE id = ${id}`
    })
    return this.getPurchaseOrder(org, id)
  }

  /** Drafts the supplier's bill from what's been received. Posting it clears "received, not billed" into what you owe. */
  static async createBillFromReceipts(org: string, id: number) {
    const settings = await this.getSettings(org)
    return getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const [p] = (await tx`SELECT * FROM public.purchase_orders WHERE id = ${id} AND organization_id = ${org}::uuid FOR UPDATE`) as Row[]
      if (!p) throw new Error('Purchase order not found.')
      if (!settings.grni_account_id) throw new Error('Set up the "received, not billed" account first.')
      const receipts = (await tx`SELECT id FROM public.goods_receipts WHERE purchase_order_id = ${id} AND bill_id IS NULL AND total > 0 FOR UPDATE`) as Row[]
      if (!receipts.length) throw new Error('Everything received on this order has already been billed.')
      const ids = receipts.map((r) => Number(r.id))
      const lines = (await tx`
        SELECT g.quantity::float, g.unit_cost::float, i.name, r.number, pl.tax_rate_id, pl.unit_name
        FROM public.goods_receipt_lines g
        JOIN public.goods_receipts r ON r.id = g.goods_receipt_id
        JOIN public.inventory_items i ON i.id = g.item_id
        JOIN public.purchase_order_lines pl ON pl.id = g.purchase_order_line_id
        WHERE g.goods_receipt_id = ANY(${ids}::bigint[]) ORDER BY g.id
      `) as Row[]
      const issue = today()
      const due = new Date(`${issue}T00:00:00Z`)
      due.setUTCDate(due.getUTCDate() + 30)
      const bill = await BooksServiceAdmin.saveDocumentIn(tx, org, {
        kind: 'bill', supplier_id: p.supplier_id ? Number(p.supplier_id) : null, party_name: p.supplier_name, issue_date: issue, due_date: due.toISOString().slice(0, 10), notes: `From ${p.number}`,
        lines: lines.map((l) => ({ description: `${l.name}${l.unit_name ? `, ${l.unit_name}` : ''} (${l.number})`, account_id: settings.grni_account_id as number, quantity: Number(l.quantity), unit_price: Number(l.unit_cost), tax_rate_id: l.tax_rate_id ? Number(l.tax_rate_id) : null })),
      })
      await tx`UPDATE public.goods_receipts SET bill_id = ${bill.id} WHERE id = ANY(${ids}::bigint[])`
      return bill
    })
  }
}

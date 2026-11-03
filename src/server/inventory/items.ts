import { getSql } from '@/server/pg'
import { getActingUserId } from '@/server/request-context'
import { DataServiceAdmin } from '@/server/data-service-admin'
import { AccountServiceAdmin } from '@/server/account-service-admin'
import { nextNumber } from '@/server/numbering'
import { defaultWarehouse, generateSerials } from '@/server/inventory/stock'
import { resetLayers } from '@/server/inventory/costing'
import { expiryStatus, quantity } from '@/server/inventory/rules'

export type Pg = ReturnType<typeof getSql>
export type Row = Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any
const DATE = /^\d{4}-\d{2}-\d{2}$/
export const today = () => new Date().toISOString().slice(0, 10)
export const requireDate = (d: unknown, name = 'Date') => {
  if (typeof d !== 'string' || !DATE.test(d) || Number.isNaN(Date.parse(d))) throw new Error(`${name} must be a real date.`)
  return d
}
export const text = (s: unknown) => (typeof s === 'string' && s.trim() ? s.trim() : null)
export const acting = () => {
  const id = getActingUserId()
  if (!id) throw new Error('User not authenticated')
  return id
}

export type TransferForm = { from_warehouse_id: number; to_warehouse_id: number; date: string; reference?: string | null; lines: { item_id: number; quantity: number; lot_id?: number | null; serial_numbers?: string[] | string | null }[] }

/** Warehouses, item details and settings. Every method takes the organization first, and every query is limited to it. */
export class InventoryItems {
  static async listWarehouses(org: string) {
    const sql = getSql()
    await sql.begin((raw) => defaultWarehouse(raw as unknown as Pg, org))
    return sql`
      SELECT w.id, w.name, w.code, w.address, w.is_default, w.is_active,
        COALESCE(SUM(l.quantity), 0)::float AS units,
        COALESCE(SUM(l.quantity * i.average_unit_cost), 0)::float AS value,
        COUNT(i.id) FILTER (WHERE l.quantity > 0)::int AS items
      FROM public.warehouses w
      LEFT JOIN public.stock_levels l ON l.warehouse_id = w.id
      LEFT JOIN public.inventory_items i ON i.id = l.item_id
      WHERE w.organization_id = ${org}::uuid
      GROUP BY w.id ORDER BY w.is_default DESC, w.name
    `
  }

  static async saveWarehouse(org: string, form: { id?: number; name: string; code?: string | null; address?: string | null; is_default?: boolean; is_active?: boolean }) {
    const name = text(form.name)
    if (!name) throw new Error('Name the warehouse.')
    return getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      if (form.is_default) await tx`UPDATE public.warehouses SET is_default = false WHERE organization_id = ${org}::uuid AND is_default`
      if (form.id) {
        const [w] = (await tx`SELECT is_default FROM public.warehouses WHERE id = ${form.id} AND organization_id = ${org}::uuid FOR UPDATE`) as Row[]
        if (!w) throw new Error('Warehouse not found.')
        if (form.is_active === false) {
          if (w.is_default && !form.is_default) throw new Error('Choose another default warehouse first.')
          const [held] = (await tx`SELECT COALESCE(SUM(quantity), 0)::float AS q FROM public.stock_levels WHERE warehouse_id = ${form.id}`) as Row[]
          if (Number(held.q) > 0) throw new Error('This warehouse still holds stock. Transfer it out first.')
        }
        await tx`UPDATE public.warehouses SET name = ${name}, code = ${text(form.code)}, address = ${text(form.address)}, is_active = ${form.is_active ?? true}, is_default = ${form.is_default ? true : w.is_default} WHERE id = ${form.id}`
        return { id: Number(form.id) }
      }
      const [{ n }] = (await tx`SELECT COUNT(*)::int AS n FROM public.warehouses WHERE organization_id = ${org}::uuid`) as Row[]
      const [row] = (await tx`INSERT INTO public.warehouses (organization_id, name, code, address, is_default) VALUES (${org}::uuid, ${name}, ${text(form.code)}, ${text(form.address)}, ${Boolean(form.is_default) || n === 0}) RETURNING id`) as Row[]
      return { id: Number(row.id) }
    })
  }

  protected static async requireWarehouse(tx: Pg, org: string, id: number | null | undefined) {
    if (!id) return defaultWarehouse(tx, org)
    const [w] = (await tx`SELECT id FROM public.warehouses WHERE id = ${id} AND organization_id = ${org}::uuid AND is_active`) as Row[]
    if (!w) throw new Error('Warehouse not found.')
    return Number(w.id)
  }

  /** Moves stock between warehouses. Value and the books don't change, only where it is. Batches keep their number and expiry. */
  static async transferStock(org: string, form: TransferForm) {
    const date = requireDate(form.date)
    const from = Number(form.from_warehouse_id)
    const to = Number(form.to_warehouse_id)
    if (from === to) throw new Error('Choose two different warehouses.')
    if (!form.lines?.length) throw new Error('Add at least one item.')
    const user = acting()
    return getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      await this.requireWarehouse(tx, org, from)
      await this.requireWarehouse(tx, org, to)
      const reference = text(form.reference) ?? (await nextNumber(tx, org, 'TR', 'public.inventory_transactions', 'reference'))
      // Always the same order, so two transfers can't lock each other out.
      for (const l of [...form.lines].sort((a, b) => Number(a.item_id) - Number(b.item_id))) {
        const q = Number(l.quantity)
        if (!(q > 0)) throw new Error('Quantities must be more than zero.')
        const base = { organization_id: org, item_id: Number(l.item_id), unit_cost: null, total_cost: null, journal_entry_id: null, reference, description: null, transaction_date: date, created_by: user, source_type: 'transfer' }
        const out = (await DataServiceAdmin.applyInventoryTransaction(tx, { ...base, transaction_type: 'transfer_out', quantity: -q, warehouse_id: from, lot_id: l.lot_id ?? null, serial_numbers: l.serial_numbers ?? null } as never)) as Row | null
        const lots: Row[] = out?.lots ?? []
        if (out?.serials?.length) {
          await DataServiceAdmin.applyInventoryTransaction(tx, { ...base, transaction_type: 'transfer_in', quantity: q, warehouse_id: to, serial_numbers: out.serials } as never)
        } else if (lots.length) {
          for (const lot of lots) await DataServiceAdmin.applyInventoryTransaction(tx, { ...base, transaction_type: 'transfer_in', quantity: Math.abs(Number(lot.quantity)), warehouse_id: to, lot_number: lot.lot_number, expiry_date: lot.expiry_date } as never)
        } else {
          await DataServiceAdmin.applyInventoryTransaction(tx, { ...base, transaction_type: 'transfer_in', quantity: q, warehouse_id: to } as never)
        }
      }
      return { reference }
    })
  }

  static getAllLevels(org: string) {
    return getSql()`
      SELECT l.item_id, l.warehouse_id, l.quantity::float
      FROM public.stock_levels l JOIN public.warehouses w ON w.id = l.warehouse_id
      WHERE w.organization_id = ${org}::uuid AND l.quantity <> 0
    `
  }

  static async getItemDetail(org: string, itemId: number) {
    const sql = getSql()
    const [item] = (await sql`
      SELECT i.*, i.quantity_available::float AS quantity_available, i.average_unit_cost::float AS average_unit_cost, i.total_value::float AS total_value,
             i.reorder_point::float AS reorder_point, i.reorder_quantity::float AS reorder_quantity, i.selling_price::float AS selling_price,
             c.name AS category_name, s.name AS supplier_name
      FROM public.inventory_items i
      LEFT JOIN public.inventory_categories c ON c.id = i.category_id
      LEFT JOIN public.suppliers s ON s.id = i.preferred_supplier_id
      WHERE i.id = ${itemId} AND i.organization_id = ${org}::uuid
    `) as Row[]
    if (!item) throw new Error('Item not found.')
    const levels = await sql`SELECT l.warehouse_id, w.name AS warehouse_name, l.quantity::float FROM public.stock_levels l JOIN public.warehouses w ON w.id = l.warehouse_id WHERE l.item_id = ${itemId} AND l.quantity <> 0 ORDER BY w.name`
    const lots = (await sql`
      SELECT l.id, l.lot_number, l.expiry_date::text AS expiry_date, l.quantity::float, w.name AS warehouse_name, l.warehouse_id
      FROM public.stock_lots l JOIN public.warehouses w ON w.id = l.warehouse_id
      WHERE l.item_id = ${itemId} AND l.quantity > 0 ORDER BY l.expiry_date NULLS LAST, l.id
    `) as Row[]
    const [order] = (await sql`
      SELECT COALESCE(SUM((pl.quantity - pl.quantity_received) * pl.unit_factor), 0)::float AS on_order
      FROM public.purchase_order_lines pl JOIN public.purchase_orders p ON p.id = pl.purchase_order_id
      WHERE pl.item_id = ${itemId} AND p.status IN ('approved', 'partial')
    `) as Row[]
    const units = await this.listUnits(org, itemId)
    const serials = item.track_serials ? await sql`
      SELECT s.id, s.serial_number, w.name AS warehouse_name FROM public.stock_serials s LEFT JOIN public.warehouses w ON w.id = s.warehouse_id
      WHERE s.item_id = ${itemId} AND s.in_stock ORDER BY s.id LIMIT 1000
    ` : []
    return { ...item, levels, lots: lots.map((l) => ({ ...l, status: expiryStatus(l.expiry_date, today()) })), on_order: Number(order.on_order), units, serials }
  }

  /** Every movement of one item with a running balance, newest first. */
  static async getStockCard(org: string, itemId: number, warehouseId?: number | null) {
    const rows = (await getSql()`
      SELECT t.id, t.transaction_date::text AS date, t.transaction_type, t.quantity::float, t.unit_cost::float, t.total_cost::float, t.reference, t.description, t.journal_entry_id, w.name AS warehouse_name,
             (SELECT string_agg(s.lot_number, ', ') FROM public.stock_lot_movements m JOIN public.stock_lots s ON s.id = m.lot_id WHERE m.transaction_id = t.id) AS lots,
             (SELECT string_agg(s.serial_number, ', ') FROM public.stock_serial_movements m JOIN public.stock_serials s ON s.id = m.serial_id WHERE m.transaction_id = t.id) AS serials
      FROM public.inventory_transactions t LEFT JOIN public.warehouses w ON w.id = t.warehouse_id
      WHERE t.organization_id = ${org}::uuid AND t.item_id = ${itemId} AND (${warehouseId ?? null}::bigint IS NULL OR t.warehouse_id = ${warehouseId ?? null}::bigint)
      ORDER BY t.transaction_date, t.id
    `) as Row[]
    let balance = 0
    const withBalance = rows.map((r) => {
      balance = quantity(balance + Number(r.quantity))
      return { ...r, balance }
    })
    return withBalance.reverse().slice(0, 300)
  }

  static async saveItemDetails(org: string, itemId: number, form: { barcode?: string | null; selling_price?: number | null; income_account_id?: number | null; preferred_supplier_id?: number | null; lead_time_days?: number | null; track_lots?: boolean; track_serials?: boolean }) {
    await getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const [i] = (await tx`SELECT id, sku, name, track_lots, track_serials FROM public.inventory_items WHERE id = ${itemId} AND organization_id = ${org}::uuid FOR UPDATE`) as Row[]
      if (!i) throw new Error('Item not found.')
      const barcode = text(form.barcode)
      if (barcode) {
        const [used] = (await tx`SELECT name FROM public.inventory_items WHERE organization_id = ${org}::uuid AND barcode = ${barcode} AND id <> ${itemId} LIMIT 1`) as Row[]
        if (used) throw new Error(`That barcode is already on ${used.name}.`)
      }
      const track = form.track_lots ?? i.track_lots
      const serials = form.track_serials ?? i.track_serials
      if (track && serials) throw new Error('Track batches or serial numbers, not both.')
      // Stock already on hand needs numbers too, so serials and warehouse totals agree from the moment tracking starts.
      if (serials && !i.track_serials) {
        const held = (await tx`SELECT warehouse_id, quantity::float AS quantity FROM public.stock_levels WHERE item_id = ${itemId} AND quantity > 0 ORDER BY warehouse_id`) as Row[]
        for (const l of held) {
          if (!Number.isInteger(Number(l.quantity))) throw new Error(`${i.name} has part units in stock, so it can't be tracked by serial number.`)
          for (const number of await generateSerials(tx, itemId, i.sku, Number(l.quantity))) await tx`INSERT INTO public.stock_serials (item_id, warehouse_id, serial_number) VALUES (${itemId}, ${l.warehouse_id}, ${number})`
        }
      }
      if (!serials && i.track_serials) {
        const [held] = (await tx`SELECT COUNT(*)::int AS n FROM public.stock_serials WHERE item_id = ${itemId} AND in_stock`) as Row[]
        if (Number(held.n) > 0) throw new Error('This item still has serial-numbered stock, so serial tracking stays on.')
      }
      // Stock already on hand needs a batch, so batch totals and warehouse totals agree from the moment tracking starts.
      if (track && !i.track_lots) {
        await tx`
          INSERT INTO public.stock_lots (item_id, warehouse_id, lot_number, quantity)
          SELECT item_id, warehouse_id, 'OPENING', quantity FROM public.stock_levels WHERE item_id = ${itemId} AND quantity > 0
          ON CONFLICT (item_id, warehouse_id, lot_number) DO NOTHING
        `
      }
      if (!track && i.track_lots) {
        const [held] = (await tx`SELECT COALESCE(SUM(quantity), 0)::float AS q FROM public.stock_lots WHERE item_id = ${itemId}`) as Row[]
        if (Number(held.q) > 0) throw new Error('This item still has stock in batches, so batch tracking stays on.')
      }
      if (form.income_account_id) {
        const [a] = (await tx`SELECT id FROM public.accounts WHERE id = ${form.income_account_id} AND organization_id = ${org}::uuid`) as Row[]
        if (!a) throw new Error('Account not found.')
      }
      if (form.preferred_supplier_id) {
        const [s] = (await tx`SELECT id FROM public.suppliers WHERE id = ${form.preferred_supplier_id} AND organization_id = ${org}::uuid`) as Row[]
        if (!s) throw new Error('Supplier not found.')
      }
      const days = form.lead_time_days == null ? 14 : Number(form.lead_time_days)
      if (!Number.isFinite(days) || days < 0 || days > 730) throw new Error('Lead time must be between 0 and 730 days.')
      await tx`
        UPDATE public.inventory_items
        SET barcode = ${barcode}, selling_price = ${form.selling_price ?? null}, income_account_id = ${form.income_account_id ?? null}, preferred_supplier_id = ${form.preferred_supplier_id ?? null}, lead_time_days = ${Math.round(days)}, track_lots = ${track}, track_serials = ${serials}, updated_at = now()
        WHERE id = ${itemId}
      `
    })
  }

  /** Adds or updates items by SKU. Quantities aren't imported: opening stock needs an entry, so it's recorded as a movement. */
  static async importItems(org: string, rows: { sku?: string; name?: string; category?: string; unit?: string; reorder_point?: string; reorder_quantity?: string; barcode?: string; selling_price?: string }[]) {
    if (!Array.isArray(rows) || !rows.length) throw new Error('No items found in the file.')
    if (rows.length > 5000) throw new Error('Import up to 5,000 items at a time.')
    const user = acting()
    return getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const cats = (await tx`SELECT id, name FROM public.inventory_categories WHERE organization_id = ${org}::uuid`) as Row[]
      const problems: string[] = []
      const number = (v?: string) => { const n = Number(String(v ?? '').replace(/,/g, '')); return v && Number.isFinite(n) && n >= 0 ? n : 0 }
      const clean = rows.flatMap((r, i) => {
        const sku = text(r.sku), name = text(r.name)
        const cat = cats.find((c) => String(c.name).toLowerCase() === String(r.category ?? '').trim().toLowerCase())
        if (!sku || !name) { problems.push(`Line ${i + 2}: SKU and name are required.`); return [] }
        if (!cat) { problems.push(`Line ${i + 2}: no category called "${r.category ?? ''}".`); return [] }
        return [{ sku, name, category_id: Number(cat.id), unit: text(r.unit) ?? 'pcs', reorder_point: number(r.reorder_point), reorder_quantity: number(r.reorder_quantity), barcode: text(r.barcode), selling_price: r.selling_price ? number(r.selling_price) : null }]
      })
      if (problems.length) throw new Error(problems.slice(0, 5).join(' '))
      let added = 0, updated = 0
      for (const r of clean) {
        const [row] = (await tx`
          INSERT INTO public.inventory_items (organization_id, category_id, sku, name, unit_of_measure, reorder_point, reorder_quantity, barcode, selling_price, created_by, costing_method)
          VALUES (${org}::uuid, ${r.category_id}, ${r.sku}, ${r.name}, ${r.unit}, ${r.reorder_point}, ${r.reorder_quantity}, ${r.barcode}, ${r.selling_price}, ${user}::uuid, COALESCE((SELECT default_costing_method FROM public.inventory_settings WHERE organization_id = ${org}::uuid), 'average'))
          ON CONFLICT (organization_id, sku) DO UPDATE SET name = EXCLUDED.name, category_id = EXCLUDED.category_id, unit_of_measure = EXCLUDED.unit_of_measure, reorder_point = EXCLUDED.reorder_point, reorder_quantity = EXCLUDED.reorder_quantity, barcode = COALESCE(EXCLUDED.barcode, public.inventory_items.barcode), selling_price = COALESCE(EXCLUDED.selling_price, public.inventory_items.selling_price), updated_at = now()
          RETURNING (xmax = 0) AS inserted
        `) as Row[]
        if (row.inserted) added++
        else updated++
      }
      return { added, updated }
    })
  }

  // ---- Units ----

  static async listUnits(org: string, itemId: number) {
    return getSql()`
      SELECT u.id, u.item_id, u.name, u.factor::float AS factor FROM public.item_units u JOIN public.inventory_items i ON i.id = u.item_id
      WHERE u.item_id = ${itemId} AND i.organization_id = ${org}::uuid ORDER BY u.factor
    `
  }

  static getAllUnits(org: string) {
    return getSql()`
      SELECT u.id, u.item_id, u.name, u.factor::float AS factor FROM public.item_units u JOIN public.inventory_items i ON i.id = u.item_id
      WHERE i.organization_id = ${org}::uuid ORDER BY u.item_id, u.factor
    `
  }

  /** 1 of this unit = factor of the item's own unit. Past orders and invoices keep the factor they used. */
  static async saveUnit(org: string, form: { id?: number; item_id: number; name: string; factor: number }) {
    const name = text(form.name)
    const factor = Number(form.factor)
    if (!name) throw new Error('Name the unit.')
    if (!Number.isFinite(factor) || factor <= 0) throw new Error('Say how many of the base unit this holds.')
    const sql = getSql()
    const [item] = (await sql`SELECT unit_of_measure FROM public.inventory_items WHERE id = ${form.item_id} AND organization_id = ${org}::uuid`) as Row[]
    if (!item) throw new Error('Item not found.')
    if (String(item.unit_of_measure).toLowerCase() === name.toLowerCase()) throw new Error(`${name} is already this item's base unit.`)
    const [same] = (await sql`SELECT id FROM public.item_units WHERE item_id = ${form.item_id} AND lower(name) = lower(${name}) AND id <> ${form.id ?? 0}`) as Row[]
    if (same) throw new Error(`This item already has a unit called ${name}.`)
    const rows = form.id
      ? await sql`UPDATE public.item_units SET name = ${name}, factor = ${factor} WHERE id = ${form.id} AND item_id = ${form.item_id} RETURNING id`
      : await sql`INSERT INTO public.item_units (item_id, name, factor) VALUES (${form.item_id}, ${name}, ${factor}) RETURNING id`
    if (!rows[0]) throw new Error('Unit not found.')
    return { id: Number(rows[0].id) }
  }

  static async deleteUnit(org: string, id: number) {
    await getSql()`DELETE FROM public.item_units u USING public.inventory_items i WHERE u.id = ${id} AND i.id = u.item_id AND i.organization_id = ${org}::uuid`
  }

  // ---- Serial numbers ----

  /** Finds a unit by its number, across every item, with everything that happened to it. */
  static async findSerial(org: string, number: string) {
    const n = text(number)
    if (!n) return []
    const sql = getSql()
    const units = (await sql`
      SELECT s.id, s.serial_number, s.in_stock, s.item_id, i.sku, i.name AS item_name, w.name AS warehouse_name
      FROM public.stock_serials s JOIN public.inventory_items i ON i.id = s.item_id LEFT JOIN public.warehouses w ON w.id = s.warehouse_id
      WHERE i.organization_id = ${org}::uuid AND lower(s.serial_number) = lower(${n}) LIMIT 20
    `) as Row[]
    const out = []
    for (const u of units) {
      const history = await sql`
        SELECT t.transaction_date::text AS date, t.transaction_type, t.reference, t.description, w.name AS warehouse_name
        FROM public.stock_serial_movements m JOIN public.inventory_transactions t ON t.id = m.transaction_id LEFT JOIN public.warehouses w ON w.id = t.warehouse_id
        WHERE m.serial_id = ${u.id} ORDER BY t.transaction_date DESC, t.id DESC
      `
      out.push({ ...u, history })
    }
    return out
  }

  // ---- Costing method ----

  /** Switching doesn't change what stock is worth today, only how later issues are costed. */
  static async setItemCosting(org: string, itemId: number, method: 'average' | 'fifo') {
    if (method !== 'average' && method !== 'fifo') throw new Error('Unknown costing method.')
    await getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const [i] = (await tx`SELECT id, costing_method, quantity_available::float AS q, total_value::float AS v FROM public.inventory_items WHERE id = ${itemId} AND organization_id = ${org}::uuid FOR UPDATE`) as Row[]
      if (!i) throw new Error('Item not found.')
      if (i.costing_method === method) return
      await resetLayers(tx, itemId, method, Number(i.q), Number(i.v), today())
      await tx`UPDATE public.inventory_items SET costing_method = ${method}, average_unit_cost = CASE WHEN quantity_available > 0 THEN total_value / quantity_available ELSE average_unit_cost END WHERE id = ${itemId}`
    })
  }

  /** The method new items start with, and optionally a switch for every item you have now. */
  static async setDefaultCosting(org: string, form: { method: 'average' | 'fifo'; apply_to_all?: boolean }) {
    if (form.method !== 'average' && form.method !== 'fifo') throw new Error('Unknown costing method.')
    await getSql()`INSERT INTO public.inventory_settings (organization_id, default_costing_method) VALUES (${org}::uuid, ${form.method}) ON CONFLICT (organization_id) DO UPDATE SET default_costing_method = EXCLUDED.default_costing_method`
    if (form.apply_to_all) {
      const items = (await getSql()`SELECT id FROM public.inventory_items WHERE organization_id = ${org}::uuid AND costing_method <> ${form.method} ORDER BY id`) as Row[]
      for (const i of items) await this.setItemCosting(org, Number(i.id), form.method)
    }
    return this.getSettings(org)
  }

  static async getSettings(org: string) {
    const [s] = (await getSql()`
      SELECT s.grni_account_id, s.default_costing_method, a.code AS grni_code, a.name AS grni_name
      FROM public.inventory_settings s LEFT JOIN public.accounts a ON a.id = s.grni_account_id
      WHERE s.organization_id = ${org}::uuid
    `) as Row[]
    return { grni_account_id: s?.grni_account_id ? Number(s.grni_account_id) : null, grni_code: s?.grni_code ?? null, grni_name: s?.grni_name ?? null, default_costing_method: (s?.default_costing_method ?? 'average') as 'average' | 'fifo' }
  }

  static async saveSettings(org: string, form: { grni_account_id: number | null }) {
    const sql = getSql()
    if (form.grni_account_id) {
      const [a] = (await sql`SELECT is_postable, account_type::text AS account_type FROM public.accounts WHERE id = ${form.grni_account_id} AND organization_id = ${org}::uuid`) as Row[]
      if (!a) throw new Error('Account not found.')
      if (!a.is_postable) throw new Error('Choose an account that can be posted to.')
      if (a.account_type !== 'liability') throw new Error('This should be a liability account, since it tracks what you owe.')
    }
    await sql`INSERT INTO public.inventory_settings (organization_id, grni_account_id) VALUES (${org}::uuid, ${form.grni_account_id}) ON CONFLICT (organization_id) DO UPDATE SET grni_account_id = EXCLUDED.grni_account_id`
    return this.getSettings(org)
  }

  /** Creates the holding account for goods received before their bill arrives, for people who'd rather not choose one. */
  static async createGrniAccount(org: string) {
    const account = await AccountServiceAdmin.createAccount({ organization_id: org, name: 'Goods received, not billed', account_type: 'liability', description: 'Stock received from suppliers, waiting for their bill.', report_category: 'current_liability', is_postable: true, is_active: true, parent_id: null, group: null, created_by: null } as never)
    return this.saveSettings(org, { grni_account_id: Number(account.id) })
  }
}

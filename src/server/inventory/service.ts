import { getSql } from '@/server/pg'
import { DataServiceAdmin } from '@/server/data-service-admin'
import { nextNumber } from '@/server/numbering'
import { netAmountForAccountType } from '@/server/data/ledger-sql'
import { InventoryAssembly } from '@/server/inventory/assembly'
import { CostPlanner } from '@/server/inventory/costing'
import { acting, requireDate, text, today, type Pg, type Row } from '@/server/inventory/items'
import { abcAnalysis, countAdjustments, expiryStatus, money, reorderLine } from '@/server/inventory/rules'

/** Stock counts, the reorder planner and stock analysis, on top of items and purchasing. */
export class InventoryServiceAdmin extends InventoryAssembly {
  static listStockCounts(org: string) {
    return getSql()`
      SELECT c.id, c.number, c.status, c.count_date::text AS count_date, w.name AS warehouse_name,
        COUNT(l.id)::int AS lines, COUNT(l.counted)::int AS counted, COUNT(l.id) FILTER (WHERE l.counted IS NOT NULL AND l.counted <> l.expected)::int AS differences
      FROM public.stock_counts c JOIN public.warehouses w ON w.id = c.warehouse_id LEFT JOIN public.stock_count_lines l ON l.stock_count_id = c.id
      WHERE c.organization_id = ${org}::uuid GROUP BY c.id, w.name ORDER BY c.count_date DESC, c.id DESC LIMIT 200
    `
  }

  static async getStockCount(org: string, id: number) {
    const sql = getSql()
    const [c] = (await sql`SELECT c.*, c.count_date::text AS count_date, w.name AS warehouse_name FROM public.stock_counts c JOIN public.warehouses w ON w.id = c.warehouse_id WHERE c.id = ${id} AND c.organization_id = ${org}::uuid`) as Row[]
    if (!c) throw new Error('Stock count not found.')
    const lines = await sql`
      SELECT l.id, l.item_id, l.expected::float, l.counted::float, i.name AS item_name, i.sku, i.barcode, i.unit_of_measure, i.average_unit_cost::float AS average_unit_cost, COALESCE(s.quantity, 0)::float AS current
      FROM public.stock_count_lines l JOIN public.inventory_items i ON i.id = l.item_id
      LEFT JOIN public.stock_levels s ON s.item_id = l.item_id AND s.warehouse_id = ${c.warehouse_id}
      WHERE l.stock_count_id = ${id} ORDER BY i.name
    `
    return { ...c, lines }
  }

  /** Starts a count with what the system expects in that warehouse today. Optionally one category, for a cycle count. */
  static async createStockCount(org: string, form: { warehouse_id?: number | null; count_date: string; category_id?: number | null; notes?: string | null }) {
    const date = requireDate(form.count_date)
    return getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const warehouse = await this.requireWarehouse(tx, org, form.warehouse_id)
      const number = await nextNumber(tx, org, 'SC', 'public.stock_counts', 'number')
      const [c] = (await tx`INSERT INTO public.stock_counts (organization_id, number, warehouse_id, count_date, notes, created_by) VALUES (${org}::uuid, ${number}, ${warehouse}, ${date}::date, ${text(form.notes)}, ${acting()}::uuid) RETURNING id`) as Row[]
      const added = await tx`
        INSERT INTO public.stock_count_lines (stock_count_id, item_id, expected)
        SELECT ${c.id}, i.id, COALESCE(s.quantity, 0)
        FROM public.inventory_items i LEFT JOIN public.stock_levels s ON s.item_id = i.id AND s.warehouse_id = ${warehouse}
        WHERE i.organization_id = ${org}::uuid AND i.is_active AND (${form.category_id ?? null}::bigint IS NULL OR i.category_id = ${form.category_id ?? null}::bigint)
        RETURNING id
      `
      if (!added.length) throw new Error('There are no items to count.')
      return { id: Number(c.id) }
    })
  }

  static async saveStockCountLines(org: string, id: number, lines: { line_id: number; counted: number | null }[]) {
    await getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const [c] = (await tx`SELECT status FROM public.stock_counts WHERE id = ${id} AND organization_id = ${org}::uuid FOR UPDATE`) as Row[]
      if (!c) throw new Error('Stock count not found.')
      if (c.status !== 'open') throw new Error('This count is finished.')
      for (const l of lines) {
        const counted = l.counted === null || l.counted === undefined ? null : Number(l.counted)
        if (counted !== null && (!Number.isFinite(counted) || counted < 0)) throw new Error("A count can't be negative.")
        await tx`UPDATE public.stock_count_lines SET counted = ${counted} WHERE id = ${l.line_id} AND stock_count_id = ${id}`
      }
    })
  }

  static async cancelStockCount(org: string, id: number) {
    const rows = await getSql()`UPDATE public.stock_counts SET status = 'cancelled' WHERE id = ${id} AND organization_id = ${org}::uuid AND status = 'open' RETURNING id`
    if (!rows.length) throw new Error('This count is already finished.')
  }

  /** Corrects stock to what was counted and records the value difference, together. */
  static async postStockCount(org: string, id: number) {
    const user = acting()
    await getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const [c] = (await tx`SELECT *, count_date::text AS date_text FROM public.stock_counts WHERE id = ${id} AND organization_id = ${org}::uuid FOR UPDATE`) as Row[]
      if (!c) throw new Error('Stock count not found.')
      if (c.status !== 'open') throw new Error('This count is finished.')
      const lines = (await tx`
        SELECT l.item_id, l.counted::float AS counted, COALESCE(s.quantity, 0)::float AS current, i.average_unit_cost::float AS average_unit_cost, ct.inventory_account_id, ct.expense_account_id,
               i.costing_method, i.quantity_available::float AS on_hand, i.total_value::float AS value
        FROM public.stock_count_lines l
        JOIN public.inventory_items i ON i.id = l.item_id
        JOIN public.inventory_categories ct ON ct.id = i.category_id
        LEFT JOIN public.stock_levels s ON s.item_id = l.item_id AND s.warehouse_id = ${c.warehouse_id}
        WHERE l.stock_count_id = ${id} ORDER BY l.item_id
        FOR UPDATE OF i
      `) as Row[]
      if (!lines.some((l) => l.counted !== null)) throw new Error('Enter at least one count first.')
      const planner = new CostPlanner(tx)
      const costed = []
      for (const l of lines) {
        const loss = l.counted === null ? 0 : Number(l.current) - Number(l.counted)
        costed.push({ item_id: Number(l.item_id), counted: l.counted === null ? null : Number(l.counted), current: Number(l.current), average_unit_cost: Number(l.average_unit_cost), inventory_account_id: Number(l.inventory_account_id), adjustment_account_id: Number(l.expense_account_id), loss_value: loss > 0 ? await planner.cost({ id: Number(l.item_id), method: l.costing_method, on_hand: Number(l.on_hand), value: Number(l.value), average: Number(l.average_unit_cost) }, loss) : undefined })
      }
      const plan = countAdjustments(costed)
      let entry: number | null = null
      if (plan.entry.length) {
        const created = await DataServiceAdmin.insertJournalEntry(tx,
          { organization_id: org, entry_number: `JE-${c.number}`, entry_date: c.date_text, description: `Stock count ${c.number}`, reference: c.number, total_amount: 0, is_posted: true, created_by: user, posted_by: user, posted_at: new Date().toISOString() } as never,
          plan.entry.map((l, i) => ({ account_id: l.account_id, description: l.description, debit_amount: l.debit, credit_amount: l.credit, line_order: i + 1 })) as never)
        entry = Number(created?.id)
      }
      for (const m of plan.moves) {
        await DataServiceAdmin.applyInventoryTransaction(tx, {
          organization_id: org, item_id: m.item_id, transaction_type: 'adjustment', quantity: m.difference, unit_cost: null, total_cost: null, journal_entry_id: m.value > 0 ? entry : null,
          reference: c.number, description: 'Stock count', transaction_date: c.date_text, created_by: user, warehouse_id: Number(c.warehouse_id), lot_number: `COUNT-${c.number}`, source_type: 'stock_count', source_id: id,
        } as never)
      }
      await tx`UPDATE public.stock_counts SET status = 'posted', journal_entry_id = ${entry}, posted_by = ${user}::uuid WHERE id = ${id}`
    })
    return this.getStockCount(org, id)
  }

  static async getReorderPlan(org: string) {
    const rows = (await getSql()`
      SELECT i.id AS item_id, i.sku, i.name, i.unit_of_measure, i.average_unit_cost::float AS unit_cost, i.quantity_available::float AS on_hand, i.reorder_point::float AS reorder_point, i.reorder_quantity::float AS reorder_quantity, i.lead_time_days, i.preferred_supplier_id, s.name AS supplier_name,
        COALESCE((SELECT SUM((pl.quantity - pl.quantity_received) * pl.unit_factor) FROM public.purchase_order_lines pl JOIN public.purchase_orders p ON p.id = pl.purchase_order_id WHERE pl.item_id = i.id AND p.status IN ('approved', 'partial')), 0)::float AS on_order,
        COALESCE((SELECT SUM(ABS(t.quantity)) FROM public.inventory_transactions t WHERE t.item_id = i.id AND t.transaction_type = 'out' AND t.transaction_date >= CURRENT_DATE - 90), 0)::float AS used_90_days
      FROM public.inventory_items i LEFT JOIN public.suppliers s ON s.id = i.preferred_supplier_id
      WHERE i.organization_id = ${org}::uuid AND i.is_active ORDER BY i.name
    `) as Row[]
    return rows.map((r) => ({ ...r, ...reorderLine({ item_id: Number(r.item_id), on_hand: Number(r.on_hand), on_order: Number(r.on_order), used_90_days: Number(r.used_90_days), reorder_point: Number(r.reorder_point), reorder_quantity: Number(r.reorder_quantity), lead_time_days: Number(r.lead_time_days) }) }))
  }

  /** Drafts one purchase order per supplier from the chosen lines. A person still approves each one. */
  static async createOrdersFromPlan(org: string, form: { warehouse_id?: number | null; lines: { item_id: number; quantity: number }[] }) {
    if (!form.lines?.length) throw new Error('Choose at least one item.')
    const ids = form.lines.map((l) => Number(l.item_id))
    const items = (await getSql()`
      SELECT i.id, i.average_unit_cost::float AS cost, i.preferred_supplier_id, s.name AS supplier_name
      FROM public.inventory_items i LEFT JOIN public.suppliers s ON s.id = i.preferred_supplier_id
      WHERE i.organization_id = ${org}::uuid AND i.id = ANY(${ids}::bigint[])
    `) as Row[]
    const groups: { supplier_id: number | null; supplier_name: string; lines: { item_id: number; quantity: number; unit_cost: number }[] }[] = []
    form.lines.forEach((l) => {
      const item = items.find((x) => Number(x.id) === Number(l.item_id))
      if (!item) throw new Error('Item not found.')
      const supplier = item.preferred_supplier_id ? Number(item.preferred_supplier_id) : null
      let g = groups.find((x) => x.supplier_id === supplier)
      if (!g) { g = { supplier_id: supplier, supplier_name: item.supplier_name ?? 'Supplier to confirm', lines: [] }; groups.push(g) }
      g.lines.push({ item_id: Number(l.item_id), quantity: Number(l.quantity), unit_cost: Number(item.cost) })
    })
    const orders: number[] = []
    for (const g of groups) orders.push((await this.savePurchaseOrder(org, { supplier_id: g.supplier_id, supplier_name: g.supplier_name, warehouse_id: form.warehouse_id, order_date: today(), lines: g.lines })).id)
    return { orders }
  }

  /** Where stock value sits, what's moving and what isn't, and what expires soon. */
  static async getAnalysis(org: string) {
    const sql = getSql()
    const items = (await sql`
      SELECT i.id AS item_id, i.sku, i.name, i.unit_of_measure, i.quantity_available::float AS on_hand, i.total_value::float AS value, c.name AS category_name,
        COALESCE((SELECT SUM(COALESCE(t.total_cost, ABS(t.quantity) * i.average_unit_cost)) FROM public.inventory_transactions t WHERE t.item_id = i.id AND t.transaction_type = 'out' AND t.transaction_date >= CURRENT_DATE - 365), 0)::float AS usage_value,
        (SELECT MAX(t.transaction_date)::text FROM public.inventory_transactions t WHERE t.item_id = i.id AND t.transaction_type = 'out') AS last_used
      FROM public.inventory_items i LEFT JOIN public.inventory_categories c ON c.id = i.category_id
      WHERE i.organization_id = ${org}::uuid AND i.is_active
    `) as Row[]
    const now = today()
    const idle = (d: string | null) => (d ? Math.floor((Date.parse(`${now}T00:00:00Z`) - Date.parse(`${d}T00:00:00Z`)) / 86400000) : null)
    const total = money(items.reduce((s, i) => s + Number(i.value), 0))
    const used = money(items.reduce((s, i) => s + Number(i.usage_value), 0))
    const byCategory: { category_name: string; value: number; items: number }[] = []
    items.forEach((i) => {
      const name = i.category_name ?? 'No category'
      const c = byCategory.find((x) => x.category_name === name)
      if (c) { c.value = money(c.value + Number(i.value)); c.items++ } else byCategory.push({ category_name: name, value: money(Number(i.value)), items: 1 })
    })
    const expiring = (await sql`
      SELECT l.id, l.lot_number, l.expiry_date::text AS expiry_date, l.quantity::float, i.name AS item_name, i.id AS item_id, w.name AS warehouse_name, (l.quantity * i.average_unit_cost)::float AS value
      FROM public.stock_lots l JOIN public.inventory_items i ON i.id = l.item_id JOIN public.warehouses w ON w.id = l.warehouse_id
      WHERE i.organization_id = ${org}::uuid AND l.quantity > 0 AND l.expiry_date IS NOT NULL AND l.expiry_date <= CURRENT_DATE + 90
      ORDER BY l.expiry_date LIMIT 100
    `) as Row[]
    return {
      total_value: total,
      usage_12_months: used,
      turnover: total > 0 ? Math.round((used / total) * 10) / 10 : null,
      by_category: byCategory.sort((a, b) => b.value - a.value),
      slow_moving: items.filter((i) => Number(i.on_hand) > 0 && (idle(i.last_used) === null || (idle(i.last_used) as number) >= 90)).map((i) => ({ item_id: i.item_id, sku: i.sku, name: i.name, on_hand: Number(i.on_hand), unit_of_measure: i.unit_of_measure, value: Number(i.value), last_used: i.last_used, days_idle: idle(i.last_used) })).sort((a, b) => b.value - a.value),
      abc: abcAnalysis(items.map((i) => ({ item_id: Number(i.item_id), sku: i.sku as string, name: i.name as string, usage_value: Number(i.usage_value) }))),
      expiring: expiring.map((l) => ({ ...l, status: expiryStatus(l.expiry_date, now) })),
    }
  }

  /** Stock value against the inventory accounts in the books. They should agree, so a gap is worth looking into. */
  static async getBooksCheck(org: string) {
    const sql = getSql()
    const stock = (await sql`
      SELECT c.inventory_account_id AS account_id, a.code, a.name, a.account_type::text AS account_type, SUM(i.total_value)::float AS stock_value
      FROM public.inventory_items i JOIN public.inventory_categories c ON c.id = i.category_id JOIN public.accounts a ON a.id = c.inventory_account_id
      WHERE i.organization_id = ${org}::uuid GROUP BY 1, 2, 3, 4 ORDER BY a.code
    `) as Row[]
    const rows = []
    for (const s of stock) {
      const [b] = (await sql`
        SELECT COALESCE(SUM(l.debit_amount), 0)::float AS dr, COALESCE(SUM(l.credit_amount), 0)::float AS cr
        FROM public.journal_entry_lines l JOIN public.journal_entries e ON e.id = l.journal_entry_id
        WHERE l.account_id = ${s.account_id} AND e.organization_id = ${org}::uuid
      `) as Row[]
      const book = money(netAmountForAccountType(Number(b.dr), Number(b.cr), s.account_type))
      rows.push({ account_id: Number(s.account_id), code: s.code, name: s.name, stock_value: money(Number(s.stock_value)), book_value: book, difference: money(Number(s.stock_value) - book) })
    }
    return { rows, agrees: rows.every((r) => Math.abs(r.difference) < 0.05) }
  }
}

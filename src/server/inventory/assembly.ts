import { getSql } from '@/server/pg'
import { DataServiceAdmin } from '@/server/data-service-admin'
import { nextNumber } from '@/server/numbering'
import { reversalLines } from '@/server/books/rules'
import { CostPlanner } from '@/server/inventory/costing'
import { InventoryPurchasing } from '@/server/inventory/purchasing'
import { acting, requireDate, text, today, type Pg, type Row } from '@/server/inventory/items'
import { assemblyEntry, findBomCycle, money, quantity as qty, type EntryLine } from '@/server/inventory/rules'

export type BomForm = { item_id: number; output_quantity?: number; notes?: string | null; lines: { item_id: number; quantity: number }[] }
export type BuildForm = { item_id: number; quantity: number; warehouse_id?: number | null; date: string; extra_cost?: number | null; extra_account_id?: number | null; lot_number?: string | null; expiry_date?: string | null; serial_numbers?: string[] | null }

const insertEntry = (tx: Pg, org: string, user: string, e: { number: string; date: string; description: string; reference: string }, lines: EntryLine[]) =>
  DataServiceAdmin.insertJournalEntry(tx,
    { organization_id: org, entry_number: e.number, entry_date: e.date, description: e.description, reference: e.reference, total_amount: 0, is_posted: true, created_by: user, posted_by: user, posted_at: new Date().toISOString() } as never,
    lines.map((l, i) => ({ account_id: l.account_id, description: l.description, debit_amount: l.debit, credit_amount: l.credit, line_order: i + 1 })) as never)

/** What an item is made of, and building it: parts go out and the finished item comes in at what they cost. */
export class InventoryAssembly extends InventoryPurchasing {
  static async listBoms(org: string) {
    const sql = getSql()
    const boms = (await sql`
      SELECT b.id, b.item_id, b.output_quantity::float AS output_quantity, b.notes, i.sku, i.name, i.unit_of_measure, i.quantity_available::float AS on_hand
      FROM public.boms b JOIN public.inventory_items i ON i.id = b.item_id
      WHERE b.organization_id = ${org}::uuid ORDER BY i.name
    `) as Row[]
    const lines = (await sql`
      SELECT l.id, l.bom_id, l.component_item_id AS item_id, l.quantity::float AS quantity, i.sku, i.name, i.unit_of_measure, i.quantity_available::float AS on_hand, i.average_unit_cost::float AS cost
      FROM public.bom_lines l JOIN public.boms b ON b.id = l.bom_id JOIN public.inventory_items i ON i.id = l.component_item_id
      WHERE b.organization_id = ${org}::uuid ORDER BY i.name
    `) as Row[]
    return boms.map((b) => {
      const parts = lines.filter((l) => Number(l.bom_id) === Number(b.id))
      const per = Number(b.output_quantity)
      return {
        ...b,
        lines: parts,
        cost_each: money(parts.reduce((s, l) => s + Number(l.quantity) * Number(l.cost), 0) / per),
        can_build: parts.length ? Math.floor(Math.min(...parts.map((l) => Number(l.on_hand) / (Number(l.quantity) / per))) + 1e-9) : 0,
      }
    })
  }

  static async saveBom(org: string, form: BomForm) {
    const output = Number(form.output_quantity ?? 1)
    if (!(output > 0)) throw new Error('Say how many one batch makes.')
    if (!form.lines?.length) throw new Error('Add at least one part.')
    return getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const itemId = Number(form.item_id)
      const ids = form.lines.map((l) => Number(l.item_id))
      const known = (await tx`SELECT id, name FROM public.inventory_items WHERE organization_id = ${org}::uuid AND id = ANY(${[itemId, ...ids]}::bigint[])`) as Row[]
      if (!known.some((k) => Number(k.id) === itemId)) throw new Error('Item not found.')
      const nameOf = (id: number) => String(known.find((k) => Number(k.id) === id)?.name ?? 'That item')
      form.lines.forEach((l) => {
        if (!known.some((k) => Number(k.id) === Number(l.item_id))) throw new Error('Choose an item for every part.')
        if (!(Number(l.quantity) > 0)) throw new Error('Quantities must be more than zero.')
      })
      if (Array.from(new Set(ids)).length !== ids.length) throw new Error('Each part can only be listed once.')
      await tx`SELECT pg_advisory_xact_lock(hashtext(${`${org}:bom`}))`
      const existing = (await tx`
        SELECT b.item_id, l.component_item_id FROM public.bom_lines l JOIN public.boms b ON b.id = l.bom_id
        WHERE b.organization_id = ${org}::uuid AND b.item_id <> ${itemId}
      `) as Row[]
      const cycle = findBomCycle(itemId, ids, existing.map((e) => ({ item_id: Number(e.item_id), component_id: Number(e.component_item_id) })))
      if (cycle !== null) throw new Error(cycle === itemId ? `${nameOf(itemId)} can't be a part of itself.` : `${nameOf(cycle)} is itself made using ${nameOf(itemId)}, so it can't be a part of it.`)
      const [bom] = (await tx`
        INSERT INTO public.boms (organization_id, item_id, output_quantity, notes, created_by)
        VALUES (${org}::uuid, ${itemId}, ${output}, ${text(form.notes)}, ${acting()}::uuid)
        ON CONFLICT (organization_id, item_id) DO UPDATE SET output_quantity = EXCLUDED.output_quantity, notes = EXCLUDED.notes, updated_at = now()
        RETURNING id
      `) as Row[]
      await tx`DELETE FROM public.bom_lines WHERE bom_id = ${bom.id}`
      for (const l of form.lines) await tx`INSERT INTO public.bom_lines (bom_id, component_item_id, quantity) VALUES (${bom.id}, ${Number(l.item_id)}, ${Number(l.quantity)})`
      return { id: Number(bom.id) }
    })
  }

  static async deleteBom(org: string, id: number) {
    const rows = await getSql()`DELETE FROM public.boms WHERE id = ${id} AND organization_id = ${org}::uuid RETURNING id`
    if (!rows.length) throw new Error('Not found.')
  }

  static listAssemblies(org: string) {
    return getSql()`
      SELECT a.id, a.number, a.status, a.item_id, a.quantity::float, a.build_date::text AS build_date, a.components_cost::float, a.extra_cost::float, a.journal_entry_id, i.sku, i.name, i.unit_of_measure, w.name AS warehouse_name
      FROM public.assemblies a JOIN public.inventory_items i ON i.id = a.item_id JOIN public.warehouses w ON w.id = a.warehouse_id
      WHERE a.organization_id = ${org}::uuid ORDER BY a.build_date DESC, a.id DESC LIMIT 300
    `
  }

  /** Builds finished stock. Parts and finished item move together with their entry, or not at all. */
  static async buildAssembly(org: string, form: BuildForm) {
    const date = requireDate(form.date)
    const made = Number(form.quantity)
    if (!(made > 0)) throw new Error('Say how many to build.')
    const extra = money(Number(form.extra_cost ?? 0))
    if (extra < 0) throw new Error("An extra cost can't be negative.")
    if (extra > 0 && !form.extra_account_id) throw new Error('Choose where the extra cost comes from.')
    const user = acting()
    return getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const [bom] = (await tx`SELECT id, output_quantity::float AS output_quantity FROM public.boms WHERE organization_id = ${org}::uuid AND item_id = ${form.item_id}`) as Row[]
      if (!bom) throw new Error('This item has no list of parts yet.')
      if (extra > 0) {
        const [a] = (await tx`SELECT is_postable FROM public.accounts WHERE id = ${form.extra_account_id ?? 0} AND organization_id = ${org}::uuid`) as Row[]
        if (!a?.is_postable) throw new Error('Choose an account that can be posted to.')
      }
      const warehouse = await this.requireWarehouse(tx, org, form.warehouse_id)
      const partRows = (await tx`SELECT component_item_id AS item_id, quantity::float AS quantity FROM public.bom_lines WHERE bom_id = ${bom.id} ORDER BY component_item_id`) as Row[]
      const ids = [Number(form.item_id), ...partRows.map((p) => Number(p.item_id))].sort((a, b) => a - b)
      // Always in the same order, so two builds can't lock each other out.
      const items = (await tx`
        SELECT i.id, i.name, i.costing_method, i.quantity_available::float AS on_hand, i.total_value::float AS value, i.average_unit_cost::float AS average, c.inventory_account_id
        FROM public.inventory_items i JOIN public.inventory_categories c ON c.id = i.category_id
        WHERE i.id = ANY(${ids}::bigint[]) ORDER BY i.id FOR UPDATE OF i
      `) as Row[]
      const find = (id: number) => items.find((i) => Number(i.id) === id) as Row
      const planner = new CostPlanner(tx)
      const parts = []
      for (const p of partRows) {
        const i = find(Number(p.item_id))
        const needed = qty((Number(p.quantity) * made) / Number(bom.output_quantity))
        const cost = await planner.cost({ id: Number(i.id), method: i.costing_method, on_hand: Number(i.on_hand), value: Number(i.value), average: Number(i.average) }, needed)
        parts.push({ item_id: Number(p.item_id), quantity: needed, cost, inventory_account_id: Number(i.inventory_account_id) })
      }
      const componentsCost = money(parts.reduce((s, p) => s + p.cost, 0))
      const total = money(componentsCost + extra)
      const number = await nextNumber(tx, org, 'AS', 'public.assemblies', 'number')
      const output = find(Number(form.item_id))
      const entry = total > 0 ? await insertEntry(tx, org, user, { number: `JE-${number}`, date, description: `Built ${made} ${output.name}`, reference: number }, assemblyEntry(Number(output.inventory_account_id), parts.map((p) => ({ inventory_account_id: p.inventory_account_id, amount: p.cost })), extra, form.extra_account_id ?? null)) : null
      const entryId = entry ? Number(entry.id) : null
      const [a] = (await tx`
        INSERT INTO public.assemblies (organization_id, number, item_id, warehouse_id, quantity, build_date, components_cost, extra_cost, extra_account_id, journal_entry_id, created_by)
        VALUES (${org}::uuid, ${number}, ${form.item_id}, ${warehouse}, ${made}, ${date}::date, ${componentsCost}, ${extra}, ${extra > 0 ? form.extra_account_id ?? null : null}, ${entryId}, ${user}::uuid) RETURNING id
      `) as Row[]
      const base = { organization_id: org, journal_entry_id: entryId, reference: number, description: `Build ${number}`, transaction_date: date, created_by: user, warehouse_id: warehouse, source_type: 'assembly', source_id: Number(a.id) }
      for (const p of parts) {
        const out = (await DataServiceAdmin.applyInventoryTransaction(tx, { ...base, item_id: p.item_id, transaction_type: 'out', quantity: -p.quantity, unit_cost: null, total_cost: p.cost } as never)) as Row
        await tx`INSERT INTO public.assembly_lines (assembly_id, item_id, quantity, cost, transaction_id) VALUES (${a.id}, ${p.item_id}, ${p.quantity}, ${p.cost}, ${out.id})`
      }
      const built = (await DataServiceAdmin.applyInventoryTransaction(tx, { ...base, item_id: Number(form.item_id), transaction_type: 'in', quantity: made, unit_cost: null, total_cost: total, lot_number: text(form.lot_number), expiry_date: form.expiry_date ?? null, serial_numbers: form.serial_numbers ?? null } as never)) as Row
      await tx`UPDATE public.assemblies SET transaction_id = ${built.id} WHERE id = ${a.id}`
      return { id: Number(a.id), number, total }
    })
  }

  /** Takes a build apart: the finished item goes out and its parts come back at the cost they left at. */
  static async reverseAssembly(org: string, id: number, form: { date?: string } = {}) {
    const date = form.date ? requireDate(form.date) : today()
    const user = acting()
    await getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const [a] = (await tx`SELECT *, build_date::text AS built_on FROM public.assemblies WHERE id = ${id} AND organization_id = ${org}::uuid FOR UPDATE`) as Row[]
      if (!a) throw new Error('Build not found.')
      if (a.status !== 'built') throw new Error('This build has already been undone.')
      const lines = (await tx`SELECT item_id, quantity::float AS quantity, cost::float AS cost, transaction_id FROM public.assembly_lines WHERE assembly_id = ${id} ORDER BY item_id`) as Row[]
      await tx`SELECT id FROM public.inventory_items WHERE id = ANY(${[Number(a.item_id), ...lines.map((l) => Number(l.item_id))]}::bigint[]) ORDER BY id FOR UPDATE`
      let reversal: number | null = null
      if (a.journal_entry_id) {
        const original = (await tx`SELECT account_id, description, debit_amount, credit_amount FROM public.journal_entry_lines WHERE journal_entry_id = ${a.journal_entry_id} ORDER BY line_order`) as Row[]
        const entry = await insertEntry(tx, org, user, { number: `REV-JE-${a.number}`, date, description: `Undo build ${a.number}`, reference: a.number }, reversalLines(original.map((l) => ({ account_id: Number(l.account_id), description: l.description, debit: Number(l.debit_amount), credit: Number(l.credit_amount) }))))
        reversal = Number(entry?.id)
        await tx`UPDATE public.journal_entries SET reverses_entry_id = ${a.journal_entry_id} WHERE id = ${reversal}`
      }
      const base = { organization_id: org, journal_entry_id: reversal, reference: a.number, description: `Undo build ${a.number}`, transaction_date: date, created_by: user, warehouse_id: Number(a.warehouse_id), source_type: 'assembly', source_id: id }
      await DataServiceAdmin.applyInventoryTransaction(tx, { ...base, item_id: Number(a.item_id), transaction_type: 'out', quantity: -Number(a.quantity), unit_cost: null, total_cost: money(Number(a.components_cost) + Number(a.extra_cost)), from_transaction_ids: a.transaction_id ? [Number(a.transaction_id)] : null } as never)
      for (const l of lines) await DataServiceAdmin.applyInventoryTransaction(tx, { ...base, item_id: Number(l.item_id), transaction_type: 'in', quantity: Number(l.quantity), unit_cost: null, total_cost: Number(l.cost), layer_date: a.built_on, from_transaction_ids: l.transaction_id ? [Number(l.transaction_id)] : null } as never)
      await tx`UPDATE public.assemblies SET status = 'reversed', reversal_entry_id = ${reversal} WHERE id = ${id}`
    })
  }
}

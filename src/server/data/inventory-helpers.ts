import { getSql } from '@/server/pg'
import type { Account, InventoryCategory, InventoryItem, InventoryTransaction } from '@/types'

type Pg = ReturnType<typeof getSql>

/** Neon/postgres.js often returns numeric columns as strings; normalize for the client. */
export function parseInventoryItemRow(i: InventoryItem): InventoryItem {
  return {
    ...i,
    id: Number(i.id),
    category_id: Number(i.category_id),
    quantity_in: Number(i.quantity_in) || 0,
    quantity_out: Number(i.quantity_out) || 0,
    quantity_available: Number(i.quantity_available) || 0,
    average_unit_cost: Number(i.average_unit_cost) || 0,
    total_value: Number(i.total_value) || 0,
    reorder_point: Number(i.reorder_point) || 0,
    reorder_quantity: Number(i.reorder_quantity) || 0,
  }
}

export function parseInventoryTransactionRow(t: InventoryTransaction): InventoryTransaction {
  return {
    ...t,
    id: Number(t.id),
    item_id: Number(t.item_id),
    quantity: Number(t.quantity) || 0,
    unit_cost: t.unit_cost != null ? Number(t.unit_cost) : null,
    total_cost: t.total_cost != null ? Number(t.total_cost) : null,
    journal_entry_id: t.journal_entry_id != null ? Number(t.journal_entry_id) : null,
  }
}

export async function attachCategoryAccounts(
  sql: Pg,
  rows: InventoryCategory[]
): Promise<InventoryCategory[]> {
  if (rows.length === 0) return []
  const ids = Array.from(
    new Set(rows.flatMap((r) => [r.inventory_account_id, r.expense_account_id].filter((x) => x)))
  )
  if (ids.length === 0) {
    return rows.map((r) => ({ ...r }))
  }
  const accs = (await sql<Account[]>`
    SELECT * FROM public.accounts
    WHERE id = ANY(${ids}::bigint[])
  `) as Account[]
  const byId = new Map(accs.map((a) => [a.id, a]))
  return rows.map((r) => ({
    ...r,
    inventory_account: byId.get(r.inventory_account_id),
    expense_account: byId.get(r.expense_account_id),
  }))
}

export async function attachItemCategory(
  sql: Pg,
  item: InventoryItem | null
): Promise<InventoryItem | null> {
  if (!item) return null
  const cats = await sql<InventoryCategory[]>`
    SELECT * FROM public.inventory_categories
    WHERE id = ${item.category_id}
    LIMIT 1
  `
  const c0 = (cats[0] as InventoryCategory) ?? null
  if (!c0) {
    return { ...parseInventoryItemRow(item), category: undefined }
  }
  const [enriched] = await attachCategoryAccounts(sql, [c0])
  const parsed = parseInventoryItemRow(item)
  return { ...parsed, category: enriched }
}

export async function attachItemsCategories(
  sql: Pg,
  items: InventoryItem[]
): Promise<InventoryItem[]> {
  if (items.length === 0) return []
  const catIds = Array.from(new Set(items.map((i) => i.category_id)))
  const rawCats = (await sql<InventoryCategory[]>`
    SELECT * FROM public.inventory_categories
    WHERE id = ANY(${catIds}::bigint[])
  `) as InventoryCategory[]
  const cats = await attachCategoryAccounts(sql, rawCats)
  const m = new Map(cats.map((c) => [Number(c.id), c]))
  return items.map((i) => {
    const parsed = parseInventoryItemRow(i)
    return { ...parsed, category: m.get(parsed.category_id) }
  })
}

export async function attachTransactionItem(
  sql: Pg,
  rows: InventoryTransaction[]
): Promise<InventoryTransaction[]> {
  if (rows.length === 0) return []
  const itemIds = Array.from(new Set(rows.map((r) => r.item_id)))
  const items = (await sql<InventoryItem[]>`
    SELECT * FROM public.inventory_items
    WHERE id = ANY(${itemIds}::bigint[])
  `) as InventoryItem[]
  const withCat = await attachItemsCategories(sql, items)
  const byItem = new Map(withCat.map((i) => [i.id, i]))
  return rows.map((r) => {
    const parsed = parseInventoryTransactionRow(r)
    return { ...parsed, item: byItem.get(parsed.item_id) }
  })
}

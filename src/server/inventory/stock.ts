import { getSql } from '@/server/pg'
import { allocateLots, parseSerials, quantity } from '@/server/inventory/rules'

type Pg = ReturnType<typeof getSql>
type Row = Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any

/** The organization's default warehouse, created the first time it's needed. */
export async function defaultWarehouse(tx: Pg, org: string): Promise<number> {
  const [w] = (await tx`SELECT id FROM public.warehouses WHERE organization_id = ${org}::uuid AND is_default LIMIT 1`) as Row[]
  if (w) return Number(w.id)
  const [made] = (await tx`
    INSERT INTO public.warehouses (organization_id, name, is_default) VALUES (${org}::uuid, 'Main', true)
    ON CONFLICT (organization_id, name) DO UPDATE SET is_default = true RETURNING id
  `) as Row[]
  return Number(made.id)
}

export type StockChange = {
  org: string
  itemId: number
  itemName: string
  trackLots: boolean
  warehouseId: number
  transactionId: number
  /** Positive adds to this warehouse, negative takes from it. */
  delta: number
  lotId?: number | null
  lotNumber?: string | null
  expiryDate?: string | null
  fallbackLot: string
}

/** Applies a quantity change to one warehouse and, for tracked items, to its batches. Refuses to go below zero. */
export async function applyToWarehouse(tx: Pg, c: StockChange) {
  const [level] = (await tx`
    INSERT INTO public.stock_levels (item_id, warehouse_id, quantity) VALUES (${c.itemId}, ${c.warehouseId}, 0)
    ON CONFLICT (item_id, warehouse_id) DO UPDATE SET quantity = public.stock_levels.quantity
    RETURNING quantity::float AS quantity
  `) as Row[]
  const after = quantity(Number(level.quantity) + c.delta)
  if (after < -1e-9) {
    const [w] = (await tx`SELECT name FROM public.warehouses WHERE id = ${c.warehouseId}`) as Row[]
    throw new Error(`Insufficient quantity: only ${Number(level.quantity)} of ${c.itemName} in ${w?.name ?? 'this warehouse'}.`)
  }
  await tx`UPDATE public.stock_levels SET quantity = ${after} WHERE item_id = ${c.itemId} AND warehouse_id = ${c.warehouseId}`
  if (!c.trackLots || !c.delta) return []

  if (c.delta > 0) {
    const number = (c.lotNumber ?? '').trim() || c.fallbackLot
    const [lot] = (await tx`
      INSERT INTO public.stock_lots (item_id, warehouse_id, lot_number, expiry_date, quantity)
      VALUES (${c.itemId}, ${c.warehouseId}, ${number}, ${c.expiryDate ?? null}::date, ${c.delta})
      ON CONFLICT (item_id, warehouse_id, lot_number) DO UPDATE
        SET quantity = public.stock_lots.quantity + ${c.delta}, expiry_date = COALESCE(EXCLUDED.expiry_date, public.stock_lots.expiry_date)
      RETURNING id
    `) as Row[]
    await tx`INSERT INTO public.stock_lot_movements (transaction_id, lot_id, quantity) VALUES (${c.transactionId}, ${lot.id}, ${c.delta})`
    return [{ lot_number: number, expiry_date: c.expiryDate ?? null, quantity: c.delta }]
  }

  const lots = (await tx`
    SELECT id, lot_number, expiry_date::text AS expiry_date, quantity::float AS quantity
    FROM public.stock_lots
    WHERE item_id = ${c.itemId} AND warehouse_id = ${c.warehouseId} AND quantity > 0
      AND (${c.lotId ?? null}::bigint IS NULL OR id = ${c.lotId ?? null}::bigint)
    FOR UPDATE
  `) as Row[]
  const { picks, short } = allocateLots(lots.map((l) => ({ ...l, id: Number(l.id), quantity: Number(l.quantity), expiry_date: l.expiry_date as string | null, lot_number: l.lot_number as string })), Math.abs(c.delta))
  if (short) throw new Error(`Insufficient quantity: ${c.lotId ? 'that batch' : 'the batches'} of ${c.itemName} are ${short} short.`)
  for (const p of picks) {
    await tx`UPDATE public.stock_lots SET quantity = quantity - ${p.quantity} WHERE id = ${p.lot.id}`
    await tx`INSERT INTO public.stock_lot_movements (transaction_id, lot_id, quantity) VALUES (${c.transactionId}, ${p.lot.id}, ${-p.quantity})`
  }
  return picks.map((p) => ({ lot_number: p.lot.lot_number, expiry_date: p.lot.expiry_date, quantity: -p.quantity }))
}

/** Puts batches back exactly as an earlier movement took them, so a voided sale restores the same batch and expiry. */
export async function restoreLots(tx: Pg, itemId: number, warehouseId: number, transactionId: number, from: number[], delta: number, fallbackLot: string) {
  const moved = (await tx`
    SELECT m.lot_id, l.lot_number, l.expiry_date::text AS expiry_date, -SUM(m.quantity)::float AS quantity
    FROM public.stock_lot_movements m JOIN public.stock_lots l ON l.id = m.lot_id
    WHERE m.transaction_id = ANY(${from}::bigint[]) AND m.quantity < 0
    GROUP BY 1, 2, 3 ORDER BY m.lot_id
  `) as Row[]
  let left = delta
  const lots = []
  for (const m of moved) {
    const q = Math.min(Number(m.quantity), left)
    if (q <= 0) break
    await tx`UPDATE public.stock_lots SET quantity = quantity + ${q} WHERE id = ${m.lot_id}`
    await tx`INSERT INTO public.stock_lot_movements (transaction_id, lot_id, quantity) VALUES (${transactionId}, ${m.lot_id}, ${q})`
    lots.push({ lot_number: m.lot_number as string, expiry_date: m.expiry_date as string | null, quantity: q })
    left = quantity(left - q)
  }
  // Tracking may have started after the original movement, so the rest has no batch to go back to.
  if (left > 1e-9) {
    const [lot] = (await tx`
      INSERT INTO public.stock_lots (item_id, warehouse_id, lot_number, quantity) VALUES (${itemId}, ${warehouseId}, ${fallbackLot}, ${left})
      ON CONFLICT (item_id, warehouse_id, lot_number) DO UPDATE SET quantity = public.stock_lots.quantity + ${left} RETURNING id
    `) as Row[]
    await tx`INSERT INTO public.stock_lot_movements (transaction_id, lot_id, quantity) VALUES (${transactionId}, ${lot.id}, ${left})`
    lots.push({ lot_number: fallbackLot, expiry_date: null, quantity: left })
  }
  return lots
}

/** The batch an earlier movement added to, so undoing it takes from that same batch. */
export async function lotAddedBy(tx: Pg, from: number[]) {
  const [m] = (await tx`SELECT lot_id FROM public.stock_lot_movements WHERE transaction_id = ANY(${from}::bigint[]) AND quantity > 0 LIMIT 1`) as Row[]
  return m ? Number(m.lot_id) : null
}

export const serialsMovedBy = async (tx: Pg, from: number[]) =>
  ((await tx`SELECT s.serial_number FROM public.stock_serial_movements m JOIN public.stock_serials s ON s.id = m.serial_id WHERE m.transaction_id = ANY(${from}::bigint[]) ORDER BY s.id`) as Row[]).map((r) => String(r.serial_number))

/** The next free numbers for units that arrive without one, made from the SKU. */
export async function generateSerials(tx: Pg, itemId: number, sku: string, count: number) {
  const taken = ((await tx`SELECT serial_number FROM public.stock_serials WHERE item_id = ${itemId}`) as Row[]).map((r) => String(r.serial_number))
  const made: string[] = []
  for (let n = taken.length + 1; made.length < count; n++) {
    const candidate = `${sku}-S${String(n).padStart(4, '0')}`
    if (!taken.includes(candidate)) made.push(candidate)
  }
  return made
}

export type SerialChange = { itemId: number; itemName: string; sku: string; warehouseId: number; transactionId: number; delta: number; serialNumbers?: string[] | string | null }

/**
 * Moves individual units. Coming in, numbers left out are created from the SKU. Going out, numbers left out take the
 * unit that has been here longest. A unit that left and comes back keeps its number and history.
 */
export async function applySerials(tx: Pg, c: SerialChange) {
  const count = Math.abs(c.delta)
  if (!Number.isInteger(quantity(count))) throw new Error(`${c.itemName} is tracked by serial number, so quantities must be whole.`)
  const named = parseSerials(c.serialNumbers)
  if (named.length && named.length !== count) throw new Error(`${c.itemName} needs ${count} serial ${count === 1 ? 'number' : 'numbers'}, but ${named.length} ${named.length === 1 ? 'was' : 'were'} given.`)
  const [w] = (await tx`SELECT name FROM public.warehouses WHERE id = ${c.warehouseId}`) as Row[]
  const moved: { id: number; serial_number: string }[] = []
  if (c.delta > 0) {
    for (const number of named.length ? named : await generateSerials(tx, c.itemId, c.sku, count)) {
      const [found] = (await tx`SELECT id, in_stock FROM public.stock_serials WHERE item_id = ${c.itemId} AND serial_number = ${number} FOR UPDATE`) as Row[]
      if (found?.in_stock) throw new Error(`Serial number ${number} of ${c.itemName} is already in stock.`)
      const [row] = (found
        ? await tx`UPDATE public.stock_serials SET in_stock = true, warehouse_id = ${c.warehouseId} WHERE id = ${found.id} RETURNING id`
        : await tx`INSERT INTO public.stock_serials (item_id, warehouse_id, serial_number) VALUES (${c.itemId}, ${c.warehouseId}, ${number}) RETURNING id`) as Row[]
      moved.push({ id: Number(row.id), serial_number: number })
    }
  } else {
    const rows = (named.length
      ? await tx`SELECT id, serial_number FROM public.stock_serials WHERE item_id = ${c.itemId} AND warehouse_id = ${c.warehouseId} AND in_stock AND serial_number = ANY(${named}::text[]) FOR UPDATE`
      : await tx`SELECT id, serial_number FROM public.stock_serials WHERE item_id = ${c.itemId} AND warehouse_id = ${c.warehouseId} AND in_stock ORDER BY id LIMIT ${count} FOR UPDATE`) as Row[]
    if (rows.length < count) {
      const missing = named.find((n) => !rows.some((r) => r.serial_number === n))
      throw new Error(missing ? `Serial number ${missing} of ${c.itemName} isn't in ${w?.name ?? 'this warehouse'}.` : `Insufficient quantity: only ${rows.length} of ${c.itemName} in ${w?.name ?? 'this warehouse'}.`)
    }
    for (const r of rows) {
      await tx`UPDATE public.stock_serials SET in_stock = false WHERE id = ${r.id}`
      moved.push({ id: Number(r.id), serial_number: String(r.serial_number) })
    }
  }
  for (const m of moved) await tx`INSERT INTO public.stock_serial_movements (transaction_id, serial_id) VALUES (${c.transactionId}, ${m.id})`
  return moved.map((m) => m.serial_number)
}

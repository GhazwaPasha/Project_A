import { getSql } from '@/server/pg'
import { consumeLayers, money, type Layer } from '@/server/inventory/rules'

type Pg = ReturnType<typeof getSql>
type Row = Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any

const openLayers = async (tx: Pg, itemId: number, onlyTransactions?: number[]): Promise<Layer[]> => {
  const rows = (await tx`
    SELECT id, quantity::float AS quantity, value::float AS value FROM public.stock_cost_layers
    WHERE item_id = ${itemId} AND quantity > 0 AND (${onlyTransactions ?? null}::bigint[] IS NULL OR transaction_id = ANY(${onlyTransactions ?? null}::bigint[]))
    ORDER BY received_date, id
  `) as Row[]
  return rows.map((r) => ({ id: Number(r.id), quantity: Number(r.quantity), value: Number(r.value) }))
}

export async function addLayer(tx: Pg, itemId: number, transactionId: number | null, date: string, quantity: number, value: number) {
  await tx`INSERT INTO public.stock_cost_layers (item_id, transaction_id, received_date, quantity, value) VALUES (${itemId}, ${transactionId}, ${date}::date, ${quantity}, ${value})`
}

/** Takes stock from the oldest purchases first, or from particular movements when undoing them, and says what it cost. */
export async function takeLayers(tx: Pg, itemId: number, transactionId: number, quantity: number, onlyTransactions?: number[]) {
  const { takes, cost, short } = consumeLayers(await openLayers(tx, itemId, onlyTransactions), quantity)
  for (const t of takes) {
    await tx`UPDATE public.stock_cost_layers SET quantity = quantity - ${t.quantity}, value = value - ${t.value} WHERE id = ${t.id}`
    await tx`INSERT INTO public.stock_cost_layer_takes (transaction_id, layer_id, quantity, value) VALUES (${transactionId}, ${t.id}, ${t.quantity}, ${t.value})`
  }
  return { cost, short }
}

/** Undoes earlier issues by putting stock back in the layers it came from, so it keeps its place in the queue. False if there's nothing to put back. */
export async function restoreLayers(tx: Pg, from: number[]) {
  const takes = (await tx`SELECT layer_id, SUM(quantity)::float AS quantity, SUM(value)::float AS value FROM public.stock_cost_layer_takes WHERE transaction_id = ANY(${from}::bigint[]) GROUP BY 1`) as Row[]
  for (const t of takes) await tx`UPDATE public.stock_cost_layers SET quantity = quantity + ${t.quantity}, value = value + ${t.value} WHERE id = ${t.layer_id}`
  return takes.length > 0
}

/** Replaces an item's layers when its method changes. Value stays exactly the same either way. */
export async function resetLayers(tx: Pg, itemId: number, method: 'average' | 'fifo', quantity: number, value: number, date: string) {
  await tx`DELETE FROM public.stock_cost_layers WHERE item_id = ${itemId}`
  if (method === 'fifo' && quantity > 0) await addLayer(tx, itemId, null, date, quantity, value)
}

export type CostableItem = { id: number; method: string; on_hand: number; value: number; average: number }

/**
 * Works out what stock will cost when it leaves, before it moves, so the entry can be shown and written first.
 * Remembers earlier lines, so two lines of one item are costed as they'll actually happen.
 */
export class CostPlanner {
  private used: Record<number, { quantity: number; value: number }> = {}
  private layers: Record<number, Layer[]> = {}
  constructor(private tx: Pg) {}

  async cost(item: CostableItem, quantity: number) {
    if (item.method === 'fifo') {
      const open = this.layers[item.id] ?? (this.layers[item.id] = await openLayers(this.tx, item.id))
      const { takes, cost } = consumeLayers(open, quantity)
      this.layers[item.id] = open.flatMap((l) => {
        const t = takes.find((x) => x.id === l.id)
        return !t ? [l] : l.quantity - t.quantity > 1e-9 ? [{ id: l.id, quantity: l.quantity - t.quantity, value: money(l.value - t.value) }] : []
      })
      return cost
    }
    const u = this.used[item.id] ?? (this.used[item.id] = { quantity: 0, value: 0 })
    const left = item.on_hand - u.quantity
    const cost = quantity >= left - 1e-9 ? money(Math.max(item.value - u.value, 0)) : money(quantity * item.average)
    u.quantity += quantity
    u.value += cost
    return cost
  }
}

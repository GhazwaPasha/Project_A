/** The rules for batches, receipts, counts, reordering and stock analysis. No database here, so they can be tested alone. */

export const money = (n: number) => Math.round((n + (n >= 0 ? Number.EPSILON : -Number.EPSILON)) * 100) / 100
export const quantity = (n: number) => Math.round(n * 10000) / 10000

export type EntryLine = { account_id: number; debit: number; credit: number; description: string | null }

function byAccount(rows: { account_id: number; amount: number }[]) {
  const totals: { account_id: number; amount: number }[] = []
  rows.forEach((r) => {
    const t = totals.find((x) => x.account_id === r.account_id)
    if (t) t.amount = money(t.amount + r.amount)
    else totals.push({ account_id: r.account_id, amount: money(r.amount) })
  })
  return totals.filter((t) => t.amount !== 0)
}

/** Takes from the batch that expires first, then the oldest. Batches with no expiry go last. */
export function allocateLots<T extends { id: number; quantity: number; expiry_date: string | null }>(lots: T[], needed: number) {
  const ordered = [...lots].filter((l) => l.quantity > 0).sort((a, b) => {
    if (a.expiry_date && b.expiry_date) return a.expiry_date < b.expiry_date ? -1 : a.expiry_date > b.expiry_date ? 1 : a.id - b.id
    if (a.expiry_date) return -1
    if (b.expiry_date) return 1
    return a.id - b.id
  })
  const picks: { lot: T; quantity: number }[] = []
  let left = needed
  for (const lot of ordered) {
    if (left <= 1e-9) break
    const take = Math.min(lot.quantity, left)
    picks.push({ lot, quantity: quantity(take) })
    left = quantity(left - take)
  }
  return { picks, short: left > 1e-9 ? left : 0 }
}

/** Goods in: stock goes up, and what's owed sits in "received, not billed" until the supplier's bill arrives. */
export function receiptEntry(lines: { inventory_account_id: number; amount: number }[], grniAccountId: number): EntryLine[] {
  const stock = byAccount(lines.map((l) => ({ account_id: l.inventory_account_id, amount: l.amount })))
  const total = money(stock.reduce((s, a) => s + a.amount, 0))
  return [
    ...stock.map((a) => ({ account_id: a.account_id, debit: a.amount, credit: 0, description: null })),
    { account_id: grniAccountId, debit: 0, credit: total, description: 'Received, not billed' },
  ]
}

/** Selling: the cost of what left moves from stock to cost of goods sold. */
export function costOfSalesEntry(lines: { expense_account_id: number; inventory_account_id: number; amount: number }[]): EntryLine[] {
  return [
    ...byAccount(lines.map((l) => ({ account_id: l.expense_account_id, amount: l.amount }))).map((a) => ({ account_id: a.account_id, debit: a.amount, credit: 0, description: 'Cost of goods sold' })),
    ...byAccount(lines.map((l) => ({ account_id: l.inventory_account_id, amount: l.amount }))).map((a) => ({ account_id: a.account_id, debit: 0, credit: a.amount, description: 'Cost of goods sold' })),
  ]
}

export type CountLine = { item_id: number; counted: number | null; current: number; average_unit_cost: number; inventory_account_id: number; adjustment_account_id: number; loss_value?: number }

/** Compares to what's on hand at posting, so stock that moved during the count isn't counted as a loss. Uncounted lines are left alone. */
export function countAdjustments(lines: CountLine[]) {
  const moves = lines.filter((l) => l.counted !== null && quantity(l.counted - l.current) !== 0).map((l) => {
    const difference = quantity((l.counted as number) - l.current)
    return { item_id: l.item_id, difference, value: difference < 0 && l.loss_value !== undefined ? money(l.loss_value) : money(Math.abs(difference) * l.average_unit_cost), gain: difference > 0, inventory_account_id: l.inventory_account_id, adjustment_account_id: l.adjustment_account_id }
  })
  const valued = moves.filter((m) => m.value > 0)
  const entry: EntryLine[] = [
    ...byAccount(valued.map((m) => ({ account_id: m.inventory_account_id, amount: m.gain ? m.value : -m.value }))).map((a) => (a.amount > 0
      ? { account_id: a.account_id, debit: a.amount, credit: 0, description: 'Stock count' }
      : { account_id: a.account_id, debit: 0, credit: -a.amount, description: 'Stock count' })),
    ...byAccount(valued.map((m) => ({ account_id: m.adjustment_account_id, amount: m.gain ? -m.value : m.value }))).map((a) => (a.amount > 0
      ? { account_id: a.account_id, debit: a.amount, credit: 0, description: 'Stock count' }
      : { account_id: a.account_id, debit: 0, credit: -a.amount, description: 'Stock count' })),
  ]
  return { moves, entry }
}

export type PlanItem = { item_id: number; on_hand: number; on_order: number; used_90_days: number; reorder_point: number; reorder_quantity: number; lead_time_days: number }

/**
 * Reorders when what's on hand and on order won't last the lead time, or falls to the reorder point.
 * Orders enough to cover the lead time and 30 more days, and at least the usual reorder quantity.
 */
export function reorderLine(i: PlanItem) {
  const daily = i.used_90_days / 90
  const available = i.on_hand + i.on_order
  const days_of_cover = daily > 0 ? Math.floor(i.on_hand / daily) : null
  const leadDemand = daily * i.lead_time_days
  const trigger = Math.max(i.reorder_point, leadDemand)
  const needed = trigger > 0 && available <= trigger
  const target = Math.ceil(daily * (i.lead_time_days + 30))
  const suggested = needed ? Math.max(Math.ceil(i.reorder_quantity), target - Math.floor(available), 1) : 0
  return { daily_usage: Math.round(daily * 100) / 100, days_of_cover, suggested, stockout_risk: needed && daily > 0 && (days_of_cover ?? 0) < i.lead_time_days }
}

/** A items make up the first 80% of value used, B the next 15%, C the rest. Items that weren't used are C. */
export function abcAnalysis<T extends { item_id: number; usage_value: number }>(items: T[]) {
  const total = items.reduce((s, i) => s + Math.max(i.usage_value, 0), 0)
  let running = 0
  return [...items].sort((a, b) => b.usage_value - a.usage_value).map((i) => {
    const before = total ? running / total : 1
    running += Math.max(i.usage_value, 0)
    return { ...i, share: total ? Math.round((i.usage_value / total) * 1000) / 10 : 0, class: (i.usage_value <= 0 || !total ? 'C' : before < 0.8 ? 'A' : before < 0.95 ? 'B' : 'C') as 'A' | 'B' | 'C' }
  })
}

export type Layer = { id: number; quantity: number; value: number }

/** First in, first out: takes from the layers in the order given. Taking all of a layer takes all its value, so no cents get left behind. */
export function consumeLayers(layers: Layer[], needed: number) {
  const takes: Layer[] = []
  let left = needed
  for (const l of layers) {
    if (left <= 1e-9) break
    const q = Math.min(l.quantity, left)
    takes.push({ id: l.id, quantity: quantity(q), value: q >= l.quantity - 1e-9 ? money(l.value) : money((q * l.value) / l.quantity) })
    left = quantity(left - q)
  }
  return { takes, cost: money(takes.reduce((s, t) => s + t.value, 0)), short: left > 1e-9 ? left : 0 }
}

/** Serial numbers typed or pasted as a list: one per line, or separated by commas. Refuses repeats. */
export function parseSerials(input: string | string[] | null | undefined) {
  const list = (Array.isArray(input) ? input : String(input ?? '').split(/[\n,;]+/)).map((s) => String(s).trim()).filter(Boolean)
  const repeat = list.find((s, i) => list.indexOf(s) !== i)
  if (repeat) throw new Error(`Serial number ${repeat} is listed twice.`)
  return list
}

/** Finished stock goes up by what its parts and any extra cost come to; parts' stock goes down, and the extra comes from its account. */
export function assemblyEntry(outputAccountId: number, parts: { inventory_account_id: number; amount: number }[], extra: number, extraAccountId: number | null): EntryLine[] {
  const total = money(parts.reduce((s, p) => s + p.amount, 0) + extra)
  return [
    { account_id: outputAccountId, debit: total, credit: 0, description: 'Built' },
    ...byAccount(parts.map((p) => ({ account_id: p.inventory_account_id, amount: p.amount }))).map((a) => ({ account_id: a.account_id, debit: 0, credit: a.amount, description: 'Parts used' })),
    ...(extra > 0 && extraAccountId ? [{ account_id: extraAccountId, debit: 0, credit: money(extra), description: 'Extra build cost' }] : []),
  ]
}

/** Would making `itemId` from these parts loop back on itself? Returns the part that causes it, or null. */
export function findBomCycle(itemId: number, parts: number[], others: { item_id: number; component_id: number }[]) {
  const reaches = (from: number, seen: number[]): boolean => {
    if (from === itemId) return true
    if (seen.includes(from)) return false
    return others.filter((o) => o.item_id === from).some((o) => reaches(o.component_id, [...seen, from]))
  }
  return parts.find((p) => reaches(p, [])) ?? null
}

export const expiryStatus = (expiry: string | null, today: string): 'expired' | 'soon' | 'ok' | null => {
  if (!expiry) return null
  const days = Math.floor((Date.parse(`${expiry.slice(0, 10)}T00:00:00Z`) - Date.parse(`${today}T00:00:00Z`)) / 86400000)
  return days < 0 ? 'expired' : days <= 30 ? 'soon' : 'ok'
}

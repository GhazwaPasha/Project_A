/** What a voucher does to the books and to stock when it's posted. No database here, so the rules can be tested alone. */

export type PostingLine = {
  line_id: number
  item_id: number
  item_name: string
  quantity_requested: number
  quantity_actual: number | null
  unit_cost_estimated: number | null
  unit_cost_actual: number | null
  quantity_available: number
  average_unit_cost: number
  inventory_account_id: number
  expense_account_id: number
  /** What issuing this line costs, when it isn't just quantity times average: first-in, first-out items. */
  issue_cost?: number
}

export type PostingInput = {
  voucher_type: string
  payment_type: string
  payment_account_id: number | null
  deposit_amount: number
  destination_account_id: number | null
  payable_account_id: number | null
  lines: PostingLine[]
}

export type StockMove = { line_id: number; item_id: number; type: 'in' | 'out'; quantity: number; unit_cost: number; total_cost: number }
export type EntryLine = { account_id: number; debit: number; credit: number; description: string }
export type PostingPlan = { lines: EntryLine[]; moves: StockMove[]; total: number; problems: string[]; needs_payable: boolean }

const money = (n: number) => Math.round((n + Number.EPSILON) * 100) / 100
const SETTLED_NOW = ['cash', 'check', 'card', 'bank_transfer']

/** Adds lines per account, keeping every amount in whole cents so debits and credits match exactly. */
function byAccount(amounts: { account_id: number; amount: number; description: string }[]) {
  const totals = new Map<number, { amount: number; items: string[] }>()
  for (const a of amounts) {
    const t = totals.get(a.account_id) ?? { amount: 0, items: [] }
    t.amount = money(t.amount + a.amount)
    t.items.push(a.description)
    totals.set(a.account_id, t)
  }
  return Array.from(totals).map(([account_id, t]) => ({ account_id, amount: t.amount, description: t.items.join(', ').slice(0, 200) }))
}

export function planVoucherPosting(input: PostingInput): PostingPlan {
  const problems: string[] = []
  const moves: StockMove[] = []
  const lines = input.lines.filter((l) => (l.quantity_actual ?? l.quantity_requested) > 0)
  if (!lines.length) problems.push('Nothing to post: every quantity on this voucher is zero.')
  const purchase = input.voucher_type === 'purchase'
  let needs_payable = false

  if (purchase) {
    const stock: { account_id: number; amount: number; description: string }[] = []
    for (const l of lines) {
      const quantity = l.quantity_actual ?? l.quantity_requested
      const unit_cost = l.unit_cost_actual ?? l.unit_cost_estimated ?? l.average_unit_cost
      if (!(unit_cost > 0)) {
        problems.push(`${l.item_name} has no cost. Add what it actually cost before posting.`)
        continue
      }
      const total_cost = money(quantity * unit_cost)
      moves.push({ line_id: l.line_id, item_id: l.item_id, type: 'in', quantity, unit_cost, total_cost })
      stock.push({ account_id: l.inventory_account_id, amount: total_cost, description: l.item_name })
    }
    const total = money(stock.reduce((s, a) => s + a.amount, 0))
    const entry: EntryLine[] = byAccount(stock).map((a) => ({ account_id: a.account_id, debit: a.amount, credit: 0, description: a.description }))

    // How it was paid decides what's credited: money that left now, or what's still owed.
    const paidNow = SETTLED_NOW.includes(input.payment_type) ? total : input.payment_type === 'partial' ? money(Math.min(Math.max(input.deposit_amount, 0), total)) : 0
    if (input.payment_type === 'partial' && input.deposit_amount > total) problems.push('The deposit is more than the voucher total.')
    if (paidNow > 0) {
      if (input.payment_account_id) entry.push({ account_id: input.payment_account_id, debit: 0, credit: paidNow, description: 'Paid' })
      else problems.push('Choose the account this was paid from. Edit the voucher to add it.')
    }
    const owed = money(total - paidNow)
    if (owed > 0) {
      if (input.payable_account_id) entry.push({ account_id: input.payable_account_id, debit: 0, credit: owed, description: 'Owed to supplier' })
      else {
        needs_payable = true
        problems.push('Choose the account that tracks what you owe this supplier.')
      }
    }
    return { lines: entry, moves, total, problems, needs_payable }
  }

  // Issuing: stock leaves at its average cost, and that cost lands on the destination or the category's cost account.
  const taken = new Map<number, number>()
  const costs: { account_id: number; amount: number; description: string }[] = []
  const stock: { account_id: number; amount: number; description: string }[] = []
  for (const l of lines) {
    const quantity = l.quantity_actual ?? l.quantity_requested
    const used = (taken.get(l.item_id) ?? 0) + quantity
    taken.set(l.item_id, used)
    if (used > l.quantity_available + 1e-9) {
      problems.push(`Only ${l.quantity_available} of ${l.item_name} on hand, but this voucher issues ${used}.`)
      continue
    }
    if (!(l.average_unit_cost > 0)) {
      problems.push(`${l.item_name} has no cost on record, so its value can't be taken out of your books.`)
      continue
    }
    const total_cost = l.issue_cost ?? money(quantity * l.average_unit_cost)
    moves.push({ line_id: l.line_id, item_id: l.item_id, type: 'out', quantity, unit_cost: l.issue_cost !== undefined ? total_cost / quantity : l.average_unit_cost, total_cost })
    costs.push({ account_id: input.destination_account_id ?? l.expense_account_id, amount: total_cost, description: l.item_name })
    stock.push({ account_id: l.inventory_account_id, amount: total_cost, description: l.item_name })
  }
  const entry: EntryLine[] = [
    ...byAccount(costs).map((a) => ({ account_id: a.account_id, debit: a.amount, credit: 0, description: a.description })),
    ...byAccount(stock).map((a) => ({ account_id: a.account_id, debit: 0, credit: a.amount, description: a.description })),
  ]
  return { lines: entry, moves, total: money(costs.reduce((s, a) => s + a.amount, 0)), problems, needs_payable }
}

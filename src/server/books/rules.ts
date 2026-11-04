/** The accounting rules for invoices, bills, stock, tax, banking and forecasts. No database here, so they can be tested alone. */

export const money = (n: number) => Math.round((n + (n >= 0 ? Number.EPSILON : -Number.EPSILON)) * 100) / 100

export type EntryLine = { account_id: number; debit: number; credit: number; description: string | null }

type Amount = { account_id: number; amount: number }
function byAccount(rows: Amount[]) {
  const totals: Amount[] = []
  rows.forEach((r) => {
    const t = totals.find((x) => x.account_id === r.account_id)
    if (t) t.amount = money(t.amount + r.amount)
    else totals.push({ account_id: r.account_id, amount: money(r.amount) })
  })
  return totals.filter((t) => t.amount !== 0)
}

export type DocLineInput = { account_id: number; quantity: number; unit_price: number; tax_rate: number; tax_account_id: number | null }

export function documentTotals(lines: { quantity: number; unit_price: number; tax_rate: number }[]) {
  const priced = lines.map((l) => {
    const amount = money(l.quantity * l.unit_price)
    return { amount, tax_amount: money((amount * l.tax_rate) / 100) }
  })
  const subtotal = money(priced.reduce((s, l) => s + l.amount, 0))
  const tax_total = money(priced.reduce((s, l) => s + l.tax_amount, 0))
  return { lines: priced, subtotal, tax_total, total: money(subtotal + tax_total) }
}

/** Invoice: you're owed the total, against income and the tax you collected. Bill: the reverse, you owe the total. */
export function documentEntry(kind: 'invoice' | 'bill', controlAccountId: number, lines: DocLineInput[]): EntryLine[] {
  const totals = documentTotals(lines)
  const income = byAccount(lines.map((l, i) => ({ account_id: l.account_id, amount: totals.lines[i].amount })))
  const taxes = byAccount(lines.flatMap((l, i) => (totals.lines[i].tax_amount && l.tax_account_id ? [{ account_id: l.tax_account_id, amount: totals.lines[i].tax_amount }] : [])))
  if (kind === 'invoice') {
    return [
      { account_id: controlAccountId, debit: totals.total, credit: 0, description: null },
      ...income.map((a) => ({ account_id: a.account_id, debit: 0, credit: a.amount, description: null })),
      ...taxes.map((a) => ({ account_id: a.account_id, debit: 0, credit: a.amount, description: 'Tax' })),
    ]
  }
  return [
    ...income.map((a) => ({ account_id: a.account_id, debit: a.amount, credit: 0, description: null })),
    ...taxes.map((a) => ({ account_id: a.account_id, debit: a.amount, credit: 0, description: 'Tax' })),
    { account_id: controlAccountId, debit: 0, credit: totals.total, description: null },
  ]
}

export function paymentEntry(kind: 'invoice' | 'bill', controlAccountId: number, bankAccountId: number, amount: number): EntryLine[] {
  const a = money(amount)
  return kind === 'invoice'
    ? [{ account_id: bankAccountId, debit: a, credit: 0, description: null }, { account_id: controlAccountId, debit: 0, credit: a, description: null }]
    : [{ account_id: controlAccountId, debit: a, credit: 0, description: null }, { account_id: bankAccountId, debit: 0, credit: a, description: null }]
}

export function reversalLines(lines: { account_id: number; debit: number; credit: number; description: string | null }[]): EntryLine[] {
  return lines.map((l) => ({ account_id: l.account_id, debit: l.credit, credit: l.debit, description: l.description }))
}

export type StockMovement = { type: 'in' | 'out' | 'adjustment'; quantity: number; total_cost: number; inventory_account_id: number; expense_account_id: number; offset_account_id: number | null }

/** The entry for a stock movement. Null when it has no value to record. */
export function stockEntry(m: StockMovement): { lines: EntryLine[] | null; problem: string | null } {
  const value = money(Math.abs(m.total_cost))
  if (!value) return { lines: null, problem: null }
  const up = m.type === 'in' || (m.type === 'adjustment' && m.quantity > 0)
  const offset = m.offset_account_id ?? (m.type === 'in' ? null : m.expense_account_id)
  if (!offset) return { lines: null, problem: 'Choose where this stock came from, such as what you owe or the bank.' }
  return {
    problem: null,
    lines: up
      ? [{ account_id: m.inventory_account_id, debit: value, credit: 0, description: null }, { account_id: offset, debit: 0, credit: value, description: null }]
      : [{ account_id: offset, debit: value, credit: 0, description: null }, { account_id: m.inventory_account_id, debit: 0, credit: value, description: null }],
  }
}

const dayNumber = (d: string) => Math.floor(Date.parse(`${d.slice(0, 10)}T00:00:00Z`) / 86400000)
export const daysBetween = (from: string, to: string) => dayNumber(to) - dayNumber(from)

export type AgedDoc = { id: number | string; party_name: string; number: string; due_date: string; balance: number }
export const AGE_BUCKETS = ['current', 'd1_30', 'd31_60', 'd61_90', 'd90_plus'] as const
type Bucket = (typeof AGE_BUCKETS)[number]
export const ageBucket = (dueDate: string, asOf: string): Bucket => {
  const late = daysBetween(dueDate, asOf)
  return late <= 0 ? 'current' : late <= 30 ? 'd1_30' : late <= 60 ? 'd31_60' : late <= 90 ? 'd61_90' : 'd90_plus'
}
type AgedRow = Record<Bucket, number> & { party_name: string; total: number }

export function agedReport(docs: AgedDoc[], asOf: string) {
  const blank = (party_name: string): AgedRow => ({ party_name, current: 0, d1_30: 0, d31_60: 0, d61_90: 0, d90_plus: 0, total: 0 })
  const rows: AgedRow[] = []
  const totals = blank('Total')
  docs.forEach((d) => {
    const bucket = ageBucket(d.due_date, asOf)
    let row = rows.find((r) => r.party_name === d.party_name)
    if (!row) { row = blank(d.party_name); rows.push(row) }
    row[bucket] = money(row[bucket] + d.balance)
    row.total = money(row.total + d.balance)
    totals[bucket] = money(totals[bucket] + d.balance)
    totals.total = money(totals.total + d.balance)
  })
  return { rows: rows.sort((a, b) => b.total - a.total), totals }
}

/** Output tax is collected on sales, input tax is paid on purchases. The difference is what's owed, or reclaimable if negative. */
export function taxSummary(rows: { kind: string; rate_name: string | null; rate: number; amount: number; tax_amount: number }[]) {
  const rates: { rate_name: string; rate: number; sales: number; output_tax: number; purchases: number; input_tax: number }[] = []
  rows.forEach((r) => {
    if (!r.tax_amount && !r.rate_name) return
    const name = r.rate_name ?? `${r.rate}%`
    let t = rates.find((x) => x.rate_name === name)
    if (!t) { t = { rate_name: name, rate: r.rate, sales: 0, output_tax: 0, purchases: 0, input_tax: 0 }; rates.push(t) }
    if (r.kind === 'invoice') { t.sales = money(t.sales + r.amount); t.output_tax = money(t.output_tax + r.tax_amount) }
    else { t.purchases = money(t.purchases + r.amount); t.input_tax = money(t.input_tax + r.tax_amount) }
  })
  const output_tax = money(rates.reduce((s, t) => s + t.output_tax, 0))
  const input_tax = money(rates.reduce((s, t) => s + t.input_tax, 0))
  return { rates, output_tax, input_tax, net_tax: money(output_tax - input_tax) }
}

/** Ledger lines that could be this bank line: same amount and direction, closest date first, within a week. */
export function matchCandidates<T extends { date: string; amount: number }>(line: { date: string; amount: number }, ledger: T[], days = 7): T[] {
  return ledger
    .filter((l) => money(l.amount) === money(line.amount) && Math.abs(daysBetween(l.date, line.date)) <= days)
    .sort((a, b) => Math.abs(daysBetween(a.date, line.date)) - Math.abs(daysBetween(b.date, line.date)))
}

/**
 * Book balance, less entries the bank hasn't shown yet, should equal the statement.
 * Anything before the first imported statement line counts as already cleared.
 */
export function reconciliation(input: { statement_balance: number; book_balance: number; outstanding: { amount: number }[]; unmatched_statement: { amount: number }[] }) {
  const outstanding = money(input.outstanding.reduce((s, l) => s + l.amount, 0))
  const unrecorded = money(input.unmatched_statement.reduce((s, l) => s + l.amount, 0))
  const reconciled = money(input.book_balance - outstanding + unrecorded)
  const difference = money(input.statement_balance - reconciled)
  return { outstanding, unrecorded, reconciled, difference, balanced: difference === 0 && input.unmatched_statement.length === 0 }
}

/** A plain estimate: the recent average carried forward with the recent trend, never below zero. */
export function forecastSeries(history: number[], months: number) {
  const recent = history.slice(-6)
  const n = recent.length
  if (!n || recent.every((v) => v === 0)) return Array.from({ length: months }, () => 0)
  const average = recent.reduce((s, v) => s + v, 0) / n
  const xMean = (n - 1) / 2
  const denominator = recent.reduce((s, _v, i) => s + (i - xMean) ** 2, 0)
  const slope = denominator ? recent.reduce((s, v, i) => s + (i - xMean) * (v - average), 0) / denominator : 0
  return Array.from({ length: months }, (_v, i) => money(Math.max(0, average + slope * (n - xMean + i))))
}

/** Parses a bank amount: brackets or a trailing minus mean money out, and separate columns work too. */
export function statementAmount(row: { amount?: string; debit?: string; credit?: string }) {
  const parse = (s?: string) => {
    if (!s || !s.trim()) return null
    // A currency label comes off whole, with its dot: "Rs. 75" is 75, not .75.
    const clean = s.replace(/[,\s]/g, '').replace(/^([(+-]?)[^\d(+\-.]+\.?/, '$1')
    const negative = /^\(.*\)$/.test(clean) || /-$/.test(clean) || clean.startsWith('-')
    const n = parseFloat(clean.replace(/[()+-]/g, ''))
    return Number.isNaN(n) ? null : money(negative ? -n : n)
  }
  const single = parse(row.amount)
  if (single !== null) return single
  const out = parse(row.debit)
  const inward = parse(row.credit)
  if (out === null && inward === null) return null
  return money((inward ?? 0) - Math.abs(out ?? 0))
}

export type CreditLine = { account_id: number; amount: number; tax_amount: number; tax_account_id: number | null }

/** The opposite of the original document, for what's being credited. What the document still owed comes off that; any more is paid back. */
export function creditNoteEntry(kind: 'invoice' | 'bill', controlId: number, refundId: number | null, lines: CreditLine[], applied: number, refund: number): EntryLine[] {
  const main = byAccount(lines.map((l) => ({ account_id: l.account_id, amount: l.amount })))
  const taxes = byAccount(lines.flatMap((l) => (l.tax_amount && l.tax_account_id ? [{ account_id: l.tax_account_id, amount: l.tax_amount }] : [])))
  const settle: { account_id: number; amount: number; description: string }[] = [
    ...(applied > 0 ? [{ account_id: controlId, amount: money(applied), description: 'Credit applied' }] : []),
    ...(refund > 0 && refundId ? [{ account_id: refundId, amount: money(refund), description: 'Refund' }] : []),
  ]
  if (kind === 'invoice') {
    return [
      ...main.map((a) => ({ account_id: a.account_id, debit: a.amount, credit: 0, description: 'Credit note' })),
      ...taxes.map((a) => ({ account_id: a.account_id, debit: a.amount, credit: 0, description: 'Tax' })),
      ...settle.map((a) => ({ account_id: a.account_id, debit: 0, credit: a.amount, description: a.description })),
    ]
  }
  return [
    ...settle.map((a) => ({ account_id: a.account_id, debit: a.amount, credit: 0, description: a.description })),
    ...main.map((a) => ({ account_id: a.account_id, debit: 0, credit: a.amount, description: 'Credit note' })),
    ...taxes.map((a) => ({ account_id: a.account_id, debit: 0, credit: a.amount, description: 'Tax' })),
  ]
}

export type CashEntryLine = { account_id: number; code: string; name: string; account_type: string; report_category: string | null; is_cash: boolean; debit: number; credit: number }
export type CashSection = 'operating' | 'investing' | 'financing'

export const cashSection = (l: Pick<CashEntryLine, 'account_type' | 'report_category'>): CashSection => {
  if (l.account_type === 'asset' && (l.report_category === 'fixed_asset' || l.report_category === 'other_asset')) return 'investing'
  if (l.account_type === 'equity' || (l.account_type === 'liability' && l.report_category === 'long_term_liability')) return 'financing'
  return 'operating'
}

/**
 * Cash flow by the direct method: each entry that moved cash is split across what was on the other side of it.
 * Moves between cash accounts cancel out and don't appear. Takes the entries' lines, grouped by entry.
 */
export function cashFlowSummary(entries: CashEntryLine[][]) {
  type Row = { account_id: number; code: string; name: string; amount: number }
  const sections: Record<CashSection, Row[]> = { operating: [], investing: [], financing: [] }
  const add = (l: CashEntryLine, amount: number) => {
    const rows = sections[cashSection(l)]
    const row = rows.find((r) => r.account_id === l.account_id)
    if (row) row.amount = money(row.amount + amount)
    else rows.push({ account_id: l.account_id, code: l.code, name: l.name, amount: money(amount) })
  }
  for (const lines of entries) {
    const net = money(lines.filter((l) => l.is_cash).reduce((s, l) => s + l.debit - l.credit, 0))
    if (!net) continue
    // Cash coming in is matched to what was credited, and cash going out to what was debited.
    const others = lines.filter((l) => !l.is_cash).map((l) => ({ l, weight: net > 0 ? l.credit - l.debit : l.debit - l.credit })).filter((o) => o.weight > 0)
    const whole = others.reduce((s, o) => s + o.weight, 0)
    if (!whole) continue
    let left = net
    others.forEach((o, i) => {
      const share = i === others.length - 1 ? left : money((net * o.weight) / whole)
      left = money(left - share)
      add(o.l, share)
    })
  }
  const summary = (rows: Row[]) => {
    const live = rows.filter((r) => r.amount !== 0).sort((a, b) => a.code.localeCompare(b.code))
    return { lines: live, in: money(live.filter((r) => r.amount > 0).reduce((s, r) => s + r.amount, 0)), out: money(live.filter((r) => r.amount < 0).reduce((s, r) => s + r.amount, 0)), net: money(live.reduce((s, r) => s + r.amount, 0)) }
  }
  const operating = summary(sections.operating), investing = summary(sections.investing), financing = summary(sections.financing)
  return { operating, investing, financing, net: money(operating.net + investing.net + financing.net) }
}

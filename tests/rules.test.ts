import { test } from 'node:test'
import assert from 'node:assert/strict'
import { ageBucket, agedReport, documentEntry, documentTotals, forecastSeries, matchCandidates, paymentEntry, reconciliation, reversalLines, statementAmount, stockEntry, taxSummary, type EntryLine } from '../src/server/books/rules'
import { planVoucherPosting } from '../src/server/voucher-posting'

const AR = 1, SALES = 2, TAX = 3, BANK = 4, INV = 5, COGS = 6, AP = 7
const balanced = (lines: EntryLine[]) => {
  const dr = lines.reduce((s, l) => s + l.debit, 0), cr = lines.reduce((s, l) => s + l.credit, 0)
  assert.ok(Math.abs(dr - cr) < 1e-9, `out of balance: ${dr} vs ${cr}`)
}
const line = (o = {}) => ({ account_id: SALES, quantity: 2, unit_price: 100, tax_rate: 17, tax_account_id: TAX, ...o })

test('document totals include tax per line', () => {
  const t = documentTotals([line(), line({ quantity: 1, unit_price: 50, tax_rate: 0 })])
  assert.deepEqual([t.subtotal, t.tax_total, t.total], [250, 34, 284])
})
test('invoice: customer owes the total, income and tax are credited', () => {
  const e = documentEntry('invoice', AR, [line()]); balanced(e)
  assert.equal(e.find((l) => l.account_id === AR)?.debit, 234)
  assert.equal(e.find((l) => l.account_id === SALES)?.credit, 200)
  assert.equal(e.find((l) => l.account_id === TAX)?.credit, 34)
})
test('bill: cost and reclaimable tax are debited, supplier is owed', () => {
  const e = documentEntry('bill', AP, [line({ account_id: COGS })]); balanced(e)
  assert.equal(e.find((l) => l.account_id === AP)?.credit, 234)
  assert.equal(e.find((l) => l.account_id === COGS)?.debit, 200)
  assert.equal(e.find((l) => l.account_id === TAX)?.debit, 34)
})
test('lines on one account combine, and tricky rounding stays balanced', () => {
  const lines = Array.from({ length: 9 }, () => line({ quantity: 3, unit_price: 33.335, tax_rate: 16.5 }))
  balanced(documentEntry('invoice', AR, lines))
  balanced(documentEntry('bill', AP, lines))
  assert.equal(documentEntry('invoice', AR, lines).filter((l) => l.account_id === SALES).length, 1)
})
test('payments move money the right way', () => {
  const inv = paymentEntry('invoice', AR, BANK, 100); balanced(inv)
  assert.equal(inv.find((l) => l.account_id === BANK)?.debit, 100)
  const bill = paymentEntry('bill', AP, BANK, 100); balanced(bill)
  assert.equal(bill.find((l) => l.account_id === BANK)?.credit, 100)
})
test('a reversal is the exact opposite', () => {
  const e = documentEntry('invoice', AR, [line()]); const r = reversalLines(e); balanced(r)
  assert.equal(r.find((l) => l.account_id === AR)?.credit, 234)
})
test('stock entries follow the direction of the stock', () => {
  const base = { quantity: 5, total_cost: 500, inventory_account_id: INV, expense_account_id: COGS, offset_account_id: null as number | null }
  const up = stockEntry({ ...base, type: 'in', offset_account_id: AP })
  assert.equal(up.lines?.find((l) => l.account_id === INV)?.debit, 500)
  assert.match(stockEntry({ ...base, type: 'in' }).problem ?? '', /came from/)
  assert.equal(stockEntry({ ...base, type: 'out' }).lines?.find((l) => l.account_id === COGS)?.debit, 500)
  assert.equal(stockEntry({ ...base, type: 'adjustment', quantity: -2 }).lines?.find((l) => l.account_id === INV)?.credit, 500)
  assert.equal(stockEntry({ ...base, type: 'adjustment', quantity: 2 }).lines?.find((l) => l.account_id === INV)?.debit, 500)
  assert.equal(stockEntry({ ...base, type: 'out', total_cost: 0 }).lines, null)
})
test('aging buckets fall on the right day', () => {
  const asOf = '2026-06-30'
  assert.equal(ageBucket('2026-06-30', asOf), 'current')
  assert.equal(ageBucket('2026-06-29', asOf), 'd1_30')
  assert.equal(ageBucket('2026-05-31', asOf), 'd1_30')
  assert.equal(ageBucket('2026-05-30', asOf), 'd31_60')
  assert.equal(ageBucket('2026-04-01', asOf), 'd61_90')
  assert.equal(ageBucket('2026-01-01', asOf), 'd90_plus')
})
test('aged report groups by party and totals match', () => {
  const r = agedReport([{ id: 1, party_name: 'A', number: '1', due_date: '2026-06-30', balance: 10 }, { id: 2, party_name: 'A', number: '2', due_date: '2026-01-01', balance: 5 }, { id: 3, party_name: 'B', number: '3', due_date: '2026-06-01', balance: 20 }], '2026-06-30')
  assert.equal(r.rows[0].party_name, 'B'); assert.equal(r.totals.total, 35); assert.equal(r.totals.d90_plus, 5)
})
test('tax summary nets output against input', () => {
  const s = taxSummary([{ kind: 'invoice', rate_name: 'GST', rate: 17, amount: 100, tax_amount: 17 }, { kind: 'bill', rate_name: 'GST', rate: 17, amount: 50, tax_amount: 8.5 }, { kind: 'invoice', rate_name: null, rate: 0, amount: 100, tax_amount: 0 }])
  assert.deepEqual([s.output_tax, s.input_tax, s.net_tax, s.rates.length], [17, 8.5, 8.5, 1])
})
test('bank amounts parse every common format', () => {
  assert.equal(statementAmount({ amount: '1,234.50' }), 1234.5)
  assert.equal(statementAmount({ amount: '(50.00)' }), -50)
  assert.equal(statementAmount({ amount: '50.00-' }), -50)
  assert.equal(statementAmount({ amount: '-50' }), -50)
  assert.equal(statementAmount({ amount: 'Rs. 75' }), 75)
  assert.equal(statementAmount({ amount: '(Rs. 75)' }), -75)
  assert.equal(statementAmount({ amount: 'PKR 1,000.50' }), 1000.5)
  assert.equal(statementAmount({ amount: '.75' }), 0.75)
  assert.equal(statementAmount({ debit: '20', credit: '' }), -20)
  assert.equal(statementAmount({ debit: '', credit: '30' }), 30)
  assert.equal(statementAmount({ amount: 'abc' }), null)
})
test('match candidates need the same amount and a near date', () => {
  const ledger = [{ date: '2026-06-02', amount: 100 }, { date: '2026-06-01', amount: 100 }, { date: '2026-07-01', amount: 100 }, { date: '2026-06-01', amount: -100 }]
  const c = matchCandidates({ date: '2026-06-01', amount: 100 }, ledger)
  assert.deepEqual(c.map((x) => x.date), ['2026-06-01', '2026-06-02'])
})
test('reconciliation only balances when nothing is left over', () => {
  assert.equal(reconciliation({ statement_balance: 900, book_balance: 1000, outstanding: [{ amount: 100 }], unmatched_statement: [] }).balanced, true)
  assert.equal(reconciliation({ statement_balance: 1000, book_balance: 1000, outstanding: [{ amount: 100 }], unmatched_statement: [] }).difference, 100)
  const open = reconciliation({ statement_balance: 990, book_balance: 1000, outstanding: [], unmatched_statement: [{ amount: -10 }] })
  assert.equal(open.difference, 0); assert.equal(open.balanced, false)
})
test('forecast follows a trend, never goes negative, and is zero without history', () => {
  assert.deepEqual(forecastSeries([10, 20, 30, 40, 50, 60], 2), [70, 80])
  assert.ok(forecastSeries([60, 50, 40, 30, 20, 10], 12).every((v) => v >= 0))
  assert.deepEqual(forecastSeries([0, 0, 0], 2), [0, 0])
})

const voucherLine = (o = {}) => ({ line_id: 1, item_id: 1, item_name: 'Cartons', quantity_requested: 10, quantity_actual: null, unit_cost_estimated: 100, unit_cost_actual: null, quantity_available: 50, average_unit_cost: 80, inventory_account_id: INV, expense_account_id: COGS, ...o })
const voucher = (o = {}) => ({ voucher_type: 'purchase', payment_type: 'credit', payment_account_id: null, deposit_amount: 0, destination_account_id: null, payable_account_id: AP, lines: [voucherLine()], ...o })
test('voucher purchase: credit, each way of paying, and a split', () => {
  const credit = planVoucherPosting(voucher())
  assert.deepEqual(credit.problems, [])
  assert.equal(credit.lines.find((l) => l.account_id === AP)?.credit, 1000)
  for (const payment_type of ['cash', 'check', 'card', 'bank_transfer']) {
    const paid = planVoucherPosting(voucher({ payment_type, payment_account_id: BANK, payable_account_id: null }))
    assert.equal(paid.lines.find((l) => l.account_id === BANK)?.credit, 1000); assert.deepEqual(paid.problems, [])
  }
  const partial = planVoucherPosting(voucher({ payment_type: 'partial', payment_account_id: BANK, deposit_amount: 300 }))
  assert.equal(partial.lines.find((l) => l.account_id === BANK)?.credit, 300)
  assert.equal(partial.lines.find((l) => l.account_id === AP)?.credit, 700)
})
test('voucher refusals: missing accounts, no cost, too many, zero quantities', () => {
  assert.equal(planVoucherPosting(voucher({ payable_account_id: null })).needs_payable, true)
  assert.ok(planVoucherPosting(voucher({ payment_type: 'cash', payable_account_id: null })).problems.length)
  assert.ok(planVoucherPosting(voucher({ payment_type: 'partial', payment_account_id: BANK, deposit_amount: 5000 })).problems.length)
  assert.ok(planVoucherPosting(voucher({ lines: [voucherLine({ unit_cost_estimated: null, average_unit_cost: 0 })] })).problems.length)
  assert.ok(planVoucherPosting(voucher({ lines: [voucherLine({ quantity_actual: 0 })] })).problems.length)
  const issue = { voucher_type: 'issuance', payable_account_id: null }
  assert.ok(planVoucherPosting(voucher({ ...issue, lines: [voucherLine({ quantity_requested: 30 }), voucherLine({ line_id: 2, quantity_requested: 30 })] })).problems.length, 'across repeated lines')
  assert.ok(planVoucherPosting(voucher({ ...issue, lines: [voucherLine({ average_unit_cost: 0 })] })).problems.length)
})
test('voucher amounts stay balanced with awkward cents', () => {
  const lines = Array.from({ length: 7 }, (_v, i) => voucherLine({ line_id: i, item_id: i, quantity_requested: 3, unit_cost_estimated: 33.335, inventory_account_id: i % 2 ? INV : 8 }))
  balanced(planVoucherPosting(voucher({ lines, payment_type: 'partial', payment_account_id: BANK, deposit_amount: 123.45 })).lines)
  balanced(planVoucherPosting(voucher({ lines: [voucherLine()], voucher_type: 'issuance', payable_account_id: null })).lines)
})

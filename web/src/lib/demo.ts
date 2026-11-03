/** Sample data for building screens locally with `?demo=1`. Loaded only in development. */
import type { AgentEvent, AgentRequest, Bootstrap, Connection, Proposal } from './api'

export const bootstrap: Bootstrap = {
  user: { id: 'demo', email: 'owner@example.com', name: 'Demo Owner' },
  isSuperAdmin: new URLSearchParams(location.search).has('super'),
  hasProfile: true,
  profile: { full_name: 'Demo Owner', phone: null },
  organizations: [
    { id: 'o1', name: 'Example Traders', role: 'organization_owner', currency: 'PKR', decimals: 2 },
    { id: 'o2', name: 'Second Example Co', role: 'accountant', currency: 'USD', decimals: 2 },
    { id: 'o3', name: 'Member Example Co', role: 'member', currency: 'PKR', decimals: 2 },
    { id: 'o4', name: 'Observer Example Co', role: 'observer', currency: 'PKR', decimals: 2 },
  ],
}

const chart = [
  ['1010', 'Cash at bank', 'asset', 412300],
  ['1200', 'Accounts receivable', 'asset', 186000],
  ['1300', 'Inventory', 'asset', 37760],
  ['2000', 'Accounts payable', 'liability', 94500],
  ['3000', "Owner's equity", 'equity', 473560],
  ['4000', 'Sales', 'revenue', 640000],
  ['5000', 'Cost of goods sold', 'expense', 352000],
  ['6000', 'Salaries', 'expense', 120000],
  ['6100', 'Utilities', 'expense', 20400],
  ['6200', 'Rent', 'expense', 65000],
  ['6300', 'Fuel and transport', 'expense', 14600],
] as const

const accountBalances = chart.map(([code, name, account_type, balance], i) => ({
  id: i + 1, code, name, account_type, balance, transaction_count: 4 + i, last_transaction_date: '2026-10-30', is_postable: true,
}))

const entries = Array.from({ length: 60 }, (_, i) => {
  const amount = 1200 + ((i * 3517) % 88000)
  return {
    id: 1000 - i,
    entry_number: `JE-${2041 - i}`,
    entry_date: `2026-10-${String(30 - (i % 28)).padStart(2, '0')}`,
    description: ['Bank charge', 'Stock sold to Apex Retail', 'Receipt from Apex Retail', 'Shop rent', 'City Power bill'][i % 5],
    reference: null,
    total_amount: amount,
    is_posted: true,
    lines: [
      { id: i * 2 + 1, account_id: 1, description: null, debit_amount: amount, credit_amount: 0 },
      { id: i * 2 + 2, account_id: 6, description: null, debit_amount: 0, credit_amount: amount },
    ],
  }
})

const items = [
  { id: 1, sku: 'CTN-L', name: 'Cartons, large', unit_of_measure: 'pcs', quantity_available: 14, average_unit_cost: 600, total_value: 8400, reorder_point: 20 },
  { id: 2, sku: 'LBL-R', name: 'Labels, roll', unit_of_measure: 'rolls', quantity_available: 6, average_unit_cost: 550, total_value: 3300, reorder_point: 10 },
  { id: 3, sku: 'FOAM', name: 'Packing foam', unit_of_measure: 'pcs', quantity_available: 140, average_unit_cost: 150, total_value: 21000, reorder_point: 40 },
  { id: 4, sku: 'TAPE', name: 'Sealing tape', unit_of_measure: 'rolls', quantity_available: 22, average_unit_cost: 230, total_value: 5060, reorder_point: 10 },
]

const sect = (type: string, name: string) => {
  const accounts = accountBalances.filter((a) => a.account_type === type).map((a) => ({ id: a.id, code: a.code, name: a.name, balance: a.balance }))
  return { name, total: accounts.reduce((s, a) => s + a.balance, 0), accounts }
}

const stockItems = items.map((i, n) => ({ ...i, category_id: n < 2 ? 1 : 2, description: null, reorder_quantity: i.reorder_point * 2, barcode: n % 2 ? null : `89012${1000 + n}`, selling_price: Math.round(i.average_unit_cost * 1.4), lead_time_days: 14, track_lots: n === 1, track_serials: n === 2, costing_method: n === 0 ? 'fifo' : 'average', preferred_supplier_id: 1, income_account_id: null }))
const demoUnits = [{ id: 1, item_id: stockItems[0].id, name: 'Bundle', factor: 25 }, { id: 2, item_id: stockItems[0].id, name: 'Pallet', factor: 500 }]
const demoWarehouses = [{ id: 1, name: 'Main', code: 'MN', address: 'Plot 12, Industrial Area', is_default: true, is_active: true, units: 180, value: 164000, items: 3 }, { id: 2, name: 'North store', code: 'NS', address: null, is_default: false, is_active: true, units: 40, value: 22000, items: 1 }]
const demoOrders = [
  { id: 1, number: 'PO-0003', status: 'draft', supplier_name: 'Noor Packaging', order_date: '2026-11-01', expected_date: '2026-11-15', warehouse_name: 'Main', total: 42000, ordered: 70, received: 0, has_unbilled: false },
  { id: 2, number: 'PO-0002', status: 'partial', supplier_name: 'Noor Packaging', order_date: '2026-10-12', expected_date: '2026-10-26', warehouse_name: 'Main', total: 30000, ordered: 50, received: 30, has_unbilled: true },
  { id: 3, number: 'PO-0001', status: 'received', supplier_name: 'Delta Supplies', order_date: '2026-09-20', expected_date: '2026-10-04', warehouse_name: 'North store', total: 22000, ordered: 40, received: 40, has_unbilled: false },
]
const demoCount = { id: 1, number: 'SC-0001', status: 'open', count_date: '2026-11-02', warehouse_name: 'Main', notes: null, lines: stockItems.map((i, n) => ({ id: n + 1, item_id: i.id, expected: i.quantity_available, counted: n === 0 ? i.quantity_available - 2 : null, item_name: i.name, sku: i.sku, barcode: i.barcode, unit_of_measure: i.unit_of_measure, average_unit_cost: i.average_unit_cost, current: i.quantity_available })) }
const categories = [
  { id: 1, name: 'Packaging', description: 'Cartons and labels', inventory_account_id: 3, expense_account_id: 7 },
  { id: 2, name: 'Supplies', description: null, inventory_account_id: 3, expense_account_id: 7 },
]
const chartRows = accountBalances.map((a) => ({ id: a.id, code: a.code, name: a.name, account_type: a.account_type, parent_id: null, description: null, group: null, report_category: null, is_postable: true, is_active: true }))
const movements = [
  { id: 1, item_id: 1, transaction_type: 'in', quantity: 50, unit_cost: 600, total_cost: 30000, reference: 'PO-114', description: 'Delivery from Noor Packaging', transaction_date: '2026-10-28', item: { name: 'Cartons, large', sku: 'CTN-L' } },
  { id: 2, item_id: 1, transaction_type: 'out', quantity: -36, unit_cost: null, total_cost: null, reference: null, description: 'Used for October orders', transaction_date: '2026-10-30', item: { name: 'Cartons, large', sku: 'CTN-L' } },
  { id: 3, item_id: 2, transaction_type: 'adjustment', quantity: -2, unit_cost: null, total_cost: null, reference: null, description: 'Stock count correction', transaction_date: '2026-10-31', item: { name: 'Labels, roll', sku: 'LBL-R' } },
]
const voucherLine = (id: number, item: (typeof items)[number], qty: number) => ({ id, item_id: item.id, line_number: id, quantity_requested: qty, quantity_actual: null, unit_cost_estimated: item.average_unit_cost, total_cost: qty * item.average_unit_cost, item: { name: item.name, sku: item.sku } })
const vouchers = [
  { id: 1, voucher_number: 'PV-2026-0012', voucher_type: 'purchase', status: 'pending_finance', requested_date: '2026-11-01', vendor_name: 'Noor Packaging', description: 'Cartons for November', payment_type: 'credit', total_estimated_cost: 30000, approval_deadline: '2026-11-08', lines: [voucherLine(1, items[0], 50)], attachments: [] },
  { id: 2, voucher_number: 'IV-2026-0007', voucher_type: 'issuance', status: 'pending_finance', requested_date: '2026-11-02', purpose: 'Eid gift packing', destination: 'Warehouse B', description: 'Foam for gift packing', payment_type: 'cash', total_estimated_cost: 3000, approval_deadline: '2026-11-09', lines: [voucherLine(2, items[2], 20)], attachments: [] },
  { id: 3, voucher_number: 'PV-2026-0011', voucher_type: 'purchase', status: 'approved', requested_date: '2026-10-24', vendor_name: 'City Print House', description: 'Label rolls', payment_type: 'bank_transfer', total_estimated_cost: 5500, lines: [voucherLine(3, items[1], 10)], attachments: [{ id: 1, file_name: 'quote-city-print.pdf' }] },
  { id: 6, voucher_number: 'PV-2026-0010', voucher_type: 'purchase', status: 'receiving', requested_date: '2026-10-20', vendor_name: 'City Print House', description: 'Label rolls', payment_type: 'credit', total_estimated_cost: 5500, lines: [voucherLine(6, items[1], 10)], attachments: [] },
  { id: 4, voucher_number: 'PV-2026-0009', voucher_type: 'purchase', status: 'completed', requested_date: '2026-10-11', vendor_name: 'Noor Packaging', description: 'Sealing tape', payment_type: 'credit', total_estimated_cost: 4600, lines: [voucherLine(4, items[3], 20)], attachments: [] },
  { id: 5, voucher_number: 'PV-2026-0008', voucher_type: 'purchase', status: 'rejected', requested_date: '2026-10-05', vendor_name: 'Gulf Trading', description: 'Foam at a higher price', rejection_reason: 'Noor Packaging quoted less.', payment_type: 'credit', total_estimated_cost: 18000, lines: [voucherLine(5, items[2], 100)], attachments: [] },
]
const suppliers = [
  { id: 1, supplier_code: 'SUP-001', name: 'Noor Packaging', contact_person: 'Sana Malik', email: 'orders@example.com', phone: '+92 300 0000000', currency: 'PKR', credit_limit: 500000, current_balance: 94500, payment_terms: 'net_30', status: 'active', is_preferred: true, billing_city: 'Lahore', billing_country: 'Pakistan' },
  { id: 2, supplier_code: 'SUP-002', name: 'City Print House', contact_person: null, email: 'hello@example.com', phone: null, currency: 'PKR', credit_limit: null, current_balance: 0, payment_terms: 'due_on_receipt', status: 'active', is_preferred: false },
  { id: 3, supplier_code: 'SUP-003', name: 'Gulf Trading', contact_person: 'Omar Aziz', email: null, phone: '+92 321 0000000', currency: 'USD', credit_limit: 20000, current_balance: 0, payment_terms: 'net_60', status: 'suspended', is_preferred: false },
]
const members = [
  { id: 'm1', user_id: 'demo', email: 'owner@example.com', full_name: 'Demo Owner', role: 'organization_owner', joined_at: '2026-01-04' },
  { id: 'm2', user_id: 'u2', email: 'accounts@example.com', full_name: 'Sample Accountant', role: 'accountant', joined_at: '2026-02-11' },
  { id: 'm3', user_id: 'u3', email: 'warehouse@example.com', full_name: null, role: 'member', joined_at: '2026-06-20' },
]

const docLine = (id: number, description: string, quantity: number, unit_price: number, taxed = true) => ({ id, description, account_id: 6, quantity, unit_price, tax_rate_id: taxed ? 1 : null, tax_rate: taxed ? 17 : 0, tax_name: taxed ? 'GST' : null, amount: quantity * unit_price, tax_amount: taxed ? quantity * unit_price * 0.17 : 0 })
const sampleDocs = [
  { id: 1, kind: 'invoice', number: 'INV-0004', status: 'draft', party_name: 'Apex Retail', issue_date: '2026-11-02', due_date: '2026-12-02', subtotal: 100000, tax_total: 17000, total: 117000, amount_paid: 0, balance: 117000 },
  { id: 2, kind: 'invoice', number: 'INV-0003', status: 'posted', party_name: 'Sunrise Foods', issue_date: '2026-10-20', due_date: '2026-11-19', subtotal: 50000, tax_total: 8500, total: 58500, amount_paid: 0, balance: 58500 },
  { id: 3, kind: 'invoice', number: 'INV-0002', status: 'partial', party_name: 'Apex Retail', issue_date: '2026-08-05', due_date: '2026-09-04', subtotal: 200000, tax_total: 34000, total: 234000, amount_paid: 100000, balance: 134000 },
  { id: 4, kind: 'invoice', number: 'INV-0001', status: 'paid', party_name: 'Delta Traders', issue_date: '2026-07-01', due_date: '2026-07-31', subtotal: 40000, tax_total: 6800, total: 46800, amount_paid: 46800, balance: 0 },
  { id: 5, kind: 'bill', number: 'BILL-0002', status: 'posted', party_name: 'City Power', issue_date: '2026-10-01', due_date: '2026-10-15', subtotal: 18750, tax_total: 0, total: 18750, amount_paid: 0, balance: 18750 },
  { id: 6, kind: 'bill', number: 'BILL-0001', status: 'paid', party_name: 'Noor Packaging', issue_date: '2026-09-10', due_date: '2026-10-10', subtotal: 30000, tax_total: 5100, total: 35100, amount_paid: 35100, balance: 0 },
]
const sampleDoc = (id: unknown) => {
  const d = sampleDocs.find((x) => String(x.id) === String(id)) ?? sampleDocs[0]
  return { ...d, customer_id: null, supplier_id: null, notes: null, void_reason: null, suggested_control_account_id: null, lines: [docLine(1, 'Packed goods', 10, d.subtotal / 10)], payments: d.amount_paid ? [{ id: 1, payment_date: '2026-09-01', amount: d.amount_paid, reference: 'Bank transfer' }] : [] }
}
const aged = (rows: { party_name: string; current?: number; d1_30?: number; d31_60?: number; d61_90?: number; d90_plus?: number }[]) => {
  const full = rows.map((r) => ({ current: 0, d1_30: 0, d31_60: 0, d61_90: 0, ...r, d90_plus: r.d90_plus ?? 0, total: (r.current ?? 0) + (r.d1_30 ?? 0) + (r.d31_60 ?? 0) + (r.d61_90 ?? 0) + (r.d90_plus ?? 0) }))
  const sum = (k: 'current' | 'd1_30' | 'd31_60' | 'd61_90' | 'd90_plus' | 'total') => full.reduce((t, r) => t + r[k], 0)
  return { as_of: '2026-11-03', rows: full, totals: { party_name: 'Total', current: sum('current'), d1_30: sum('d1_30'), d31_60: sum('d31_60'), d61_90: sum('d61_90'), d90_plus: sum('d90_plus'), total: sum('total') } }
}
const bookSamples: Record<string, (args: unknown[]) => unknown> = {
  getWorkSummary: () => ({ overdue_invoices: 1, overdue_bills: 1, unmatched_bank_lines: 2 }),
  listDocuments: (args) => sampleDocs.filter((d) => d.kind === args[1]),
  getDocument: (args) => sampleDoc(args[1]),
  previewDocument: (args) => {
    const chosen = (args[2] as { control_account_id?: number | null } | undefined)?.control_account_id
    return { problems: chosen ? [] : ['Choose the account that tracks what customers owe you.'], suggested_control_account_id: null, lines: [...(chosen ? [{ account_id: 2, code: '1200', name: 'Accounts receivable', debit: 117000, credit: 0 }] : []), { account_id: 6, code: '4000', name: 'Sales', debit: 0, credit: 100000 }, { account_id: 4, code: '2000', name: 'GST payable', debit: 0, credit: 17000 }] }
  },
  listCustomers: () => [{ id: 1, name: 'Apex Retail', email: 'ap@example.com', phone: null, address: null, tax_id: null, receivable_account_id: null, balance: 251000 }, { id: 2, name: 'Sunrise Foods', email: null, phone: '+92 300 0000000', address: null, tax_id: null, receivable_account_id: 2, balance: 58500 }],
  listTaxRates: () => [{ id: 1, name: 'GST', rate: 17, sales_account_id: 4, purchase_account_id: 3, is_active: true }, { id: 2, name: 'Old rate', rate: 16, sales_account_id: 4, purchase_account_id: 3, is_active: false }],
  getTaxSummary: () => ({ from: '2026-10-01', to: '2026-11-03', output_tax: 25500, input_tax: 5100, net_tax: 20400, rates: [{ rate_name: 'GST', rate: 17, sales: 150000, output_tax: 25500, purchases: 30000, input_tax: 5100 }] }),
  listTaxReturns: () => [{ id: 1, period_from: '2026-07-01', period_to: '2026-09-30', output_tax: 40800, input_tax: 5100, net_tax: 35700, reference: 'Q3 return', filed_at: '2026-10-14' }],
  getAgedReport: (args) => (args[1] === 'invoice' ? aged([{ party_name: 'Apex Retail', current: 117000, d61_90: 134000 }, { party_name: 'Sunrise Foods', current: 58500 }]) : aged([{ party_name: 'City Power', d1_30: 18750 }])),
  getReconciliation: (args) => {
    const balance = (args[2] as { statement_balance?: number | null } | undefined)?.statement_balance
    const outstanding = [{ id: 11, date: '2026-10-30', entry_number: 'JE-2040', description: 'Cheque to City Power', amount: -18750 }]
    return { as_of: '2026-11-03', book_balance: 412300, outstanding, history: [], summary: balance == null ? null : { outstanding: -18750, unrecorded: -350, reconciled: 430700, difference: balance - 430700, balanced: false }, lines: [
      { id: 1, date: '2026-10-28', description: 'Deposit, Apex Retail', reference: null, amount: 100000, status: 'unmatched', candidates: [{ id: 10, date: '2026-10-27', entry_number: 'JE-2039', description: 'Receipt from Apex Retail', amount: 100000 }] },
      { id: 2, date: '2026-10-31', description: 'Monthly bank charge', reference: null, amount: -350, status: 'unmatched', candidates: [] },
      { id: 3, date: '2026-10-15', description: 'Rent', reference: null, amount: -65000, status: 'matched', candidates: [] },
    ] }
  },
  listBudgets: () => [{ id: 1, name: 'Plan', year: 2026, total: 1800000 }],
  getBudgetReport: () => {
    const row = (account_id: number, code: string, name: string, account_type: string, month: number, spent: number) => ({ account_id, code, name, account_type, budget: Array(12).fill(month), actual: Array.from({ length: 12 }, (_v, i) => (i < 10 ? spent : 0)), budget_total: month * 12, actual_total: spent * 10, variance: spent * 10 - month * 12 })
    const accounts = [row(6, '4000', 'Sales', 'revenue', 70000, 64000), row(8, '6000', 'Salaries', 'expense', 12000, 12000), row(10, '6200', 'Rent', 'expense', 6000, 6500), row(9, '6100', 'Utilities', 'expense', 1500, 2040)]
    return { id: 1, name: 'Plan', year: 2026, accounts, revenue: { budget: 840000, actual: 640000 }, expense: { budget: 234000, actual: 205400 } }
  },
  getForecast: (args) => {
    const n = Number(args[1]) || 6
    return { months_of_history: 9, confidence: 'reasonable', cash_today: 412300, history: [], rows: Array.from({ length: n }, (_v, i) => {
      const d = new Date(2026, 10 + i, 1)
      const revenue = 420000 + i * 8000, expenses = 360000 + i * 3000
      return { month: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`, revenue, expenses, net: revenue - expenses, receivable_due: i === 0 ? 175500 : 0, payable_due: i === 0 ? 18750 : 0, cash: 412300 + (i + 1) * 60000 + (i * (i + 1) * 2500) }
    }) }
  },
  getBooksLock: () => ({ closed_through: '2026-09-30', history: [{ id: 1, through_date: '2026-09-30', notes: 'Q3 done', closed_at: '2026-10-05', reopened_at: null, reopen_reason: null }] }),
  getCloseChecklist: () => ({ balanced: true, draft_documents: 1, unmatched_bank_lines: 2, pending_proposals: 0, unposted_stock: 0, unposted_vouchers: 1 }),
  listUnpostedStock: () => [],
  ...Object.fromEntries(['reverseEntry', 'closeBooks', 'reopenBooks', 'postStockMovement', 'recordStockMovement', 'saveCustomer', 'archiveCustomer', 'saveTaxRate', 'deleteDocument', 'postDocument', 'recordPayment', 'voidDocument', 'recordTaxReturn', 'matchStatementLine', 'unmatchStatementLine', 'ignoreStatementLine', 'createEntryFromStatementLine', 'completeReconciliation', 'deleteBudget'].map((m) => [m, () => ({})])),
  saveDocument: () => ({ id: 1 }),
  saveBudget: () => ({ id: 1 }),
  importStatement: () => ({ added: 12, skipped: 0 }),
}

const handlers: Record<string, (args: unknown[]) => unknown> = {
  getDashboardBundle: () => ({ financialMetrics: { totalRevenue: 640000, totalExpenses: 572000 }, accountBalances }),
  generateBalanceSheet: () => ({
    assetSections: [sect('asset', 'Assets')], liabilitySections: [sect('liability', 'Liabilities')], equitySections: [sect('equity', 'Equity')],
    totalAssets: 636060, totalLiabilities: 94500, totalEquity: 541560, isBalanced: true,
  }),
  generateIncomeStatement: () => ({
    revenue: { total: 640000, breakdown: [{ account: 'Sales', amount: 640000 }] },
    costOfSales: { total: 352000, breakdown: [{ account: 'Cost of goods sold', amount: 352000 }] },
    operatingExpenses: { total: 220000, breakdown: [{ account: 'Salaries', amount: 120000 }, { account: 'Rent', amount: 65000 }, { account: 'Utilities', amount: 20400 }, { account: 'Fuel and transport', amount: 14600 }] },
    otherExpenses: { total: 0, breakdown: [] },
    grossProfit: 288000,
    netIncome: 68000,
  }),
  getTrialBalance: () => accountBalances.map((a) => {
    const debit = a.account_type === 'asset' || a.account_type === 'expense'
    return { account_id: a.id, account_code: a.code, account_name: a.name, account_type: a.account_type, debit_balance: debit ? a.balance : 0, credit_balance: debit ? 0 : a.balance }
  }),
  getJournalEntriesWithLines: () => entries,
  getAccounts: () => chartRows,
  createAccount: () => ({ id: Date.now() }),
  updateAccount: () => ({}),
  deleteAccount: () => null,
  getInventoryCategories: () => categories,
  createInventoryCategory: () => ({ id: Date.now() }),
  updateInventoryCategory: () => ({}),
  deleteInventoryCategory: () => null,
  createInventoryItem: () => ({ id: Date.now() }),
  updateInventoryItem: () => ({}),
  deleteInventoryItem: () => null,
  getInventoryTransactions: () => movements,
  createInventoryTransaction: () => ({ id: Date.now() }),
  getVouchers: (args) => {
    const f = (args[1] ?? {}) as { status?: string[]; voucher_type?: string[]; search?: string }
    return vouchers.filter((v) => (!f.status || f.status.includes(v.status)) && (!f.voucher_type || f.voucher_type.includes(v.voucher_type)) && (!f.search || JSON.stringify(v).toLowerCase().includes(f.search.toLowerCase())))
  },
  getVoucher: (args) => vouchers.find((v) => v.id === args[0]) ?? null,
  createVoucher: () => ({ id: Date.now() }),
  ...Object.fromEntries(['submitForApproval', 'approveVoucher', 'rejectVoucher', 'renewExpiredVoucher', 'executeVoucher', 'postVoucher', 'completeVoucher', 'deleteVoucher', 'deleteAttachment'].map((m) => [m, () => ({})])),
  previewVoucherPosting: (args) => {
    const payable = (args[1] as { payable_account_id?: number | null } | undefined)?.payable_account_id
    const owed = payable ?? null
    return { total: 5500, needs_payable: !owed, suggested_payable_account_id: null, problems: owed ? [] : ['Choose the account that tracks what you owe this supplier.'], lines: [{ account_id: 3, code: '1300', name: 'Inventory', debit: 5500, credit: 0 }, ...(owed ? [{ account_id: 4, code: '2000', name: 'Accounts payable', debit: 0, credit: 5500 }] : [])] }
  },
  getSuppliers: () => suppliers,
  ...bookSamples,
  getSuppliersForVoucher: () => suppliers.map(({ id, supplier_code, name }) => ({ id, supplier_code, name })),
  getSupplierContacts: () => [{ id: 1, name: 'Sana Malik', title: 'Sales', email: 'orders@example.com', phone: null, mobile: null, is_primary: true, is_billing: false }],
  getSupplierAccountMappings: () => ({ payable_account_id: 4 }),
  ...Object.fromEntries(['createSupplier', 'updateSupplier', 'deleteSupplier', 'addSupplierContact', 'deleteSupplierContact', 'updateUserProfile'].map((m) => [m, () => ({})])),
  getAccountBalances: () => accountBalances,
  getAccountTransactions: () => {
    let balance = 0
    return Array.from({ length: longMode() ? 150 : 60 }, (_, i) => {
      const amount = 1200 + ((i * 3517) % 40000)
      const debit = i % 3 !== 2
      balance += debit ? amount : -amount
      const day = new Date(2026, 3, 1 + Math.floor((i * 215) / (longMode() ? 150 : 60)))
      return { id: i + 1, entry_id: i + 1, entry_number: `JE-${1000 + i}`, entry_date: `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, '0')}-${String(day.getDate()).padStart(2, '0')}`, description: ['Bank charge', 'Stock sold to Apex Retail', 'Receipt from Apex Retail', 'Shop rent', 'City Power bill'][i % 5], reference: i % 4 ? null : `REF-${i}`, debit_amount: debit ? amount : 0, credit_amount: debit ? 0 : amount, balance }
    })
  },
  getInventoryItems: () => stockItems,
  listWarehouses: () => demoWarehouses,
  getAllUnits: () => demoUnits,
  findSerial: () => [{ id: 1, serial_number: 'FOAM-S0001', in_stock: true, item_id: stockItems[2].id, sku: stockItems[2].sku, item_name: stockItems[2].name, warehouse_name: 'Main', history: [] }],
  listBoms: () => [{ id: 1, item_id: stockItems[0].id, output_quantity: 1, notes: null, sku: stockItems[0].sku, name: stockItems[0].name, unit_of_measure: stockItems[0].unit_of_measure, on_hand: stockItems[0].quantity_available, cost_each: 610, can_build: 6, lines: stockItems.slice(1, 3).map((i, n) => ({ id: n + 1, item_id: i.id, quantity: n + 1, sku: i.sku, name: i.name, unit_of_measure: i.unit_of_measure, on_hand: i.quantity_available, cost: i.average_unit_cost })) }, { id: 2, item_id: stockItems[3].id, output_quantity: 10, notes: null, sku: stockItems[3].sku, name: stockItems[3].name, unit_of_measure: stockItems[3].unit_of_measure, on_hand: stockItems[3].quantity_available, cost_each: 42, can_build: 0, lines: [{ id: 3, item_id: stockItems[1].id, quantity: 20, sku: stockItems[1].sku, name: stockItems[1].name, unit_of_measure: stockItems[1].unit_of_measure, on_hand: stockItems[1].quantity_available, cost: stockItems[1].average_unit_cost }] }],
  listAssemblies: () => [{ id: 1, number: 'AS-0002', status: 'built', item_id: stockItems[0].id, quantity: 4, build_date: '2026-11-01', components_cost: 2440, extra_cost: 300, sku: stockItems[0].sku, name: stockItems[0].name, unit_of_measure: stockItems[0].unit_of_measure, warehouse_name: 'Main' }, { id: 2, number: 'AS-0001', status: 'reversed', item_id: stockItems[0].id, quantity: 2, build_date: '2026-10-20', components_cost: 1220, extra_cost: 0, sku: stockItems[0].sku, name: stockItems[0].name, unit_of_measure: stockItems[0].unit_of_measure, warehouse_name: 'Main' }],
  getAllLevels: () => [],
  getItemDetail: (args) => {
    const i = stockItems.find((x) => Number(x.id) === Number(args[1])) ?? stockItems[0]
    return { ...i, category_name: 'Packaging', supplier_name: 'Noor Packaging', on_order: 20, units: demoUnits.filter((u) => u.item_id === i.id), serials: i.track_serials ? Array.from({ length: 14 }, (_v, n) => ({ id: n + 1, serial_number: `${i.sku}-S${String(n + 1).padStart(4, '0')}`, warehouse_name: 'Main' })) : [], levels: [{ warehouse_id: 1, warehouse_name: 'Main', quantity: i.quantity_available }], lots: i.track_lots ? [{ id: 1, lot_number: 'LOT-2041', expiry_date: '2026-11-20', quantity: 12, warehouse_name: 'Main', warehouse_id: 1, status: 'soon' }, { id: 2, lot_number: 'LOT-2107', expiry_date: '2027-06-01', quantity: 20, warehouse_name: 'Main', warehouse_id: 1, status: 'ok' }] : [] }
  },
  getStockCard: () => [
    { id: 3, date: '2026-10-31', transaction_type: 'adjustment', quantity: -2, unit_cost: 600, total_cost: 1200, reference: 'SC-0001', description: 'Stock count', journal_entry_id: 9, warehouse_name: 'Main', lots: null, serials: null, balance: 12 },
    { id: 2, date: '2026-10-30', transaction_type: 'out', quantity: -36, unit_cost: 600, total_cost: 21600, reference: 'INV-0012', description: 'Invoice', journal_entry_id: 8, warehouse_name: 'Main', lots: null, balance: 14 },
    { id: 1, date: '2026-10-28', transaction_type: 'in', quantity: 50, unit_cost: 600, total_cost: 30000, reference: 'GR-0002', description: 'PO-0002', journal_entry_id: 7, warehouse_name: 'Main', lots: null, balance: 50 },
  ],
  getSettings: () => ({ grni_account_id: 4, grni_code: '2000', grni_name: 'Accounts payable', default_costing_method: 'average' }),
  listPurchaseOrders: () => demoOrders,
  getPurchaseOrder: (args) => {
    const o = demoOrders.find((x) => x.id === Number(args[1])) ?? demoOrders[0]
    return { ...o, supplier_id: 1, warehouse_id: 1, notes: null, lines: stockItems.slice(0, 2).map((i, n) => ({ id: n + 1, item_id: i.id, quantity: 25, quantity_received: o.status === 'received' ? 25 : o.status === 'partial' ? 15 : 0, unit_cost: i.average_unit_cost, item_name: i.name, sku: i.sku, unit_of_measure: i.unit_of_measure, track_lots: i.track_lots, track_serials: i.track_serials, unit_id: n === 0 ? 1 : null, unit_name: n === 0 ? 'Bundle' : null, unit_factor: n === 0 ? 25 : 1 })), receipts: o.received ? [{ id: 1, number: 'GR-0002', receipt_date: '2026-10-28', total: 18000, bill_id: null, bill_number: null }] : [] }
  },
  listStockCounts: () => [{ id: 1, number: 'SC-0001', status: 'open', count_date: '2026-11-02', warehouse_name: 'Main', lines: stockItems.length, counted: 1, differences: 1 }],
  getStockCount: () => demoCount,
  getReorderPlan: () => stockItems.map((i, n) => ({ item_id: i.id, sku: i.sku, name: i.name, unit_of_measure: i.unit_of_measure, unit_cost: i.average_unit_cost, on_hand: i.quantity_available, on_order: n === 0 ? 20 : 0, used_90_days: 90 - n * 20, lead_time_days: 14, supplier_name: 'Noor Packaging', daily_usage: (90 - n * 20) / 90, days_of_cover: Math.floor(i.quantity_available / Math.max((90 - n * 20) / 90, 0.1)), suggested: n < 2 ? 40 : 0, stockout_risk: n === 1 })),
  getAnalysis: () => ({ total_value: 186000, usage_12_months: 610000, turnover: 3.3, by_category: [{ category_name: 'Packaging', value: 142000, items: 2 }, { category_name: 'Supplies', value: 44000, items: 1 }], slow_moving: stockItems.slice(0, 1).map((i) => ({ item_id: i.id, sku: i.sku, name: i.name, on_hand: i.quantity_available, unit_of_measure: i.unit_of_measure, value: i.total_value, last_used: '2026-05-02', days_idle: 185 })), abc: stockItems.map((i, n) => ({ item_id: i.id, sku: i.sku, name: i.name, usage_value: 400000 - n * 150000, share: 66 - n * 25, class: ['A', 'B', 'C'][Math.min(n, 2)] })), expiring: [{ id: 1, lot_number: 'LOT-2041', expiry_date: '2026-11-20', quantity: 12, item_name: stockItems[1].name, item_id: stockItems[1].id, warehouse_name: 'Main', value: 2400, status: 'soon' }] }),
  getBooksCheck: () => ({ agrees: true, rows: [{ account_id: 3, code: '1300', name: 'Inventory', stock_value: 186000, book_value: 186000, difference: 0 }] }),
  ...Object.fromEntries(['saveWarehouse', 'transferStock', 'saveItemDetails', 'importItems', 'savePurchaseOrder', 'approvePurchaseOrder', 'cancelPurchaseOrder', 'receivePurchaseOrder', 'createBillFromReceipts', 'createStockCount', 'saveStockCountLines', 'cancelStockCount', 'postStockCount', 'createOrdersFromPlan', 'saveSettings', 'createGrniAccount', 'saveUnit', 'deleteUnit', 'saveBom', 'deleteBom', 'buildAssembly', 'reverseAssembly', 'setItemCosting', 'setDefaultCosting'].map((m) => [m, () => ({ id: 1, orders: [1] })])),
  getLowStockItems: () => items.filter((i) => i.quantity_available <= i.reorder_point),
  getVoucherStats: () => ({ total_vouchers: 5, pending_approval: 2, approved: 1, rejected: 1, expired: 0, completed: 1, total_value: 61100 }),
  createJournalEntry: () => ({ id: 9999 }),
  monthly: () => ['2025-12', '2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08', '2026-09', '2026-10', '2026-11'].map((month, i) => ({
    month, revenue: 410000 + ((i * 53000) % 240000), expenses: 330000 + ((i * 37000) % 180000),
  })),
}

/** `?long=1` makes lists as long as a real business's, to check how screens hold up. */
const LONG: Record<string, number> = { getAccounts: 126, getAccountBalances: 126, getTrialBalance: 126, getJournalEntriesWithLines: 200, getInventoryItems: 80, getInventoryTransactions: 120, getVouchers: 70, getSuppliers: 45 }
const longMode = () => {
  if (new URLSearchParams(location.search).has('long')) sessionStorage.setItem('long', '1')
  return sessionStorage.getItem('long') === '1'
}
const stretch = (rows: Record<string, unknown>[], n: number, method: string) => Array.from({ length: n }, (_, i) => {
  const row = rows[i % rows.length]
  if (i < rows.length) return row
  const text = (k: string) => (typeof row[k] === 'string' ? { [k]: `${row[k]} ${i}` } : {})
  const ids = method === 'getTrialBalance' ? { account_id: i + 1 } : { id: i + 1 }
  const nested = method === 'getAccounts' ? { parent_id: row.id } : {}
  return { ...row, ...ids, ...nested, ...text('name'), ...text('account_name'), ...text('code'), ...text('account_code'), ...text('sku'), ...text('supplier_code'), ...text('voucher_number'), ...text('entry_number') }
})

export async function respond(method: string, args: unknown[]) {
  await new Promise((r) => setTimeout(r, 120))
  const handler = handlers[method]
  if (!handler) throw new Error(`No sample data for ${method}`)
  const result = handler(args)
  return longMode() && LONG[method] && Array.isArray(result) ? stretch(result, LONG[method], method) : result
}

/** Sample answers for the app's REST routes. Saves succeed without changing anything. */
export async function demoRest(path: string, method: string, _body: unknown) {
  await new Promise((r) => setTimeout(r, 120))
  if (method !== 'GET') return { id: 'o1' }
  if (path.endsWith('/members')) return { members }
  if (path.startsWith('/api/oauth/client')) return { name: 'Claude Desktop' }
  if (path === '/api/super-admin/overview') {
    return {
      stats: { totalUsers: 3, totalOrganizations: 2, superAdmins: 1, activeMemberships: 4 },
      users: members.map((m, i) => ({ id: m.user_id, email: m.email, full_name: m.full_name, is_super_admin: i === 0 })),
      organizations: bootstrap.organizations.map((o) => ({ id: o.id, name: o.name, member_count: 3, owner_emails: ['owner@example.com'], created_at: '2026-01-04' })),
      memberships: members.map((m) => ({ id: m.id, organization_name: 'Example Traders', email: m.email, role: m.role })),
    }
  }
  throw new Error(`No sample data for ${path}`)
}

const pause = (ms: number) => new Promise((r) => setTimeout(r, ms))

/** Scripted replies, so the agent's screens can be built without calling the model. */
export async function streamDemo(body: AgentRequest, onEvent: (e: AgentEvent) => void) {
  const last = body.messages.at(-1)?.text.toLowerCase() ?? ''
  onEvent({ type: 'status', text: 'Looking at your accounts' })
  await pause(500)
  if (/paid|bought|received|customer/.test(last)) {
    onEvent({ type: 'text', text: 'Here is the entry. Please check it.' })
    const proposal: Proposal = {
      id: `demo-${Date.now()}`, source: 'app', source_name: null, status: 'pending',
      date: body.today, description: 'Rent paid from bank',
      explanation: 'This records 65,000 of rent as a cost, and takes the same amount out of your bank balance.',
      confidence: 'high',
      lines: [{ account_id: 10, code: '6200', name: 'Rent', debit: 65000, credit: 0 }, { account_id: 1, code: '1010', name: 'Cash at bank', debit: 0, credit: 65000 }],
    }
    demoProposals.unshift(proposal)
    onEvent({ type: 'proposal', proposal })
    return
  }
  onEvent({ type: 'status', text: 'Reading your income statement' })
  await pause(500)
  onEvent({ type: 'text', text: `[Sample: I can see "${body.page?.title}" at ${body.page?.url}, filters: ${body.page?.filters.join(', ') || 'none'}, ${body.page?.text.length} characters of page.] ` })
  for (const word of 'Sample answer: you made 68,000 profit from 640,000 in sales. Your biggest cost after stock is salaries at 120,000.'.split(' ')) {
    onEvent({ type: 'text', text: `${word} ` })
    await pause(25)
  }
}

const demoProposals: Proposal[] = [{
  id: 'demo-mcp', source: 'mcp', source_name: 'My laptop', status: 'pending',
  date: '2026-11-02', description: 'City Power bill', confidence: 'medium',
  explanation: 'This records 18,750 of electricity as a cost, and adds it to the bills you still have to pay.',
  lines: [{ account_id: 9, code: '6100', name: 'Utilities', debit: 18750, credit: 0 }, { account_id: 4, code: '2000', name: 'Accounts payable', debit: 0, credit: 18750 }],
}]
export const listDemoProposals = async () => [...demoProposals]
export const decideDemoProposal = async (id: string) => {
  const i = demoProposals.findIndex((p) => p.id === id)
  if (i >= 0) demoProposals.splice(i, 1)
  return { status: 'ok' }
}
export const demoConnections: Connection[] = [{ id: 'c1', name: 'My laptop', token_hint: 'x7Qa', can_record: false, created_at: '2026-11-01', last_used_at: '2026-11-02' }]
export const addDemoConnection = async (name: string, canRecord: boolean) => {
  const row: Connection = { id: `c${Date.now()}`, name, token_hint: 'demo', can_record: canRecord, created_at: '2026-11-03', last_used_at: null }
  demoConnections.unshift(row)
  return { token: 'acct_sample_token_for_demo_only', row }
}
export const removeDemoConnection = async (id: string) => {
  const i = demoConnections.findIndex((c) => c.id === id)
  if (i >= 0) demoConnections.splice(i, 1)
  return { status: 'revoked' }
}

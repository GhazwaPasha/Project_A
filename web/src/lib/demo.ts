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

const stockItems = items.map((i, n) => ({ ...i, category_id: n < 2 ? 1 : 2, description: null, reorder_quantity: i.reorder_point * 2 }))
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
  getSuppliers: () => suppliers,
  getSuppliersForVoucher: () => suppliers.map(({ id, supplier_code, name }) => ({ id, supplier_code, name })),
  getSupplierContacts: () => [{ id: 1, name: 'Sana Malik', title: 'Sales', email: 'orders@example.com', phone: null, mobile: null, is_primary: true, is_billing: false }],
  getSupplierAccountMappings: () => ({ payable_account_id: 4 }),
  ...Object.fromEntries(['createSupplier', 'updateSupplier', 'deleteSupplier', 'addSupplierContact', 'deleteSupplierContact', 'updateUserProfile'].map((m) => [m, () => ({})])),
  getAccountBalances: () => accountBalances,
  getAccountTransactions: () => entries.slice(0, 8).map((e, i) => ({ id: e.id, entry_number: e.entry_number, entry_date: e.entry_date, description: e.description, debit_amount: i % 2 ? 0 : e.total_amount, credit_amount: i % 2 ? e.total_amount : 0, balance: 200000 + i * 1000 })),
  getInventoryItems: () => stockItems,
  getLowStockItems: () => items.filter((i) => i.quantity_available <= i.reorder_point),
  getVoucherStats: () => ({ total_vouchers: 5, pending_approval: 2, approved: 1, rejected: 1, expired: 0, completed: 1, total_value: 61100 }),
  createJournalEntry: () => ({ id: 9999 }),
  monthly: () => ['2025-12', '2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08', '2026-09', '2026-10', '2026-11'].map((month, i) => ({
    month, revenue: 410000 + ((i * 53000) % 240000), expenses: 330000 + ((i * 37000) % 180000),
  })),
}

/** `?long=1` makes lists as long as a real business's, to check how screens hold up. */
const LONG: Record<string, number> = { getAccounts: 126, getAccountBalances: 126, getTrialBalance: 126, getJournalEntriesWithLines: 200, getAccountTransactions: 150, getInventoryItems: 80, getInventoryTransactions: 120, getVouchers: 70, getSuppliers: 45 }
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

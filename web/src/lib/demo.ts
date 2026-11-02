/** Sample data for building screens locally with `?demo=1`. Loaded only in development. */
import type { AgentEvent, AgentRequest, Bootstrap, Connection, Proposal } from './api'

export const bootstrap: Bootstrap = {
  user: { id: 'demo', email: 'owner@example.com', name: 'Demo Owner' },
  isSuperAdmin: false,
  hasProfile: true,
  organizations: [
    { id: 'o1', name: 'Example Traders', role: 'organization_owner', currency: 'PKR', decimals: 2 },
    { id: 'o2', name: 'Second Example Co', role: 'accountant', currency: 'USD', decimals: 2 },
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
  getAccounts: () => accountBalances.map((a) => ({ id: a.id, code: a.code, name: a.name })),
  getAccountBalances: () => accountBalances,
  getAccountTransactions: () => entries.slice(0, 8).map((e, i) => ({ id: e.id, entry_number: e.entry_number, entry_date: e.entry_date, description: e.description, debit_amount: i % 2 ? 0 : e.total_amount, credit_amount: i % 2 ? e.total_amount : 0, balance: 200000 + i * 1000 })),
  getInventoryItems: () => items,
  getLowStockItems: () => items.filter((i) => i.quantity_available <= i.reorder_point),
  getVoucherStats: () => ({ pending_approval: 2 }),
  createJournalEntry: () => ({ id: 9999 }),
  monthly: () => ['2025-12', '2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08', '2026-09', '2026-10', '2026-11'].map((month, i) => ({
    month, revenue: 410000 + ((i * 53000) % 240000), expenses: 330000 + ((i * 37000) % 180000),
  })),
}

export async function respond(method: string, args: unknown[]) {
  await new Promise((r) => setTimeout(r, 120))
  const handler = handlers[method]
  if (!handler) throw new Error(`No sample data for ${method}`)
  return handler(args)
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

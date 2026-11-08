/**
 * A small-business chart of accounts, fully classified, so a new organization's reports, cash flow and control
 * checks work from the first entry. Seeded when an organization is created, or on request while its chart is empty.
 */

type Exec = <T = unknown>(strings: TemplateStringsArray, ...values: unknown[]) => PromiseLike<T>

type Starter = {
  code: string
  name: string
  type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense'
  category: string
  role?: string
  control?: boolean
  cash?: 'cash' | 'operating' | 'investing' | 'financing'
  pl?: 'investing' | 'financing' | 'income_tax'
  contra?: boolean
  description?: string
}

export const STARTER_CHART: Starter[] = [
  { code: '1000', name: 'Cash on hand', type: 'asset', category: 'current_asset', role: 'cash', cash: 'cash' },
  { code: '1010', name: 'Bank account', type: 'asset', category: 'current_asset', role: 'bank', cash: 'cash' },
  { code: '1200', name: 'Accounts receivable', type: 'asset', category: 'current_asset', role: 'receivable', control: true, cash: 'operating', description: 'What customers owe. Kept by invoices and payments.' },
  { code: '1300', name: 'Inventory', type: 'asset', category: 'current_asset', role: 'inventory', control: true, cash: 'operating', description: 'Stock on hand. Kept by stock movements.' },
  { code: '1400', name: 'Tax paid on purchases', type: 'asset', category: 'current_asset', role: 'input_tax', cash: 'operating' },
  { code: '1500', name: 'Prepaid expenses', type: 'asset', category: 'current_asset', cash: 'operating' },
  { code: '1600', name: 'Equipment', type: 'asset', category: 'fixed_asset', cash: 'investing' },
  { code: '1610', name: 'Accumulated depreciation', type: 'asset', category: 'fixed_asset', cash: 'investing', contra: true },
  { code: '2000', name: 'Accounts payable', type: 'liability', category: 'current_liability', role: 'payable', control: true, cash: 'operating', description: 'What you owe suppliers. Kept by bills and payments.' },
  { code: '2050', name: 'Goods received, not billed', type: 'liability', category: 'current_liability', role: 'grni', control: true, cash: 'operating', description: 'Stock received from suppliers, waiting for their bill.' },
  { code: '2100', name: 'Tax collected on sales', type: 'liability', category: 'current_liability', role: 'output_tax', cash: 'operating' },
  { code: '2200', name: 'Accrued expenses', type: 'liability', category: 'current_liability', cash: 'operating' },
  { code: '2300', name: 'Short-term loans', type: 'liability', category: 'current_liability', cash: 'financing' },
  { code: '2500', name: 'Long-term loans', type: 'liability', category: 'long_term_liability', cash: 'financing' },
  { code: '3000', name: "Owner's capital", type: 'equity', category: 'owners_equity', cash: 'financing' },
  { code: '3100', name: "Owner's drawings", type: 'equity', category: 'owners_equity', cash: 'financing', contra: true },
  { code: '3200', name: 'Retained earnings', type: 'equity', category: 'retained_earnings', role: 'retained_earnings', cash: 'financing' },
  { code: '3900', name: 'Opening balances', type: 'equity', category: 'other_equity', role: 'opening_balance', cash: 'financing', description: 'The other side of balances brought in when you start.' },
  { code: '4000', name: 'Sales', type: 'revenue', category: 'operating_revenue' },
  { code: '4100', name: 'Service income', type: 'revenue', category: 'operating_revenue' },
  { code: '4900', name: 'Sales returns and discounts', type: 'revenue', category: 'operating_revenue', contra: true },
  { code: '4950', name: 'Interest income', type: 'revenue', category: 'other_revenue', pl: 'investing' },
  { code: '5000', name: 'Cost of goods sold', type: 'expense', category: 'cost_of_sales' },
  { code: '5100', name: 'Purchase price differences', type: 'expense', category: 'cost_of_sales', role: 'price_variance', description: "Where a supplier's bill differs from the price the goods were received at." },
  { code: '5200', name: 'Stock adjustments', type: 'expense', category: 'cost_of_sales' },
  { code: '6000', name: 'Salaries and wages', type: 'expense', category: 'operating_expense' },
  { code: '6100', name: 'Rent', type: 'expense', category: 'operating_expense' },
  { code: '6200', name: 'Utilities', type: 'expense', category: 'operating_expense' },
  { code: '6300', name: 'Office and supplies', type: 'expense', category: 'operating_expense' },
  { code: '6400', name: 'Marketing', type: 'expense', category: 'operating_expense' },
  { code: '6500', name: 'Professional fees', type: 'expense', category: 'operating_expense' },
  { code: '6600', name: 'Bank charges', type: 'expense', category: 'operating_expense' },
  { code: '6700', name: 'Depreciation', type: 'expense', category: 'operating_expense' },
  { code: '6800', name: 'Bad debts', type: 'expense', category: 'operating_expense' },
  { code: '7000', name: 'Interest expense', type: 'expense', category: 'other_expense', pl: 'financing' },
  { code: '8000', name: 'Income tax', type: 'expense', category: 'other_expense', pl: 'income_tax' },
]

/** Adds the starter chart when the organization has no accounts. Returns how many were added: 0 when it already has a chart. */
export async function seedStarterChart(exec: unknown, org: string, userId: string | null) {
  const sql = exec as Exec
  await sql`SELECT pg_advisory_xact_lock(hashtext(${`${org}:starter-chart`}))`
  const [{ n }] = (await sql`SELECT COUNT(*)::int AS n FROM public.accounts WHERE organization_id = ${org}::uuid`) as { n: number }[]
  if (n > 0) return 0
  let grni: number | null = null
  for (const a of STARTER_CHART) {
    const [row] = (await sql`
      INSERT INTO public.accounts (organization_id, code, name, account_type, report_category, description, is_postable, is_active, created_by,
                                   system_role, is_control, cash_flow_category, pl_category, is_contra)
      VALUES (${org}::uuid, ${a.code}, ${a.name}, ${a.type}::public.account_type, ${a.category}::public.account_report_category, ${a.description ?? null}, true, true, ${userId}::uuid,
              ${a.role ?? null}, ${a.control ?? false}, ${a.cash ?? null}, ${a.pl ?? null}, ${a.contra ?? false})
      RETURNING id
    `) as { id: number }[]
    if (a.role === 'grni') grni = Number(row.id)
  }
  if (grni) {
    await sql`INSERT INTO public.inventory_settings (organization_id, grni_account_id) VALUES (${org}::uuid, ${grni}) ON CONFLICT (organization_id) DO UPDATE SET grni_account_id = COALESCE(public.inventory_settings.grni_account_id, EXCLUDED.grni_account_id)`
  }
  return STARTER_CHART.length
}

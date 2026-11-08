/** Rules that keep the chart of accounts and the ledger from contradicting their own history. */

type Exec = <T = unknown>(strings: TemplateStringsArray, ...values: unknown[]) => PromiseLike<T>
type Row = Record<string, unknown>

/**
 * Accounts a subledger keeps (receivables, payables, stock, received-not-billed, tax) only move through the work
 * that keeps the subledger in step: invoices, bills, payments, credit notes and stock movements. A manual entry,
 * or one an AI proposes, can't post to them, or the ledger and the subledger would disagree.
 */
export async function assertNoControlAccounts(exec: unknown, org: string, accountIds: number[]) {
  const ids = Array.from(new Set(accountIds.filter((id) => Number(id) > 0).map(Number)))
  if (!ids.length) return
  const sql = exec as Exec
  const rows = (await sql`
    SELECT code, name, to_jsonb(a) ->> 'system_role' AS role
    FROM public.accounts a
    WHERE a.organization_id = ${org}::uuid AND a.id = ANY(${ids}::bigint[])
      AND COALESCE((to_jsonb(a) ->> 'is_control')::boolean, false)
  `) as Row[]
  if (rows.length) {
    const names = rows.map((r) => `${r.code} ${r.name}`).join(', ')
    throw new Error(`${names} ${rows.length > 1 ? 'are' : 'is a'} control account${rows.length > 1 ? 's' : ''}, kept by invoices, bills, payments or stock. Record this there, so the two stay in step.`)
  }
}

/**
 * An account with history can't change type, because that would rewrite every past report, closed periods
 * included. An account still holding a balance can't be made inactive, or it would drop out of the reports
 * while its balance stayed in the books.
 */
export async function assertAccountChangeAllowed(
  exec: unknown,
  existing: { id: number | string; account_type: string; is_active?: boolean | null },
  updates: { account_type?: string | null; is_active?: boolean | null }
) {
  const sql = exec as Exec
  const changingType = updates.account_type != null && updates.account_type !== existing.account_type
  const deactivating = updates.is_active === false && existing.is_active !== false
  if (!changingType && !deactivating) return
  const [r] = (await sql`
    SELECT COUNT(*)::int AS lines, COALESCE(SUM(l.debit_amount - l.credit_amount), 0)::text AS net
    FROM public.journal_entry_lines l WHERE l.account_id = ${Number(existing.id)}
  `) as Row[]
  if (changingType && Number(r?.lines ?? 0) > 0) {
    throw new Error("This account already has entries, so its type can't change: every past report would change with it. Create a new account and move the balance with a journal entry.")
  }
  if (deactivating && Math.abs(Number(r?.net ?? 0)) >= 0.005) {
    throw new Error('This account still has a balance. Move the balance to another account first, then make it inactive.')
  }
}

export const SYSTEM_ROLES = ['receivable', 'payable', 'inventory', 'grni', 'output_tax', 'input_tax', 'bank', 'cash', 'retained_earnings', 'opening_balance', 'price_variance'] as const
const CONTROL_ROLES = new Set(['receivable', 'payable', 'inventory', 'grni'])
const ROLE_TYPE: Record<string, string> = { receivable: 'asset', inventory: 'asset', input_tax: 'asset', bank: 'asset', cash: 'asset', payable: 'liability', grni: 'liability', output_tax: 'liability', retained_earnings: 'equity', opening_balance: 'equity', price_variance: 'expense' }
const CASH_FLOW = ['cash', 'operating', 'investing', 'financing']
const PL = ['operating', 'investing', 'financing', 'income_tax']

/**
 * The classification fields from a create or update, checked against the account's type. Leaves out what the
 * caller didn't send, so an update only changes what it names. A control role makes the account a control account.
 */
export function classificationFields(input: Record<string, unknown>, accountType: string) {
  const out: { system_role?: string | null; is_control?: boolean; cash_flow_category?: string | null; pl_category?: string | null; is_contra?: boolean } = {}
  const text = (v: unknown) => (typeof v === 'string' && v.trim() ? v.trim() : null)
  if ('system_role' in input) {
    const role = text(input.system_role)
    if (role && !(SYSTEM_ROLES as readonly string[]).includes(role)) throw new Error(`Unknown account role "${role}".`)
    if (role && ROLE_TYPE[role] !== accountType) throw new Error(`The ${role.replace(/_/g, ' ')} role belongs on ${ROLE_TYPE[role]} accounts.`)
    out.system_role = role
    out.is_control = role ? CONTROL_ROLES.has(role) : false
  }
  if ('cash_flow_category' in input) {
    const c = text(input.cash_flow_category)
    if (c && !CASH_FLOW.includes(c)) throw new Error(`Unknown cash flow category "${c}".`)
    if (c && !['asset', 'liability', 'equity'].includes(accountType)) throw new Error('Only balance sheet accounts take a cash flow category.')
    if (c === 'cash' && accountType !== 'asset') throw new Error('Only an asset account can be cash.')
    out.cash_flow_category = c
  }
  if ('pl_category' in input) {
    const c = text(input.pl_category)
    if (c && !PL.includes(c)) throw new Error(`Unknown income statement category "${c}".`)
    if (c && !['revenue', 'expense'].includes(accountType)) throw new Error('Only income and expense accounts take an income statement category.')
    if (c === 'income_tax' && accountType !== 'expense') throw new Error('Income tax is an expense.')
    out.pl_category = c
  }
  if ('is_contra' in input) out.is_contra = Boolean(input.is_contra)
  return out
}

/** Writes classification fields, if any were sent. Runs after the account itself is saved. */
export async function saveClassification(exec: unknown, accountId: number, fields: ReturnType<typeof classificationFields>) {
  if (!Object.keys(fields).length) return
  const sql = exec as Exec
  const has = (k: keyof typeof fields) => k in fields
  await sql`
    UPDATE public.accounts SET
      system_role = CASE WHEN ${has('system_role')} THEN ${fields.system_role ?? null} ELSE system_role END,
      is_control = CASE WHEN ${has('is_control')} THEN ${fields.is_control ?? false} ELSE is_control END,
      cash_flow_category = CASE WHEN ${has('cash_flow_category')} THEN ${fields.cash_flow_category ?? null} ELSE cash_flow_category END,
      pl_category = CASE WHEN ${has('pl_category')} THEN ${fields.pl_category ?? null} ELSE pl_category END,
      is_contra = CASE WHEN ${has('is_contra')} THEN ${fields.is_contra ?? false} ELSE is_contra END
    WHERE id = ${accountId}
  `.then(undefined, (e: unknown) => {
    if (e && typeof e === 'object' && 'code' in e && (e as { code: string }).code === '23505') throw new Error('Another account already has that role. An organization has one of each.')
    throw e
  })
}

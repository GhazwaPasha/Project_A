import { getSql } from '@/server/pg'
import type { AccountType } from '@/types'

type TrialRow = {
  id: number
  code: string
  name: string
  account_type: AccountType
  dr: string | null
  cr: string | null
}

/** Second argument to `fetchTrialBalanceSums`: legacy string = as-of date, or structured range. */
export type LedgerLineDateFilter =
  | string
  | {
      asOfDate?: string
      fromDate?: string
      toDate?: string
    }

function parseLedgerLineDateFilter(filter?: LedgerLineDateFilter | null): {
  asOf: string | null
  from: string | null
  to: string | null
} {
  if (filter == null || filter === '') {
    return { asOf: null, from: null, to: null }
  }
  if (typeof filter === 'string') {
    const t = filter.trim()
    return t ? { asOf: t, from: null, to: null } : { asOf: null, from: null, to: null }
  }
  const asOf = filter.asOfDate?.trim() || null
  if (asOf) return { asOf, from: null, to: null }
  return {
    asOf: null,
    from: filter.fromDate?.trim() || null,
    to: filter.toDate?.trim() || null,
  }
}

function journalLineDateFragment(
  sql: ReturnType<typeof getSql>,
  parts: ReturnType<typeof parseLedgerLineDateFilter>
) {
  const { asOf, from, to } = parts
  if (asOf) return sql`AND je.entry_date <= ${asOf}::date`
  if (from && to) return sql`AND je.entry_date >= ${from}::date AND je.entry_date <= ${to}::date`
  if (from) return sql`AND je.entry_date >= ${from}::date`
  if (to) return sql`AND je.entry_date <= ${to}::date`
  return sql``
}

/**
 * Trial balance: debit/credit totals per account in one query.
 * - Pass a string for legacy as-of (`entry_date <= date`).
 * - Pass `{ fromDate, toDate }` for dashboard date range (same rules as `getAccountBalances`).
 */
export async function fetchTrialBalanceSums(
  organizationId: string,
  dateFilter?: LedgerLineDateFilter | null
): Promise<TrialRow[]> {
  const sql = getSql()
  const parts = parseLedgerLineDateFilter(dateFilter ?? undefined)
  const d = journalLineDateFragment(sql, parts)
  return (await sql<TrialRow[]>`
    WITH sums AS (
      SELECT
        jel.account_id,
        COALESCE(SUM(jel.debit_amount), 0)::numeric AS dr,
        COALESCE(SUM(jel.credit_amount), 0)::numeric AS cr
      FROM public.journal_entry_lines jel
      INNER JOIN public.journal_entries je ON je.id = jel.journal_entry_id
      WHERE je.organization_id = ${organizationId}::uuid
      ${d}
      GROUP BY jel.account_id
    )
    SELECT
      a.id,
      a.code,
      a.name,
      a.account_type,
      s.dr::text AS dr,
      s.cr::text AS cr
    FROM public.accounts a
    LEFT JOIN sums s ON s.account_id = a.id
    WHERE a.organization_id = ${organizationId}::uuid
      AND a.is_active = true
    ORDER BY a.code
  `) as TrialRow[]
}

/** Per-account aggregates for balances UI — all work in Postgres (no row-by-row line fetch). */
export type JournalLineAggRow = {
  account_id: number
  dr: string
  cr: string
  txn_count: string
  last_entry: string | null
  /** Latest `journal_entries.created_at` for lines in scope (wall-clock last activity). */
  last_activity_at: string | null
}

export async function fetchJournalLineAggregatesByOrg(
  organizationId: string,
  fromDate?: string,
  toDate?: string
): Promise<JournalLineAggRow[]> {
  const sql = getSql()
  const parts = parseLedgerLineDateFilter({ fromDate, toDate })
  const d = journalLineDateFragment(sql, parts)
  return (await sql<JournalLineAggRow[]>`
    SELECT
      jel.account_id,
      COALESCE(SUM(jel.debit_amount), 0)::numeric::text AS dr,
      COALESCE(SUM(jel.credit_amount), 0)::numeric::text AS cr,
      COUNT(*)::text AS txn_count,
      MAX(je.entry_date)::text AS last_entry,
      MAX(je.created_at)::text AS last_activity_at
    FROM public.journal_entry_lines jel
    INNER JOIN public.journal_entries je ON je.id = jel.journal_entry_id
    WHERE je.organization_id = ${organizationId}::uuid
    ${d}
    GROUP BY jel.account_id
  `) as JournalLineAggRow[]
}

export function trialRowToDebitsCredits(row: TrialRow): {
  debit_balance: number
  credit_balance: number
} {
  const dr = row.dr != null ? Number(row.dr) : 0
  const cr = row.cr != null ? Number(row.cr) : 0
  const t = String(row.account_type).toLowerCase()
  if (t === 'asset' || t === 'expense') {
    const net = dr - cr
    if (net >= 0) return { debit_balance: net, credit_balance: 0 }
    return { debit_balance: 0, credit_balance: -net }
  }
  const net = cr - dr
  if (net >= 0) return { debit_balance: 0, credit_balance: net }
  return { debit_balance: -net, credit_balance: 0 }
}

export function netAmountForAccountType(
  dr: number,
  cr: number,
  accountType: string
): number {
  const t = accountType.toLowerCase()
  if (t === 'asset' || t === 'expense') return dr - cr
  return cr - dr
}

/**
 * Net balance for one account in an org, same rules as trial balance.
 */
export async function fetchAccountNetBalance(
  accountId: number,
  organizationId: string
): Promise<number> {
  const sql = getSql()
  const rows = await sql<{ dr: string; cr: string; at: AccountType }[]>`
    SELECT
      a.account_type AS at,
      COALESCE(t.dr, 0)::numeric::text AS dr,
      COALESCE(t.cr, 0)::numeric::text AS cr
    FROM public.accounts a
    LEFT JOIN (
      SELECT
        jel.account_id,
        COALESCE(SUM(jel.debit_amount), 0) AS dr,
        COALESCE(SUM(jel.credit_amount), 0) AS cr
      FROM public.journal_entry_lines jel
      INNER JOIN public.journal_entries je ON je.id = jel.journal_entry_id
      WHERE jel.account_id = ${accountId}
        AND je.organization_id = ${organizationId}::uuid
      GROUP BY jel.account_id
    ) t ON t.account_id = a.id
    WHERE a.id = ${accountId}
    LIMIT 1
  `
  if (rows.length === 0) return 0
  const dr = Number(rows[0].dr)
  const cr = Number(rows[0].cr)
  return netAmountForAccountType(dr, cr, String(rows[0].at))
}

/**
 * An account's type and its balance before a date, in the account's natural direction.
 * With no date there's nothing before the first entry, so the balance is 0.
 */
export async function fetchAccountOpening(
  accountId: number,
  organizationId: string,
  beforeDate?: string
): Promise<{ accountType: string; opening: number } | null> {
  const sql = getSql()
  const rows = await sql<{ at: string; dr: string; cr: string }[]>`
    SELECT
      a.account_type AS at,
      COALESCE(t.dr, 0)::numeric::text AS dr,
      COALESCE(t.cr, 0)::numeric::text AS cr
    FROM public.accounts a
    LEFT JOIN (
      SELECT
        jel.account_id,
        COALESCE(SUM(jel.debit_amount), 0) AS dr,
        COALESCE(SUM(jel.credit_amount), 0) AS cr
      FROM public.journal_entry_lines jel
      INNER JOIN public.journal_entries je ON je.id = jel.journal_entry_id
      WHERE jel.account_id = ${accountId}
        AND je.organization_id = ${organizationId}::uuid
        AND ${beforeDate ? sql`je.entry_date < ${beforeDate}::date` : sql`false`}
      GROUP BY jel.account_id
    ) t ON t.account_id = a.id
    WHERE a.id = ${accountId}
      AND a.organization_id = ${organizationId}::uuid
    LIMIT 1
  `
  if (rows.length === 0) return null
  const accountType = String(rows[0].at)
  return { accountType, opening: netAmountForAccountType(Number(rows[0].dr), Number(rows[0].cr), accountType) }
}

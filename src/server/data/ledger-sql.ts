import { getSql } from '@/server/pg'
import { fromCents, toCents } from '@/lib/money'
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
        AND je.is_posted
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
      AND (a.is_active OR COALESCE(s.dr, 0) <> 0 OR COALESCE(s.cr, 0) <> 0)
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
      AND je.is_posted
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
  // In whole cents, so a balance is exact to the cent.
  if (t === 'asset' || t === 'expense') return fromCents(toCents(dr) - toCents(cr))
  return fromCents(toCents(cr) - toCents(dr))
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
        AND je.is_posted
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
        AND je.is_posted
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

/** One account's figures for a report: its classification and its balance in its natural direction. */
export type ReportAccount = {
  id: number
  code: string
  name: string
  account_type: AccountType
  report_category: string | null
  group: string | null
  parent_id: number | null
  is_active: boolean
  is_postable: boolean
  /** Classification added by migration 014. Read through to_jsonb, so reports still run before it is applied. */
  system_role: string | null
  cash_flow_category: string | null
  pl_category: string | null
  is_contra: boolean
  dr: number
  cr: number
  /** Debits less credits for assets and expenses, credits less debits for the rest. */
  balance: number
}


/**
 * Every report's balances come from here, so the reports always agree with each other.
 * Posted entries only. Inactive accounts are kept while they still hold a balance, or the totals would stop adding up.
 */
export async function fetchReportBalances(organizationId: string, dateFilter?: LedgerLineDateFilter | null): Promise<ReportAccount[]> {
  const sql = getSql()
  const d = journalLineDateFragment(sql, parseLedgerLineDateFilter(dateFilter ?? undefined))
  const rows = (await sql`
    WITH sums AS (
      SELECT jel.account_id, SUM(jel.debit_amount) AS dr, SUM(jel.credit_amount) AS cr
      FROM public.journal_entry_lines jel
      JOIN public.journal_entries je ON je.id = jel.journal_entry_id
      WHERE je.organization_id = ${organizationId}::uuid AND je.is_posted
      ${d}
      GROUP BY jel.account_id
    )
    SELECT a.id, a.code, a.name, a.account_type::text AS account_type, a.report_category::text AS report_category, a."group" AS "group",
           a.parent_id, a.is_active, a.is_postable,
           to_jsonb(a) ->> 'system_role' AS system_role,
           to_jsonb(a) ->> 'cash_flow_category' AS cash_flow_category,
           to_jsonb(a) ->> 'pl_category' AS pl_category,
           COALESCE((to_jsonb(a) ->> 'is_contra')::boolean, false) AS is_contra,
           COALESCE(s.dr, 0)::text AS dr, COALESCE(s.cr, 0)::text AS cr
    FROM public.accounts a
    LEFT JOIN sums s ON s.account_id = a.id
    WHERE a.organization_id = ${organizationId}::uuid
      AND (a.is_active OR COALESCE(s.dr, 0) <> 0 OR COALESCE(s.cr, 0) <> 0)
    ORDER BY a.code
  `) as unknown as Record<string, unknown>[]
  return rows.map((r) => {
    const drCents = toCents(String(r.dr))
    const crCents = toCents(String(r.cr))
    const dr = fromCents(drCents)
    const cr = fromCents(crCents)
    const account_type = String(r.account_type) as AccountType
    const naturalCents = account_type === 'asset' || account_type === 'expense' ? drCents - crCents : crCents - drCents
    return {
      id: Number(r.id),
      code: String(r.code ?? ''),
      name: String(r.name),
      account_type,
      report_category: (r.report_category as string | null) ?? null,
      group: (r.group as string | null) ?? null,
      parent_id: r.parent_id == null ? null : Number(r.parent_id),
      is_active: Boolean(r.is_active),
      is_postable: r.is_postable !== false,
      system_role: (r.system_role as string | null) ?? null,
      cash_flow_category: (r.cash_flow_category as string | null) ?? null,
      pl_category: (r.pl_category as string | null) ?? null,
      is_contra: Boolean(r.is_contra),
      dr,
      cr,
      balance: fromCents(naturalCents),
    }
  })
}

/** Profit (revenue less expenses) before a year's start and from it to a date, for the balance sheet's earnings lines. */
export async function fetchEarningsSplit(organizationId: string, yearStart: string, asOf: string): Promise<{ prior: number; current: number }> {
  const sql = getSql()
  const [row] = (await sql`
    SELECT
      COALESCE(SUM(CASE WHEN je.entry_date < ${yearStart}::date THEN jel.credit_amount - jel.debit_amount END), 0)::text AS prior,
      COALESCE(SUM(CASE WHEN je.entry_date >= ${yearStart}::date THEN jel.credit_amount - jel.debit_amount END), 0)::text AS current
    FROM public.journal_entry_lines jel
    JOIN public.journal_entries je ON je.id = jel.journal_entry_id
    JOIN public.accounts a ON a.id = jel.account_id
    WHERE je.organization_id = ${organizationId}::uuid AND je.is_posted
      AND je.entry_date <= ${asOf}::date
      AND a.account_type IN ('revenue', 'expense')
  `) as unknown as { prior: string; current: string }[]
  return { prior: fromCents(toCents(String(row?.prior ?? 0))), current: fromCents(toCents(String(row?.current ?? 0))) }
}

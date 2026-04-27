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

/**
 * One-query trial balance: debit/credit totals per account, optional as-of date on journal entry_date.
 */
export async function fetchTrialBalanceSums(
  organizationId: string,
  asOfDate?: string
): Promise<TrialRow[]> {
  const sql = getSql()
  const asOf = asOfDate && asOfDate.trim() !== '' ? asOfDate : null

  if (asOf) {
    return (await sql<TrialRow[]>`
      WITH sums AS (
        SELECT
          jel.account_id,
          COALESCE(SUM(jel.debit_amount), 0)::numeric AS dr,
          COALESCE(SUM(jel.credit_amount), 0)::numeric AS cr
        FROM public.journal_entry_lines jel
        INNER JOIN public.journal_entries je ON je.id = jel.journal_entry_id
        WHERE je.organization_id = ${organizationId}::uuid
          AND je.entry_date <= ${asOf}::date
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

  return (await sql<TrialRow[]>`
    WITH sums AS (
      SELECT
        jel.account_id,
        COALESCE(SUM(jel.debit_amount), 0)::numeric AS dr,
        COALESCE(SUM(jel.credit_amount), 0)::numeric AS cr
      FROM public.journal_entry_lines jel
      INNER JOIN public.journal_entries je ON je.id = jel.journal_entry_id
      WHERE je.organization_id = ${organizationId}::uuid
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

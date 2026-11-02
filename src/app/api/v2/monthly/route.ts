import { NextResponse } from 'next/server'
import { authInApiRoute } from '@/auth'
import { authorizeAppDataCall } from '@/server/app-data-authorize'
import { getSql } from '@/server/pg'

/** Real revenue and expenses for each of the last 12 months, summed in the database. */
export async function GET(req: Request) {
  const session = await authInApiRoute()
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const org = new URL(req.url).searchParams.get('org')
  try {
    await authorizeAppDataCall('DataService', 'getDashboardBundle', [org], session.user.id)
  } catch {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  const sql = getSql()
  const rows = await sql<{ month: string; revenue: string; expenses: string }[]>`
    WITH months AS (
      SELECT generate_series(
        date_trunc('month', now()) - interval '11 months',
        date_trunc('month', now()),
        interval '1 month'
      )::date AS start
    ),
    sums AS (
      SELECT
        date_trunc('month', je.entry_date)::date AS start,
        SUM(CASE WHEN a.account_type = 'revenue' THEN jel.credit_amount - jel.debit_amount ELSE 0 END) AS revenue,
        SUM(CASE WHEN a.account_type = 'expense' THEN jel.debit_amount - jel.credit_amount ELSE 0 END) AS expenses
      FROM public.journal_entry_lines jel
      JOIN public.journal_entries je ON je.id = jel.journal_entry_id
      JOIN public.accounts a ON a.id = jel.account_id
      WHERE je.organization_id = ${org}::uuid
        AND je.entry_date >= date_trunc('month', now()) - interval '11 months'
      GROUP BY 1
    )
    SELECT to_char(m.start, 'YYYY-MM') AS month,
           COALESCE(s.revenue, 0)::text AS revenue,
           COALESCE(s.expenses, 0)::text AS expenses
    FROM months m
    LEFT JOIN sums s ON s.start = m.start
    ORDER BY m.start
  `
  return NextResponse.json(rows)
}

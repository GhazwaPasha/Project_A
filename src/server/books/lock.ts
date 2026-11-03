type Exec = <T = unknown>(strings: TemplateStringsArray, ...values: unknown[]) => PromiseLike<T>

/** Refuses any entry dated inside a closed period. Every journal entry passes through here. */
export async function assertPeriodOpen(exec: unknown, organizationId: string, entryDate: string) {
  const sql = exec as Exec
  // Keeps recording working if this code is deployed before the migration that adds closing.
  const [table] = await sql<{ t: string | null }[]>`SELECT to_regclass('public.period_closes')::text AS t`
  if (!table?.t) return
  const [row] = await sql<{ through: string | null }[]>`
    SELECT MAX(through_date)::text AS through FROM public.period_closes
    WHERE organization_id = ${organizationId}::uuid AND reopened_at IS NULL
  `
  if (row?.through && String(entryDate).slice(0, 10) <= row.through) {
    throw new Error(`The books are closed through ${row.through}. Use a later date, or have an owner reopen the period.`)
  }
}

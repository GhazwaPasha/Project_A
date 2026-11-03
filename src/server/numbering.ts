import { getSql } from '@/server/pg'

type Pg = ReturnType<typeof getSql>

/**
 * The next free number for a prefix, one at a time per organization, so two people can't get the same one.
 * Uses the highest number so far rather than a count, so deleting a draft can't bring a used number back.
 * The table and column come from this codebase, never from a request.
 */
export async function nextNumber(tx: Pg, org: string, prefix: string, table: string, column: string) {
  await tx`SELECT pg_advisory_xact_lock(hashtext(${`${org}:${prefix}`}))`
  const [row] = (await tx.unsafe(
    `SELECT COALESCE(MAX(substring(${column} from '^${prefix}-([0-9]+)$')::bigint), 0) + 1 AS next FROM ${table} WHERE organization_id = $1::uuid`,
    [org]
  )) as unknown as { next: string | number }[]
  return `${prefix}-${String(row.next).padStart(4, '0')}`
}

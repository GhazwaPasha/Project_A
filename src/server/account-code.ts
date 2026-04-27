import type { Sql } from 'postgres'
import type { AccountType } from '@/types'

/** Classic COA bands: first digit = category; full range 1000–5999 in steps of 1000 per type. */
const TYPE_BAND: Record<AccountType, { min: number; max: number }> = {
  asset: { min: 1000, max: 1999 },
  liability: { min: 2000, max: 2999 },
  equity: { min: 3000, max: 3999 },
  revenue: { min: 4000, max: 4999 },
  expense: { min: 5000, max: 5999 },
}

export function parseFourDigitNumericCode(code: string): number | null {
  const s = code.trim()
  if (!/^[0-9]{4}$/.test(s)) return null
  return parseInt(s, 10)
}

export function formatFourDigitCode(n: number): string {
  if (!Number.isFinite(n) || n < 0 || n > 9999) {
    throw new Error('Account code must be a 4-digit number')
  }
  return String(Math.floor(n)).padStart(4, '0')
}

async function codeTaken(sql: Sql, organizationId: string, code: string): Promise<boolean> {
  const rows = await sql<{ c: number }[]>`
    SELECT 1::int AS c FROM public.accounts
    WHERE organization_id = ${organizationId}::uuid AND code = ${code}
    LIMIT 1
  `
  return rows.length > 0
}

/** Next candidate integer strictly inside [band.min, band.max], advancing past collisions. */
async function nextUnusedInBand(
  sql: Sql,
  organizationId: string,
  start: number,
  band: { min: number; max: number }
): Promise<number> {
  let n = Math.max(start, band.min)
  if (n > band.max) {
    throw new Error(
      `No available account codes left in this category (${band.min}–${band.max}). Remove accounts or contact support.`
    )
  }
  let guard = 0
  while (n <= band.max) {
    const code = formatFourDigitCode(n)
    if (!(await codeTaken(sql, organizationId, code))) return n
    n += 1
    guard += 1
    if (guard > 2000) {
      throw new Error('Could not allocate a unique account code in this category.')
    }
  }
  throw new Error(
    `No available account codes left in this category (${band.min}–${band.max}). Remove accounts or contact support.`
  )
}

/**
 * Structured 4-digit numeric code: type band + hierarchy (top-level vs child under parent).
 * Ignores client-supplied codes — server-only allocation.
 */
export async function allocateStructuredAccountCode(
  sql: Sql,
  organizationId: string,
  accountType: AccountType,
  parentId: number | null
): Promise<string> {
  const band = TYPE_BAND[accountType]

  if (parentId == null) {
    /** Numeric max within this type band only — never use MAX(text), which is lexicographic (wrong for COA digits). */
    const maxRows = await sql<{ m: string | null }[]>`
      SELECT MAX(code::integer)::text AS m
      FROM public.accounts
      WHERE organization_id = ${organizationId}::uuid
        AND account_type = ${accountType}::public.account_type
        AND parent_id IS NULL
        AND code ~ '^[0-9]{4}$'
        AND code::integer >= ${band.min}
        AND code::integer <= ${band.max}
    `
    const raw = maxRows[0]?.m
    let start = band.min
    if (raw != null && /^[0-9]{4}$/.test(raw)) {
      const parsed = parseInt(raw, 10)
      start = parsed + 1
    }
    const n = await nextUnusedInBand(sql, organizationId, start, band)
    return formatFourDigitCode(n)
  }

  const parents = await sql<{ code: string }[]>`
    SELECT code FROM public.accounts WHERE id = ${parentId} LIMIT 1
  `
  const parentRow = parents[0]
  if (!parentRow) {
    throw new Error('Parent account not found.')
  }

  const parentNum = parseFourDigitNumericCode(parentRow.code)

  const maxChildRows = await sql<{ m: string | null }[]>`
    SELECT MAX(code::integer)::text AS m
    FROM public.accounts
    WHERE organization_id = ${organizationId}::uuid
      AND parent_id = ${parentId}
      AND code ~ '^[0-9]{4}$'
      AND code::integer >= ${band.min}
      AND code::integer <= ${band.max}
  `
  const rawMaxChild = maxChildRows[0]?.m
  let start: number
  if (rawMaxChild != null && /^[0-9]{4}$/.test(rawMaxChild)) {
    start = parseInt(rawMaxChild, 10) + 1
  } else if (parentNum != null && parentNum >= band.min && parentNum <= band.max) {
    start = parentNum + 1
  } else {
    start = band.min
  }

  const n = await nextUnusedInBand(sql, organizationId, start, band)
  return formatFourDigitCode(n)
}

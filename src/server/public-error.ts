/**
 * Decides what a person sees when a request fails. Errors the app throws on purpose are written for people, so they
 * pass through. Database and connection errors carry a `code` and can name tables or hosts, so they never do.
 */
export const isStillInUse = (e: unknown) => ['23503', '23001'].includes(String((e as { code?: unknown } | null)?.code))

export function publicError(e: unknown): { status: number; error: string; code?: 'SCHEMA_NOT_READY'; hint?: string } {
  const code = (e as { code?: unknown } | null)?.code
  if (typeof code !== 'string') {
    return { status: 500, error: e instanceof Error ? e.message : 'Something went wrong. Please try again.' }
  }
  if (isStillInUse(e)) return { status: 409, error: "This is still being used elsewhere, so it can't be deleted or changed." }
  if (code === '23505') return { status: 409, error: 'That already exists. Use a different name or code.' }
  if (code === '23502' || code === '23514' || code.startsWith('22')) return { status: 400, error: "Some of that information isn't valid. Check it and try again." }
  if (code === '42P01' || code === '42704' || code === '42703') {
    return { status: 503, error: "Part of the database isn't set up yet.", code: 'SCHEMA_NOT_READY', hint: 'Run the database migrations, then try again.' }
  }
  return { status: 500, error: 'Something went wrong. Please try again.' }
}

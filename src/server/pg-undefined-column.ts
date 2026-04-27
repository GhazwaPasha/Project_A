/** Postgres SQLSTATE 42703 — undefined_column */
export function isUndefinedColumnError(error: unknown, columnName: string): boolean {
  if (!error || typeof error !== 'object') return false
  const e = error as { code?: string; message?: string }
  if (String(e.code) !== '42703') return false
  const msg = String(e.message ?? '')
  return msg.includes(columnName) && (msg.includes('does not exist') || msg.includes('undefined_column'))
}

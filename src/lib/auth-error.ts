/** Normalize Neon / better-auth client error objects for display */
export function getNeonAuthErrorMessage(err: unknown, fallback: string): string {
  if (err == null) return fallback
  if (err instanceof Error && err.message) return err.message
  if (typeof err === 'object' && err !== null && 'message' in err) {
    const m = (err as { message?: unknown }).message
    if (typeof m === 'string' && m.length > 0) return m
  }
  if (typeof err === 'object' && err !== null && 'code' in err) {
    const c = (err as { code?: unknown }).code
    if (typeof c === 'string' && c.length > 0) return c
  }
  return fallback
}

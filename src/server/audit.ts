import { getSql } from '@/server/pg'

const READS = /^(get|list|preview|find|search|validate|generate|export)/
const PRIVATE = /password|secret|token|api_?key|credential/i
const MAX_DETAILS = 2000

/** Reads leave no trace. Everything else that gets through the data API changes something. */
export const isWrite = (method: string) => !READS.test(method)

/** "postDocument" becomes "Post document". */
export const actionLabel = (method: string) => {
  const words = method.replace(/([A-Z])/g, ' $1').toLowerCase().trim()
  return words.charAt(0).toUpperCase() + words.slice(1)
}

/** What's kept about a change: no secrets, and a limit on size, since a bank statement import can be thousands of lines. */
export function safeDetails(value: unknown) {
  const scrub = (v: unknown, depth: number): unknown => {
    if (v === null || typeof v !== 'object') return typeof v === 'string' && v.length > 300 ? `${v.slice(0, 300)}…` : v
    if (depth > 5) return '…'
    if (Array.isArray(v)) return v.length > 50 ? [...v.slice(0, 50).map((x) => scrub(x, depth + 1)), `and ${v.length - 50} more`] : v.map((x) => scrub(x, depth + 1))
    return Object.fromEntries(Object.entries(v as Record<string, unknown>).map(([k, x]) => [k, PRIVATE.test(k) ? '[hidden]' : scrub(x, depth + 1)]))
  }
  const clean = scrub(value, 0)
  const text = JSON.stringify(clean) ?? 'null'
  return text.length > MAX_DETAILS ? { truncated: text.slice(0, MAX_DETAILS) } : clean
}

export type AuditEvent = { org: string; userId: string | null; source?: string; action: string; targetType?: string | null; targetId?: string | number | null; details?: unknown }

/**
 * Adds to the audit log after a change has happened. A failure here is reported on the server but doesn't undo the
 * change or fail the request, because the person's work has already been saved.
 */
export async function recordAudit(e: AuditEvent) {
  try {
    const details = e.details === undefined ? null : safeDetails(e.details)
    await getSql()`
      INSERT INTO public.audit_log (organization_id, user_id, source, action, target_type, target_id, details)
      VALUES (${e.org}::uuid, ${e.userId}::uuid, ${e.source ?? 'app'}, ${e.action}, ${e.targetType ?? null}, ${e.targetId === undefined || e.targetId === null ? null : String(e.targetId)}, ${details === null ? null : getSql().json(details as never)})
    `
  } catch (err) {
    console.error('audit log failed', e.action, (err as { code?: string })?.code ?? (err instanceof Error ? err.message.slice(0, 120) : ''))
  }
}

/** Newest first. */
export function listAuditLog(org: string, options: { limit?: number } = {}) {
  const limit = Math.min(Math.max(Math.floor(Number(options.limit)) || 300, 1), 1000)
  return getSql()`
    SELECT a.id, a.user_id, a.source, a.action, a.target_type, a.target_id, a.details, a.created_at::text AS created_at, p.email, p.full_name
    FROM public.audit_log a LEFT JOIN public.user_profiles p ON p.id = a.user_id
    WHERE a.organization_id = ${org}::uuid
    ORDER BY a.created_at DESC, a.id DESC LIMIT ${limit}
  `
}

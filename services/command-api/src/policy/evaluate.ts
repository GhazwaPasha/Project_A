/**
 * Policy stub (plan: rules-as-code / versioned packs later).
 * Every journal command consults this before mutating state.
 */

export type JournalPolicyAction = 'propose' | 'approve' | 'post' | 'reverse'

export type JournalPolicyContext = {
  userId: string
  organizationId: string
  action: JournalPolicyAction
}

export type JournalPolicyResult =
  | { ok: true }
  | { ok: false; violations: string[] }

/** Replace with compiled rule packs + role matrix; for now optional kill-switch only. */
export function evaluateJournalPolicy(ctx: JournalPolicyContext, _detail?: unknown): JournalPolicyResult {
  if (process.env.POLICY_DENY_ALL === 'true') {
    return {
      ok: false,
      violations: [`POLICY_DENY_ALL: blocked action "${ctx.action}" for org ${ctx.organizationId}`],
    }
  }
  return { ok: true }
}

export function assertJournalPolicy(ctx: JournalPolicyContext, detail?: unknown): void {
  const r = evaluateJournalPolicy(ctx, detail)
  if (!r.ok) {
    const err = new Error(r.violations.join('; ') || 'Policy denied')
    ;(err as Error & { status?: number }).status = 403
    throw err
  }
}

import type { Sql, TransactionSql } from 'postgres'
import { z } from 'zod'
import { assertJournalPolicy } from '../policy/evaluate.js'

/** Sql connection or transaction client (both support tagged templates + `.json`). */
export type ExecSql = Sql | TransactionSql

function parsePayloadRecord(raw: unknown): Record<string, unknown> {
  if (raw == null) return {}
  if (typeof raw === 'string') {
    try {
      return JSON.parse(raw) as Record<string, unknown>
    } catch {
      return {}
    }
  }
  if (typeof raw === 'object') return raw as Record<string, unknown>
  return {}
}

const proposalLineSchema = z.object({
  account_id: z.number().int().positive(),
  debit_amount: z.number().nonnegative(),
  credit_amount: z.number().nonnegative(),
  description: z.string().optional().nullable(),
})

export const proposeBodySchema = z.object({
  organization_id: z.string().uuid(),
  description: z.string().min(1),
  entry_date: z.string().min(1),
  reference: z.string().optional().nullable(),
  lines: z.array(proposalLineSchema).min(2),
})

export const approveBodySchema = z.object({
  organization_id: z.string().uuid(),
  proposal_id: z.number().int().positive(),
})

export const postBodySchema = z.object({
  organization_id: z.string().uuid(),
  proposal_id: z.number().int().positive(),
})

export const reverseBodySchema = z.object({
  organization_id: z.string().uuid(),
  posted_ledger_event_id: z.number().int().positive(),
})

export type ProposeBody = z.infer<typeof proposeBodySchema>

export function assertBalanced(lines: ProposeBody['lines']) {
  let deb = 0
  let cred = 0
  for (const l of lines) {
    if (l.debit_amount > 0 && l.credit_amount > 0) {
      throw new Error('Each line must be either debit or credit, not both')
    }
    deb += l.debit_amount
    cred += l.credit_amount
  }
  if (Math.abs(deb - cred) > 0.000001) {
    throw new Error('Debits must equal credits')
  }
}

export async function assertOrgMembership(sql: Sql, userId: string, organizationId: string) {
  const rows = await sql<{ ok: number }[]>`
    SELECT 1 AS ok
    FROM public.organization_members
    WHERE user_id = ${userId}
      AND organization_id = ${organizationId}
      AND is_active = true
    LIMIT 1
  `
  if (rows.length === 0) {
    const err = new Error('Forbidden')
    ;(err as Error & { status?: number }).status = 403
    throw err
  }
}

async function findIdempotent(
  sql: Sql,
  organizationId: string,
  idempotencyKey: string | undefined
) {
  if (!idempotencyKey) return null
  const rows = await sql<
    { id: string; event_type: string; payload: unknown }[]
  >`
    SELECT id, event_type, payload
    FROM public.ledger_events
    WHERE organization_id = ${organizationId}::uuid
      AND idempotency_key = ${idempotencyKey}
    LIMIT 1
  `
  return rows[0] ?? null
}

export async function handlePropose(
  sql: Sql,
  userId: string,
  body: ProposeBody,
  idempotencyKey: string | undefined
) {
  await assertOrgMembership(sql, userId, body.organization_id)
  assertJournalPolicy(
    { userId, organizationId: body.organization_id, action: 'propose' },
    body
  )
  const existing = await findIdempotent(sql, body.organization_id, idempotencyKey)
  if (existing) {
    return { deduplicated: true, ledger_event: existing }
  }
  assertBalanced(body.lines)

  const payload = {
    kind: 'journal_proposal',
    description: body.description,
    entry_date: body.entry_date,
    reference: body.reference ?? null,
    lines: body.lines,
  }

  const rows = await sql.begin(async (tx) => {
    const [ev] = await tx<{ id: string }[]>`
      INSERT INTO public.ledger_events (
        organization_id, event_type, payload, idempotency_key, created_by
      ) VALUES (
        ${body.organization_id}::uuid,
        'journal.proposed',
        ${tx.json(payload as never)},
        ${idempotencyKey ?? null},
        ${userId}
      )
      RETURNING id
    `
    const [prop] = await tx<{ id: number }[]>`
      INSERT INTO public.journal_proposals (
        organization_id, status, payload, created_by
      ) VALUES (
        ${body.organization_id}::uuid,
        'pending',
        ${tx.json({ ...payload, ledger_event_id: ev.id } as never)},
        ${userId}
      )
      RETURNING id
    `
    return { ledger_event_id: ev.id, proposal_id: prop.id }
  })

  return { deduplicated: false, ...rows }
}

export async function handleApprove(sql: Sql, userId: string, body: z.infer<typeof approveBodySchema>) {
  await assertOrgMembership(sql, userId, body.organization_id)
  assertJournalPolicy(
    { userId, organizationId: body.organization_id, action: 'approve' },
    body
  )
  const [prop] = await sql<{ id: number; status: string }[]>`
    SELECT id, status FROM public.journal_proposals
    WHERE id = ${body.proposal_id}
      AND organization_id = ${body.organization_id}::uuid
    LIMIT 1
  `
  if (!prop) {
    const e = new Error('Proposal not found')
    ;(e as Error & { status?: number }).status = 404
    throw e
  }
  if (prop.status !== 'pending') {
    const e = new Error('Proposal is not pending')
    ;(e as Error & { status?: number }).status = 409
    throw e
  }

  await sql.begin(async (tx) => {
    await tx`
      UPDATE public.journal_proposals
      SET status = 'approved', approved_by = ${userId}, updated_at = NOW()
      WHERE id = ${body.proposal_id}
    `
    await tx`
      INSERT INTO public.ledger_events (organization_id, event_type, payload, created_by)
      VALUES (
        ${body.organization_id}::uuid,
        'journal.approved',
        ${tx.json({ proposal_id: body.proposal_id } as never)},
        ${userId}
      )
    `
  })

  return { ok: true, proposal_id: body.proposal_id }
}

async function applyProjectionDeltas(
  tx: ExecSql,
  organizationId: string,
  lines: { account_id: number; debit_amount: number; credit_amount: number }[],
  sign: 1 | -1
) {
  for (const l of lines) {
    const d = sign * Number(l.debit_amount)
    const c = sign * Number(l.credit_amount)
    await tx`
      INSERT INTO public.ledger_projection_account_balance (
        organization_id, account_id, debit_total, credit_total
      ) VALUES (
        ${organizationId}::uuid,
        ${l.account_id},
        ${d},
        ${c}
      )
      ON CONFLICT (organization_id, account_id)
      DO UPDATE SET
        debit_total = ledger_projection_account_balance.debit_total + EXCLUDED.debit_total,
        credit_total = ledger_projection_account_balance.credit_total + EXCLUDED.credit_total,
        updated_at = NOW()
    `
  }
}

async function dualWriteLegacyJournal(
  tx: ExecSql,
  organizationId: string,
  userId: string,
  description: string,
  entryDate: string,
  reference: string | null,
  lines: ProposeBody['lines']
) {
  const total = lines.reduce((s, l) => s + Number(l.debit_amount), 0)
  const entryNumber = `V2-${Date.now()}`
  const [entry] = await tx<{ id: number }[]>`
    INSERT INTO public.journal_entries (
      organization_id,
      entry_number,
      entry_date,
      description,
      reference,
      total_amount,
      is_posted,
      created_by,
      posted_by,
      posted_at
    ) VALUES (
      ${organizationId}::uuid,
      ${entryNumber},
      ${entryDate}::date,
      ${description},
      ${reference},
      ${total},
      true,
      ${userId},
      ${userId},
      NOW()
    )
    RETURNING id
  `
  let order = 1
  for (const l of lines) {
    await tx`
      INSERT INTO public.journal_entry_lines (
        journal_entry_id,
        account_id,
        description,
        debit_amount,
        credit_amount,
        line_order
      ) VALUES (
        ${entry.id},
        ${l.account_id},
        ${l.description ?? null},
        ${l.debit_amount},
        ${l.credit_amount},
        ${order++}
      )
    `
  }
  return entry.id
}

export async function handlePost(sql: Sql, userId: string, body: z.infer<typeof postBodySchema>) {
  await assertOrgMembership(sql, userId, body.organization_id)
  assertJournalPolicy(
    { userId, organizationId: body.organization_id, action: 'post' },
    body
  )
  const [prop] = await sql<
    { id: number; status: string; payload: { lines?: ProposeBody['lines']; description?: string; entry_date?: string; reference?: string | null } }[]
  >`
    SELECT id, status, payload
    FROM public.journal_proposals
    WHERE id = ${body.proposal_id}
      AND organization_id = ${body.organization_id}::uuid
    LIMIT 1
  `
  if (!prop) {
    const e = new Error('Proposal not found')
    ;(e as Error & { status?: number }).status = 404
    throw e
  }
  if (prop.status !== 'approved') {
    const e = new Error('Proposal must be approved before posting')
    ;(e as Error & { status?: number }).status = 409
    throw e
  }
  const pl = parsePayloadRecord(prop.payload) as {
    lines?: ProposeBody['lines']
    description?: string
    entry_date?: string
    reference?: string | null
  }
  const lines = pl.lines
  if (!lines?.length) {
    const e = new Error('Invalid proposal payload')
    ;(e as Error & { status?: number }).status = 400
    throw e
  }
  assertBalanced(lines as ProposeBody['lines'])

  const dual = process.env.DUAL_WRITE_LEGACY_JOURNAL === 'true'

  const result = await sql.begin(async (tx) => {
    const postedPayload = {
      proposal_id: prop.id,
      description: pl.description,
      entry_date: pl.entry_date,
      reference: pl.reference ?? null,
      lines,
    }
    const [ev] = await tx<{ id: string }[]>`
      INSERT INTO public.ledger_events (organization_id, event_type, payload, created_by)
      VALUES (
        ${body.organization_id}::uuid,
        'journal.posted',
        ${tx.json(postedPayload as never)},
        ${userId}
      )
      RETURNING id
    `
    await applyProjectionDeltas(tx, body.organization_id, lines as ProposeBody['lines'], 1)
    await tx`
      UPDATE public.journal_proposals
      SET status = 'posted', updated_at = NOW()
      WHERE id = ${body.proposal_id}
    `
    let legacyJournalId: number | undefined
    if (dual) {
      legacyJournalId = await dualWriteLegacyJournal(
        tx,
        body.organization_id,
        userId,
        String(pl.description ?? ''),
        String(pl.entry_date ?? ''),
        pl.reference ?? null,
        lines as ProposeBody['lines']
      )
    }
    return { ledger_event_id: ev.id, legacy_journal_entry_id: legacyJournalId }
  })

  return { ok: true, ...result }
}

export async function handleReverse(sql: Sql, userId: string, body: z.infer<typeof reverseBodySchema>) {
  await assertOrgMembership(sql, userId, body.organization_id)
  assertJournalPolicy(
    { userId, organizationId: body.organization_id, action: 'reverse' },
    body
  )
  const [ev] = await sql<{ id: string; event_type: string; payload: { lines?: ProposeBody['lines'] } }[]>`
    SELECT id, event_type, payload
    FROM public.ledger_events
    WHERE id = ${body.posted_ledger_event_id}
      AND organization_id = ${body.organization_id}::uuid
    LIMIT 1
  `
  if (!ev || ev.event_type !== 'journal.posted') {
    const e = new Error('Posted ledger event not found')
    ;(e as Error & { status?: number }).status = 404
    throw e
  }
  const posted = parsePayloadRecord(ev.payload) as { lines?: ProposeBody['lines'] }
  const lines = posted.lines
  if (!lines?.length) {
    const e = new Error('Invalid posted payload')
    ;(e as Error & { status?: number }).status = 400
    throw e
  }

  await sql.begin(async (tx) => {
    await tx`
      INSERT INTO public.ledger_events (organization_id, event_type, payload, created_by)
      VALUES (
        ${body.organization_id}::uuid,
        'journal.reversed',
        ${tx.json({ reverses_ledger_event_id: ev.id } as never)},
        ${userId}
      )
    `
    await applyProjectionDeltas(tx, body.organization_id, lines as ProposeBody['lines'], -1)
  })

  return { ok: true, reversed_ledger_event_id: ev.id }
}

export async function listProposals(sql: Sql, userId: string, organizationId: string, status?: string) {
  await assertOrgMembership(sql, userId, organizationId)
  const rows = status
    ? await sql<
        {
          id: number
          status: string
          payload: unknown
          created_at: string
          created_by: string
        }[]
      >`
        SELECT id, status, payload, created_at, created_by
        FROM public.journal_proposals
        WHERE organization_id = ${organizationId}::uuid
          AND status = ${status}
        ORDER BY id DESC
        LIMIT 100
      `
    : await sql<
        {
          id: number
          status: string
          payload: unknown
          created_at: string
          created_by: string
        }[]
      >`
        SELECT id, status, payload, created_at, created_by
        FROM public.journal_proposals
        WHERE organization_id = ${organizationId}::uuid
        ORDER BY id DESC
        LIMIT 100
      `
  return rows
}

export async function projectionTrialBalance(sql: Sql, userId: string, organizationId: string) {
  await assertOrgMembership(sql, userId, organizationId)
  return sql<
    {
      account_id: number
      account_code: string
      account_name: string
      account_type: string
      debit_balance: string
      credit_balance: string
    }[]
  >`
    SELECT
      a.id AS account_id,
      a.code AS account_code,
      a.name AS account_name,
      a.account_type::text AS account_type,
      COALESCE(p.debit_total, 0)::text AS debit_balance,
      COALESCE(p.credit_total, 0)::text AS credit_balance
    FROM public.accounts a
    LEFT JOIN public.ledger_projection_account_balance p
      ON p.organization_id = a.organization_id
     AND p.account_id = a.id
    WHERE a.organization_id = ${organizationId}::uuid
      AND a.is_active = true
    ORDER BY a.code
  `
}

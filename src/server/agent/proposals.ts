import { validateJournalLinesForSave } from '@/lib/journal-validation'
import { authorizeAppDataCall } from '@/server/app-data-authorize'
import { DataServiceAdmin } from '@/server/data-service-admin'
import { BooksServiceAdmin } from '@/server/books/service'
import { assertNoControlAccounts } from '@/server/books/guards'
import { money, paymentEntry } from '@/server/books/rules'
import { getSql } from '@/server/pg'
import { actingUserStore } from '@/server/request-context'

export type ProposalLine = { account_id: number; code: string; name: string; debit: number; credit: number }
export type ProposalKind = 'journal' | 'payment' | 'post_document'
export type ProposalInput = {
  date: string
  description: string
  explanation: string
  confidence: 'high' | 'medium' | 'low'
  lines: { account_id: number; debit: number; credit: number }[]
  /** Set only when the person has confirmed this is not the same as a similar recent entry. */
  not_a_duplicate?: boolean
}
export type PaymentProposalInput = {
  document_id: number
  date: string
  amount: number
  bank_account_id: number
  reference?: string | null
  explanation: string
  confidence: 'high' | 'medium' | 'low'
}
export type PostDocumentProposalInput = {
  document_id: number
  control_account_id?: number | null
  explanation: string
  confidence: 'high' | 'medium' | 'low'
}
export type Proposal = {
  id: string
  kind: ProposalKind
  source: 'app' | 'mcp'
  source_name: string | null
  status: 'pending' | 'recorded' | 'discarded'
  date: string
  description: string
  explanation: string
  confidence: 'high' | 'medium' | 'low'
  lines: ProposalLine[]
  payload: Record<string, unknown> | null
  /** Things a person should look at before approving, worked out by rules, not by the AI. */
  warnings: string[]
  created_at: string
}

type Row = Proposal
type ChartRow = { id: number; code: string; name: string; account_type: string; is_postable?: boolean; is_contra?: boolean; is_control?: boolean }
const COLUMNS = 'id::text, kind, source, source_name, status, entry_date::text AS date, description, explanation, confidence, lines, payload, warnings, created_at::text'

const toValidationLines = (lines: { account_id: number; debit: number; credit: number }[]) =>
  lines.map((l, i) => ({ account_id: l.account_id, description: null, debit_amount: l.debit, credit_amount: l.credit, line_order: i + 1 }))

async function chartOf(org: string) {
  const chart = (await DataServiceAdmin.getAccounts(org, false)) as unknown as ChartRow[]
  return new Map(chart.map((a) => [Number(a.id), a]))
}

/** Account names for display, checking every account is this organization's and can be posted to. */
function named(byId: Map<number, ChartRow>, lines: { account_id: number; debit: number; credit: number }[]): ProposalLine[] {
  return lines.map((l) => {
    const a = byId.get(Number(l.account_id))
    if (!a) throw new Error(`Account ${l.account_id} is not in this organization. Use list_accounts.`)
    if (a.is_postable === false) throw new Error(`${a.name} is a header account and cannot be posted to.`)
    return { account_id: Number(l.account_id), code: a.code, name: a.name, debit: money(l.debit), credit: money(l.credit) }
  })
}

/** Plain checks a person should see before approving. They don't stop the proposal. */
function journalWarnings(byId: Map<number, ChartRow>, lines: ProposalLine[]) {
  const warnings: string[] = []
  for (const l of lines) {
    const a = byId.get(l.account_id)
    if (!a || a.is_contra) continue
    if (a.account_type === 'revenue' && l.debit > 0) warnings.push(`It takes ${l.debit} off ${a.name}, an income account. That's right for a refund or a correction, not for a sale.`)
    if (a.account_type === 'expense' && l.credit > 0) warnings.push(`It takes ${l.credit} off ${a.name}, a cost account. That's right for a refund or a correction, not for a purchase.`)
  }
  return warnings
}

const dayDiff = (a: string, b: string) => Math.abs(Date.parse(`${a.slice(0, 10)}T00:00:00Z`) - Date.parse(`${b.slice(0, 10)}T00:00:00Z`)) / 86400000
const signature = (lines: { account_id: number; debit: number; credit: number }[]) =>
  lines.map((l) => `${l.account_id}:${money(l.debit)}:${money(l.credit)}`).sort().join('|')

/** Refuses an entry that matches one already recorded or waiting, with the same accounts and amounts within a week. */
async function assertNotDuplicate(org: string, date: string, lines: ProposalLine[]) {
  const sql = getSql()
  const mine = signature(lines)
  const total = money(lines.reduce((s, l) => s + l.debit, 0))
  const recorded = (await sql`
    SELECT e.id, e.entry_number, e.entry_date::text AS date,
           json_agg(json_build_object('account_id', l.account_id, 'debit', l.debit_amount::float, 'credit', l.credit_amount::float)) AS lines
    FROM public.journal_entries e JOIN public.journal_entry_lines l ON l.journal_entry_id = e.id
    WHERE e.organization_id = ${org}::uuid AND e.total_amount = ${total}
      AND e.entry_date BETWEEN (${date}::date - 7) AND (${date}::date + 7)
    GROUP BY e.id
  `) as unknown as { entry_number: string; date: string; lines: { account_id: number; debit: number; credit: number }[] }[]
  const hit = recorded.find((e) => signature(e.lines.map((l) => ({ ...l, account_id: Number(l.account_id) }))) === mine)
  if (hit) throw new Error(`This looks the same as ${hit.entry_number} on ${hit.date}. Ask the person whether it's a separate transaction; if they say it is, propose it again with not_a_duplicate set.`)
  const waiting = (await sql`
    SELECT entry_date::text AS date, lines FROM public.agent_proposals
    WHERE organization_id = ${org}::uuid AND status = 'pending' AND kind = 'journal'
      AND entry_date BETWEEN (${date}::date - 7) AND (${date}::date + 7)
  `) as unknown as { date: string; lines: ProposalLine[] }[]
  if (waiting.some((p) => signature(p.lines) === mine && dayDiff(p.date, date) <= 7)) {
    throw new Error('The same entry is already waiting for approval. Point the person to it instead of proposing it again.')
  }
}

async function insertProposal(org: string, userId: string, source: 'app' | 'mcp', sourceName: string | null, p: { kind: ProposalKind; date: string; description: string; explanation: string; confidence: string; lines: ProposalLine[]; payload?: Record<string, unknown> | null; warnings?: string[]; status?: 'pending' | 'recorded'; journal_entry_id?: number | null }) {
  const sql = getSql()
  const rows = await sql.unsafe(
    `INSERT INTO public.agent_proposals (organization_id, proposed_by, source, source_name, kind, entry_date, description, explanation, confidence, lines, payload, warnings, status, decided_by, decided_at, journal_entry_id)
     VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6::date, $7, $8, $9, $10::jsonb, $11::jsonb, $12::jsonb, $13, $14::uuid, $15::timestamptz, $16)
     RETURNING ${COLUMNS}`,
    [org, userId, source, sourceName, p.kind, p.date, p.description, p.explanation, p.confidence, sql.json(p.lines as never), p.payload ? sql.json(p.payload as never) : null, sql.json((p.warnings ?? []) as never),
      p.status ?? 'pending', p.status === 'recorded' ? userId : null, p.status === 'recorded' ? new Date().toISOString() : null, p.journal_entry_id ?? null]
  )
  return rows[0] as unknown as Proposal
}

/** Checks balance, accounts, control accounts and duplicates before a journal proposal can exist. */
async function checkJournal(org: string, input: ProposalInput) {
  validateJournalLinesForSave(toValidationLines(input.lines))
  const byId = await chartOf(org)
  const lines = named(byId, input.lines)
  // Receivables, payables and stock move through invoices, bills, payments and stock, never a raw entry.
  await assertNoControlAccounts(getSql(), org, lines.map((l) => l.account_id))
  if (!input.not_a_duplicate) await assertNotDuplicate(org, input.date, lines)
  return { lines, warnings: journalWarnings(byId, lines) }
}

export async function createProposal(userId: string, org: string, source: 'app' | 'mcp', sourceName: string | null, input: ProposalInput): Promise<Proposal> {
  await authorizeAppDataCall('DataService', 'createJournalEntry', [{ organization_id: org }], userId)
  const { lines, warnings } = await checkJournal(org, input)
  return insertProposal(org, userId, source, sourceName, { kind: 'journal', date: input.date, description: input.description, explanation: input.explanation, confidence: input.confidence, lines, warnings })
}

type Doc = { id: number; kind: 'invoice' | 'bill'; number: string; status: string; party_name: string; issue_date: string; total: number; balance: number; control_account_id: number | null }

/** A payment against an open invoice or bill. Approving it records the payment there, so the invoice shows as paid. */
export async function createPaymentProposal(userId: string, org: string, source: 'app' | 'mcp', sourceName: string | null, input: PaymentProposalInput): Promise<Proposal> {
  await authorizeAppDataCall('BooksService', 'recordPayment', [org], userId)
  const doc = (await BooksServiceAdmin.getDocument(org, Number(input.document_id))) as unknown as Doc
  if (doc.status !== 'posted' && doc.status !== 'partial') throw new Error(doc.status === 'draft' ? `${doc.number} is still a draft. Propose posting it first.` : `${doc.number} is ${doc.status === 'paid' ? 'already paid' : doc.status}.`)
  const amount = money(Number(input.amount))
  if (!(amount > 0)) throw new Error('The amount must be more than zero.')
  if (input.date < doc.issue_date) throw new Error(`The payment can't be dated before ${doc.number} (${doc.issue_date}).`)
  const sql = getSql()
  const [{ waiting }] = (await sql`
    SELECT COALESCE(SUM((payload ->> 'amount')::numeric), 0)::float AS waiting FROM public.agent_proposals
    WHERE organization_id = ${org}::uuid AND status = 'pending' AND kind = 'payment' AND (payload ->> 'document_id')::bigint = ${doc.id}
  `) as unknown as { waiting: number }[]
  if (amount > money(Number(doc.balance) - Number(waiting)) + 0.004) {
    throw new Error(Number(waiting) > 0 ? `A payment for ${doc.number} is already waiting for approval, and together they'd be more than the ${Number(doc.balance).toFixed(2)} still open.` : `That's more than the ${Number(doc.balance).toFixed(2)} still open on ${doc.number}.`)
  }
  const byId = await chartOf(org)
  const bank = byId.get(Number(input.bank_account_id))
  if (!bank || bank.account_type !== 'asset' || bank.is_control) throw new Error('Choose a bank or cash account for the money, from list_accounts.')
  const lines = named(byId, paymentEntry(doc.kind, Number(doc.control_account_id), Number(input.bank_account_id), amount).map((l) => ({ account_id: l.account_id, debit: l.debit, credit: l.credit })))
  const warnings = Number(input.amount) < Number(doc.balance) ? [`This pays part of ${doc.number}: ${(Number(doc.balance) - amount).toFixed(2)} will still be open.`] : []
  return insertProposal(org, userId, source, sourceName, {
    kind: 'payment', date: input.date,
    description: `Payment ${doc.kind === 'invoice' ? 'from' : 'to'} ${doc.party_name} for ${doc.number}`,
    explanation: input.explanation, confidence: input.confidence, lines, warnings,
    payload: { document_id: doc.id, number: doc.number, amount, bank_account_id: Number(input.bank_account_id), reference: input.reference ?? null },
  })
}

/** Posting a draft invoice or bill. Approving it posts the document itself, with its stock and cost of sales. */
export async function createPostDocumentProposal(userId: string, org: string, source: 'app' | 'mcp', sourceName: string | null, input: PostDocumentProposalInput): Promise<Proposal> {
  await authorizeAppDataCall('BooksService', 'postDocument', [org], userId)
  const doc = (await BooksServiceAdmin.getDocument(org, Number(input.document_id))) as unknown as Doc
  if (doc.status !== 'draft') throw new Error(`${doc.number} is already posted.`)
  const preview = await BooksServiceAdmin.previewDocument(org, doc.id, { control_account_id: input.control_account_id ?? null })
  if (preview.problems.length) throw new Error(preview.problems.join(' '))
  const control = Number(input.control_account_id ?? preview.suggested_control_account_id ?? 0)
  const lines = preview.lines.map((l) => ({ account_id: l.account_id, code: l.code, name: l.name, debit: l.debit, credit: l.credit }))
  return insertProposal(org, userId, source, sourceName, {
    kind: 'post_document', date: doc.issue_date,
    description: `Post ${doc.kind} ${doc.number}, ${doc.party_name}`,
    explanation: input.explanation, confidence: input.confidence, lines,
    payload: { document_id: doc.id, number: doc.number, control_account_id: control || null },
  })
}

export async function listProposals(org: string, status: 'pending' | 'all' = 'pending'): Promise<Proposal[]> {
  const sql = getSql()
  return (await sql.unsafe(
    `SELECT ${COLUMNS} FROM public.agent_proposals WHERE organization_id = $1::uuid AND ($2 = 'all' OR status = 'pending') ORDER BY created_at DESC LIMIT 50`,
    [org, status]
  )) as unknown as Proposal[]
}

export async function discardProposal(userId: string, org: string, id: string) {
  await authorizeAppDataCall('DataService', 'createJournalEntry', [{ organization_id: org }], userId)
  const sql = getSql()
  const rows = await sql`
    UPDATE public.agent_proposals
    SET status = 'discarded', decided_by = ${userId}::uuid, decided_at = now()
    WHERE id = ${id}::uuid AND organization_id = ${org}::uuid AND status = 'pending'
    RETURNING id
  `
  if (rows.length === 0) throw new Error('This proposal was already decided.')
}

async function postEntry(userId: string, org: string, p: { date: string; description: string; lines: { account_id: number; debit: number; credit: number }[]; source: 'agent' | 'mcp'; source_id?: string | null }) {
  await authorizeAppDataCall('DataService', 'createJournalEntry', [{ organization_id: org }], userId)
  const { totalDebits, normalized } = validateJournalLinesForSave(toValidationLines(p.lines))
  const entry = await actingUserStore.run(userId, () => DataServiceAdmin.createJournalEntry({
    organization_id: org,
    entry_number: '',
    entry_date: p.date,
    description: p.description,
    reference: null,
    total_amount: totalDebits,
    is_posted: true,
    created_by: userId,
    posted_by: userId,
    posted_at: new Date().toISOString(),
    source: p.source,
    source_id: p.source_id ?? null,
  }, normalized))
  if (!entry) throw new Error('The entry could not be recorded.')
  return entry
}

/** Carries out a claimed proposal through the service its kind belongs to. Returns the entry it made. */
async function carryOut(userId: string, org: string, p: Row): Promise<{ id: number; entry_number: string }> {
  const sql = getSql()
  const payload = (p.payload ?? {}) as Record<string, unknown>
  if (p.kind === 'payment') {
    await authorizeAppDataCall('BooksService', 'recordPayment', [org], userId)
    const documentId = Number(payload.document_id)
    await actingUserStore.run(userId, () => BooksServiceAdmin.recordPayment(org, documentId, { date: p.date, amount: Number(payload.amount), bank_account_id: Number(payload.bank_account_id), reference: (payload.reference as string | null) ?? null }))
    const [e] = (await sql`
      SELECT e.id, e.entry_number FROM public.trade_payments t JOIN public.journal_entries e ON e.id = t.journal_entry_id
      WHERE t.document_id = ${documentId} AND t.organization_id = ${org}::uuid ORDER BY t.id DESC LIMIT 1
    `) as unknown as { id: number; entry_number: string }[]
    return e
  }
  if (p.kind === 'post_document') {
    await authorizeAppDataCall('BooksService', 'postDocument', [org], userId)
    const documentId = Number(payload.document_id)
    await actingUserStore.run(userId, () => BooksServiceAdmin.postDocument(org, documentId, { control_account_id: payload.control_account_id ? Number(payload.control_account_id) : null }))
    const [e] = (await sql`
      SELECT e.id, e.entry_number FROM public.trade_documents d JOIN public.journal_entries e ON e.id = d.journal_entry_id
      WHERE d.id = ${documentId} AND d.organization_id = ${org}::uuid
    `) as unknown as { id: number; entry_number: string }[]
    return e
  }
  const entry = await postEntry(userId, org, { date: p.date, description: p.description, lines: p.lines, source: p.source === 'mcp' ? 'mcp' : 'agent', source_id: p.id })
  return { id: Number(entry.id), entry_number: entry.entry_number }
}

/** Whether the organization wants a second person to approve what the agent proposes. */
export async function requiresSecondApprover(org: string) {
  const [row] = (await getSql()`
    SELECT COALESCE((settings -> 'accountingSettings' ->> 'requireSecondApprover')::boolean, false) AS on
    FROM public.organizations WHERE id = ${org}::uuid
  `) as unknown as { on: boolean }[]
  return Boolean(row?.on)
}

/** Claims the proposal first, so approving twice can never post twice. */
export async function approveProposal(userId: string, org: string, id: string) {
  await authorizeAppDataCall('DataService', 'createJournalEntry', [{ organization_id: org }], userId)
  const sql = getSql()
  if (await requiresSecondApprover(org)) {
    const [mine] = (await sql`SELECT 1 AS x FROM public.agent_proposals WHERE id = ${id}::uuid AND organization_id = ${org}::uuid AND proposed_by = ${userId}::uuid`) as unknown as unknown[]
    if (mine) throw new Error('Your organization needs a second person to approve this, so someone other than the person who asked for it has to approve it.')
  }
  const claimed = (await sql.unsafe(
    `UPDATE public.agent_proposals SET status = 'recorded', decided_by = $1::uuid, decided_at = now()
     WHERE id = $2::uuid AND organization_id = $3::uuid AND status = 'pending'
     RETURNING ${COLUMNS}`,
    [userId, id, org]
  )) as unknown as Row[]
  const p = claimed[0]
  if (!p) throw new Error('This proposal was already decided.')
  try {
    const entry = await carryOut(userId, org, p)
    await sql`UPDATE public.agent_proposals SET journal_entry_id = ${entry?.id ?? null} WHERE id = ${id}::uuid`
    return entry
  } catch (e) {
    await sql`UPDATE public.agent_proposals SET status = 'pending', decided_by = NULL, decided_at = NULL WHERE id = ${id}::uuid`
    throw e
  }
}

/**
 * Direct recording, only for MCP connections the person allowed to record. The same checks as a proposal apply,
 * and a proposal row marked recorded is kept, so every AI entry can be traced the same way.
 */
export async function recordDirectly(userId: string, org: string, input: ProposalInput, sourceName: string | null = null) {
  await authorizeAppDataCall('DataService', 'createJournalEntry', [{ organization_id: org }], userId)
  if (await requiresSecondApprover(org)) throw new Error('This organization needs a second person to approve entries from AI apps, so recording directly is off. Use propose_journal_entry instead.')
  const { lines, warnings } = await checkJournal(org, input)
  const entry = await postEntry(userId, org, { date: input.date, description: input.description, lines, source: 'mcp' })
  await insertProposal(org, userId, 'mcp', sourceName, { kind: 'journal', date: input.date, description: input.description, explanation: input.explanation, confidence: input.confidence, lines, warnings, status: 'recorded', journal_entry_id: Number(entry.id) })
  return entry
}

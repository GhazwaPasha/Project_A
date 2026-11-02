import { validateJournalLinesForSave } from '@/lib/journal-validation'
import { authorizeAppDataCall } from '@/server/app-data-authorize'
import { DataServiceAdmin } from '@/server/data-service-admin'
import { getSql } from '@/server/pg'
import { actingUserStore } from '@/server/request-context'

export type ProposalLine = { account_id: number; code: string; name: string; debit: number; credit: number }
export type ProposalInput = {
  date: string
  description: string
  explanation: string
  confidence: 'high' | 'medium' | 'low'
  lines: { account_id: number; debit: number; credit: number }[]
}
export type Proposal = {
  id: string
  source: 'app' | 'mcp'
  source_name: string | null
  status: 'pending' | 'recorded' | 'discarded'
  date: string
  description: string
  explanation: string
  confidence: 'high' | 'medium' | 'low'
  lines: ProposalLine[]
  created_at: string
}

const toValidationLines = (lines: { account_id: number; debit: number; credit: number }[]) =>
  lines.map((l, i) => ({ account_id: l.account_id, description: null, debit_amount: l.debit, credit_amount: l.credit, line_order: i + 1 }))

/** Checks balance and accounts, and fills in account names, before a proposal can exist. */
async function resolveLines(org: string, lines: ProposalInput['lines']): Promise<ProposalLine[]> {
  validateJournalLinesForSave(toValidationLines(lines))
  const chart = await DataServiceAdmin.getAccounts(org, false)
  const byId = new Map(chart.map((a) => [Number(a.id), a]))
  return lines.map((l) => {
    const a = byId.get(l.account_id)
    if (!a) throw new Error(`Account ${l.account_id} is not in this organization. Use list_accounts.`)
    if (a.is_postable === false) throw new Error(`${a.name} is a header account and cannot be posted to.`)
    return { account_id: l.account_id, code: a.code, name: a.name, debit: l.debit, credit: l.credit }
  })
}

type Row = { id: string; source: Proposal['source']; source_name: string | null; status: Proposal['status']; date: string; description: string; explanation: string; confidence: Proposal['confidence']; lines: ProposalLine[]; created_at: string }

export async function createProposal(userId: string, org: string, source: 'app' | 'mcp', sourceName: string | null, input: ProposalInput): Promise<Proposal> {
  await authorizeAppDataCall('DataService', 'createJournalEntry', [{ organization_id: org }], userId)
  const lines = await resolveLines(org, input.lines)
  const sql = getSql()
  const rows = await sql<Row[]>`
    INSERT INTO public.agent_proposals
      (organization_id, proposed_by, source, source_name, entry_date, description, explanation, confidence, lines)
    VALUES
      (${org}::uuid, ${userId}::uuid, ${source}, ${sourceName}, ${input.date}::date, ${input.description}, ${input.explanation}, ${input.confidence}, ${sql.json(lines)})
    RETURNING id::text, source, source_name, status, entry_date::text AS date, description, explanation, confidence, lines, created_at::text
  `
  return rows[0]
}

export async function listProposals(org: string, status: 'pending' | 'all' = 'pending'): Promise<Proposal[]> {
  const sql = getSql()
  return (await sql<Row[]>`
    SELECT id::text, source, source_name, status, entry_date::text AS date, description, explanation, confidence, lines, created_at::text
    FROM public.agent_proposals
    WHERE organization_id = ${org}::uuid
      AND (${status} = 'all' OR status = 'pending')
    ORDER BY created_at DESC
    LIMIT 50
  `) as Proposal[]
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

async function postEntry(userId: string, org: string, p: { date: string; description: string; lines: { account_id: number; debit: number; credit: number }[] }) {
  await authorizeAppDataCall('DataService', 'createJournalEntry', [{ organization_id: org }], userId)
  const { totalDebits, normalized } = validateJournalLinesForSave(toValidationLines(p.lines))
  const entry = await actingUserStore.run(userId, () => DataServiceAdmin.createJournalEntry({
    organization_id: org,
    entry_number: `JE-${Date.now()}`,
    entry_date: p.date,
    description: p.description,
    reference: null,
    total_amount: totalDebits,
    is_posted: true,
    created_by: userId,
    posted_by: userId,
    posted_at: new Date().toISOString(),
  }, normalized))
  if (!entry) throw new Error('The entry could not be recorded.')
  return entry
}

/** Claims the proposal first, so approving twice can never post twice. */
export async function approveProposal(userId: string, org: string, id: string) {
  await authorizeAppDataCall('DataService', 'createJournalEntry', [{ organization_id: org }], userId)
  const sql = getSql()
  const claimed = await sql<Row[]>`
    UPDATE public.agent_proposals
    SET status = 'recorded', decided_by = ${userId}::uuid, decided_at = now()
    WHERE id = ${id}::uuid AND organization_id = ${org}::uuid AND status = 'pending'
    RETURNING id::text, source, source_name, status, entry_date::text AS date, description, explanation, confidence, lines, created_at::text
  `
  const p = claimed[0]
  if (!p) throw new Error('This proposal was already decided.')
  try {
    const entry = await postEntry(userId, org, { date: p.date, description: p.description, lines: p.lines })
    await sql`UPDATE public.agent_proposals SET journal_entry_id = ${entry.id} WHERE id = ${id}::uuid`
    return entry
  } catch (e) {
    await sql`UPDATE public.agent_proposals SET status = 'pending', decided_by = NULL, decided_at = NULL WHERE id = ${id}::uuid`
    throw e
  }
}

/** Direct recording, only for MCP tokens the user explicitly allowed to record. */
export async function recordDirectly(userId: string, org: string, input: ProposalInput) {
  await resolveLines(org, input.lines)
  return postEntry(userId, org, input)
}

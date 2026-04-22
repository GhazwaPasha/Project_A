/**
 * Phase 3: agent-facing tools must only create **proposals**, never post.
 * Wire your agent runtime to call `POST /journal/propose` (command-api) or the
 * Next.js BFF `/api/commands/journal/propose` — never `/journal/post` without human/policy gates.
 */

import { proposeBodySchema, type ProposeBody } from '../journal/handlers.js'

export const PROPOSAL_ONLY_TOOL_NAMES = ['propose_journal'] as const

export type ProposalOnlyToolName = (typeof PROPOSAL_ONLY_TOOL_NAMES)[number]

export const proposalOnlyToolCatalog = [
  {
    name: 'propose_journal' as const,
    description:
      'Create a balanced journal entry proposal (journal.proposed event). Does not post to the ledger.',
    inputSchema: proposeBodySchema,
  },
]

/** Validates agent tool input; execution still goes through the authenticated command API. */
export function parseProposeJournalInput(input: unknown): ProposeBody {
  const parsed = proposeBodySchema.safeParse(input)
  if (!parsed.success) {
    throw new Error(`Invalid propose_journal payload: ${parsed.error.message}`)
  }
  return parsed.data
}

export function assertToolIsProposalOnly(name: string): asserts name is 'propose_journal' {
  if (name !== 'propose_journal') {
    throw new Error(`Agent tool "${name}" is not allowed in proposal-only mode`)
  }
}

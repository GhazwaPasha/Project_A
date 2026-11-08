import type { JournalEntryLine } from '@/types'


import { roundMoney as exactRound, toCents, fromCents } from '@/lib/money'

export function roundMoney(n: number): number {
  return exactRound(n)
}

export function parseMoneyInput(s: string): number {
  const n = parseFloat(s.trim())
  if (Number.isNaN(n) || n < 0) return 0
  return roundMoney(n)
}

export type NormalizedLine = Omit<JournalEntryLine, 'id' | 'journal_entry_id'>

/**
 * Enforces:
 * - At least two non-empty lines (debit or credit amount)
 * - Each line: not both debit and credit positive (no "two-sided" single line)
 * - Each line with an amount: must have account_id
 * - Sum(debits) === sum(credits)
 *
 * Reindexes `line_order` 1..n (blank UI rows are dropped).
 */
export function validateJournalLinesForSave(
  lines: Array<Omit<JournalEntryLine, 'id' | 'journal_entry_id'>>
): { totalDebits: number; totalCredits: number; normalized: NormalizedLine[] } {
  if (!lines?.length) {
    throw new Error('A journal entry must include at least one line row.')
  }

  const nonEmpty: NormalizedLine[] = []
  for (const l of lines) {
    const rawDebit = Number(l.debit_amount ?? 0)
    const rawCredit = Number(l.credit_amount ?? 0)
    if (!Number.isFinite(rawDebit) || !Number.isFinite(rawCredit)) {
      throw new Error('Every amount must be a number.')
    }
    if (rawDebit < 0 || rawCredit < 0) {
      throw new Error("Amounts can't be negative. Put the amount on the other side instead.")
    }
    const debit_amount = roundMoney(rawDebit)
    const credit_amount = roundMoney(rawCredit)
    if (debit_amount === 0 && credit_amount === 0) {
      continue
    }
    nonEmpty.push({ ...l, debit_amount, credit_amount, line_order: 0 })
  }

  if (nonEmpty.length < 2) {
    throw new Error('Add at least two lines with amounts that balance (total debits = total credits).')
  }

  let drCents = 0
  let crCents = 0
  for (const line of nonEmpty) {
    if (!line.account_id || line.account_id <= 0) {
      throw new Error('Each line with an amount must have a valid account.')
    }
    if (line.debit_amount > 0 && line.credit_amount > 0) {
      throw new Error(
        'Each line must be only a debit or only a credit, not both. Split mixed amounts into two lines.'
      )
    }
    drCents += toCents(line.debit_amount)
    crCents += toCents(line.credit_amount)
  }

  const tDr = fromCents(drCents)
  const tCr = fromCents(crCents)
  // Exact, in whole cents.
  if (drCents !== crCents) {
    throw new Error(
      `Debits (${tDr.toFixed(2)}) and credits (${tCr.toFixed(2)}) must be equal.`
    )
  }

  const normalized = nonEmpty.map((l, i) => ({ ...l, line_order: i + 1 }))
  return { totalDebits: tDr, totalCredits: tCr, normalized }
}

/** Client-side check from draft rows before calling the API. */
export function validateDraftLines(
  lines: Array<{ accountId: string; debit: string; credit: string }>
): { ok: true; message?: never } | { ok: false; message: string } {
  const built: Omit<JournalEntryLine, 'id' | 'journal_entry_id'>[] = []
  let order = 1
  for (const row of lines) {
    const dr = parseMoneyInput(row.debit)
    const cr = parseMoneyInput(row.credit)
    if (dr === 0 && cr === 0) continue
    if (!row.accountId.trim()) {
      return { ok: false, message: 'Each line with an amount must have an account selected.' }
    }
    const account_id = parseInt(row.accountId, 10)
    if (!Number.isFinite(account_id)) {
      return { ok: false, message: 'Invalid account on one of the lines.' }
    }
    built.push({
      account_id,
      description: null,
      debit_amount: dr,
      credit_amount: cr,
      line_order: order++,
    })
  }
  try {
    validateJournalLinesForSave(built)
  } catch (e) {
    return { ok: false, message: e instanceof Error ? e.message : 'Invalid lines' }
  }
  return { ok: true }
}

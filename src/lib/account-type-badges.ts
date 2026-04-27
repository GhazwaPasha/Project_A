import type { AccountType } from '@/types'

const LEVEL_COLOR_COUNT = 4

/**
 * M3 account-type chips. Uses `.m3-chip` in globals.css — Tailwind does not emit
 * `bg-*-container/40` or `text-on-*-container` for md-sys tokens, so plain utility
 * class names were inert in the built CSS.
 */
export function accountTypeBadgeClass(type: AccountType): string {
  const base = 'm3-chip m3-chip--account'
  switch (type) {
    case 'asset':
      return `${base} m3-chip--account-asset`
    case 'liability':
      return `${base} m3-chip--account-liability`
    case 'equity':
      return `${base} m3-chip--account-equity`
    case 'revenue':
      return `${base} m3-chip--account-revenue`
    case 'expense':
      return `${base} m3-chip--account-expense`
    default:
      return `${base} m3-chip--account-default`
  }
}

/** Distinct tints; cycles every four levels. Class names are literals (not template-built)
 *  so they cannot be mis-parsed, and we avoid the `*level-1` Tailwind / plugin collision
 *  pattern by using a dedicated `m3-ledger-lvl-*` prefix. */
const LEDGER_LEVEL_LIT: readonly string[] = [
  'm3-chip m3-ledger-lvl-1',
  'm3-chip m3-ledger-lvl-2',
  'm3-chip m3-ledger-lvl-3',
  'm3-chip m3-ledger-lvl-4',
]

export function accountLevelBadgeClass(level: number | string | null | undefined): string {
  const L = Math.max(1, Math.floor(Math.abs(Number(level)) || 1))
  return LEDGER_LEVEL_LIT[(L - 1) % LEVEL_COLOR_COUNT]!
}

/** Account code pill on ledger cards. */
export function accountCodeChipClass(): string {
  return 'm3-chip m3-chip--code'
}

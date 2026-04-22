'use client'

import { Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { AccountSearch } from '@/components/ui/account-search'
import { Account } from '@/types'
import { parseMoneyInput, roundMoney } from '@/lib/journal-validation'

export type DraftLine = { key: string; accountId: string; debit: string; credit: string }

function newLine(): DraftLine {
  return { key: crypto.randomUUID(), accountId: '', debit: '', credit: '' }
}

export function createInitialJournalLines(): DraftLine[] {
  return [newLine(), newLine()]
}

type Props = {
  accounts: Account[]
  lines: DraftLine[]
  onLinesChange: (lines: DraftLine[]) => void
  disabled?: boolean
}

function sumStr(lines: DraftLine[], field: 'debit' | 'credit'): number {
  return roundMoney(
    lines.reduce((s, l) => s + parseMoneyInput(l[field]), 0)
  )
}

export function JournalLinesEditor({ accounts, lines, onLinesChange, disabled }: Props) {
  const updateLine = (key: string, patch: Partial<DraftLine>) => {
    onLinesChange(
      lines.map((row) => (row.key === key ? { ...row, ...patch } : row))
    )
  }

  const addLine = () => {
    onLinesChange([...lines, newLine()])
  }

  const removeLine = (key: string) => {
    if (lines.length <= 2) return
    onLinesChange(lines.filter((l) => l.key !== key))
  }

  const tDr = sumStr(lines, 'debit')
  const tCr = sumStr(lines, 'credit')
  const diff = roundMoney(tDr - tCr)
  const balanced = Math.abs(diff) < 0.005

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label className="md-text-field-label">Entry lines (double-entry)</Label>
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={addLine}
          disabled={disabled}
          className="gap-1"
        >
          <Plus className="h-4 w-4" />
          Add line
        </Button>
      </div>
      <p className="text-xs text-on-surface-variant">
        For each line enter either a debit or a credit (not both). Add more lines for compound
        entries. Totals must match before you can post.
      </p>
      <div className="rounded-lg border border-outline overflow-hidden">
        <div
          className="grid gap-0 text-xs font-medium text-on-surface-variant border-b border-outline bg-surface-container-highest"
          style={{ gridTemplateColumns: '1fr minmax(0,6rem) minmax(0,6rem) auto' }}
        >
          <div className="px-3 py-2">Account</div>
          <div className="px-2 py-2 text-right">Debit</div>
          <div className="px-2 py-2 text-right">Credit</div>
          <div className="w-10" />
        </div>
        {lines.map((row) => (
          <div
            key={row.key}
            className="grid gap-0 border-b border-outline/80 last:border-0"
            style={{ gridTemplateColumns: '1fr minmax(0,6rem) minmax(0,6rem) auto' }}
          >
            <div className="p-2 min-w-0">
              <AccountSearch
                accounts={accounts}
                value={row.accountId}
                onChange={(accountId) => updateLine(row.key, { accountId })}
                placeholder="Account"
                className="w-full"
                disabled={disabled}
              />
            </div>
            <div className="p-2">
              <Input
                type="text"
                inputMode="decimal"
                placeholder="0.00"
                className="text-right font-mono text-sm"
                value={row.debit}
                onChange={(e) => {
                  const v = e.target.value
                  if (v && row.credit) {
                    updateLine(row.key, { debit: v, credit: '' })
                  } else {
                    updateLine(row.key, { debit: v })
                  }
                }}
                disabled={disabled}
              />
            </div>
            <div className="p-2">
              <Input
                type="text"
                inputMode="decimal"
                placeholder="0.00"
                className="text-right font-mono text-sm"
                value={row.credit}
                onChange={(e) => {
                  const v = e.target.value
                  if (v && row.debit) {
                    updateLine(row.key, { credit: v, debit: '' })
                  } else {
                    updateLine(row.key, { credit: v })
                  }
                }}
                disabled={disabled}
              />
            </div>
            <div className="p-1 flex items-center">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-8 w-8 shrink-0"
                onClick={() => removeLine(row.key)}
                disabled={disabled || lines.length <= 2}
                aria-label="Remove line"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
        <div
          className="grid gap-0 bg-surface-container/50 font-medium text-on-surface"
          style={{ gridTemplateColumns: '1fr minmax(0,6rem) minmax(0,6rem) auto' }}
        >
          <div className="px-3 py-2">Totals</div>
          <div className="px-2 py-2 text-right font-mono text-sm tabular-nums">
            {tDr.toFixed(2)}
          </div>
          <div className="px-2 py-2 text-right font-mono text-sm tabular-nums">
            {tCr.toFixed(2)}
          </div>
          <div className="w-10" />
        </div>
      </div>
      <div
        className={`text-sm ${
          balanced ? 'text-on-surface-variant' : 'text-on-error'
        }`}
        role="status"
      >
        {balanced
          ? 'Debits and credits are balanced.'
          : `Out of balance by ${Math.abs(diff).toFixed(2)} (${tDr > tCr ? 'debit' : 'credit'} side is higher).`}
      </div>
    </div>
  )
}

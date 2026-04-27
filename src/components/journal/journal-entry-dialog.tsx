'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Calendar } from '@/components/ui/calendar'
import { AlertCircle, Sparkles } from 'lucide-react'
import { DataService } from '@/lib/data-service'
import { Account, JournalEntry, JournalEntryLine } from '@/types'
import { parseTransaction } from '@/lib/ai-transaction-parser'
import { useCurrentOrganization } from '@/hooks/use-current-organization'
import { parseMoneyInput, validateJournalLinesForSave, roundMoney } from '@/lib/journal-validation'
import {
  JournalLinesEditor,
  createInitialJournalLines,
  type DraftLine,
} from '@/components/journal/journal-lines-editor'

interface JournalEntryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onEntryCreated?: (entry: JournalEntry) => void
  organizationId?: string
}

export function JournalEntryDialog({
  open,
  onOpenChange,
  onEntryCreated,
  organizationId: _organizationId,
}: JournalEntryDialogProps) {
  const currentOrganization = useCurrentOrganization()
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [aiInput, setAiInput] = useState('')
  const [aiLoading, setAiLoading] = useState(false)
  const [aiProgress, setAiProgress] = useState(0)
  const [entryDate, setEntryDate] = useState(new Date())
  const [description, setDescription] = useState('')
  const [lines, setLines] = useState<DraftLine[]>(() => createInitialJournalLines())

  useEffect(() => {
    if (open && currentOrganization) {
      void loadAccounts()
    }
  }, [open, currentOrganization])

  const loadAccounts = async () => {
    if (!currentOrganization) {
      setError('No organization selected')
      return
    }
    try {
      setLoading(true)
      const accountsData = await DataService.getAccounts(currentOrganization.id, true)
      setAccounts(accountsData.filter((acc) => acc.is_postable === true))
    } catch (err) {
      console.error('Error loading accounts:', err)
      setError('Failed to load accounts')
    } finally {
      setLoading(false)
    }
  }

  const handleAIParse = async () => {
    if (!aiInput.trim()) {
      setError('Please enter a description to parse.')
      return
    }
    try {
      setAiLoading(true)
      setAiProgress(0)
      setError(null)
      const progressInterval = setInterval(() => {
        setAiProgress((prev) => (prev >= 90 ? prev : prev + Math.random() * 15))
      }, 200)

      const parsed = await parseTransaction(aiInput, accounts)
      clearInterval(progressInterval)
      setAiProgress(100)

      const debitAccount = accounts.find(
        (acc) => String(acc.code) === String(parsed.debit_account_code)
      )
      const creditAccount = accounts.find(
        (acc) => String(acc.code) === String(parsed.credit_account_code)
      )

      if (!debitAccount || !creditAccount) {
        throw new Error(
          `Could not find accounts with codes: "${parsed.debit_account_code}" or "${parsed.credit_account_code}".`
        )
      }

      setDescription(parsed.description)
      setLines([
        {
          key: crypto.randomUUID(),
          accountId: String(debitAccount.id),
          debit: parsed.amount.toString(),
          credit: '',
        },
        {
          key: crypto.randomUUID(),
          accountId: String(creditAccount.id),
          debit: '',
          credit: parsed.amount.toString(),
        },
      ])
      if (parsed.date?.trim()) {
        const d = new Date(parsed.date)
        if (!isNaN(d.getTime())) setEntryDate(d)
      }
      setAiInput('')
    } catch (err) {
      console.error('Error parsing transaction:', err)
      setError(err instanceof Error ? err.message : 'Failed to parse transaction')
    } finally {
      setAiLoading(false)
      setAiProgress(0)
    }
  }

  const handleSubmit = async () => {
    if (!description.trim()) {
      setError('Description is required')
      return
    }
    if (!currentOrganization) {
      setError('No organization selected')
      return
    }
    const desc = description.trim()
    const built: Omit<JournalEntryLine, 'id' | 'journal_entry_id'>[] = []
    for (const row of lines) {
      const dr = parseMoneyInput(row.debit)
      const cr = parseMoneyInput(row.credit)
      if (dr === 0 && cr === 0) continue
      if (!row.accountId.trim()) {
        setError('Each line with an amount must have an account selected.')
        return
      }
      const accountId = parseInt(row.accountId, 10)
      if (!Number.isFinite(accountId)) {
        setError('Invalid account on one of the lines.')
        return
      }
      built.push({
        account_id: accountId,
        description: desc,
        debit_amount: dr,
        credit_amount: cr,
        line_order: 0,
      })
    }
    let totalDebits: number
    let normalized: Omit<JournalEntryLine, 'id' | 'journal_entry_id'>[]
    try {
      const v = validateJournalLinesForSave(built)
      totalDebits = v.totalDebits
      normalized = v.normalized
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Invalid entry lines')
      return
    }
    const tDr = roundMoney(totalDebits)
    const entryNumber = `JE-${Date.now()}`

    try {
      setLoading(true)
      setError(null)
      const journalEntry: Omit<JournalEntry, 'id' | 'created_at' | 'updated_at'> = {
        organization_id: currentOrganization.id,
        entry_number: entryNumber,
        entry_date: entryDate.toISOString().split('T')[0],
        description: desc,
        reference: null,
        total_amount: tDr,
        is_posted: true,
        created_by: null,
        posted_by: null,
        posted_at: new Date().toISOString(),
      }
      const createdEntry = await DataService.createJournalEntry(journalEntry, normalized)
      if (createdEntry) {
        setEntryDate(new Date())
        setDescription('')
        setLines(createInitialJournalLines())
        onEntryCreated?.(createdEntry)
        onOpenChange(false)
      } else {
        throw new Error('Failed to create journal entry')
      }
    } catch (err) {
      console.error('Error creating journal entry:', err)
      setError(
        err instanceof Error ? err.message : 'Failed to create journal entry'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    setEntryDate(new Date())
    setDescription('')
    setLines(createInitialJournalLines())
    setError(null)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-2xl max-h-[90vh] flex flex-col"
        style={{
          backgroundColor: 'var(--md-sys-color-surface-container-low)',
          color: 'var(--md-sys-color-on-surface)',
          borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24)',
          border: '1px solid var(--md-sys-color-outline-variant)',
        }}
      >
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>New journal entry</DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto space-y-6 scrollbar-hide">
          {error && (
            <div className="flex items-center space-x-3 p-4 bg-error-container rounded-lg border border-error">
              <AlertCircle className="h-5 w-5 text-on-error-container flex-shrink-0" />
              <span className="md-body-medium text-on-error-container">{error}</span>
            </div>
          )}

          <div className="md-text-field">
            <Label htmlFor="aiInput" className="md-text-field-label">
              AI assistant
            </Label>
            <div className="flex gap-2">
              <Input
                id="aiInput"
                placeholder="Describe the transaction; AI fills a simple 2-line entry"
                value={aiInput}
                onChange={(e) => setAiInput(e.target.value)}
                className="flex-1"
                disabled={aiLoading}
              />
              {aiLoading ? (
                <div className="relative w-32 h-10 bg-surface-container-highest rounded-lg overflow-hidden border border-outline">
                  <div
                    className="absolute inset-0 bg-primary transition-all duration-300 ease-out"
                    style={{ width: `${aiProgress}%` }}
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-sm font-medium text-on-primary relative z-10">
                      {aiProgress < 100 ? 'Thinking...' : 'Complete!'}
                    </span>
                  </div>
                </div>
              ) : (
                <Button
                  type="button"
                  onClick={handleAIParse}
                  disabled={!aiInput.trim()}
                  className="md-button bg-primary text-on-primary border-0 px-6 h-10 hover:opacity-90"
                >
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4" />
                    <span>AI fill</span>
                  </div>
                </Button>
              )}
            </div>
          </div>

          <div className="md-text-field">
            <Label htmlFor="description" className="md-text-field-label">
              Description <span className="text-error">*</span>
            </Label>
            <Input
              id="description"
              placeholder="Entry description"
              value={description}
              onChange={(e) => {
                setDescription(e.target.value)
                setError(null)
              }}
              className="w-full"
              autoFocus
            />
          </div>

          <JournalLinesEditor
            accounts={accounts}
            lines={lines}
            onLinesChange={(next) => {
              setLines(next)
              setError(null)
            }}
            disabled={loading}
          />

          <div className="md-text-field">
            <Label htmlFor="entryDate" className="md-text-field-label">
              Entry date
            </Label>
            <Calendar
              selected={entryDate}
              onChange={(date) => date && setEntryDate(date)}
              placeholder="Select date"
              className="w-full"
            />
          </div>
        </div>

        <DialogFooter className="flex-shrink-0 pt-4 border-t border-outline-variant">
          <Button className="md-button-outlined" onClick={handleCancel} disabled={loading}>
            Cancel
          </Button>
          <Button className="md-button" onClick={handleSubmit} disabled={loading}>
            {loading ? 'Creating…' : 'Create entry'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

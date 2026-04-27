'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { AlertCircle, Plus, Trash2, Upload, Download } from 'lucide-react'
import { DataService } from '@/lib/data-service'
import { Account, JournalEntry, JournalEntryLine } from '@/types'
import { handleFileImport, downloadCSVTemplate } from '@/lib/file-import-utils'
import { useCurrentOrganization } from '@/hooks/use-current-organization'
import {
  parseMoneyInput,
  validateJournalLinesForSave,
  roundMoney,
  validateDraftLines,
} from '@/lib/journal-validation'
import {
  JournalLinesEditor,
  createInitialJournalLines,
  type DraftLine,
} from '@/components/journal/journal-lines-editor'
import { useOrganizationFormatters } from '@/hooks/use-organization-formatters'

interface BulkEntryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onEntriesCreated?: (entries: JournalEntry[]) => void
  organizationId?: string
}

interface BulkEntryFormData {
  entryDate: Date
  description: string
  lines: DraftLine[]
}

interface BulkEntryCard {
  id: string
  data: BulkEntryFormData
  isValid: boolean
}

function cardDataFromTwoAccounts(
  debitId: string,
  creditId: string,
  amount: string
): DraftLine[] {
  return [
    { key: crypto.randomUUID(), accountId: debitId, debit: amount, credit: '' },
    { key: crypto.randomUUID(), accountId: creditId, debit: '', credit: amount },
  ]
}

export function BulkEntryDialog({
  open,
  onOpenChange,
  onEntriesCreated,
  organizationId: _organizationId,
}: BulkEntryDialogProps) {
  const currentOrganization = useCurrentOrganization()
  const { formatCurrency } = useOrganizationFormatters()
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cards, setCards] = useState<BulkEntryCard[]>([])
  const [importing, setImporting] = useState(false)

  useEffect(() => {
    if (open && currentOrganization) {
      void loadAccounts()
      if (cards.length === 0) {
        addNewCard()
      }
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
      setAccounts(accountsData.filter((a) => a.is_postable === true))
    } catch (err) {
      console.error('Error loading accounts:', err)
      setError('Failed to load accounts')
    } finally {
      setLoading(false)
    }
  }

  const createEmptyCard = (): BulkEntryCard => ({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
    data: {
      entryDate: new Date(),
      description: '',
      lines: createInitialJournalLines(),
    },
    isValid: false,
  })

  const addNewCard = () => {
    setCards((prev) => [...prev, createEmptyCard()])
  }

  const removeCard = (cardId: string) => {
    setCards((prev) => prev.filter((card) => card.id !== cardId))
  }

  const updateCard = (cardId: string, field: keyof BulkEntryFormData, value: string | Date) => {
    setCards((prev) =>
      prev.map((card) => {
        if (card.id !== cardId) return card
        const data = { ...card.data, [field]: value }
        return { ...card, data, isValid: validateCardData(data) }
      })
    )
  }

  const updateCardLines = (cardId: string, lines: DraftLine[]) => {
    setCards((prev) =>
      prev.map((card) => {
        if (card.id !== cardId) return card
        const data = { ...card.data, lines }
        return { ...card, data, isValid: validateCardData(data) }
      })
    )
  }

  const validateCardData = (data: BulkEntryFormData): boolean => {
    if (!data.description.trim()) return false
    const { ok } = validateDraftLines(data.lines)
    return ok
  }

  const getTotalDebits = () => {
    let sum = 0
    for (const c of cards) {
      if (!c.isValid) continue
      for (const row of c.data.lines) {
        sum += parseMoneyInput(row.debit)
      }
    }
    return roundMoney(sum)
  }

  const saveAllEntries = async () => {
    const validCards = cards.filter((card) => card.isValid)
    if (validCards.length === 0) {
      setError('No valid entries to save.')
      return
    }
    if (!currentOrganization) {
      setError('No organization selected')
      return
    }
    try {
      setLoading(true)
      setError(null)
      const createdEntries: JournalEntry[] = []
      for (const card of validCards) {
        const desc = card.data.description.trim()
        const built: Omit<JournalEntryLine, 'id' | 'journal_entry_id'>[] = []
        for (const row of card.data.lines) {
          const dr = parseMoneyInput(row.debit)
          const cr = parseMoneyInput(row.credit)
          if (dr === 0 && cr === 0) continue
          if (!row.accountId.trim()) {
            setError('Each line with an amount must have an account in every valid entry.')
            return
          }
          const account_id = parseInt(row.accountId, 10)
          if (!Number.isFinite(account_id)) {
            setError('Invalid account on a line in one of the cards.')
            return
          }
          built.push({
            account_id,
            description: desc,
            debit_amount: dr,
            credit_amount: cr,
            line_order: 0,
          })
        }
        const { totalDebits, normalized } = validateJournalLinesForSave(built)
        const entryNumber = `JE-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
        const journalEntry: Omit<JournalEntry, 'id' | 'created_at' | 'updated_at'> = {
          organization_id: currentOrganization.id,
          entry_number: entryNumber,
          entry_date: card.data.entryDate.toISOString().split('T')[0],
          description: desc,
          reference: null,
          total_amount: totalDebits,
          is_posted: true,
          created_by: null,
          posted_by: null,
          posted_at: new Date().toISOString(),
        }
        const created = await DataService.createJournalEntry(journalEntry, normalized)
        if (created) {
          createdEntries.push(created)
        }
      }
      if (createdEntries.length > 0) {
        onEntriesCreated?.(createdEntries)
        setCards([])
        onOpenChange(false)
      }
    } catch (err) {
      console.error('Error saving entries:', err)
      setError(err instanceof Error ? err.message : 'Failed to save entries')
    } finally {
      setLoading(false)
    }
  }

  const clearAllCards = () => {
    setCards([createEmptyCard()])
  }

  const onBulkFileInputChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    try {
      setImporting(true)
      setError(null)
      const result = await handleFileImport(file)
      if (!result.success) {
        setError(result.errors.join('; '))
        return
      }
      if (result.entries.length === 0) {
        setError('No valid entries found in the file')
        return
      }
      const newCards: BulkEntryCard[] = result.entries.map((entry, index) => {
        const debitAccount = accounts.find(
          (acc) =>
            acc.name.toLowerCase().includes(entry.debitAccount.toLowerCase()) ||
            acc.code.toLowerCase().includes(entry.debitAccount.toLowerCase())
        )
        const creditAccount = accounts.find(
          (acc) =>
            acc.name.toLowerCase().includes(entry.creditAccount.toLowerCase()) ||
            acc.code.toLowerCase().includes(entry.creditAccount.toLowerCase())
        )
        let entryDate = new Date()
        try {
          if (entry.date.includes('/')) {
            const [month, day, year] = entry.date.split('/')
            entryDate = new Date(parseInt(year, 10), parseInt(month, 10) - 1, parseInt(day, 10))
          } else if (entry.date.includes('-')) {
            entryDate = new Date(entry.date)
          }
        } catch {
          entryDate = new Date()
        }
        const lines =
          debitAccount && creditAccount
            ? cardDataFromTwoAccounts(
                String(debitAccount.id),
                String(creditAccount.id),
                String(entry.amount)
              )
            : createInitialJournalLines()
        const data: BulkEntryFormData = {
          entryDate,
          description: entry.description,
          lines,
        }
        return {
          id: `imported-${Date.now()}-${index}`,
          data,
          isValid: validateCardData(data),
        }
      })
      setCards((prev) => [...prev, ...newCards])
      if (result.errors.length > 0) {
        setError(
          `Imported ${result.validRows} of ${result.totalRows} entries. Warnings: ${result.errors
            .slice(0, 3)
            .join('; ')}${result.errors.length > 3 ? '...' : ''}`
        )
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import file')
    } finally {
      setImporting(false)
      event.target.value = ''
    }
  }

  const handleDownloadTemplate = () => {
    downloadCSVTemplate()
  }

  const validCardsCount = cards.filter((card) => card.isValid).length

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-[95vw] max-h-[95vh] w-full flex flex-col"
        style={{
          backgroundColor: 'var(--md-sys-color-surface-container-low)',
          color: 'var(--md-sys-color-on-surface)',
          borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24)',
          border: '1px solid var(--md-sys-color-outline-variant)',
        }}
      >
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>Bulk entry</DialogTitle>
          <div className="flex items-center justify-between mt-2 flex-wrap gap-2">
            <span className="text-sm text-on-surface-variant">
              {validCardsCount} valid, {formatCurrency(getTotalDebits())} total debits
            </span>
            <div className="flex gap-2">
              <Button
                type="button"
                onClick={addNewCard}
                className="md-button-outlined"
                size="sm"
              >
                <Plus className="w-4 h-4 mr-1" />
                Add entry
              </Button>
              <Button
                type="button"
                onClick={handleDownloadTemplate}
                className="md-button-outlined"
                size="sm"
              >
                <Download className="w-4 h-4 mr-1" />
                Template
              </Button>
              <div className="relative">
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={onBulkFileInputChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  disabled={importing}
                />
                <Button
                  type="button"
                  className="md-button-outlined"
                  size="sm"
                  disabled={importing}
                >
                  <Upload className="w-4 h-4 mr-1" />
                  {importing ? 'Importing...' : 'Import'}
                </Button>
              </div>
              <Button
                type="button"
                onClick={clearAllCards}
                className="md-button-outlined"
                size="sm"
                variant="destructive"
              >
                <Trash2 className="w-4 h-4 mr-1" />
                Clear all
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto space-y-4 scrollbar-hide min-h-0">
          {error && (
            <div className="flex items-center space-x-3 p-4 bg-error-container rounded-lg border border-error">
              <AlertCircle className="h-5 w-5 text-on-error-container flex-shrink-0" />
              <span className="md-body-medium text-on-error-container">{error}</span>
            </div>
          )}

          <div className="space-y-3">
            {cards.map((card, index) => (
              <div
                key={card.id}
                className="md-card p-4 border border-outline-variant rounded-lg"
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="md-title-small text-on-surface">Entry #{index + 1}</h4>
                  <Button
                    type="button"
                    onClick={() => removeCard(card.id)}
                    className="md-button-outlined"
                    size="sm"
                    variant="destructive"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                  <div className="md-text-field">
                    <Label className="md-text-field-label">Date</Label>
                    <Input
                      type="date"
                      value={card.data.entryDate.toISOString().split('T')[0]}
                      onChange={(e) => updateCard(card.id, 'entryDate', new Date(e.target.value))}
                      className="w-full"
                    />
                  </div>
                  <div className="md-text-field md:col-span-1">
                    <Label className="md-text-field-label">Description</Label>
                    <Input
                      placeholder="Description"
                      value={card.data.description}
                      onChange={(e) => updateCard(card.id, 'description', e.target.value)}
                      className="w-full"
                    />
                  </div>
                </div>
                <JournalLinesEditor
                  accounts={accounts}
                  lines={card.data.lines}
                  onLinesChange={(lines) => updateCardLines(card.id, lines)}
                  disabled={loading}
                />
                <div className="mt-2 flex items-center justify-between text-sm">
                  <div
                    className={`flex items-center gap-2 ${
                      card.isValid ? 'text-on-surface-variant' : 'text-on-error'
                    }`}
                  >
                    <div
                      className={`w-2 h-2 rounded-full ${
                        card.isValid ? 'bg-green-500' : 'bg-destructive'
                      }`}
                    />
                    {card.isValid ? 'Valid (balanced lines)' : 'Add description and balanced lines'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <DialogFooter className="flex-shrink-0 pt-4 border-t border-outline-variant">
          <Button
            className="md-button-outlined"
            onClick={() => onOpenChange(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            className="md-button"
            onClick={() => void saveAllEntries()}
            disabled={loading || validCardsCount === 0}
          >
            {loading ? 'Saving...' : `Save ${validCardsCount} ${validCardsCount === 1 ? 'entry' : 'entries'}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

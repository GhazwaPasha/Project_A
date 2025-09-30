'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { AccountSearch } from '@/components/ui/account-search'
import { Calendar } from '@/components/ui/calendar'
import { X, AlertCircle, Plus, Trash2, Save, Upload, Download } from 'lucide-react'
import { DataService } from '@/lib/data-service'
import { Account, JournalEntry, JournalEntryLine } from '@/types'
import { formatCurrency, formatDate } from '@/lib/utils'
import { handleFileImport, ImportedEntry, downloadCSVTemplate } from '@/lib/file-import-utils'

interface BulkEntryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onEntriesCreated?: (entries: JournalEntry[]) => void
  organizationId: string
}

interface BulkEntryFormData {
  entryDate: Date
  description: string
  debitAccountId: string
  creditAccountId: string
  amount: string
}

interface BulkEntryCard {
  id: string
  data: BulkEntryFormData
  isValid: boolean
}

export function BulkEntryDialog({ 
  open, 
  onOpenChange, 
  onEntriesCreated,
  organizationId 
}: BulkEntryDialogProps) {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cards, setCards] = useState<BulkEntryCard[]>([])
  const [importing, setImporting] = useState(false)

  // Load accounts when dialog opens
  useEffect(() => {
    if (open && organizationId) {
      loadAccounts()
      // Start with one empty card
      if (cards.length === 0) {
        addNewCard()
      }
    }
  }, [open, organizationId])

  const loadAccounts = async () => {
    try {
      setLoading(true)
      const accountsData = await DataService.getAccounts(organizationId, true)
      setAccounts(accountsData)
    } catch (err) {
      console.error('Error loading accounts:', err)
      setError('Failed to load accounts')
    } finally {
      setLoading(false)
    }
  }

  const createEmptyCard = (): BulkEntryCard => ({
    id: Date.now().toString(),
    data: {
      entryDate: new Date(),
      description: '',
      debitAccountId: '',
      creditAccountId: '',
      amount: ''
    },
    isValid: false
  })

  const addNewCard = () => {
    const newCard = createEmptyCard()
    setCards(prev => [...prev, newCard])
  }

  const removeCard = (cardId: string) => {
    setCards(prev => prev.filter(card => card.id !== cardId))
  }

  const updateCard = (cardId: string, field: keyof BulkEntryFormData, value: string | Date) => {
    setCards(prev => prev.map(card => {
      if (card.id === cardId) {
        const updatedData = { ...card.data, [field]: value }
        const isValid = validateCardData(updatedData)
        return { ...card, data: updatedData, isValid }
      }
      return card
    }))
  }

  const validateCardData = (data: BulkEntryFormData): boolean => {
    return !!(
      data.description.trim() &&
      data.debitAccountId &&
      data.creditAccountId &&
      data.amount &&
      parseFloat(data.amount) > 0 &&
      data.debitAccountId !== data.creditAccountId
    )
  }


  const saveAllEntries = async () => {
    const validCards = cards.filter(card => card.isValid)
    
    if (validCards.length === 0) {
      setError('No valid entries to save.')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const createdEntries: JournalEntry[] = []

      for (const card of validCards) {
        const debitAccount = accounts.find(acc => acc.id.toString() === card.data.debitAccountId)
        const creditAccount = accounts.find(acc => acc.id.toString() === card.data.creditAccountId)

        if (!debitAccount || !creditAccount) {
          throw new Error(`Could not find accounts for entry: ${card.data.description}`)
        }

        const amount = parseFloat(card.data.amount)
        const entryNumber = `JE-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

        // Create journal entry
        const journalEntry: Omit<JournalEntry, 'id' | 'created_at' | 'updated_at'> = {
          organization_id: organizationId,
          entry_number: entryNumber,
          entry_date: card.data.entryDate.toISOString().split('T')[0],
          description: card.data.description.trim(),
          reference: null,
          total_amount: amount,
          is_posted: true,
          created_by: null,
          posted_by: null,
          posted_at: new Date().toISOString()
        }

        // Create journal entry lines
        const lines: Omit<JournalEntryLine, 'id' | 'journal_entry_id'>[] = [
          {
            account_id: debitAccount.id,
            description: card.data.description.trim(),
            debit_amount: amount,
            credit_amount: 0,
            line_order: 1
          },
          {
            account_id: creditAccount.id,
            description: card.data.description.trim(),
            debit_amount: 0,
            credit_amount: amount,
            line_order: 2
          }
        ]

        const createdEntry = await DataService.createJournalEntry(journalEntry, lines)
        if (createdEntry) {
          createdEntries.push(createdEntry)
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
    setCards([])
    addNewCard()
  }

  const handleFileImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
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

      // Convert imported entries to cards
      const newCards: BulkEntryCard[] = result.entries.map((entry, index) => {
        // Find matching accounts
        const debitAccount = accounts.find(acc => 
          acc.name.toLowerCase().includes(entry.debitAccount.toLowerCase()) ||
          acc.code.toLowerCase().includes(entry.debitAccount.toLowerCase())
        )
        
        const creditAccount = accounts.find(acc => 
          acc.name.toLowerCase().includes(entry.creditAccount.toLowerCase()) ||
          acc.code.toLowerCase().includes(entry.creditAccount.toLowerCase())
        )

        // Parse date
        let entryDate = new Date()
        try {
          // Try different date formats
          if (entry.date.includes('/')) {
            const [month, day, year] = entry.date.split('/')
            entryDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(day))
          } else if (entry.date.includes('-')) {
            entryDate = new Date(entry.date)
          }
        } catch (e) {
          // Use current date as fallback
          entryDate = new Date()
        }

        return {
          id: `imported-${Date.now()}-${index}`,
          data: {
            entryDate,
            description: entry.description,
            debitAccountId: debitAccount?.id.toString() || '',
            creditAccountId: creditAccount?.id.toString() || '',
            amount: entry.amount
          },
          isValid: !!(debitAccount && creditAccount && entry.description && entry.amount)
        }
      })

      setCards(prev => [...prev, ...newCards])

      // Show import summary
      if (result.errors.length > 0) {
        setError(`Imported ${result.validRows} of ${result.totalRows} entries. Some rows had errors: ${result.errors.slice(0, 3).join('; ')}${result.errors.length > 3 ? '...' : ''}`)
      }

    } catch (err) {
      console.error('Error importing file:', err)
      setError(err instanceof Error ? err.message : 'Failed to import file')
    } finally {
      setImporting(false)
      // Reset file input
      event.target.value = ''
    }
  }

  const handleDownloadTemplate = () => {
    downloadCSVTemplate()
  }

  const getTotalAmount = () => {
    return cards
      .filter(card => card.isValid)
      .reduce((total, card) => total + parseFloat(card.data.amount || '0'), 0)
  }

  const validCardsCount = cards.filter(card => card.isValid).length

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[95vw] max-h-[95vh] w-full flex flex-col" style={{
        backgroundColor: 'var(--md-sys-color-surface-container-low)',
        color: 'var(--md-sys-color-on-surface)',
        borderRadius: '12px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24)',
        border: '1px solid var(--md-sys-color-outline-variant)'
      }}>
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>Bulk Entry</DialogTitle>
          <div className="flex items-center justify-between mt-2">
            <span className="text-sm text-on-surface-variant">
              {validCardsCount} valid entries, {formatCurrency(getTotalAmount())} total
            </span>
            <div className="flex gap-2">
              <Button
                type="button"
                onClick={addNewCard}
                className="md-button-outlined"
                size="sm"
              >
                <Plus className="w-4 h-4 mr-1" />
                Add Entry
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
                  onChange={handleFileImport}
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
                Clear All
              </Button>
            </div>
          </div>
        </DialogHeader>
        
        <div className="flex-1 overflow-y-auto space-y-4 scrollbar-hide">
          {/* Error Message */}
          {error && (
            <div className="flex items-center space-x-3 p-4 bg-error-container rounded-lg border border-error">
              <AlertCircle className="h-5 w-5 text-on-error-container flex-shrink-0" />
              <span className="md-body-medium text-on-error-container">{error}</span>
            </div>
          )}


          {/* Entry Cards */}
          <div className="space-y-3">
            {cards.map((card, index) => (
              <div key={card.id} className="md-card p-4 border border-outline-variant rounded-lg">
                <div className="flex items-center justify-between mb-4">
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

                <div className="grid grid-cols-5 gap-3">
                  {/* Date Field */}
                  <div className="md-text-field">
                    <Label className="md-text-field-label">Date</Label>
                    <Input
                      type="date"
                      value={card.data.entryDate.toISOString().split('T')[0]}
                      onChange={(e) => updateCard(card.id, 'entryDate', new Date(e.target.value))}
                      className="w-full"
                    />
                  </div>

                  {/* Description Field */}
                  <div className="md-text-field">
                    <Label className="md-text-field-label">Description</Label>
                    <Input
                      placeholder="Enter description"
                      value={card.data.description}
                      onChange={(e) => updateCard(card.id, 'description', e.target.value)}
                      className="w-full"
                    />
                  </div>

                  {/* Debit Account */}
                  <div className="md-text-field">
                    <Label className="md-text-field-label">Debit Account</Label>
                    <AccountSearch
                      accounts={accounts}
                      value={card.data.debitAccountId}
                      onChange={(accountId) => updateCard(card.id, 'debitAccountId', accountId)}
                      placeholder="Search debit account..."
                      className="w-full"
                    />
                  </div>

                  {/* Credit Account */}
                  <div className="md-text-field">
                    <Label className="md-text-field-label">Credit Account</Label>
                    <AccountSearch
                      accounts={accounts}
                      value={card.data.creditAccountId}
                      onChange={(accountId) => updateCard(card.id, 'creditAccountId', accountId)}
                      placeholder="Search credit account..."
                      className="w-full"
                    />
                  </div>

                  {/* Amount Field */}
                  <div className="md-text-field">
                    <Label className="md-text-field-label">Amount</Label>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      value={card.data.amount}
                      onChange={(e) => updateCard(card.id, 'amount', e.target.value)}
                      className="w-full"
                    />
                  </div>
                </div>

                {/* Validation Status */}
                <div className="mt-3 flex items-center justify-between">
                  <div className={`flex items-center gap-2 text-sm ${
                    card.isValid ? 'text-success' : 'text-error'
                  }`}>
                    <div className={`w-2 h-2 rounded-full ${
                      card.isValid ? 'bg-success' : 'bg-error'
                    }`} />
                    <span>{card.isValid ? 'Valid' : 'Incomplete'}</span>
                  </div>
                  {card.isValid && (
                    <span className="text-sm text-on-surface-variant">
                      {formatCurrency(parseFloat(card.data.amount || '0'))}
                    </span>
                  )}
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
            onClick={saveAllEntries} 
            disabled={loading || validCardsCount === 0}
          >
            {loading ? 'Saving Entries...' : `Save ${validCardsCount} Entries`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

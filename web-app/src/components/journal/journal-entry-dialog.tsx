'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { AccountSearch } from '@/components/ui/account-search'
import { Calendar } from '@/components/ui/calendar'
import { X, AlertCircle, Sparkles } from 'lucide-react'
import { DataService } from '@/lib/data-service'
import { Account, JournalEntry, JournalEntryLine } from '@/types'
import { parseTransaction, findAccountByName } from '@/lib/ai-transaction-parser'

interface JournalEntryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onEntryCreated?: (entry: JournalEntry) => void
  organizationId: string
}

interface JournalEntryFormData {
  entryDate: Date
  description: string
  debitAccountId: string
  creditAccountId: string
  amount: string
}

export function JournalEntryDialog({ 
  open, 
  onOpenChange, 
  onEntryCreated,
  organizationId 
}: JournalEntryDialogProps) {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [aiInput, setAiInput] = useState('')
  const [aiLoading, setAiLoading] = useState(false)
  const [formData, setFormData] = useState<JournalEntryFormData>({
    entryDate: new Date(),
    description: '',
    debitAccountId: '',
    creditAccountId: '',
    amount: ''
  })

  // Load accounts when dialog opens
  useEffect(() => {
    if (open && organizationId) {
      loadAccounts()
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

  const handleInputChange = (field: keyof JournalEntryFormData, value: string | Date) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    setError(null)
  }

  const handleAIParse = async () => {
    if (!aiInput.trim()) {
      setError('Please enter a description to parse.')
      return
    }

    try {
      setAiLoading(true)
      setError(null)

      const parsed = await parseTransaction(aiInput, accounts)
      
      // Find account IDs by name
      const debitAccount = findAccountByName(accounts, parsed.debit_account)
      const creditAccount = findAccountByName(accounts, parsed.credit_account)

      if (!debitAccount || !creditAccount) {
        throw new Error('Could not find matching accounts. Please check your account setup.')
      }

      // Update form data
      setFormData(prev => ({
        ...prev,
        description: parsed.description,
        debitAccountId: debitAccount.id.toString(),
        creditAccountId: creditAccount.id.toString(),
        amount: parsed.amount.toString()
      }))

      // Clear AI input
      setAiInput('')
    } catch (err) {
      console.error('Error parsing transaction:', err)
      setError(err instanceof Error ? err.message : 'Failed to parse transaction')
    } finally {
      setAiLoading(false)
    }
  }

  const validateForm = (): string | null => {
    if (!formData.description.trim()) {
      return 'Description is required'
    }
    if (!formData.debitAccountId) {
      return 'Debit account is required'
    }
    if (!formData.creditAccountId) {
      return 'Credit account is required'
    }
    if (formData.debitAccountId === formData.creditAccountId) {
      return 'Debit and credit accounts must be different'
    }
    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      return 'Amount must be greater than 0'
    }
    return null
  }

  const handleSubmit = async () => {
    const validationError = validateForm()
    if (validationError) {
      setError(validationError)
      return
    }

    try {
      setLoading(true)
      setError(null)

      const debitAccount = accounts.find(acc => acc.id.toString() === formData.debitAccountId)
      const creditAccount = accounts.find(acc => acc.id.toString() === formData.creditAccountId)

      if (!debitAccount || !creditAccount) {
        throw new Error('Selected accounts not found')
      }

      const amount = parseFloat(formData.amount)
      const entryNumber = `JE-${Date.now()}`

      // Create journal entry
      const journalEntry: Omit<JournalEntry, 'id' | 'created_at' | 'updated_at'> = {
        organization_id: organizationId,
        entry_number: entryNumber,
        entry_date: formData.entryDate.toISOString().split('T')[0],
        description: formData.description.trim(),
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
          description: formData.description.trim(),
          debit_amount: amount,
          credit_amount: 0,
          line_order: 1
        },
        {
          account_id: creditAccount.id,
          description: formData.description.trim(),
          debit_amount: 0,
          credit_amount: amount,
          line_order: 2
        }
      ]

      const createdEntry = await DataService.createJournalEntry(journalEntry, lines)
      
      if (createdEntry) {
        // Reset form
        setFormData({
          entryDate: new Date(),
          description: '',
          debitAccountId: '',
          creditAccountId: '',
          amount: ''
        })
        
        onEntryCreated?.(createdEntry)
        onOpenChange(false)
      } else {
        throw new Error('Failed to create journal entry')
      }
    } catch (err) {
      console.error('Error creating journal entry:', err)
      setError(err instanceof Error ? err.message : 'Failed to create journal entry')
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    setFormData({
      entryDate: new Date(),
      description: '',
      debitAccountId: '',
      creditAccountId: '',
      amount: ''
    })
    setError(null)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col" style={{
        backgroundColor: 'var(--md-sys-color-surface-container-low)',
        color: 'var(--md-sys-color-on-surface)',
        borderRadius: '12px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24)',
        border: '1px solid var(--md-sys-color-outline-variant)'
      }}>
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>New Journal Entry</DialogTitle>
        </DialogHeader>
        
        <div className="flex-1 overflow-y-auto space-y-6 scrollbar-hide">
          {/* Error Message */}
          {error && (
            <div className="flex items-center space-x-3 p-4 bg-error-container rounded-lg border border-error">
              <AlertCircle className="h-5 w-5 text-on-error-container flex-shrink-0" />
              <span className="md-body-medium text-on-error-container">{error}</span>
            </div>
          )}

          {/* Date Field */}
          <div className="md-text-field">
            <Label htmlFor="entryDate" className="md-text-field-label">
              Entry Date
            </Label>
            <Calendar
              selected={formData.entryDate}
              onChange={(date) => date && handleInputChange('entryDate', date)}
              placeholder="Select date"
              className="w-full"
              autoFocus={false}
              open={false}
            />
          </div>

          {/* AI Input Field - Full Width */}
          <div className="md-text-field">
            <Label htmlFor="aiInput" className="md-text-field-label">
              AI Assistant <span className="text-primary">✨</span>
            </Label>
            <div className="flex gap-2">
              <Input
                id="aiInput"
                placeholder="Go ahead, type your transaction as you'd say it out loud (e.g., 'Paid electricity bill $150')"
                value={aiInput}
                onChange={(e) => setAiInput(e.target.value)}
                className="flex-1"
                disabled={aiLoading}
              />
              <Button
                type="button"
                onClick={handleAIParse}
                disabled={aiLoading || !aiInput.trim()}
                className="md-button bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white border-0 px-6 h-14"
              >
                {aiLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Parsing...</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4" />
                    <span>AI Fill</span>
                  </div>
                )}
              </Button>
            </div>
          </div>

          {/* Description Field - Full Width */}
          <div className="md-text-field">
            <Label htmlFor="description" className="md-text-field-label">
              Description <span className="text-error">*</span>
            </Label>
            <Input
              id="description"
              placeholder="Enter transaction description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              className="w-full"
              autoFocus
            />
          </div>

          {/* Account Selection Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Debit Account */}
            <div className="md-text-field">
              <Label htmlFor="debitAccount" className="md-text-field-label">
                Debit Account <span className="text-error">*</span>
              </Label>
              <AccountSearch
                accounts={accounts}
                value={formData.debitAccountId}
                onChange={(accountId) => handleInputChange('debitAccountId', accountId)}
                placeholder="Search debit account..."
                className="w-full"
              />
            </div>

            {/* Credit Account */}
            <div className="md-text-field">
              <Label htmlFor="creditAccount" className="md-text-field-label">
                Credit Account <span className="text-error">*</span>
              </Label>
              <AccountSearch
                accounts={accounts}
                value={formData.creditAccountId}
                onChange={(accountId) => handleInputChange('creditAccountId', accountId)}
                placeholder="Search credit account..."
                className="w-full"
              />
            </div>
          </div>

          {/* Amount Field - Full Width */}
          <div className="md-text-field">
            <Label htmlFor="amount" className="md-text-field-label">
              Amount <span className="text-error">*</span>
            </Label>
            <Input
              id="amount"
              type="number"
              step="0.01"
              min="0"
              placeholder="0.00"
              value={formData.amount}
              onChange={(e) => handleInputChange('amount', e.target.value)}
              className="w-full"
            />
          </div>

          {/* Entry Summary */}
          {formData.debitAccountId && formData.creditAccountId && formData.amount && (
            <div className="p-4 bg-surface-container rounded-lg border border-outline">
              <h4 className="md-title-small text-on-surface mb-3">Entry Summary</h4>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="md-body-medium text-on-surface-variant">Debit:</span>
                  <span className="md-body-large text-on-surface font-medium">
                    {accounts.find(acc => acc.id.toString() === formData.debitAccountId)?.name}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="md-body-medium text-on-surface-variant">Credit:</span>
                  <span className="md-body-large text-on-surface font-medium">
                    {accounts.find(acc => acc.id.toString() === formData.creditAccountId)?.name}
                  </span>
                </div>
                <div className="flex justify-between items-center pt-2 border-t border-outline">
                  <span className="md-title-medium text-on-surface">Amount:</span>
                  <span className="md-title-large text-on-surface font-semibold">
                    ${parseFloat(formData.amount || '0').toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="flex-shrink-0 pt-4 border-t border-outline-variant">
          <Button 
            className="md-button-outlined" 
            onClick={handleCancel} 
            disabled={loading}
          >
            Cancel
          </Button>
          <Button 
            className="md-button" 
            onClick={handleSubmit} 
            disabled={loading}
          >
            {loading ? 'Creating Entry...' : 'Create Entry'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

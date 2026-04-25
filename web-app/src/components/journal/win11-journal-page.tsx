'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Plus, 
  Search, 
  Trash2,
  Calendar,
  FileText,
  Grid3X3,
  List,
  Info,
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { JournalEntryDialog } from './journal-entry-dialog'
import { BulkEntryDialog } from './bulk-entry-dialog'
import { JournalEntry, Account, JournalEntryLine } from '@/types'
import { useJournalEntries, useAccounts } from '@/hooks/use-organization-data'
import { useOrgDataPermission, useOrgMemberRoleResolved } from '@/hooks/use-org-permissions'
import { Alert, AlertDescription } from '@/components/ui/alert'

export function Win11JournalPage() {
  const roleResolved = useOrgMemberRoleResolved()
  const canWriteJournal = useOrgDataPermission('ledger.write')
  const writeDisabled = !roleResolved || !canWriteJournal
  const writeBlockTitle = !roleResolved
    ? 'Checking your access…'
    : !canWriteJournal
      ? 'Your role cannot post journal entries'
      : undefined
  const [searchTerm, setSearchTerm] = useState('')
  const [viewMode, setViewMode] = useState('cards') // 'cards' or 'table'
  const [showNewEntryDialog, setShowNewEntryDialog] = useState(false)
  const [showBulkEntryDialog, setShowBulkEntryDialog] = useState(false)
  const [showSearchField, setShowSearchField] = useState(false)

  // Use optimized hooks instead of manual data loading
  const { 
    data: journalEntries = [], 
    isLoading: entriesLoading, 
    error: entriesError,
    refetch: refetchEntries
  } = useJournalEntries()
  
  const { 
    data: accounts = [], 
    isLoading: accountsLoading, 
    error: accountsError 
  } = useAccounts()
  
  const loading = entriesLoading || accountsLoading
  const error = entriesError || accountsError

  const handleNewEntryCreated = (newEntry: JournalEntry) => {
    // React Query will automatically refetch the data
    refetchEntries()
  }

  const handleBulkEntriesCreated = (newEntries: JournalEntry[]) => {
    // React Query will automatically refetch the data
    refetchEntries()
  }

  const getAccountName = (accountId: number): string => {
    const account = accounts.find(acc => acc.id === accountId)
    return account ? `${account.code} - ${account.name}` : `Account ${accountId}`
  }

  const getDebitAndCreditSummary = (entry: JournalEntry & { lines: JournalEntryLine[] }) => {
    const lineCount = entry.lines?.length ?? 0
    const drLines = (entry.lines ?? []).filter((l) => l.debit_amount > 0)
    const crLines = (entry.lines ?? []).filter((l) => l.credit_amount > 0)
    if (lineCount > 2 || drLines.length + crLines.length > 2) {
      return {
        debit: `${drLines.length} debit line(s)`,
        credit: `${crLines.length} credit line(s)`,
        detail: `${lineCount} lines — balanced double-entry`,
      }
    }
    return {
      debit: drLines[0] ? getAccountName(drLines[0].account_id) : '—',
      credit: crLines[0] ? getAccountName(crLines[0].account_id) : '—',
      detail: null,
    }
  }

  const filteredTransactions = journalEntries.filter(entry => {
    const matchesSearch = entry.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (entry.reference && entry.reference.toLowerCase().includes(searchTerm.toLowerCase()))
    return matchesSearch
  })

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
      <div className="px-6 pt-6 space-y-3">
        {roleResolved && !canWriteJournal ? (
          <Alert className="border-primary/30 bg-primary-container/30">
            <Info className="h-4 w-4" />
            <AlertDescription>
              <span className="font-medium text-on-surface">View only in this organization.</span>{' '}
              Your role can browse the journal; posting and new entries are limited to Owner and
              Accountant.
            </AlertDescription>
          </Alert>
        ) : null}
      </div>
      {/* Fixed Header */}
      <div className="app-page-header sticky top-0 z-30">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="md-headline-small text-on-background">Journal Entries</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                {filteredTransactions.length} {filteredTransactions.length === 1 ? 'entry' : 'entries'}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className={`relative transition-all duration-300 ease-out overflow-hidden ${
                showSearchField 
                  ? 'w-80 opacity-100 translate-x-0' 
                  : 'w-0 opacity-0 -translate-x-4'
              }`}>
                <input
                  type="text"
                  placeholder="Search by description, reference, or account..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-80 h-10 px-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                  aria-label="Search transactions"
                  autoFocus={showSearchField}
                />
              </div>
              <Button 
                className="md-button-outlined"
                onClick={() => setShowSearchField(!showSearchField)}
              >
                <Search className="w-4 h-4" />
              </Button>
              <Button 
                className="md-button"
                disabled={writeDisabled}
                title={writeBlockTitle}
                onClick={() => roleResolved && canWriteJournal && setShowNewEntryDialog(true)}
              >
                <Plus className="w-4 h-4 mr-2" />
                New Entry
              </Button>
              <Button 
                className="md-button-outlined"
                disabled={writeDisabled}
                title={writeBlockTitle}
                onClick={() => roleResolved && canWriteJournal && setShowBulkEntryDialog(true)}
              >
                <FileText className="w-4 h-4 mr-2" />
                Bulk Entry
              </Button>
            </div>
          </div>

        </div>
      </div>

      {/* Main Content */}
      <div className="px-6 py-6">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
            <p className="text-on-surface-variant">Loading journal entries...</p>
          </div>
        ) : filteredTransactions.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-20 h-20 bg-primary-container rounded-3xl flex items-center justify-center mb-6">
              <FileText className="w-10 h-10 text-on-primary-container" />
            </div>
            <h3 className="md-headline-small text-on-surface mb-3">No transactions found</h3>
            <p className="md-body-large text-on-surface-variant text-center mb-8 max-w-md">
              {searchTerm 
                ? 'Try adjusting your search criteria.'
                : 'Get started by creating your first journal entry.'
              }
            </p>
            <div className="flex items-center gap-3">
              <Button 
                className="md-button"
                disabled={writeDisabled}
                title={writeBlockTitle}
                onClick={() => roleResolved && canWriteJournal && setShowNewEntryDialog(true)}
              >
                <Plus className="w-4 h-4 mr-2" />
                New Entry
              </Button>
              <Button 
                className="md-button-outlined"
                disabled={writeDisabled}
                title={writeBlockTitle}
                onClick={() => roleResolved && canWriteJournal && setShowBulkEntryDialog(true)}
              >
                <FileText className="w-4 h-4 mr-2" />
                Bulk Entry
              </Button>
            </div>
          </div>
        ) : (
           /* Transaction List - Compact Two-Line Cards */
           <div className="space-y-2">
             {filteredTransactions.map((entry) => {
               const { debit, credit, detail } = getDebitAndCreditSummary(entry)
               return (
                 <Card key={entry.id} className="md-card-expressive group hover:md-elevation-1 transition-all duration-200">
                   <CardContent className="p-4">
                     {/* First Line - Transaction Info */}
                     <div className="flex items-center justify-between mb-2">
                       <div className="flex items-center space-x-3 flex-1 min-w-0">
                         <h3 className="md-title-medium text-on-surface truncate">{entry.description}</h3>
                       </div>
                       {/* Debit and Credit Accounts - Moved to top right */}
                         <div className="flex flex-col items-end gap-1 text-sm min-w-0 max-w-md">
                         <div className="flex items-center space-x-4 flex-wrap justify-end">
                         <div className="flex items-center space-x-2 min-w-0">
                           <span className="px-2 py-1 rounded-md text-xs font-medium bg-primary text-on-primary">Debit</span>
                           <span className="text-on-surface font-medium truncate max-w-40">{debit}</span>
                         </div>
                         <div className="flex items-center space-x-2 min-w-0">
                           <span className="px-2 py-1 rounded-md text-xs font-medium bg-primary text-on-primary">Credit</span>
                           <span className="text-on-surface font-medium truncate max-w-40">{credit}</span>
                         </div>
                         </div>
                         {detail ? (
                           <span className="text-xs text-on-surface-variant text-right w-full">{detail}</span>
                         ) : null}
                       </div>
                     </div>

                     {/* Third Line - Date, Reference, and Total Amount */}
                     <div className="flex items-center justify-between">
                       <div className="flex items-center space-x-4 text-sm text-on-surface-variant">
                         <span className="flex items-center space-x-1">
                           <Calendar className="w-3 h-3" />
                           <span>{formatDate(entry.entry_date)}</span>
                         </span>
                         {entry.reference && (
                           <span className="flex items-center space-x-1">
                             <span className="w-1 h-1 bg-outline rounded-full"></span>
                             <span>{entry.reference}</span>
                           </span>
                         )}
                         <span className="flex items-center space-x-1">
                           <span className="w-1 h-1 bg-outline rounded-full"></span>
                           <span>{entry.entry_number}</span>
                         </span>
                       </div>
                       <div className="flex items-center space-x-6">
                         <span className="md-title-large text-on-surface font-medium">
                           {formatCurrency(entry.total_amount)}
                         </span>
                       </div>
                     </div>
                   </CardContent>
                 </Card>
               )
             })}
           </div>
        )}
      </div>

      {/* Journal Entry Dialog */}
      <JournalEntryDialog
        open={showNewEntryDialog}
        onOpenChange={setShowNewEntryDialog}
        onEntryCreated={handleNewEntryCreated}
        organizationId="current" // Will be resolved by the dialog
      />

      {/* Bulk Entry Dialog */}
      <BulkEntryDialog
        open={showBulkEntryDialog}
        onOpenChange={setShowBulkEntryDialog}
        onEntriesCreated={handleBulkEntriesCreated}
        organizationId="current" // Will be resolved by the dialog
      />
    </div>
  )
}
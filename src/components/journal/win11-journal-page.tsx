'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  Plus, 
  Search, 
  Calendar,
  FileText,
  Info,
} from 'lucide-react'
import { formatEntryDateTime } from '@/lib/utils'
import { useOrganizationFormatters } from '@/hooks/use-organization-formatters'
import { accountCodeChipClass } from '@/lib/account-type-badges'
import { JournalEntryDialog } from './journal-entry-dialog'
import { BulkEntryDialog } from './bulk-entry-dialog'
import { JournalEntry, Account, JournalEntryLine } from '@/types'
import { useJournalEntries, useAccounts } from '@/hooks/use-organization-data'
import { useOrgDataPermission, useOrgMemberRoleResolved } from '@/hooks/use-org-permissions'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { JournalListSkeleton } from '@/components/loading/app-page-skeletons'

export function Win11JournalPage() {
  const { formatCurrency } = useOrganizationFormatters()
  const roleResolved = useOrgMemberRoleResolved()
  const canWriteJournal = useOrgDataPermission('ledger.write')
  const [searchTerm, setSearchTerm] = useState('')
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

  const accessGateLoading = !roleResolved && (entriesLoading || accountsLoading)
  const writeDisabled = !roleResolved || !canWriteJournal
  const writeBlockTitle = accessGateLoading
    ? 'Loading your access…'
    : !roleResolved
      ? 'Checking your access…'
      : !canWriteJournal
        ? 'Your role cannot post journal entries'
        : undefined

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
                className="md-button"
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
                className="md-button"
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
          <JournalListSkeleton />
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
                className="md-button"
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
          <div
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5"
            role="list"
            aria-label="Journal entries"
          >
            {filteredTransactions.map((entry) => {
              const { debit, credit, detail } = getDebitAndCreditSummary(entry)
              return (
                <Card
                  key={entry.id}
                  role="listitem"
                  className="md-card-expressive group relative overflow-hidden border border-outline-variant/30 hover:border-primary/25 hover:md-elevation-1 transition-all duration-200 h-full flex flex-col"
                >
                  <div
                    className="absolute left-0 top-0 bottom-0 w-1 bg-primary/35 group-hover:bg-primary/55 transition-colors"
                    aria-hidden
                  />
                  <CardContent className="p-0 flex flex-col flex-1 min-h-0 pl-1">
                    <div className="px-4 pt-4 pb-3 space-y-3 flex-1">
                      <div className="flex items-start justify-between gap-3">
                        <span className={accountCodeChipClass()}>{entry.entry_number}</span>
                        <span className="md-title-large text-on-surface tabular-nums text-right leading-none shrink-0">
                          {formatCurrency(entry.total_amount)}
                        </span>
                      </div>

                      <p className="md-title-small text-on-surface line-clamp-3 leading-snug">{entry.description}</p>

                      <dl className="grid grid-cols-[2.25rem_1fr] gap-x-2 gap-y-1.5 text-sm">
                        <dt className="text-on-surface-variant/80 font-medium tabular-nums">Dr</dt>
                        <dd className="text-on-surface min-w-0 line-clamp-2 leading-tight">{debit}</dd>
                        <dt className="text-on-surface-variant/80 font-medium tabular-nums">Cr</dt>
                        <dd className="text-on-surface min-w-0 line-clamp-2 leading-tight">{credit}</dd>
                      </dl>

                      {detail ? (
                        <p className="text-xs text-on-surface-variant/90 leading-relaxed line-clamp-2 border-l-2 border-outline-variant/60 pl-2">
                          {detail}
                        </p>
                      ) : null}
                    </div>

                    <div className="px-4 py-2.5 bg-surface-container/50 border-t border-outline-variant/40 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-on-surface-variant">
                      <span className="inline-flex items-center gap-1 min-w-0">
                        <Calendar className="w-3.5 h-3.5 shrink-0 text-on-surface-variant/70" aria-hidden />
                        <span className="min-w-0 break-words">
                          {formatEntryDateTime(entry.entry_date, entry.created_at)}
                        </span>
                      </span>
                      {entry.reference ? (
                        <>
                          <span className="text-on-surface-variant/40" aria-hidden>
                            |
                          </span>
                          <span className="min-w-0 truncate max-w-full" title={entry.reference}>
                            {entry.reference}
                          </span>
                        </>
                      ) : null}
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
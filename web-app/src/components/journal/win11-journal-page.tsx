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
  List
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { JournalEntryDialog } from './journal-entry-dialog'
import { BulkEntryDialog } from './bulk-entry-dialog'
import { DataService } from '@/lib/data-service'
import { JournalEntry, Account, JournalEntryLine } from '@/types'

export function Win11JournalPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [viewMode, setViewMode] = useState('cards') // 'cards' or 'table'
  const [journalEntries, setJournalEntries] = useState<(JournalEntry & { lines: JournalEntryLine[] })[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [showNewEntryDialog, setShowNewEntryDialog] = useState(false)
  const [showBulkEntryDialog, setShowBulkEntryDialog] = useState(false)
  const [currentOrganizationId, setCurrentOrganizationId] = useState<string | null>(null)
  const [showSearchField, setShowSearchField] = useState(false)

  // Load data on component mount
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      
      // Get current user and organization
      const user = await DataService.getCurrentUser()
      if (!user) {
        console.error('No user found')
        return
      }

      const userProfile = await DataService.getUserProfile(user.id)
      if (!userProfile) {
        console.error('No user profile found')
        return
      }

      // For now, use the first organization or default
      const organizations = await DataService.getUserOrganizations(user.id)
      if (organizations.length === 0) {
        console.error('No organizations found')
        return
      }

      const organizationId = organizations[0].id
      setCurrentOrganizationId(organizationId)

      // Load journal entries with lines and accounts
      const [entries, accountsData] = await Promise.all([
        DataService.getJournalEntriesWithLines(organizationId),
        DataService.getAccounts(organizationId, true)
      ])

      setJournalEntries(entries)
      setAccounts(accountsData)
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleNewEntryCreated = (newEntry: JournalEntry) => {
    // Reload data to get the new entry with lines
    loadData()
  }

  const handleBulkEntriesCreated = (newEntries: JournalEntry[]) => {
    // Reload data to get the new entries with lines
    loadData()
  }

  const getAccountName = (accountId: number): string => {
    const account = accounts.find(acc => acc.id === accountId)
    return account ? `${account.code} - ${account.name}` : `Account ${accountId}`
  }

  const getDebitAndCreditAccounts = (entry: JournalEntry & { lines: JournalEntryLine[] }) => {
    const debitLine = entry.lines.find(line => line.debit_amount > 0)
    const creditLine = entry.lines.find(line => line.credit_amount > 0)
    
    return {
      debit: debitLine ? getAccountName(debitLine.account_id) : 'Unknown',
      credit: creditLine ? getAccountName(creditLine.account_id) : 'Unknown'
    }
  }

  const filteredTransactions = journalEntries.filter(entry => {
    const matchesSearch = entry.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (entry.reference && entry.reference.toLowerCase().includes(searchTerm.toLowerCase()))
    return matchesSearch
  })

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
      {/* Fixed Header */}
      <div className="sticky top-0 z-30 backdrop-blur-sm border-b border-outline-variant" style={{ backgroundColor: 'var(--md-sys-color-surface)' }}>
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
                onClick={() => setShowNewEntryDialog(true)}
              >
                <Plus className="w-4 h-4 mr-2" />
                New Entry
              </Button>
              <Button 
                className="md-button-outlined"
                onClick={() => setShowBulkEntryDialog(true)}
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
                onClick={() => setShowNewEntryDialog(true)}
              >
                <Plus className="w-4 h-4 mr-2" />
                New Entry
              </Button>
              <Button 
                className="md-button-outlined"
                onClick={() => setShowBulkEntryDialog(true)}
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
               const { debit, credit } = getDebitAndCreditAccounts(entry)
               return (
                 <Card key={entry.id} className="md-card-expressive group hover:md-elevation-1 transition-all duration-200">
                   <CardContent className="p-4">
                     {/* First Line - Transaction Info */}
                     <div className="flex items-center justify-between mb-2">
                       <div className="flex items-center space-x-3 flex-1 min-w-0">
                         <h3 className="md-title-medium text-on-surface truncate">{entry.description}</h3>
                       </div>
                       {/* Debit and Credit Accounts - Moved to top right */}
                       <div className="flex items-center space-x-6 text-sm">
                         <div className="flex items-center space-x-2">
                           <span className="px-2 py-1 rounded-md text-xs font-medium bg-primary text-on-primary">Debit</span>
                           <span className="text-on-surface font-medium truncate max-w-32">{debit}</span>
                         </div>
                         <div className="flex items-center space-x-2">
                           <span className="px-2 py-1 rounded-md text-xs font-medium bg-primary text-on-primary">Credit</span>
                           <span className="text-on-surface font-medium truncate max-w-32">{credit}</span>
                         </div>
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
      {currentOrganizationId && (
        <JournalEntryDialog
          open={showNewEntryDialog}
          onOpenChange={setShowNewEntryDialog}
          onEntryCreated={handleNewEntryCreated}
          organizationId={currentOrganizationId}
        />
      )}

      {/* Bulk Entry Dialog */}
      {currentOrganizationId && (
        <BulkEntryDialog
          open={showBulkEntryDialog}
          onOpenChange={setShowBulkEntryDialog}
          onEntriesCreated={handleBulkEntriesCreated}
          organizationId={currentOrganizationId}
        />
      )}
    </div>
  )
}
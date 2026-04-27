'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Search, 
  Filter, 
  Download,
  RefreshCw,
  FileText,
  ArrowLeft,
  Printer,
  Eye,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  DollarSign
} from 'lucide-react'
import {
  formatAccountLastActivity,
  formatDateTime,
  formatEntryDateTime,
} from '@/lib/utils'
import { useOrganizationFormatters } from '@/hooks/use-organization-formatters'
import { accountTypeBadgeClass, accountLevelBadgeClass, accountCodeChipClass } from '@/lib/account-type-badges'
import { DataService } from '@/lib/data-service'
import type { AccountBalanceRow, AccountTransactionRow, AccountType } from '@/types'
import { useOrganization } from '@/hooks/use-organization'
import { DateFilter, DateRange } from '@/components/ui/date-filter'

type AccountData = AccountBalanceRow
type TransactionData = AccountTransactionRow

export function Win11LedgerPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedAccount, setSelectedAccount] = useState<string | null>(null)
  const [accounts, setAccounts] = useState<AccountData[]>([])
  const [transactions, setTransactions] = useState<TransactionData[]>([])
  const [loading, setLoading] = useState(true)
  const { currentOrganization } = useOrganization()
  const { formatCurrency } = useOrganizationFormatters()
  const [showSearchField, setShowSearchField] = useState(false)
  const [dateRange, setDateRange] = useState<DateRange>({ startDate: null, endDate: null })
  const [accountsLastUpdated, setAccountsLastUpdated] = useState<Date | null>(null)

  // Load data on component mount and when organization changes
  useEffect(() => {
    if (currentOrganization) {
      loadData()
    }
  }, [currentOrganization])

  const loadData = async (dateRange?: DateRange) => {
    if (!currentOrganization) return
    
    try {
      setLoading(true)
      
      // Convert Date objects to ISO string format for the API
      const fromDate = dateRange?.startDate ? dateRange.startDate.toISOString().split('T')[0] : undefined
      const toDate = dateRange?.endDate ? dateRange.endDate.toISOString().split('T')[0] : undefined

      // Load account balances with date filtering for current organization
      const accountBalances = await DataService.getAccountBalances(currentOrganization.id, fromDate, toDate)
      setAccounts(accountBalances)
      setAccountsLastUpdated(new Date())
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadAccountTransactions = async (accountId: number, dateRange?: DateRange) => {
    if (!currentOrganization) return
    
    try {
      // Convert Date objects to ISO string format for the API
      const fromDate = dateRange?.startDate ? dateRange.startDate.toISOString().split('T')[0] : undefined
      const toDate = dateRange?.endDate ? dateRange.endDate.toISOString().split('T')[0] : undefined
      
      const accountTransactions = await DataService.getAccountTransactions(
        accountId, 
        currentOrganization.id,
        fromDate,
        toDate
      )
      
      setTransactions(accountTransactions)
    } catch (error) {
      console.error('Error loading account transactions:', error)
    }
  }

  const filteredAccounts = accounts.filter(account => {
    const matchesSearch = account.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         account.code.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesSearch
  })

  const handleAccountClick = async (accountId: string) => {
    setSelectedAccount(accountId)
    const accountIdNum = parseInt(accountId)
    await loadAccountTransactions(accountIdNum, dateRange)
  }

  const handleDateRangeChange = async (newDateRange: DateRange) => {
    setDateRange(newDateRange)
    
    // Reload account balances with new date range
    await loadData(newDateRange)
    
    // If an account is selected, also reload transactions with new date range
    if (selectedAccount) {
      const accountIdNum = parseInt(selectedAccount)
      await loadAccountTransactions(accountIdNum, newDateRange)
    }
  }

  const handleBackToOverview = () => {
    setSelectedAccount(null)
    setTransactions([])
  }

  const handlePrint = () => {
    const printWindow = window.open('', '_blank')
    if (!printWindow) return

    const account = accounts.find(acc => acc.id.toString() === selectedAccount)
    if (!account) return

    const printContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Ledger Report - ${account.name}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            .account-info { margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            .text-right { text-align: right; }
            .summary { margin-bottom: 20px; padding: 15px; background-color: #f9f9f9; }
            .print-button { 
              position: fixed; 
              top: 20px; 
              right: 20px; 
              padding: 10px 20px; 
              background-color: #007bff; 
              color: white; 
              border: none; 
              border-radius: 5px; 
              cursor: pointer; 
              font-size: 14px;
            }
            .print-button:hover { background-color: #0056b3; }
          </style>
        </head>
        <body>
          <button class="print-button" onclick="window.print()">Print Report</button>
          
          <div class="header">
            <h1>General Ledger Report</h1>
            <h2>${account.name}</h2>
            <p>Account Code: ${account.code} | Generated: ${new Date().toLocaleDateString()}</p>
          </div>
          
          <div class="summary">
            <h3>Account Summary</h3>
            <p><strong>Account Name:</strong> ${account.name}</p>
            <p><strong>Account Code:</strong> ${account.code}</p>
            <p><strong>Account Type:</strong> ${account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1)}</p>
            <p><strong>Current Balance:</strong> ${formatCurrency(account.balance)}</p>
            <p><strong>Total Transactions:</strong> ${transactions.length}</p>
            ${formatAccountLastActivity(account.last_transaction_date, account.last_transaction_at) ? `<p><strong>Last activity:</strong> ${formatAccountLastActivity(account.last_transaction_date, account.last_transaction_at)}</p>` : ''}
          </div>

          <h3>Transaction History</h3>
          <table>
            <thead>
              <tr>
                <th>Date & time</th>
                <th>Description</th>
                <th>Reference</th>
                <th class="text-right">Debit</th>
                <th class="text-right">Credit</th>
                <th class="text-right">Balance</th>
              </tr>
            </thead>
            <tbody>
              ${transactions.map(transaction => `
                <tr>
                  <td>${formatEntryDateTime(transaction.entry_date, transaction.created_at)}</td>
                  <td>${transaction.description}</td>
                  <td>${transaction.reference || transaction.entry_number}</td>
                  <td class="text-right">${transaction.debit_amount > 0 ? formatCurrency(transaction.debit_amount) : '-'}</td>
                  <td class="text-right">${transaction.credit_amount > 0 ? formatCurrency(transaction.credit_amount) : '-'}</td>
                  <td class="text-right">${formatCurrency(transaction.balance)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </body>
      </html>
    `

    printWindow.document.write(printContent)
    printWindow.document.close()
    printWindow.focus()
  }

  const handleExport = async () => {
    const account = accounts.find(acc => acc.id.toString() === selectedAccount)
    if (!account) return

    const baseFileName = `ledger_${account.code}_${account.name.replace(/[^a-zA-Z0-9]/g, '_')}_${new Date().toISOString().split('T')[0]}`
    
    // Check if File System Access API is supported (modern browsers)
    if ('showSaveFilePicker' in window) {
      try {
        const fileHandle = await (window as any).showSaveFilePicker({
          suggestedName: baseFileName,
          types: [
            {
              description: 'CSV files',
              accept: {
                'text/csv': ['.csv'],
              },
            },
            {
              description: 'Excel files',
              accept: {
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
              },
            },
            {
              description: 'PDF files',
              accept: {
                'application/pdf': ['.pdf'],
              },
            },
          ],
        })
        
        // Only proceed if user didn't cancel (fileHandle exists)
        if (fileHandle) {
          const writable = await fileHandle.createWritable()
          const fileName = fileHandle.name
          
          // Determine file type based on extension
          if (fileName.endsWith('.csv')) {
            const csvContent = generateCSVContent()
            await writable.write(csvContent)
          } else if (fileName.endsWith('.xlsx')) {
            const excelContent = await generateExcelContent()
            await writable.write(excelContent)
          } else if (fileName.endsWith('.pdf')) {
            const pdfContent = await generatePDFContent(account)
            await writable.write(pdfContent)
          }
          
          await writable.close()
        }
      } catch (error) {
        // User cancelled the dialog - do nothing
        if (error instanceof Error && error.name === 'AbortError') {
          console.log('User cancelled the save dialog')
          return
        }
        // Other errors - show user-friendly message
        console.error('Export failed:', error)
        alert('Export failed. Please try again.')
      }
    } else {
      // Fallback for browsers that don't support File System Access API
      // Show a simple confirmation dialog before downloading
      const confirmed = confirm('This browser doesn\'t support the native save dialog. Would you like to download the CSV file?')
      if (confirmed) {
        downloadFileDirectly(generateCSVContent(), `${baseFileName}.csv`)
      }
    }
  }

  const generateCSVContent = () => {
    const csvHeader = 'Date and time,Description,Reference,Debit,Credit,Balance\n'
    const esc = (s: string) => `"${s.replace(/"/g, '""')}"`
    const csvRows = transactions.map((transaction) =>
      `${esc(formatEntryDateTime(transaction.entry_date, transaction.created_at))},${esc(transaction.description)},${esc(transaction.reference || transaction.entry_number)},${transaction.debit_amount > 0 ? transaction.debit_amount : ''},${transaction.credit_amount > 0 ? transaction.credit_amount : ''},${transaction.balance}`
    ).join('\n')
    return csvHeader + csvRows
  }

  const generateExcelContent = async () => {
    // For Excel, we'll create a simple HTML table that can be opened in Excel
    const account = accounts.find(acc => acc.id.toString() === selectedAccount)
    if (!account) return ''

    const htmlContent = `
      <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
        <head>
          <meta charset="utf-8">
          <meta name="ExcelCreated" content="1">
          <style>
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            .text-right { text-align: right; }
          </style>
        </head>
        <body>
          <h1>General Ledger Report - ${account.name}</h1>
          <h2>Account Code: ${account.code} | Generated: ${new Date().toLocaleDateString()}</h2>
          
          <h3>Account Summary</h3>
          <table>
            <tr><td><strong>Account Name:</strong></td><td>${account.name}</td></tr>
            <tr><td><strong>Account Code:</strong></td><td>${account.code}</td></tr>
            <tr><td><strong>Account Type:</strong></td><td>${account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1)}</td></tr>
            <tr><td><strong>Current Balance:</strong></td><td>${formatCurrency(account.balance)}</td></tr>
            <tr><td><strong>Total Transactions:</strong></td><td>${transactions.length}</td></tr>
            ${formatAccountLastActivity(account.last_transaction_date, account.last_transaction_at) ? `<tr><td><strong>Last activity:</strong></td><td>${formatAccountLastActivity(account.last_transaction_date, account.last_transaction_at)}</td></tr>` : ''}
          </table>

          <h3>Transaction History</h3>
          <table>
            <thead>
              <tr>
                <th>Date & time</th>
                <th>Description</th>
                <th>Reference</th>
                <th class="text-right">Debit</th>
                <th class="text-right">Credit</th>
                <th class="text-right">Balance</th>
              </tr>
            </thead>
            <tbody>
              ${transactions.map(transaction => `
                <tr>
                  <td>${formatEntryDateTime(transaction.entry_date, transaction.created_at)}</td>
                  <td>${transaction.description}</td>
                  <td>${transaction.reference || transaction.entry_number}</td>
                  <td class="text-right">${transaction.debit_amount > 0 ? formatCurrency(transaction.debit_amount) : '-'}</td>
                  <td class="text-right">${transaction.credit_amount > 0 ? formatCurrency(transaction.credit_amount) : '-'}</td>
                  <td class="text-right">${formatCurrency(transaction.balance)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </body>
      </html>
    `
    return htmlContent
  }

  const generatePDFContent = async (account: AccountData) => {
    // For PDF, we'll create a simple HTML that can be printed to PDF
    const htmlContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Ledger Report - ${account.name}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            .text-right { text-align: right; }
            .summary { margin-bottom: 20px; padding: 15px; background-color: #f9f9f9; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>General Ledger Report</h1>
            <h2>${account.name}</h2>
            <p>Account Code: ${account.code} | Generated: ${new Date().toLocaleDateString()}</p>
          </div>
          
          <div class="summary">
            <h3>Account Summary</h3>
            <p><strong>Account Name:</strong> ${account.name}</p>
            <p><strong>Account Code:</strong> ${account.code}</p>
            <p><strong>Account Type:</strong> ${account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1)}</p>
            <p><strong>Current Balance:</strong> ${formatCurrency(account.balance)}</p>
            <p><strong>Total Transactions:</strong> ${transactions.length}</p>
            ${formatAccountLastActivity(account.last_transaction_date, account.last_transaction_at) ? `<p><strong>Last activity:</strong> ${formatAccountLastActivity(account.last_transaction_date, account.last_transaction_at)}</p>` : ''}
          </div>

          <h3>Transaction History</h3>
          <table>
            <thead>
              <tr>
                <th>Date & time</th>
                <th>Description</th>
                <th>Reference</th>
                <th class="text-right">Debit</th>
                <th class="text-right">Credit</th>
                <th class="text-right">Balance</th>
              </tr>
            </thead>
            <tbody>
              ${transactions.map(transaction => `
                <tr>
                  <td>${formatEntryDateTime(transaction.entry_date, transaction.created_at)}</td>
                  <td>${transaction.description}</td>
                  <td>${transaction.reference || transaction.entry_number}</td>
                  <td class="text-right">${transaction.debit_amount > 0 ? formatCurrency(transaction.debit_amount) : '-'}</td>
                  <td class="text-right">${transaction.credit_amount > 0 ? formatCurrency(transaction.credit_amount) : '-'}</td>
                  <td class="text-right">${formatCurrency(transaction.balance)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </body>
      </html>
    `
    return htmlContent
  }

  const downloadFileDirectly = (content: string, fileName: string) => {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', fileName)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const getChangeIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="w-4 h-4 text-primary" />
    if (change < 0) return <TrendingDown className="w-4 h-4 text-error" />
    return <DollarSign className="w-4 h-4 text-on-surface-variant" />
  }

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-primary'
    if (change < 0) return 'text-error'
    return 'text-on-surface-variant'
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-on-surface-variant">Loading ledger data...</p>
        </div>
      </div>
    )
  }

  if (selectedAccount) {
    const account = accounts.find(acc => acc.id.toString() === selectedAccount)
    const accountLastActivity = account
      ? formatAccountLastActivity(account.last_transaction_date, account.last_transaction_at)
      : null

    return (
      <div className="min-h-screen" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
        {/* Fixed Header */}
        <div className="app-page-header sticky top-0 z-30">
          <div className="px-6 py-4">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between mb-4 gap-4">
              <div className="flex items-center space-x-4">
                <Button 
                  variant="outline" 
                  onClick={handleBackToOverview}
                  className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  <span className="hidden sm:inline">Back to Accounts</span>
                  <span className="sm:hidden">Back</span>
                </Button>
                <div>
                  <h1 className="md-headline-small text-on-background">{account?.name}</h1>
                  <p className="md-body-medium text-on-surface-variant mt-1">
                    Account Code: {account?.code} • {transactions.length} transactions
                  </p>
                </div>
              </div>
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3">
                <DateFilter
                  onDateRangeChange={handleDateRangeChange}
                  initialDateRange={dateRange}
                  placeholder="Filter by date"
                />
                <div className="flex items-center gap-2">
                  <Button 
                    className="md-button"
                    onClick={handlePrint}
                    title="Print"
                  >
                    <Printer className="w-4 h-4" />
                  </Button>
                  <Button 
                    className="md-button"
                    onClick={handleExport}
                    title="Export"
                  >
                    <Download className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* Account Summary */}
        <div className="px-6 py-6">
          <Card className="md-card-expressive mb-6">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div>
                  <h3 className="md-title-large text-on-surface">{account?.name}</h3>
                  <p className="md-body-medium text-on-surface-variant">Account Code: {account?.code}</p>
                </div>
              </div>
                <div className="text-right">
                  <div className="md-headline-small text-on-surface">
                    {formatCurrency(account?.balance || 0)}
                  </div>
                  <div className="text-sm text-on-surface-variant">
                    {account?.transaction_count || 0} transactions
                  </div>
                  {accountLastActivity ? (
                    <div className="text-sm text-on-surface-variant">
                      Last activity: {accountLastActivity}
                    </div>
                  ) : null}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Transactions Table */}
          {transactions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="w-20 h-20 bg-primary-container rounded-3xl flex items-center justify-center mb-6">
                <FileText className="w-10 h-10 text-on-primary-container" />
              </div>
              <h3 className="md-headline-small text-on-surface mb-3">No transactions found</h3>
              <p className="md-body-large text-on-surface-variant text-center mb-8 max-w-md">
                No transactions found for this account in the selected date range.
              </p>
            </div>
          ) : (
            <Card className="md-card-expressive">
              <CardHeader>
                <CardTitle className="md-title-large text-on-surface">Transaction History</CardTitle>
                <CardDescription className="md-body-medium text-on-surface-variant">
                  Detailed transaction history for {account?.name}
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="border-b border-outline-variant">
                      <tr>
                        <th className="text-left p-4 md-body-large text-on-surface font-medium">Date & time</th>
                        <th className="text-left p-4 md-body-large text-on-surface font-medium">Description</th>
                        <th className="text-left p-4 md-body-large text-on-surface font-medium">Reference</th>
                        <th className="text-right p-4 md-body-large text-on-surface font-medium">Debit</th>
                        <th className="text-right p-4 md-body-large text-on-surface font-medium">Credit</th>
                        <th className="text-right p-4 md-body-large text-on-surface font-medium">Balance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.map((transaction, index) => (
                        <tr key={transaction.id} className={`border-b border-outline-variant/50 ${index % 2 === 0 ? 'bg-surface-container/30' : ''}`}>
                          <td className="p-4 md-body-medium text-on-surface-variant">
                            {formatEntryDateTime(transaction.entry_date, transaction.created_at)}
                          </td>
                          <td className="p-4 md-body-medium text-on-surface">
                            {transaction.description}
                          </td>
                          <td className="p-4 md-body-medium text-on-surface-variant">
                            {transaction.reference || transaction.entry_number}
                          </td>
                          <td className="p-4 md-body-medium text-on-surface text-right">
                            {transaction.debit_amount > 0 ? formatCurrency(transaction.debit_amount) : '-'}
                          </td>
                          <td className="p-4 md-body-medium text-on-surface text-right">
                            {transaction.credit_amount > 0 ? formatCurrency(transaction.credit_amount) : '-'}
                          </td>
                          <td className="p-4 md-body-medium text-on-surface font-medium text-right">
                            {formatCurrency(transaction.balance)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
      {/* Fixed Header */}
      <div className="app-page-header sticky top-0 z-30">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="md-headline-small text-on-background">General Ledger</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                {accounts.length} {accounts.length === 1 ? 'account' : 'accounts'}
                {accountsLastUpdated ? (
                  <>
                    {' '}
                    · Last updated {formatDateTime(accountsLastUpdated)}
                  </>
                ) : null}
              </p>
            </div>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-2">
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <DateFilter
                  onDateRangeChange={handleDateRangeChange}
                  initialDateRange={dateRange}
                  placeholder="Filter by date"
                />
                <div className={`transition-all duration-200 overflow-hidden ${
                  showSearchField 
                    ? 'w-60 sm:w-80 opacity-100 translate-x-0' 
                    : 'w-0 opacity-0 -translate-x-4'
                }`}>
                  <input
                    type="text"
                    placeholder="Search by account name or code..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-60 sm:w-80 h-10 px-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                    aria-label="Search accounts"
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
                  onClick={() => void loadData()}
                  className="md-button"
                >
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Main Content */}
      <div className="px-6 py-6">
        {filteredAccounts.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-20 h-20 bg-primary-container rounded-3xl flex items-center justify-center mb-6">
              <FileText className="w-10 h-10 text-on-primary-container" />
            </div>
            <h3 className="md-headline-small text-on-surface mb-3">No accounts found</h3>
            <p className="md-body-large text-on-surface-variant text-center mb-8 max-w-md">
              {searchTerm 
                ? 'Try adjusting your search criteria.'
                : 'No accounts have been created yet.'
              }
            </p>
          </div>
        ) : (
          /* Account Cards Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredAccounts.map((account) => {
              const lastActivity = formatAccountLastActivity(
                account.last_transaction_date,
                account.last_transaction_at
              )
              return (
              <Card 
                key={account.id} 
                className="md-card-expressive group hover:md-elevation-1 transition-all duration-200 cursor-pointer"
                onClick={() => handleAccountClick(account.id.toString())}
              >
                <CardContent className="p-6">
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="md-title-medium text-on-surface">{account.name}</h3>
                      <ChevronRight className="w-5 h-5 text-on-surface-variant group-hover:text-on-surface transition-colors" />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={accountCodeChipClass()}>
                          {account.code}
                        </span>
                        <span className={accountTypeBadgeClass(account.account_type as AccountType)}>
                          {account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1)}
                        </span>
                        <span className={accountLevelBadgeClass(account.level)}>
                          L{account.level}
                        </span>
                      </div>
                      {account.group && (
                        <span className="text-xs text-on-surface-variant">
                          {account.group.replace('_', ' ')}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="md-body-medium text-on-surface-variant">Balance</span>
                      <span className="md-title-large font-medium text-on-surface">
                        {formatCurrency(Math.abs(account.balance))}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="md-body-small text-on-surface-variant">Transactions</span>
                      <span className="md-body-small text-on-surface">{account.transaction_count}</span>
                    </div>
                    
                    {lastActivity ? (
                      <div className="flex items-center justify-between gap-2">
                        <span className="md-body-small text-on-surface-variant shrink-0">Last activity</span>
                        <span className="md-body-small text-on-surface-variant text-right tabular-nums">
                          {lastActivity}
                        </span>
                      </div>
                    ) : null}
                  </div>
                </CardContent>
              </Card>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

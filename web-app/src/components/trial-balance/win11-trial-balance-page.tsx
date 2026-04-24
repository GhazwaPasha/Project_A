'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Search, 
  Download,
  RefreshCw,
  FileText,
  Calculator,
  CheckCircle,
  AlertCircle,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  DollarSign
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { accountTypeBadgeClass } from '@/lib/account-type-badges'
import { DataService } from '@/lib/data-service'
import { AccountType } from '@/types'
import { useOrganization } from '@/hooks/use-organization'

// Interface for trial balance account data
interface TrialBalanceAccount {
  account_id: number
  account_code: string
  account_name: string
  account_type: AccountType
  debit_balance: number
  credit_balance: number
}

// Mock data for trial balance accounts (fallback)
const mockTrialBalanceAccounts = [
  {
    id: '1',
    code: '1000',
    name: 'Cash',
    type: 'Asset',
    debitBalance: 15420.50,
    creditBalance: 0.00,
    isPostable: true
  },
  {
    id: '2',
    code: '1100',
    name: 'Accounts Receivable',
    type: 'Asset',
    debitBalance: 8750.00,
    creditBalance: 0.00,
    isPostable: true
  },
  {
    id: '3',
    code: '1500',
    name: 'Office Equipment',
    type: 'Asset',
    debitBalance: 12500.00,
    creditBalance: 0.00,
    isPostable: true
  },
  {
    id: '4',
    code: '2000',
    name: 'Accounts Payable',
    type: 'Liability',
    debitBalance: 0.00,
    creditBalance: 3200.75,
    isPostable: true
  },
  {
    id: '5',
    code: '2100',
    name: 'Accrued Expenses',
    type: 'Liability',
    debitBalance: 0.00,
    creditBalance: 1500.00,
    isPostable: true
  },
  {
    id: '6',
    code: '3000',
    name: 'Owner\'s Equity',
    type: 'Equity',
    debitBalance: 0.00,
    creditBalance: 25000.00,
    isPostable: false
  },
  {
    id: '7',
    code: '4000',
    name: 'Revenue',
    type: 'Income',
    debitBalance: 0.00,
    creditBalance: 45000.00,
    isPostable: true
  },
  {
    id: '8',
    code: '5000',
    name: 'Office Expenses',
    type: 'Expense',
    debitBalance: 1250.50,
    creditBalance: 0.00,
    isPostable: true
  },
  {
    id: '9',
    code: '5100',
    name: 'Marketing Expenses',
    type: 'Expense',
    debitBalance: 3200.00,
    creditBalance: 0.00,
    isPostable: true
  },
  {
    id: '10',
    code: '5200',
    name: 'Utilities',
    type: 'Expense',
    debitBalance: 850.25,
    creditBalance: 0.00,
    isPostable: true
  }
]

export function Win11TrialBalancePage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [accounts, setAccounts] = useState<TrialBalanceAccount[]>([])
  const [loading, setLoading] = useState(true)
  const { currentOrganization } = useOrganization()
  const [error, setError] = useState<string | null>(null)
  const [showSearchField, setShowSearchField] = useState(false)

  // Load data on component mount and when organization changes
  useEffect(() => {
    if (currentOrganization) {
      loadTrialBalanceData()
    }
  }, [currentOrganization])

  const loadTrialBalanceData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Get current user and organization
      const user = await DataService.getCurrentUser()
      if (!user) {
        console.error('No user found')
        setError('No user found. Please log in.')
        return
      }

      const userProfile = await DataService.getUserProfile(user.id)
      if (!userProfile) {
        console.error('No user profile found')
        setError('No user profile found.')
        return
      }

      // Get user organizations
      const organizations = await DataService.getUserOrganizations(user.id)
      if (organizations.length === 0) {
        console.error('No organizations found')
        setError('No organizations found.')
        return
      }

      if (!currentOrganization) {
        setError('No organization selected.')
        return
      }

      // Load trial balance data for current organization
      const trialBalanceData = await DataService.getTrialBalance(currentOrganization.id)
      console.log('Trial balance data loaded:', trialBalanceData)
      console.log('Number of accounts:', trialBalanceData.length)
      setAccounts(trialBalanceData)
    } catch (error) {
      console.error('Error loading trial balance data:', error)
      setError('Failed to load trial balance data. Please try again.')
      // Fallback to mock data for development
      setAccounts(mockTrialBalanceAccounts.map(acc => ({
        account_id: parseInt(acc.id),
        account_code: acc.code,
        account_name: acc.name,
        account_type: acc.type as AccountType,
        debit_balance: acc.debitBalance,
        credit_balance: acc.creditBalance
      })))
    } finally {
      setLoading(false)
    }
  }

  const filteredAccounts = accounts.filter(account => {
    const matchesSearch = account.account_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (account.account_code && account.account_code.toLowerCase().includes(searchTerm.toLowerCase()))
    return matchesSearch
  })

  // Calculate totals
  const totalDebits = accounts.reduce((sum, account) => sum + account.debit_balance, 0)
  const totalCredits = accounts.reduce((sum, account) => sum + account.credit_balance, 0)
  const isBalanced = Math.abs(totalDebits - totalCredits) < 0.01

  const handleRefresh = () => {
    loadTrialBalanceData()
  }

  const handleExport = async () => {
    const baseFileName = `trial_balance_${new Date().toISOString().split('T')[0]}`
    
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
            const pdfContent = await generatePDFContent()
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
    const csvHeader = 'Account Code,Account Name,Account Type,Debit Balance,Credit Balance\n'
    const csvRows = filteredAccounts.map(account => 
      `"${account.account_code || 'N/A'}","${account.account_name}","${account.account_type}",${account.debit_balance},${account.credit_balance}`
    ).join('\n')
    return csvHeader + csvRows
  }

  const generateExcelContent = async () => {
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
            .summary { margin-bottom: 20px; padding: 15px; background-color: #f9f9f9; }
          </style>
        </head>
        <body>
          <h1>Trial Balance Report</h1>
          <h2>Generated: ${new Date().toLocaleDateString()}</h2>
          
          <div class="summary">
            <h3>Summary</h3>
            <p><strong>Total Debits:</strong> ${formatCurrency(totalDebits)}</p>
            <p><strong>Total Credits:</strong> ${formatCurrency(totalCredits)}</p>
            <p><strong>Difference:</strong> ${formatCurrency(Math.abs(totalDebits - totalCredits))}</p>
            <p><strong>Status:</strong> ${isBalanced ? 'Balanced' : 'Out of Balance'}</p>
            <p><strong>Number of Accounts:</strong> ${filteredAccounts.length}</p>
          </div>

          <h3>Trial Balance</h3>
          <table>
            <thead>
              <tr>
                <th>Account Code</th>
                <th>Account Name</th>
                <th>Account Type</th>
                <th class="text-right">Debit Balance</th>
                <th class="text-right">Credit Balance</th>
              </tr>
            </thead>
            <tbody>
              ${filteredAccounts.map(account => `
                <tr>
                  <td>${account.account_code || 'N/A'}</td>
                  <td>${account.account_name}</td>
                  <td>${account.account_type}</td>
                  <td class="text-right">${account.debit_balance > 0 ? formatCurrency(account.debit_balance) : '-'}</td>
                  <td class="text-right">${account.credit_balance > 0 ? formatCurrency(account.credit_balance) : '-'}</td>
                </tr>
              `).join('')}
            </tbody>
            <tfoot>
              <tr style="font-weight: bold; background-color: #f0f0f0;">
                <td colspan="3">TOTALS</td>
                <td class="text-right">${formatCurrency(totalDebits)}</td>
                <td class="text-right">${formatCurrency(totalCredits)}</td>
              </tr>
            </tfoot>
          </table>
        </body>
      </html>
    `
    return htmlContent
  }

  const generatePDFContent = async () => {
    const htmlContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Trial Balance Report</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            .text-right { text-align: right; }
            .summary { margin-bottom: 20px; padding: 15px; background-color: #f9f9f9; }
            .balanced { color: green; font-weight: bold; }
            .unbalanced { color: red; font-weight: bold; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>Trial Balance Report</h1>
            <p>Generated: ${new Date().toLocaleDateString()}</p>
          </div>
          
          <div class="summary">
            <h3>Summary</h3>
            <p><strong>Total Debits:</strong> ${formatCurrency(totalDebits)}</p>
            <p><strong>Total Credits:</strong> ${formatCurrency(totalCredits)}</p>
            <p><strong>Difference:</strong> ${formatCurrency(Math.abs(totalDebits - totalCredits))}</p>
            <p><strong>Status:</strong> <span class="${isBalanced ? 'balanced' : 'unbalanced'}">${isBalanced ? 'Balanced' : 'Out of Balance'}</span></p>
            <p><strong>Number of Accounts:</strong> ${filteredAccounts.length}</p>
          </div>

          <h3>Trial Balance</h3>
          <table>
            <thead>
              <tr>
                <th>Account Code</th>
                <th>Account Name</th>
                <th>Account Type</th>
                <th class="text-right">Debit Balance</th>
                <th class="text-right">Credit Balance</th>
              </tr>
            </thead>
            <tbody>
              ${filteredAccounts.map(account => `
                <tr>
                  <td>${account.account_code || 'N/A'}</td>
                  <td>${account.account_name}</td>
                  <td>${account.account_type}</td>
                  <td class="text-right">${account.debit_balance > 0 ? formatCurrency(account.debit_balance) : '-'}</td>
                  <td class="text-right">${account.credit_balance > 0 ? formatCurrency(account.credit_balance) : '-'}</td>
                </tr>
              `).join('')}
            </tbody>
            <tfoot>
              <tr style="font-weight: bold; background-color: #f0f0f0;">
                <td colspan="3">TOTALS</td>
                <td class="text-right">${formatCurrency(totalDebits)}</td>
                <td class="text-right">${formatCurrency(totalCredits)}</td>
              </tr>
            </tfoot>
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

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
      {/* Fixed Header */}
      <div className="app-page-header sticky top-0 z-30">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="md-headline-small text-on-background">Trial Balance</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                Account balances verification • {filteredAccounts.length} accounts
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className={`transition-all duration-200 overflow-hidden ${
                showSearchField 
                  ? 'w-80 opacity-100 translate-x-0' 
                  : 'w-0 opacity-0 -translate-x-4'
              }`}>
                <input
                  type="text"
                  placeholder="Search by account name or code..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-80 h-10 px-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                  aria-label="Search accounts"
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
                onClick={handleRefresh}
                className="md-button-outlined"
                disabled={loading}
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
              <Button 
                className="md-button-outlined"
                onClick={handleExport}
              >
                <Download className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-6 py-6">
        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-16 h-16 bg-primary-container rounded-3xl flex items-center justify-center mb-6 animate-pulse">
              <RefreshCw className="w-8 h-8 text-on-primary-container animate-spin" />
            </div>
            <h3 className="md-headline-small text-on-surface mb-3">Loading Trial Balance</h3>
            <p className="md-body-large text-on-surface-variant text-center">
              Please wait while we fetch your trial balance data...
            </p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-16 h-16 bg-error-container rounded-3xl flex items-center justify-center mb-6">
              <AlertCircle className="w-8 h-8 text-on-error-container" />
            </div>
            <h3 className="md-headline-small text-on-surface mb-3">Error Loading Data</h3>
            <p className="md-body-large text-on-surface-variant text-center mb-8 max-w-md">
              {error}
            </p>
            <Button onClick={handleRefresh} className="bg-primary text-on-primary">
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          </div>
        )}

        {/* Main Content - only show when not loading and no error */}
        {!loading && !error && (
          <>
            {/* Balance Verification Card */}
            <Card className="md-card-expressive mb-6">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${
                  isBalanced ? 'bg-green-100' : 'bg-red-100'
                }`}>
                  {isBalanced ? (
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  ) : (
                    <AlertCircle className="w-6 h-6 text-red-600" />
                  )}
                </div>
                <div>
                  <h3 className="md-title-large text-on-surface">
                    {isBalanced ? 'Trial Balance is Balanced' : 'Trial Balance is Out of Balance'}
                  </h3>
                  <p className="md-body-medium text-on-surface-variant">
                    {isBalanced 
                      ? 'All debits equal credits - accounting equation is satisfied'
                      : `Difference: ${formatCurrency(Math.abs(totalDebits - totalCredits))}`
                    }
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="grid grid-cols-2 gap-8">
                  <div>
                    <p className="md-body-small text-on-surface-variant mb-1">Total Debits</p>
                    <p className="md-title-large text-on-surface font-medium">
                      {formatCurrency(totalDebits)}
                    </p>
                  </div>
                  <div>
                    <p className="md-body-small text-on-surface-variant mb-1">Total Credits</p>
                    <p className="md-title-large text-on-surface font-medium">
                      {formatCurrency(totalCredits)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Trial Balance Table */}
        {filteredAccounts.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-20 h-20 bg-primary-container rounded-3xl flex items-center justify-center mb-6">
              <Calculator className="w-10 h-10 text-on-primary-container" />
            </div>
            <h3 className="md-headline-small text-on-surface mb-3">No accounts with balances found</h3>
            <p className="md-body-large text-on-surface-variant text-center mb-8 max-w-md">
              {searchTerm 
                ? 'Try adjusting your search criteria.'
                : 'No accounts have balances to display. Create some journal entries to see trial balance data.'
              }
            </p>
          </div>
        ) : (
          <Card className="md-card-expressive">
            <CardHeader>
              <CardTitle className="md-title-large text-on-surface">Trial Balance Report</CardTitle>
              <CardDescription className="md-body-medium text-on-surface-variant">
                As of {formatDate(new Date().toISOString())} • {filteredAccounts.length} accounts
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-outline-variant">
                    <tr>
                      <th className="text-left p-4 md-body-large text-on-surface font-medium">Account Code</th>
                      <th className="text-left p-4 md-body-large text-on-surface font-medium">Account Name</th>
                      <th className="text-left p-4 md-body-large text-on-surface font-medium">Type</th>
                      <th className="text-right p-4 md-body-large text-on-surface font-medium">Debit Balance</th>
                      <th className="text-right p-4 md-body-large text-on-surface font-medium">Credit Balance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredAccounts.map((account, index) => {
                      return (
                        <tr key={account.account_id} className={`border-b border-outline-variant/50 ${index % 2 === 0 ? 'bg-surface-container/30' : ''}`}>
                          <td className="p-4 md-body-medium text-on-surface-variant font-mono">
                            {account.account_code || 'N/A'}
                          </td>
                          <td className="p-4 md-body-medium text-on-surface">
                            <div className="flex items-center space-x-2">
                              <span>{account.account_name}</span>
                            </div>
                          </td>
                          <td className="p-4">
                            <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium ${accountTypeBadgeClass(account.account_type)}`}>
                              {account.account_type}
                            </span>
                          </td>
                          <td className="p-4 md-body-medium text-on-surface text-right">
                            {account.debit_balance > 0 ? (
                              <span className="text-primary font-medium">
                                {formatCurrency(account.debit_balance)}
                              </span>
                            ) : (
                              <span className="text-on-surface-variant">-</span>
                            )}
                          </td>
                          <td className="p-4 md-body-medium text-on-surface text-right">
                            {account.credit_balance > 0 ? (
                              <span className="text-error font-medium">
                                {formatCurrency(account.credit_balance)}
                              </span>
                            ) : (
                              <span className="text-on-surface-variant">-</span>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                  <tfoot className="border-t-2 border-outline-variant bg-surface-container/50">
                    <tr>
                      <td colSpan={3} className="p-4 md-body-large text-on-surface font-semibold">
                        TOTALS
                      </td>
                      <td className="p-4 md-body-large text-on-surface font-semibold text-right">
                        <span className="text-green-600">
                          {formatCurrency(totalDebits)}
                        </span>
                      </td>
                      <td className="p-4 md-body-large text-on-surface font-semibold text-right">
                        <span className="text-red-600">
                          {formatCurrency(totalCredits)}
                        </span>
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
          </>
        )}
      </div>
    </div>
  )
}

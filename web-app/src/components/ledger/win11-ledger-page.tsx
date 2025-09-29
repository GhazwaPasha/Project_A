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
import { formatCurrency, formatDate } from '@/lib/utils'

// Mock data for accounts
const mockAccounts = [
  {
    id: '1',
    name: 'Cash',
    type: 'Asset',
    code: '1000',
    balance: 15420.50,
    change: 2450.00,
    changePercent: 18.9,
    transactionCount: 23,
    lastTransaction: '2024-12-19'
  },
  {
    id: '2',
    name: 'Accounts Receivable',
    type: 'Asset',
    code: '1100',
    balance: 8750.00,
    change: -1250.00,
    changePercent: -12.5,
    transactionCount: 15,
    lastTransaction: '2024-12-18'
  },
  {
    id: '3',
    name: 'Office Equipment',
    type: 'Asset',
    code: '1500',
    balance: 12500.00,
    change: 0.00,
    changePercent: 0,
    transactionCount: 3,
    lastTransaction: '2024-11-15'
  },
  {
    id: '4',
    name: 'Accounts Payable',
    type: 'Liability',
    code: '2000',
    balance: 3200.75,
    change: 800.25,
    changePercent: 33.3,
    transactionCount: 12,
    lastTransaction: '2024-12-17'
  },
  {
    id: '5',
    name: 'Revenue',
    type: 'Income',
    code: '4000',
    balance: 45000.00,
    change: 8500.00,
    changePercent: 23.3,
    transactionCount: 8,
    lastTransaction: '2024-12-19'
  },
  {
    id: '6',
    name: 'Office Expenses',
    type: 'Expense',
    code: '5000',
    balance: 1250.50,
    change: 245.50,
    changePercent: 24.4,
    transactionCount: 18,
    lastTransaction: '2024-12-19'
  }
]

// Mock data for account transactions
const mockTransactions = {
  '1': [
    {
      id: '1',
      date: '2024-12-19',
      description: 'Client Payment - Project Alpha',
      reference: 'PAY-001',
      debit: 5000.00,
      credit: 0.00,
      balance: 15420.50
    },
    {
      id: '2',
      date: '2024-12-18',
      description: 'Office Supplies Purchase',
      reference: 'INV-001',
      debit: 0.00,
      credit: 245.50,
      balance: 10420.50
    },
    {
      id: '3',
      date: '2024-12-17',
      description: 'Initial Deposit',
      reference: 'DEP-001',
      debit: 10000.00,
      credit: 0.00,
      balance: 10666.00
    }
  ],
  '2': [
    {
      id: '4',
      date: '2024-12-18',
      description: 'Invoice #INV-2024-001',
      reference: 'INV-001',
      debit: 2500.00,
      credit: 0.00,
      balance: 8750.00
    },
    {
      id: '5',
      date: '2024-12-15',
      description: 'Invoice #INV-2024-002',
      reference: 'INV-002',
      debit: 3000.00,
      credit: 0.00,
      balance: 6250.00
    }
  ]
}

export function Win11LedgerPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [selectedAccount, setSelectedAccount] = useState<string | null>(null)
  const [accounts, setAccounts] = useState(mockAccounts)

  const filteredAccounts = accounts.filter(account => {
    const matchesSearch = account.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         account.code.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = filterType === 'all' || account.type.toLowerCase() === filterType.toLowerCase()
    return matchesSearch && matchesType
  })

  const handleAccountClick = (accountId: string) => {
    setSelectedAccount(accountId)
  }

  const handleBackToOverview = () => {
    setSelectedAccount(null)
  }

  const getAccountTypeColor = (type: string) => {
    switch (type) {
      case 'Asset': return 'text-green-600 bg-green-50'
      case 'Liability': return 'text-red-600 bg-red-50'
      case 'Equity': return 'text-blue-600 bg-blue-50'
      case 'Income': return 'text-purple-600 bg-purple-50'
      case 'Expense': return 'text-orange-600 bg-orange-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getChangeIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="w-4 h-4 text-green-600" />
    if (change < 0) return <TrendingDown className="w-4 h-4 text-red-600" />
    return <DollarSign className="w-4 h-4 text-gray-600" />
  }

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600'
    if (change < 0) return 'text-red-600'
    return 'text-gray-600'
  }

  if (selectedAccount) {
    const account = accounts.find(acc => acc.id === selectedAccount)
    const transactions = mockTransactions[selectedAccount as keyof typeof mockTransactions] || []
    
    return (
      <div className="min-h-screen" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
        {/* Fixed Header */}
        <div className="sticky top-0 z-30 backdrop-blur-sm border-b border-outline-variant" style={{ backgroundColor: 'var(--md-sys-color-surface)' }}>
          <div className="px-6 py-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <Button 
                  variant="outline" 
                  onClick={handleBackToOverview}
                  className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Accounts
                </Button>
                <div>
                  <h1 className="md-headline-small text-on-background">{account?.name}</h1>
                  <p className="md-body-medium text-on-surface-variant mt-1">
                    Account Code: {account?.code} • {transactions.length} transactions
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Button variant="outline" className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container">
                  <Printer className="w-4 h-4 mr-2" />
                  Print
                </Button>
                <Button variant="outline" className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container">
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </Button>
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
                  <div className={`flex items-center space-x-2 ${getChangeColor(account?.change || 0)}`}>
                    {getChangeIcon(account?.change || 0)}
                    <span className="text-sm font-medium">
                      {account?.change && account.change > 0 ? '+' : ''}{formatCurrency(account?.change || 0)}
                    </span>
                    <span className="text-sm">
                      ({account?.changePercent && account.changePercent > 0 ? '+' : ''}{account?.changePercent || 0}%)
                    </span>
                  </div>
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
                        <th className="text-left p-4 md-body-large text-on-surface font-medium">Date</th>
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
                            {formatDate(transaction.date)}
                          </td>
                          <td className="p-4 md-body-medium text-on-surface">
                            {transaction.description}
                          </td>
                          <td className="p-4 md-body-medium text-on-surface-variant">
                            {transaction.reference}
                          </td>
                          <td className="p-4 md-body-medium text-on-surface text-right">
                            {transaction.debit > 0 ? formatCurrency(transaction.debit) : '-'}
                          </td>
                          <td className="p-4 md-body-medium text-on-surface text-right">
                            {transaction.credit > 0 ? formatCurrency(transaction.credit) : '-'}
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
      <div className="sticky top-0 z-30 backdrop-blur-sm border-b border-outline-variant" style={{ backgroundColor: 'var(--md-sys-color-surface)' }}>
        <div className="px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="md-headline-small text-on-background">General Ledger</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                Account balances and transaction details
              </p>
            </div>
            <Button 
              onClick={() => setAccounts([...accounts])}
              className="md-button"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh Balances
            </Button>
          </div>

          {/* Search and Filters */}
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
              <input
                type="text"
                placeholder="Search accounts by name or code..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-12 pl-12 pr-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                aria-label="Search accounts"
              />
            </div>
            
            <div className="flex gap-3">
              <div className="relative">
                 <select
                   value={filterType}
                   onChange={(e) => setFilterType(e.target.value)}
                   className="h-12 pl-4 pr-12 py-3 bg-surface-container border border-outline rounded-2xl text-sm text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200 appearance-none cursor-pointer min-w-[160px]"
                 >
                  <option value="all">All Types</option>
                  <option value="asset">Asset</option>
                  <option value="liability">Liability</option>
                  <option value="equity">Equity</option>
                  <option value="income">Income</option>
                  <option value="expense">Expense</option>
                </select>
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
                  <svg className="w-4 h-4 text-on-surface-variant" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
              <Button variant="outline" className="h-12 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container">
                <Filter className="w-4 h-4 mr-2" />
                Filter
              </Button>
              <Button variant="outline" className="h-12 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
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
              {searchTerm || filterType !== 'all' 
                ? 'Try adjusting your search or filter criteria.'
                : 'No accounts have been created yet.'
              }
            </p>
          </div>
        ) : (
          /* Account Cards Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredAccounts.map((account) => (
              <Card 
                key={account.id} 
                className="md-card-expressive group hover:md-elevation-1 transition-all duration-200 cursor-pointer"
                onClick={() => handleAccountClick(account.id)}
              >
                <CardContent className="p-6">
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="md-title-medium text-on-surface">{account.name}</h3>
                      <ChevronRight className="w-5 h-5 text-on-surface-variant group-hover:text-on-surface transition-colors" />
                    </div>
                    <p className="md-body-small text-on-surface-variant">Code: {account.code}</p>
                    <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium mt-2 ${getAccountTypeColor(account.type)}`}>
                      {account.type}
                    </span>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="md-body-medium text-on-surface-variant">Balance</span>
                      <span className="md-title-large text-on-surface font-medium">
                        {formatCurrency(account.balance)}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="md-body-small text-on-surface-variant">Change</span>
                      <div className={`flex items-center space-x-1 ${getChangeColor(account.change)}`}>
                        {getChangeIcon(account.change)}
                        <span className="text-sm font-medium">
                          {account.change > 0 ? '+' : ''}{formatCurrency(account.change)}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="md-body-small text-on-surface-variant">Transactions</span>
                      <span className="md-body-small text-on-surface">{account.transactionCount}</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="md-body-small text-on-surface-variant">Last Activity</span>
                      <span className="md-body-small text-on-surface-variant">
                        {formatDate(account.lastTransaction)}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Search, 
  Filter, 
  Download,
  RefreshCw,
  Plus,
  Edit,
  Trash2,
  Eye,
  ChevronRight,
  ChevronDown,
  Building2,
  DollarSign,
  FileText,
  Settings
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'

// Mock data for accounts with hierarchy
const mockAccounts = [
  {
    id: '1',
    code: '1000',
    name: 'Assets',
    type: 'Asset',
    parentId: null,
    isPostable: false,
    balance: 0,
    description: 'All company assets',
    isExpanded: true,
    children: [
      {
        id: '2',
        code: '1100',
        name: 'Current Assets',
        type: 'Asset',
        parentId: '1',
        isPostable: false,
        balance: 0,
        description: 'Assets expected to be converted to cash within one year',
        isExpanded: true,
        children: [
          {
            id: '3',
            code: '1110',
            name: 'Cash',
            type: 'Asset',
            parentId: '2',
            isPostable: true,
            balance: 15420.50,
            description: 'Cash on hand and in bank accounts',
            isExpanded: false,
            children: []
          },
          {
            id: '4',
            code: '1120',
            name: 'Accounts Receivable',
            type: 'Asset',
            parentId: '2',
            isPostable: true,
            balance: 8750.00,
            description: 'Amounts owed by customers',
            isExpanded: false,
            children: []
          }
        ]
      },
      {
        id: '5',
        code: '1500',
        name: 'Fixed Assets',
        type: 'Asset',
        parentId: '1',
        isPostable: false,
        balance: 0,
        description: 'Long-term assets used in business operations',
        isExpanded: false,
        children: [
          {
            id: '6',
            code: '1510',
            name: 'Office Equipment',
            type: 'Asset',
            parentId: '5',
            isPostable: true,
            balance: 12500.00,
            description: 'Computers, furniture, and office equipment',
            isExpanded: false,
            children: []
          }
        ]
      }
    ]
  },
  {
    id: '7',
    code: '2000',
    name: 'Liabilities',
    type: 'Liability',
    parentId: null,
    isPostable: false,
    balance: 0,
    description: 'All company liabilities',
    isExpanded: true,
    children: [
      {
        id: '8',
        code: '2100',
        name: 'Current Liabilities',
        type: 'Liability',
        parentId: '7',
        isPostable: false,
        balance: 0,
        description: 'Liabilities due within one year',
        isExpanded: false,
        children: [
          {
            id: '9',
            code: '2110',
            name: 'Accounts Payable',
            type: 'Liability',
            parentId: '8',
            isPostable: true,
            balance: 3200.75,
            description: 'Amounts owed to suppliers',
            isExpanded: false,
            children: []
          }
        ]
      }
    ]
  },
  {
    id: '10',
    code: '3000',
    name: 'Equity',
    type: 'Equity',
    parentId: null,
    isPostable: false,
    balance: 0,
    description: 'Owner\'s equity and retained earnings',
    isExpanded: true,
    children: [
      {
        id: '11',
        code: '3100',
        name: 'Owner\'s Capital',
        type: 'Equity',
        parentId: '10',
        isPostable: true,
        balance: 25000.00,
        description: 'Initial investment by owner',
        isExpanded: false,
        children: []
      }
    ]
  },
  {
    id: '12',
    code: '4000',
    name: 'Revenue',
    type: 'Income',
    parentId: null,
    isPostable: false,
    balance: 0,
    description: 'All income accounts',
    isExpanded: true,
    children: [
      {
        id: '13',
        code: '4100',
        name: 'Service Revenue',
        type: 'Income',
        parentId: '12',
        isPostable: true,
        balance: 45000.00,
        description: 'Revenue from services provided',
        isExpanded: false,
        children: []
      }
    ]
  },
  {
    id: '14',
    code: '5000',
    name: 'Expenses',
    type: 'Expense',
    parentId: null,
    isPostable: false,
    balance: 0,
    description: 'All expense accounts',
    isExpanded: true,
    children: [
      {
        id: '15',
        code: '5100',
        name: 'Office Expenses',
        type: 'Expense',
        parentId: '14',
        isPostable: true,
        balance: 1250.50,
        description: 'General office supplies and expenses',
        isExpanded: false,
        children: []
      },
      {
        id: '16',
        code: '5200',
        name: 'Marketing Expenses',
        type: 'Expense',
        parentId: '14',
        isPostable: true,
        balance: 3200.00,
        description: 'Advertising and marketing costs',
        isExpanded: false,
        children: []
      }
    ]
  }
]

export function Win11AccountsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [accounts, setAccounts] = useState(mockAccounts)
  const [selectedAccount, setSelectedAccount] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)

  const filteredAccounts = accounts.filter(account => {
    const matchesSearch = account.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         account.code.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = filterType === 'all' || account.type.toLowerCase() === filterType.toLowerCase()
    return matchesSearch && matchesType
  })

  const toggleExpanded = (accountId: string) => {
    const updateAccounts = (accs: any[]): any[] => {
      return accs.map(acc => {
        if (acc.id === accountId) {
          return { ...acc, isExpanded: !acc.isExpanded }
        }
        if (acc.children) {
          return { ...acc, children: updateAccounts(acc.children) }
        }
        return acc
      })
    }
    setAccounts(updateAccounts(accounts))
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

  const renderAccountItem = (account: any, level: number = 0) => {
    const hasChildren = account.children && account.children.length > 0
    const isSelected = selectedAccount === account.id

    return (
      <div key={account.id}>
        <div 
          className={`flex items-center p-3 rounded-lg cursor-pointer transition-all duration-200 ${
            isSelected 
              ? 'bg-primary-container text-on-primary-container' 
              : 'hover:bg-surface-container'
          }`}
          style={{ paddingLeft: `${12 + (level * 24)}px` }}
          onClick={() => setSelectedAccount(account.id)}
        >
          <div className="flex items-center flex-1 min-w-0">
            {hasChildren ? (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  toggleExpanded(account.id)
                }}
                className="mr-2 p-1 hover:bg-surface-container-highest rounded"
              >
                {account.isExpanded ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </button>
            ) : (
              <div className="w-6 mr-2" />
            )}
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-3">
                <span className="font-mono text-sm text-on-surface-variant min-w-0">
                  {account.code}
                </span>
                <span className="md-body-medium text-on-surface truncate">
                  {account.name}
                </span>
                <span className={`inline-block px-2 py-0.5 rounded-md text-xs font-medium ${getAccountTypeColor(account.type)}`}>
                  {account.type}
                </span>
                {!account.isPostable && (
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-md">
                    Non-Postable
                  </span>
                )}
              </div>
              {account.description && (
                <p className="text-xs text-on-surface-variant mt-1 truncate">
                  {account.description}
                </p>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              {account.isPostable && account.balance !== 0 && (
                <span className="text-sm font-medium text-on-surface">
                  {formatCurrency(account.balance)}
                </span>
              )}
              <div className="flex items-center space-x-1">
                <button className="p-1 hover:bg-surface-container-highest rounded">
                  <Eye className="w-4 h-4" />
                </button>
                <button className="p-1 hover:bg-surface-container-highest rounded">
                  <Edit className="w-4 h-4" />
                </button>
                <button className="p-1 hover:bg-surface-container-highest rounded text-red-600">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
        
        {hasChildren && account.isExpanded && (
          <div>
            {account.children.map((child: any) => renderAccountItem(child, level + 1))}
          </div>
        )}
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
              <h1 className="md-headline-small text-on-background">Chart of Accounts</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                Manage your account structure and hierarchy
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Button 
                onClick={() => setShowCreateModal(true)}
                className="md-button"
              >
                <Plus className="w-4 h-4 mr-2" />
                New Account
              </Button>
              <Button 
                onClick={() => setAccounts([...accounts])}
                variant="outline"
                className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Button variant="outline" className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
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
              <Building2 className="w-10 h-10 text-on-primary-container" />
            </div>
            <h3 className="md-headline-small text-on-surface mb-3">No accounts found</h3>
            <p className="md-body-large text-on-surface-variant text-center mb-8 max-w-md">
              {searchTerm || filterType !== 'all' 
                ? 'Try adjusting your search or filter criteria.'
                : 'Get started by creating your first account.'
              }
            </p>
            <Button onClick={() => setShowCreateModal(true)} className="md-button">
              <Plus className="w-4 h-4 mr-2" />
              Create Account
            </Button>
          </div>
        ) : (
          /* Accounts List */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Accounts Tree */}
            <div className="lg:col-span-2">
              <Card className="md-card-expressive">
                <CardHeader>
                  <CardTitle className="md-title-large text-on-surface">Account Hierarchy</CardTitle>
                  <CardDescription className="md-body-medium text-on-surface-variant">
                    Click to expand/collapse account groups
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="max-h-96 overflow-y-auto">
                    {filteredAccounts.map(account => renderAccountItem(account))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Account Details */}
            <div className="lg:col-span-1">
              {selectedAccount ? (
                <Card className="md-card-expressive">
                  <CardHeader>
                    <CardTitle className="md-title-large text-on-surface">Account Details</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium text-on-surface-variant">Account Code</label>
                        <p className="text-lg font-mono text-on-surface">1110</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-on-surface-variant">Account Name</label>
                        <p className="text-lg text-on-surface">Cash</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-on-surface-variant">Account Type</label>
                        <span className="inline-block px-2 py-1 rounded-md text-xs font-medium bg-green-50 text-green-600">
                          Asset
                        </span>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-on-surface-variant">Current Balance</label>
                        <p className="text-lg font-semibold text-on-surface">$15,420.50</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-on-surface-variant">Description</label>
                        <p className="text-sm text-on-surface-variant">Cash on hand and in bank accounts</p>
                      </div>
                      <div className="pt-4 border-t border-outline-variant">
                        <div className="flex space-x-2">
                          <Button variant="outline" className="flex-1">
                            <Edit className="w-4 h-4 mr-2" />
                            Edit
                          </Button>
                          <Button variant="outline" className="flex-1">
                            <Settings className="w-4 h-4 mr-2" />
                            Settings
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="md-card-expressive">
                  <CardContent className="p-6 text-center">
                    <FileText className="w-12 h-12 text-on-surface-variant mx-auto mb-4" />
                    <h3 className="md-title-medium text-on-surface mb-2">Select an Account</h3>
                    <p className="text-sm text-on-surface-variant">
                      Click on any account to view its details and manage settings.
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

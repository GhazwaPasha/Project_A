'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Plus, 
  Search, 
  Filter, 
  Download,
  Edit,
  Trash2,
  Eye,
  MoreVertical,
  Calendar,
  FileText,
  Grid3X3,
  List
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'

const mockTransactions = [
  {
    id: '1',
    date: '2024-12-19',
    description: 'Office Supplies Purchase',
    reference: 'INV-001',
    totalAmount: 245.50,
    status: 'Posted',
    entries: [
      { account: 'Office Expenses', debit: 245.50, credit: 0 },
      { account: 'Cash', debit: 0, credit: 245.50 }
    ]
  },
  {
    id: '2',
    date: '2024-12-18',
    description: 'Client Payment - Project Alpha',
    reference: 'PAY-001',
    totalAmount: 5000.00,
    status: 'Posted',
    entries: [
      { account: 'Cash', debit: 5000.00, credit: 0 },
      { account: 'Accounts Receivable', debit: 0, credit: 5000.00 }
    ]
  },
  {
    id: '3',
    date: '2024-12-17',
    description: 'Software Subscription',
    reference: 'SUB-001',
    totalAmount: 99.00,
    status: 'Draft',
    entries: [
      { account: 'Software Expenses', debit: 99.00, credit: 0 },
      { account: 'Accounts Payable', debit: 0, credit: 99.00 }
    ]
  }
]

export function Win11JournalPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [viewMode, setViewMode] = useState('cards') // 'cards' or 'table'

  const filteredTransactions = mockTransactions.filter(transaction => {
    const matchesSearch = transaction.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         transaction.reference.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterStatus === 'all' || transaction.status.toLowerCase() === filterStatus
    return matchesSearch && matchesFilter
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
            <Button className="md-button">
              <Plus className="w-4 h-4 mr-2" />
              New Entry
            </Button>
          </div>

          {/* Enhanced Search and Controls */}
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
              <input
                type="text"
                placeholder="Search by description, reference, or account..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-12 pl-12 pr-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                aria-label="Search transactions"
              />
            </div>
            <div className="flex gap-3">
              <div className="relative">
                 <select
                   value={filterStatus}
                   onChange={(e) => setFilterStatus(e.target.value)}
                   className="h-12 pl-4 pr-12 py-3 bg-surface-container border border-outline rounded-2xl text-sm text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200 appearance-none cursor-pointer min-w-[160px]"
                 >
                  <option value="all">All Status</option>
                  <option value="posted">Posted</option>
                  <option value="draft">Draft</option>
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
        {filteredTransactions.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-20 h-20 bg-primary-container rounded-3xl flex items-center justify-center mb-6">
              <FileText className="w-10 h-10 text-on-primary-container" />
            </div>
            <h3 className="md-headline-small text-on-surface mb-3">No transactions found</h3>
            <p className="md-body-large text-on-surface-variant text-center mb-8 max-w-md">
              {searchTerm || filterStatus !== 'all' 
                ? 'Try adjusting your search or filter criteria.'
                : 'Get started by creating your first journal entry.'
              }
            </p>
            <Button className="md-button">
              <Plus className="w-4 h-4 mr-2" />
              New Entry
            </Button>
          </div>
        ) : (
           /* Transaction List - Compact Two-Line Cards */
           <div className="space-y-2">
             {filteredTransactions.map((transaction) => (
               <Card key={transaction.id} className="md-card-expressive group hover:md-elevation-1 transition-all duration-200">
                 <CardContent className="p-4">
                   {/* First Line - Transaction Info */}
                   <div className="flex items-center justify-between mb-2">
                     <div className="flex items-center space-x-3 flex-1 min-w-0">
                       <h3 className="md-title-medium text-on-surface truncate">{transaction.description}</h3>
                       <span className={`px-2 py-0.5 rounded-md text-xs font-medium ${
                         transaction.status === 'Posted' 
                           ? 'bg-tertiary-container text-on-tertiary-container' 
                           : 'bg-error-container text-on-error-container'
                       }`}>
                         {transaction.status}
                       </span>
                     </div>
                       <div className="flex items-center space-x-3">
                         <div 
                           className="cursor-pointer"
                           title="View"
                         >
                           <Eye className="w-4 h-4 text-on-surface-variant" />
                         </div>
                         <div 
                           className="cursor-pointer"
                           title="Edit"
                         >
                           <Edit className="w-4 h-4 text-on-surface-variant" />
                         </div>
                         <div 
                           className="cursor-pointer"
                           title="More options"
                         >
                           <MoreVertical className="w-4 h-4 text-on-surface-variant" />
                         </div>
                       </div>
                   </div>

                   {/* Second Line - Date, Reference, Accounts, and Total Amount */}
                   <div className="flex items-center justify-between">
                     <div className="flex items-center space-x-4 text-sm text-on-surface-variant">
                       <span className="flex items-center space-x-1">
                         <Calendar className="w-3 h-3" />
                         <span>{formatDate(transaction.date)}</span>
                       </span>
                       <span className="flex items-center space-x-1">
                         <span className="w-1 h-1 bg-outline rounded-full"></span>
                         <span>{transaction.reference}</span>
                       </span>
                     </div>
                     <div className="flex items-center space-x-6">
                       <div className="flex space-x-4">
                         {transaction.entries.map((entry, index) => (
                           <div key={index} className="flex items-center space-x-2">
                             <span className="md-body-large text-on-surface font-medium">{entry.account}</span>
                             <span className={`px-2 py-1 rounded-md text-xs font-medium ${
                               entry.debit > 0 
                                 ? 'bg-primary text-white' 
                                 : 'bg-primary text-white'
                             }`}>
                               {entry.debit > 0 ? 'Debit' : 'Credit'}
                             </span>
                           </div>
                         ))}
                       </div>
                       <span className="md-title-large text-on-surface font-medium">
                         {formatCurrency(transaction.totalAmount)}
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
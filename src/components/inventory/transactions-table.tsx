'use client'

import { InventoryTransaction } from '@/types'
import { formatCurrency, formatDate } from '@/lib/utils'
import { ArrowUpCircle, ArrowDownCircle, RefreshCcw } from 'lucide-react'

interface TransactionsTableProps {
  transactions: InventoryTransaction[]
  onRefresh: () => void
}

export function TransactionsTable({ transactions, onRefresh }: TransactionsTableProps) {
  if (transactions.length === 0) {
    return (
      <div className="text-center py-12 md-card rounded-lg">
        <p className="text-on-surface-variant">No transactions found</p>
      </div>
    )
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'in':
        return <ArrowUpCircle className="h-4 w-4 text-green-600" />
      case 'out':
        return <ArrowDownCircle className="h-4 w-4 text-red-600" />
      case 'adjustment':
        return <RefreshCcw className="h-4 w-4 text-orange-600" />
      default:
        return null
    }
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'in':
        return 'IN'
      case 'out':
        return 'OUT'
      case 'adjustment':
        return 'ADJ'
      default:
        return type
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'in':
        return 'text-green-600 bg-green-100'
      case 'out':
        return 'text-red-600 bg-red-100'
      case 'adjustment':
        return 'text-orange-600 bg-orange-100'
      default:
        return ''
    }
  }

  return (
    <div className="md-card rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-[var(--md-sys-color-surface-container-highest)] border-b border-[var(--md-sys-color-outline-variant)]">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-on-surface">Date</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-on-surface">Type</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-on-surface">Item</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-on-surface">Category</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-on-surface">Quantity</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-on-surface">Unit Cost</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-on-surface">Total Cost</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-on-surface">Reference</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant">
            {transactions.map((transaction) => (
              <tr key={transaction.id} className="hover:bg-surface-container/50 transition-colors">
                <td className="px-4 py-3 text-sm">
                  {formatDate(transaction.transaction_date)}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {getTypeIcon(transaction.transaction_type)}
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getTypeColor(transaction.transaction_type)}`}>
                      {getTypeLabel(transaction.transaction_type)}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div>
                    <p className="font-medium">{transaction.item?.name}</p>
                    <p className="text-xs text-on-surface-variant font-mono">{transaction.item?.sku}</p>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm">{transaction.item?.category?.name || '-'}</td>
                <td className="px-4 py-3 text-sm text-right">
                  <span className={transaction.quantity >= 0 ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                    {transaction.quantity >= 0 ? '+' : ''}{transaction.quantity.toFixed(2)}
                  </span>
                  <span className="text-on-surface-variant ml-1">
                    {transaction.item?.unit_of_measure}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-right">
                  {transaction.unit_cost ? formatCurrency(transaction.unit_cost) : '-'}
                </td>
                <td className="px-4 py-3 text-sm text-right font-medium">
                  {transaction.total_cost ? formatCurrency(transaction.total_cost) : '-'}
                </td>
                <td className="px-4 py-3 text-sm">
                  {transaction.reference || transaction.description || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}


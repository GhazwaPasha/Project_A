'use client'

import { InventoryItem } from '@/types'
import { formatCurrency } from '@/lib/utils'
import { Edit, Trash2, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DataService } from '@/lib/data-service'

interface ItemsTableProps {
  items: InventoryItem[]
  onEdit: (item: InventoryItem) => void
  onRefresh: () => void
}

export function ItemsTable({ items, onEdit, onRefresh }: ItemsTableProps) {
  const handleDelete = async (itemId: number) => {
    if (!confirm('Are you sure you want to delete this item?')) return
    
    await DataService.deleteInventoryItem(itemId)
    onRefresh()
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-12 md-card rounded-lg">
        <p className="text-on-surface-variant">No inventory items found</p>
      </div>
    )
  }

  return (
    <div className="md-card rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-surface-container">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-on-surface-variant">SKU</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-on-surface-variant">Name</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-on-surface-variant">Category</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-on-surface-variant">In</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-on-surface-variant">Out</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-on-surface-variant">Available</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-on-surface-variant">Unit Cost</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-on-surface-variant">Total Value</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-on-surface-variant">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant">
            {items.map((item) => {
              const isLowStock = item.reorder_point > 0 && item.quantity_available <= item.reorder_point
              
              return (
                <tr key={item.id} className="hover:bg-surface-container/50 transition-colors">
                  <td className="px-4 py-3 text-sm font-mono">{item.sku}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{item.name}</span>
                      {isLowStock && (
                        <AlertTriangle className="h-4 w-4 text-error" title="Low stock" />
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">{item.category?.name || '-'}</td>
                  <td className="px-4 py-3 text-sm text-right text-green-600 font-medium">
                    {item.quantity_in.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-red-600 font-medium">
                    {item.quantity_out.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-sm text-right font-bold">
                    <span className={isLowStock ? 'text-error' : ''}>
                      {item.quantity_available.toFixed(2)} {item.unit_of_measure}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-right">{formatCurrency(item.average_unit_cost)}</td>
                  <td className="px-4 py-3 text-sm text-right font-medium">{formatCurrency(item.total_value)}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEdit(item)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(item.id)}
                      >
                        <Trash2 className="h-4 w-4 text-error" />
                      </Button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}


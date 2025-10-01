'use client'

import { InventoryCategory } from '@/types'
import { Edit, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DataService } from '@/lib/data-service'

interface CategoriesTableProps {
  categories: InventoryCategory[]
  onEdit: (category: InventoryCategory) => void
  onRefresh: () => void
}

export function CategoriesTable({ categories, onEdit, onRefresh }: CategoriesTableProps) {
  const handleDelete = async (categoryId: number) => {
    if (!confirm('Are you sure you want to delete this category? This will affect all items in this category.')) return
    
    await DataService.deleteInventoryCategory(categoryId)
    onRefresh()
  }

  if (categories.length === 0) {
    return (
      <div className="text-center py-12 md-card rounded-lg">
        <p className="text-on-surface-variant">No categories found</p>
      </div>
    )
  }

  return (
    <div className="md-card rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-surface-container">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-on-surface-variant">Category Name</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-on-surface-variant">Description</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-on-surface-variant">Inventory Account (IN)</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-on-surface-variant">Expense Account (OUT)</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-on-surface-variant">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant">
            {categories.map((category) => (
              <tr key={category.id} className="hover:bg-surface-container/50 transition-colors">
                <td className="px-4 py-3 font-medium">{category.name}</td>
                <td className="px-4 py-3 text-sm text-on-surface-variant">{category.description || '-'}</td>
                <td className="px-4 py-3 text-sm">
                  {category.inventory_account ? (
                    <span className="font-mono text-xs">
                      {category.inventory_account.code} - {category.inventory_account.name}
                    </span>
                  ) : '-'}
                </td>
                <td className="px-4 py-3 text-sm">
                  {category.expense_account ? (
                    <span className="font-mono text-xs">
                      {category.expense_account.code} - {category.expense_account.name}
                    </span>
                  ) : '-'}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onEdit(category)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(category.id)}
                    >
                      <Trash2 className="h-4 w-4 text-error" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}


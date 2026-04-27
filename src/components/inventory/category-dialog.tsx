'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { AccountSearch } from '@/components/ui/account-search'
import { DataService } from '@/lib/data-service'
import { InventoryCategory, Account } from '@/types'

interface CategoryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  category: InventoryCategory | null
  onSuccess: () => void
  organizationId: string
}

export function CategoryDialog({ open, onOpenChange, category, onSuccess, organizationId }: CategoryDialogProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [accounts, setAccounts] = useState<Account[]>([])
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    inventory_account_id: '',
    expense_account_id: ''
  })

  useEffect(() => {
    if (open && organizationId) {
      loadAccounts()
    }
  }, [open, organizationId])

  useEffect(() => {
    if (category) {
      setFormData({
        name: category.name,
        description: category.description || '',
        inventory_account_id: category.inventory_account_id.toString(),
        expense_account_id: category.expense_account_id.toString()
      })
    } else {
      setFormData({
        name: '',
        description: '',
        inventory_account_id: '',
        expense_account_id: ''
      })
    }
  }, [category])

  const loadAccounts = async () => {
    const accountsData = await DataService.getAccounts(organizationId, true)
    setAccounts(accountsData)
  }

  const handleSubmit = async () => {
    if (!formData.name || !formData.inventory_account_id || !formData.expense_account_id) {
      setError('Please fill in all required fields')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const categoryData = {
        organization_id: organizationId,
        name: formData.name,
        description: formData.description || null,
        inventory_account_id: parseInt(formData.inventory_account_id),
        expense_account_id: parseInt(formData.expense_account_id),
        parent_id: null,
        is_active: true,
        created_by: null
      }

      if (category) {
        await DataService.updateInventoryCategory(category.id, categoryData)
      } else {
        await DataService.createInventoryCategory(categoryData)
      }

      onSuccess()
      onOpenChange(false)
    } catch (err) {
      console.error('Error saving category:', err)
      setError('Failed to save category')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl md-card">
        <DialogHeader>
          <DialogTitle>{category ? 'Edit Category' : 'Create Category'}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {error && (
            <div className="p-3 bg-error-container rounded-lg text-error text-sm">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="name">Category Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Meats, Vegetables, Dairy"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Optional description"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="inventory-account">Inventory Account (IN) *</Label>
            <AccountSearch
              accounts={accounts}
              value={formData.inventory_account_id}
              onChange={(value) => setFormData({ ...formData, inventory_account_id: value })}
              placeholder="Select inventory asset account"
            />
            <p className="text-xs text-on-surface-variant">
              Debited when purchasing inventory (Asset account)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="expense-account">Expense Account (OUT) *</Label>
            <AccountSearch
              accounts={accounts}
              value={formData.expense_account_id}
              onChange={(value) => setFormData({ ...formData, expense_account_id: value })}
              placeholder="Select COGS/expense account"
            />
            <p className="text-xs text-on-surface-variant">
              Debited when selling/using inventory (COGS/Expense account)
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? 'Saving...' : (category ? 'Update' : 'Create')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}


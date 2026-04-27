'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { DataService } from '@/lib/data-service'
import { InventoryItem, InventoryTransactionType } from '@/types'

interface TransactionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  items: InventoryItem[]
  onSuccess: () => void
  organizationId: string
}

export function TransactionDialog({ open, onOpenChange, items, onSuccess, organizationId }: TransactionDialogProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const [formData, setFormData] = useState({
    item_id: '',
    transaction_type: 'in' as InventoryTransactionType,
    quantity: '',
    unit_cost: '',
    description: '',
    reference: '',
    transaction_date: new Date().toISOString().split('T')[0]
  })

  const handleSubmit = async () => {
    if (!formData.item_id || !formData.quantity) {
      setError('Please fill in all required fields')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const quantity = parseFloat(formData.quantity)
      const unitCost = parseFloat(formData.unit_cost) || 0
      
      // For OUT transactions, make quantity negative
      const finalQuantity = formData.transaction_type === 'out' ? -Math.abs(quantity) : Math.abs(quantity)

      const transactionData = {
        organization_id: organizationId,
        item_id: parseInt(formData.item_id),
        transaction_type: formData.transaction_type,
        quantity: finalQuantity,
        unit_cost: unitCost > 0 ? unitCost : null,
        total_cost: unitCost > 0 ? Math.abs(quantity) * unitCost : null,
        description: formData.description || null,
        reference: formData.reference || null,
        transaction_date: formData.transaction_date,
        journal_entry_id: null,
        created_by: null
      }

      await DataService.createInventoryTransaction(transactionData)

      onSuccess()
      onOpenChange(false)
      
      // Reset form
      setFormData({
        item_id: '',
        transaction_type: 'in',
        quantity: '',
        unit_cost: '',
        description: '',
        reference: '',
        transaction_date: new Date().toISOString().split('T')[0]
      })
    } catch (err) {
      console.error('Error creating transaction:', err)
      setError('Failed to create transaction')
    } finally {
      setLoading(false)
    }
  }

  const selectedItem = items.find(i => i.id.toString() === formData.item_id)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl md-card">
        <DialogHeader>
          <DialogTitle>New Inventory Transaction</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {error && (
            <div className="p-3 bg-error-container rounded-lg text-error text-sm">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="item">Item *</Label>
            <Select value={formData.item_id} onValueChange={(value) => setFormData({ ...formData, item_id: value })}>
              <SelectTrigger>
                <SelectValue placeholder="Select item" />
              </SelectTrigger>
              <SelectContent>
                {items.map(item => (
                  <SelectItem key={item.id} value={item.id.toString()}>
                    {item.name} ({item.sku}) - Available: {item.quantity_available} {item.unit_of_measure}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedItem && (
            <div className="p-3 bg-surface-container rounded-lg">
              <p className="text-sm">
                <span className="text-on-surface-variant">Current Stock:</span>{' '}
                <span className="font-medium">{selectedItem.quantity_available} {selectedItem.unit_of_measure}</span>
              </p>
              <p className="text-sm">
                <span className="text-on-surface-variant">Category:</span>{' '}
                <span className="font-medium">{selectedItem.category?.name}</span>
              </p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="type">Transaction Type *</Label>
              <Select value={formData.transaction_type} onValueChange={(value: InventoryTransactionType) => setFormData({ ...formData, transaction_type: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="in">IN - Receive Stock</SelectItem>
                  <SelectItem value="out">OUT - Use/Sell Stock</SelectItem>
                  <SelectItem value="adjustment">Adjustment</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="date">Date *</Label>
              <Input
                id="date"
                type="date"
                value={formData.transaction_date}
                onChange={(e) => setFormData({ ...formData, transaction_date: e.target.value })}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="quantity">Quantity * {selectedItem && `(${selectedItem.unit_of_measure})`}</Label>
              <Input
                id="quantity"
                type="number"
                step="0.01"
                value={formData.quantity}
                onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                placeholder="0.00"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="unit-cost">Unit Cost</Label>
              <Input
                id="unit-cost"
                type="number"
                step="0.01"
                value={formData.unit_cost}
                onChange={(e) => setFormData({ ...formData, unit_cost: e.target.value })}
                placeholder="0.00"
              />
            </div>
          </div>

          {formData.quantity && formData.unit_cost && (
            <div className="p-3 bg-primary-container/20 rounded-lg">
              <p className="text-sm font-medium">
                Total Cost: ${(parseFloat(formData.quantity) * parseFloat(formData.unit_cost)).toFixed(2)}
              </p>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="reference">Reference</Label>
            <Input
              id="reference"
              value={formData.reference}
              onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
              placeholder="e.g., PO-12345, Invoice #"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Optional notes"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? 'Processing...' : 'Create Transaction'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}


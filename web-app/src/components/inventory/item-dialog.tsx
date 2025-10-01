'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { DataService } from '@/lib/data-service'
import { InventoryCategory, InventoryItem } from '@/types'

interface ItemDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  item: InventoryItem | null
  categories: InventoryCategory[]
  onSuccess: () => void
  organizationId: string
}

export function ItemDialog({ open, onOpenChange, item, categories, onSuccess, organizationId }: ItemDialogProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    description: '',
    category_id: '',
    unit_of_measure: 'kg',
    average_unit_cost: '',
    reorder_point: '',
    reorder_quantity: ''
  })

  useEffect(() => {
    if (item) {
      setFormData({
        sku: item.sku,
        name: item.name,
        description: item.description || '',
        category_id: item.category_id.toString(),
        unit_of_measure: item.unit_of_measure,
        average_unit_cost: item.average_unit_cost.toString(),
        reorder_point: item.reorder_point.toString(),
        reorder_quantity: item.reorder_quantity.toString()
      })
    } else {
      setFormData({
        sku: '',
        name: '',
        description: '',
        category_id: '',
        unit_of_measure: 'kg',
        average_unit_cost: '0',
        reorder_point: '0',
        reorder_quantity: '0'
      })
    }
  }, [item])

  const handleSubmit = async () => {
    if (!formData.sku || !formData.name || !formData.category_id) {
      setError('Please fill in all required fields')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const itemData = {
        organization_id: organizationId,
        sku: formData.sku,
        name: formData.name,
        description: formData.description || null,
        category_id: parseInt(formData.category_id),
        unit_of_measure: formData.unit_of_measure,
        quantity_in: item?.quantity_in || 0,
        quantity_out: item?.quantity_out || 0,
        average_unit_cost: parseFloat(formData.average_unit_cost) || 0,
        reorder_point: parseFloat(formData.reorder_point) || 0,
        reorder_quantity: parseFloat(formData.reorder_quantity) || 0,
        is_active: true,
        created_by: null
      }

      if (item) {
        await DataService.updateInventoryItem(item.id, itemData)
      } else {
        await DataService.createInventoryItem(itemData)
      }

      onSuccess()
      onOpenChange(false)
    } catch (err) {
      console.error('Error saving item:', err)
      setError('Failed to save item')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl md-card">
        <DialogHeader>
          <DialogTitle>{item ? 'Edit Item' : 'Create Item'}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {error && (
            <div className="p-3 bg-error-container rounded-lg text-error text-sm">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="sku">SKU *</Label>
              <Input
                id="sku"
                value={formData.sku}
                onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                placeholder="e.g., BEEF-RIB-001"
                disabled={!!item}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="category">Category *</Label>
              <Select value={formData.category_id} onValueChange={(value) => setFormData({ ...formData, category_id: value })}>
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map(cat => (
                    <SelectItem key={cat.id} value={cat.id.toString()}>
                      {cat.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="name">Item Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Beef Ribeye Steak"
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

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="unit">Unit of Measure</Label>
              <Select value={formData.unit_of_measure} onValueChange={(value) => setFormData({ ...formData, unit_of_measure: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="kg">Kilogram (kg)</SelectItem>
                  <SelectItem value="g">Gram (g)</SelectItem>
                  <SelectItem value="lb">Pound (lb)</SelectItem>
                  <SelectItem value="pcs">Pieces (pcs)</SelectItem>
                  <SelectItem value="box">Box</SelectItem>
                  <SelectItem value="liter">Liter</SelectItem>
                  <SelectItem value="each">Each</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="cost">Average Unit Cost</Label>
              <Input
                id="cost"
                type="number"
                step="0.01"
                value={formData.average_unit_cost}
                onChange={(e) => setFormData({ ...formData, average_unit_cost: e.target.value })}
                placeholder="0.00"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="reorder-point">Reorder Point</Label>
              <Input
                id="reorder-point"
                type="number"
                step="0.01"
                value={formData.reorder_point}
                onChange={(e) => setFormData({ ...formData, reorder_point: e.target.value })}
                placeholder="0"
              />
              <p className="text-xs text-on-surface-variant">Alert when stock falls below this</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="reorder-qty">Reorder Quantity</Label>
              <Input
                id="reorder-qty"
                type="number"
                step="0.01"
                value={formData.reorder_quantity}
                onChange={(e) => setFormData({ ...formData, reorder_quantity: e.target.value })}
                placeholder="0"
              />
              <p className="text-xs text-on-surface-variant">Suggested reorder amount</p>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? 'Saving...' : (item ? 'Update' : 'Create')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}


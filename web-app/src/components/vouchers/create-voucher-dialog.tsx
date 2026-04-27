'use client'

import React, { useState, useEffect } from 'react'
import { VoucherFormData, VoucherType, InventoryItem, Account } from '@/types'
import { useCreateVoucher } from '@/hooks/use-vouchers'
import { useAccounts } from '@/hooks/use-accounts'
import { useOrganization } from '@/hooks/use-organization'
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogFooter 
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table'
import { 
  Plus, 
  Trash2, 
  ShoppingCart, 
  Package,
  DollarSign,
  Calendar,
  RefreshCw
} from 'lucide-react'

interface CreateVoucherDialogProps {
  voucherType: VoucherType
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
  items: InventoryItem[]
}

export function CreateVoucherDialog({ 
  voucherType, 
  open, 
  onOpenChange, 
  onSuccess,
  items
}: CreateVoucherDialogProps) {
  const [formData, setFormData] = useState<VoucherFormData>({
    voucher_type: voucherType,
    description: '',
    notes: '',
    payment_type: 'credit',
    lines: []
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const { currentOrganization } = useOrganization()
  const createVoucher = useCreateVoucher(currentOrganization?.id || '')
  const { data: accounts = [] } = useAccounts()

  // Generate purchase order number
  const generatePONumber = () => {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    const timestamp = now.getTime().toString().slice(-4) // Last 4 digits of timestamp
    return `PO-${year}${month}${day}-${timestamp}`
  }

  // Reset form when dialog opens
  useEffect(() => {
    if (open) {
      setFormData({
        voucher_type: voucherType,
        description: '',
        notes: '',
        payment_type: 'credit',
        lines: [],
        // Auto-generate PO number for purchase vouchers
        purchase_order_number: voucherType === 'purchase' ? generatePONumber() : ''
      })
      setErrors({})
    }
  }, [open, voucherType])

  const handleInputChange = (field: keyof VoucherFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }))
    }
  }

  const addLineItem = () => {
    setFormData(prev => ({
      ...prev,
      lines: [...prev.lines, {
        item_id: 0,
        quantity_requested: 0,
        unit_cost_estimated: 0,
        notes: ''
      }]
    }))
  }

  const removeLineItem = (index: number) => {
    setFormData(prev => ({
      ...prev,
      lines: prev.lines.filter((_, i) => i !== index)
    }))
  }

  const updateLineItem = (index: number, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      lines: prev.lines.map((line, i) => 
        i === index ? { ...line, [field]: value } : line
      )
    }))
  }

  const calculateTotal = () => {
    return formData.lines.reduce((sum, line) => 
      sum + (line.quantity_requested * (line.unit_cost_estimated || 0)), 0
    )
  }

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required'
    }

    if (voucherType === 'purchase' && !formData.vendor_name?.trim()) {
      newErrors.vendor_name = 'Vendor name is required for purchase vouchers'
    }

    if (voucherType === 'issuance' && !formData.purpose?.trim()) {
      newErrors.purpose = 'Purpose is required for issuance vouchers'
    }

    if (voucherType === 'issuance' && !formData.destination_account_id) {
      newErrors.destination_account_id = 'Destination account is required for issuance vouchers'
    }

    if (formData.lines.length === 0) {
      newErrors.lines = 'At least one line item is required'
    }

    formData.lines.forEach((line, index) => {
      if (!line.item_id) {
        newErrors[`line_${index}_item`] = 'Item is required'
      }
      if (line.quantity_requested <= 0) {
        newErrors[`line_${index}_quantity`] = 'Quantity must be greater than 0'
      }
    })

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async () => {
    if (!validateForm()) return

    try {
      await createVoucher.mutateAsync(formData)
      onSuccess()
    } catch (error) {
      console.error('Error creating voucher:', error)
    }
  }

  const getItemName = (itemId: number) => {
    const item = items.find(i => i.id === itemId)
    return item ? `${item.name} (${item.sku})` : 'Select item'
  }

  const getAccountName = (accountId: number) => {
    const account = accounts.find(a => a.id === accountId)
    return account ? `${account.code} - ${account.name}` : 'Select account'
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {voucherType === 'purchase' ? (
              <ShoppingCart className="h-5 w-5 text-blue-600" />
            ) : (
              <Package className="h-5 w-5 text-green-600" />
            )}
            Create {voucherType === 'purchase' ? 'Purchase' : 'Issuance'} Voucher
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="description">Description *</Label>
                  <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="Brief description of the voucher"
                  />
                  {errors.description && (
                    <p className="text-sm text-red-600">{errors.description}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="notes">Notes</Label>
                  <Input
                    id="notes"
                    value={formData.notes || ''}
                    onChange={(e) => handleInputChange('notes', e.target.value)}
                    placeholder="Additional notes"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Purchase-specific fields */}
          {voucherType === 'purchase' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Purchase Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="vendor_name">Vendor Name *</Label>
                    <Input
                      id="vendor_name"
                      value={formData.vendor_name || ''}
                      onChange={(e) => handleInputChange('vendor_name', e.target.value)}
                      placeholder="Vendor company name"
                    />
                    {errors.vendor_name && (
                      <p className="text-sm text-red-600">{errors.vendor_name}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="vendor_contact">Vendor Contact</Label>
                    <Input
                      id="vendor_contact"
                      value={formData.vendor_contact || ''}
                      onChange={(e) => handleInputChange('vendor_contact', e.target.value)}
                      placeholder="Phone, email, or contact person"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="purchase_order_number">PO Number</Label>
                    <div className="flex gap-2">
                      <Input
                        id="purchase_order_number"
                        value={formData.purchase_order_number || ''}
                        onChange={(e) => handleInputChange('purchase_order_number', e.target.value)}
                        placeholder="Purchase order number"
                        readOnly={voucherType === 'purchase'}
                        className={voucherType === 'purchase' ? 'bg-gray-50 cursor-not-allowed' : ''}
                      />
                      {voucherType === 'purchase' && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleInputChange('purchase_order_number', generatePONumber())}
                          className="px-3"
                        >
                          <RefreshCw className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                    {voucherType === 'purchase' && (
                      <p className="text-xs text-muted-foreground">
                        Auto-generated purchase order number
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="expected_delivery_date">Expected Delivery</Label>
                    <Input
                      id="expected_delivery_date"
                      type="date"
                      value={formData.expected_delivery_date || ''}
                      onChange={(e) => handleInputChange('expected_delivery_date', e.target.value)}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="payment_type">Payment Type</Label>
                    <Select
                      value={formData.payment_type}
                      onValueChange={(value) => handleInputChange('payment_type', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="credit">Credit (Accounts Payable)</SelectItem>
                        <SelectItem value="cash">Cash</SelectItem>
                        <SelectItem value="check">Check</SelectItem>
                        <SelectItem value="card">Credit Card</SelectItem>
                        <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                        <SelectItem value="partial">Partial Payment</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {formData.payment_type === 'partial' && (
                    <div className="space-y-2">
                      <Label htmlFor="deposit_amount">Deposit Amount</Label>
                      <Input
                        id="deposit_amount"
                        type="number"
                        step="0.01"
                        value={formData.deposit_amount || ''}
                        onChange={(e) => handleInputChange('deposit_amount', parseFloat(e.target.value) || 0)}
                        placeholder="0.00"
                      />
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Issuance-specific fields */}
          {voucherType === 'issuance' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Issuance Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="purpose">Purpose *</Label>
                  <Textarea
                    id="purpose"
                    value={formData.purpose || ''}
                    onChange={(e) => handleInputChange('purpose', e.target.value)}
                    placeholder="Why is this inventory needed?"
                    rows={3}
                  />
                  {errors.purpose && (
                    <p className="text-sm text-red-600">{errors.purpose}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="destination">Destination</Label>
                    <Input
                      id="destination"
                      value={formData.destination || ''}
                      onChange={(e) => handleInputChange('destination', e.target.value)}
                      placeholder="Where is it going?"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="cost_center">Cost Center</Label>
                    <Input
                      id="cost_center"
                      value={formData.cost_center || ''}
                      onChange={(e) => handleInputChange('cost_center', e.target.value)}
                      placeholder="Cost center code"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="project_code">Project Code</Label>
                    <Input
                      id="project_code"
                      value={formData.project_code || ''}
                      onChange={(e) => handleInputChange('project_code', e.target.value)}
                      placeholder="Project code"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="destination_account_id">Destination Account *</Label>
                    <Select
                      value={formData.destination_account_id?.toString() || ''}
                      onValueChange={(value) => handleInputChange('destination_account_id', parseInt(value))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select account" />
                      </SelectTrigger>
                      <SelectContent>
                        {accounts
                          .filter(account => account.account_type === 'expense' || account.account_type === 'asset')
                          .map(account => (
                            <SelectItem key={account.id} value={account.id.toString()}>
                              {account.code} - {account.name}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                    {errors.destination_account_id && (
                      <p className="text-sm text-red-600">{errors.destination_account_id}</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Line Items */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center justify-between">
                Line Items
                <Button onClick={addLineItem} size="sm" disabled={items.length === 0}>
                  <Plus className="h-4 w-4 mr-1" />
                  Add Item
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {items.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No inventory items available</p>
                  <p className="text-sm">Please add inventory items first before creating vouchers</p>
                </div>
              ) : formData.lines.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No line items added yet</p>
                  <p className="text-sm">Click "Add Item" to start adding inventory items</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Item</TableHead>
                      <TableHead>Quantity</TableHead>
                      <TableHead>Unit Cost</TableHead>
                      <TableHead>Total</TableHead>
                      <TableHead>Notes</TableHead>
                      <TableHead className="w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {formData.lines.map((line, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Select
                            value={line.item_id.toString()}
                            onValueChange={(value) => updateLineItem(index, 'item_id', parseInt(value))}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select item" />
                            </SelectTrigger>
                            <SelectContent>
                              {items.map(item => (
                                <SelectItem key={item.id} value={item.id.toString()}>
                                  {item.name} ({item.sku})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          {errors[`line_${index}_item`] && (
                            <p className="text-sm text-red-600">{errors[`line_${index}_item`]}</p>
                          )}
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            min="0"
                            step="0.01"
                            value={line.quantity_requested}
                            onChange={(e) => updateLineItem(index, 'quantity_requested', parseFloat(e.target.value) || 0)}
                          />
                          {errors[`line_${index}_quantity`] && (
                            <p className="text-sm text-red-600">{errors[`line_${index}_quantity`]}</p>
                          )}
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            min="0"
                            step="0.01"
                            value={line.unit_cost_estimated || ''}
                            onChange={(e) => updateLineItem(index, 'unit_cost_estimated', parseFloat(e.target.value) || 0)}
                            placeholder="0.00"
                          />
                        </TableCell>
                        <TableCell>
                          <span className="font-medium">
                            ${((line.quantity_requested || 0) * (line.unit_cost_estimated || 0)).toFixed(2)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Input
                            value={line.notes || ''}
                            onChange={(e) => updateLineItem(index, 'notes', e.target.value)}
                            placeholder="Notes"
                          />
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeLineItem(index)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}

              {errors.lines && (
                <p className="text-sm text-red-600 mt-2">{errors.lines}</p>
              )}
            </CardContent>
          </Card>

          {/* Total Summary */}
          {formData.lines.length > 0 && (
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between text-lg font-semibold">
                  <span>Total Estimated Cost:</span>
                  <span className="flex items-center gap-2">
                    <DollarSign className="h-5 w-5" />
                    {calculateTotal().toLocaleString('en-US', {
                      style: 'currency',
                      currency: 'USD',
                      minimumFractionDigits: 2
                    })}
                  </span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit}
            disabled={createVoucher.isPending}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {createVoucher.isPending ? 'Creating...' : 'Create Voucher'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

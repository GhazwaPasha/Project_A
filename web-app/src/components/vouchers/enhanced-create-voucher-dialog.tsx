'use client'

import React, { useState, useEffect } from 'react'
import {
  VoucherFormData,
  VoucherType,
  InventoryItem,
  Account,
  Supplier,
  SupplierVoucherPicker,
} from '@/types'
import { useCreateVoucher } from '@/hooks/use-vouchers'
import { useAccounts } from '@/hooks/use-accounts'
import { useOrganization } from '@/hooks/use-organization'
import { SupplierService } from '@/lib/supplier-service'
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
  RefreshCw,
  Building,
  MapPin,
  Phone,
  Mail
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

interface EnhancedCreateVoucherDialogProps {
  voucherType: VoucherType
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
  items: InventoryItem[]
}

export function EnhancedCreateVoucherDialog({ 
  voucherType, 
  open, 
  onOpenChange, 
  onSuccess,
  items
}: EnhancedCreateVoucherDialogProps) {
  const [formData, setFormData] = useState<VoucherFormData>({
    voucher_type: voucherType,
    description: '',
    notes: '',
    payment_type: 'credit',
    lines: []
  })

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [suppliers, setSuppliers] = useState<SupplierVoucherPicker[]>([])
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null)
  const [loadingSuppliers, setLoadingSuppliers] = useState(false)

  const { currentOrganization } = useOrganization()
  const createVoucher = useCreateVoucher(currentOrganization?.id || '')
  const { data: accounts = [] } = useAccounts()
  const { toast } = useToast()

  // Load suppliers when dialog opens
  useEffect(() => {
    if (open && currentOrganization?.id) {
      loadSuppliers()
    }
  }, [open, currentOrganization?.id])

  const loadSuppliers = async () => {
    if (!currentOrganization?.id) return
    
    try {
      setLoadingSuppliers(true)
      const data = await SupplierService.getSuppliersForVoucher(currentOrganization.id)
      setSuppliers(data)
    } catch (error) {
      console.error('Error loading suppliers:', error)
      toast({
        title: 'Error',
        description: 'Failed to load suppliers',
        variant: 'destructive',
      })
    } finally {
      setLoadingSuppliers(false)
    }
  }

  // Generate purchase order number
  const generatePONumber = () => {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    const timestamp = now.getTime().toString().slice(-4)
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
        purchase_order_number: voucherType === 'purchase' ? generatePONumber() : ''
      })
      setSelectedSupplier(null)
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

  const handleSupplierChange = async (supplierId: string) => {
    if (!supplierId) {
      setSelectedSupplier(null)
      return
    }

    try {
      const supplier = await SupplierService.getSupplier(parseInt(supplierId))
      if (supplier) {
        setSelectedSupplier(supplier)
        
        // Auto-populate form fields with supplier data
        setFormData(prev => ({
          ...prev,
          vendor_name: supplier.name,
          vendor_contact: supplier.contact_person || supplier.email || supplier.phone || '',
          // Auto-populate account mappings if available
          destination_account_id: supplier.account_mappings?.expense_account_id,
          payment_account_id: supplier.account_mappings?.cash_account_id,
        }))
      }
    } catch (error) {
      console.error('Error loading supplier details:', error)
      toast({
        title: 'Error',
        description: 'Failed to load supplier details',
        variant: 'destructive',
      })
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
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
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

          {/* Purchase-specific fields with Supplier Integration */}
          {voucherType === 'purchase' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Purchase Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Supplier Selection */}
                <div className="space-y-2">
                  <Label htmlFor="supplier">Select Supplier (Optional)</Label>
                  <Select onValueChange={handleSupplierChange}>
                    <SelectTrigger>
                      <SelectValue placeholder="Choose a supplier to auto-populate fields" />
                    </SelectTrigger>
                    <SelectContent>
                      {loadingSuppliers ? (
                        <SelectItem value="" disabled>Loading suppliers...</SelectItem>
                      ) : suppliers.length === 0 ? (
                        <SelectItem value="" disabled>No suppliers available</SelectItem>
                      ) : (
                        suppliers.map((supplier) => (
                          <SelectItem key={supplier.id} value={supplier.id.toString()}>
                            {supplier.supplier_code} - {supplier.name}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>

                {/* Selected Supplier Info */}
                {selectedSupplier && (
                  <Card className="bg-blue-50 border-blue-200">
                    <CardContent className="pt-4">
                      <div className="flex items-start justify-between">
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <Building className="h-4 w-4 text-blue-600" />
                            <span className="font-medium">{selectedSupplier.name}</span>
                            {selectedSupplier.is_preferred && (
                              <Badge variant="secondary" className="text-xs">Preferred</Badge>
                            )}
                          </div>
                          
                          {selectedSupplier.contact_person && (
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <Phone className="h-3 w-3" />
                              <span>{selectedSupplier.contact_person}</span>
                            </div>
                          )}
                          
                          {selectedSupplier.email && (
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <Mail className="h-3 w-3" />
                              <span>{selectedSupplier.email}</span>
                            </div>
                          )}
                          
                          {selectedSupplier.billing_city && (
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <MapPin className="h-3 w-3" />
                              <span>{selectedSupplier.billing_city}, {selectedSupplier.billing_state}</span>
                            </div>
                          )}
                        </div>
                        
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedSupplier(null)
                            setFormData(prev => ({
                              ...prev,
                              vendor_name: '',
                              vendor_contact: '',
                              destination_account_id: undefined,
                              payment_account_id: undefined,
                            }))
                          }}
                        >
                          Clear
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}

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
                        placeholder="Auto-generated"
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => handleInputChange('purchase_order_number', generatePONumber())}
                      >
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                    </div>
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
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="purpose">Purpose *</Label>
                    <Input
                      id="purpose"
                      value={formData.purpose || ''}
                      onChange={(e) => handleInputChange('purpose', e.target.value)}
                      placeholder="Why is this inventory needed?"
                    />
                    {errors.purpose && (
                      <p className="text-sm text-red-600">{errors.purpose}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="destination">Destination</Label>
                    <Input
                      id="destination"
                      value={formData.destination || ''}
                      onChange={(e) => handleInputChange('destination', e.target.value)}
                      placeholder="Where is it going?"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="cost_center">Cost Center</Label>
                    <Input
                      id="cost_center"
                      value={formData.cost_center || ''}
                      onChange={(e) => handleInputChange('cost_center', e.target.value)}
                      placeholder="Cost center code"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="project_code">Project Code</Label>
                    <Input
                      id="project_code"
                      value={formData.project_code || ''}
                      onChange={(e) => handleInputChange('project_code', e.target.value)}
                      placeholder="Project code"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="destination_account_id">Destination Account *</Label>
                  <Select
                    value={formData.destination_account_id?.toString() || ''}
                    onValueChange={(value) => handleInputChange('destination_account_id', parseInt(value))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select destination account" />
                    </SelectTrigger>
                    <SelectContent>
                      {accounts
                        .filter(account => account.account_type === 'expense' && account.is_active)
                        .map((account) => (
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
              </CardContent>
            </Card>
          )}

          {/* Payment Details */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Payment Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
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

                <div className="space-y-2">
                  <Label htmlFor="payment_account_id">Payment Account</Label>
                  <Select
                    value={formData.payment_account_id?.toString() || ''}
                    onValueChange={(value) => handleInputChange('payment_account_id', parseInt(value))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select payment account" />
                    </SelectTrigger>
                    <SelectContent>
                      {accounts
                        .filter(account => 
                          (account.account_type === 'asset' || account.account_type === 'liability') && 
                          account.is_active
                        )
                        .map((account) => (
                          <SelectItem key={account.id} value={account.id.toString()}>
                            {account.code} - {account.name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
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

              <div className="space-y-2">
                <Label htmlFor="payment_reference">Payment Reference</Label>
                <Input
                  id="payment_reference"
                  value={formData.payment_reference || ''}
                  onChange={(e) => handleInputChange('payment_reference', e.target.value)}
                  placeholder="Check #, transaction ID, etc."
                />
              </div>
            </CardContent>
          </Card>

          {/* Line Items */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Line Items</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <Button type="button" onClick={addLineItem} size="sm">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Item
                  </Button>
                  {errors.lines && (
                    <p className="text-sm text-red-600">{errors.lines}</p>
                  )}
                </div>

                {formData.lines.length > 0 && (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Item</TableHead>
                        <TableHead>Quantity</TableHead>
                        <TableHead>Unit Cost</TableHead>
                        <TableHead>Total</TableHead>
                        <TableHead>Notes</TableHead>
                        <TableHead className="w-[50px]"></TableHead>
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
                                {items.map((item) => (
                                  <SelectItem key={item.id} value={item.id.toString()}>
                                    {item.name} ({item.sku})
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            {errors[`line_${index}_item`] && (
                              <p className="text-xs text-red-600 mt-1">{errors[`line_${index}_item`]}</p>
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
                              <p className="text-xs text-red-600 mt-1">{errors[`line_${index}_quantity`]}</p>
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
                              type="button"
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

                {formData.lines.length > 0 && (
                  <div className="flex justify-end">
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">Total Estimated Cost</p>
                      <p className="text-2xl font-bold">${calculateTotal().toFixed(2)}</p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={createVoucher.isPending}>
            {createVoucher.isPending ? 'Creating...' : 'Create Voucher'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

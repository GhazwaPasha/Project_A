'use client'

import React from 'react'
import { InventoryVoucher } from '@/types'
import { useVoucherStatusColor, useVoucherStatusIcon } from '@/hooks/use-vouchers'
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table'
import { 
  DollarSign, 
  User, 
  Calendar,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  FileText,
  ShoppingCart,
  Package
} from 'lucide-react'

interface VoucherViewDialogProps {
  voucher: InventoryVoucher
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function VoucherViewDialog({ voucher, open, onOpenChange }: VoucherViewDialogProps) {
  const getStatusColor = useVoucherStatusColor
  const getStatusIcon = useVoucherStatusIcon

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getTimeUntilDeadline = (deadline: string) => {
    const now = new Date()
    const deadlineDate = new Date(deadline)
    const diffMs = deadlineDate.getTime() - now.getTime()
    const diffHours = Math.ceil(diffMs / (1000 * 60 * 60))
    
    if (diffHours <= 0) return 'Expired'
    if (diffHours < 24) return `${diffHours}h left`
    const diffDays = Math.ceil(diffHours / 24)
    return `${diffDays}d left`
  }

  const getTimeSinceEvent = (dateString: string) => {
    const now = new Date()
    const eventDate = new Date(dateString)
    const diffMs = now.getTime() - eventDate.getTime()
    const diffHours = Math.ceil(diffMs / (1000 * 60 * 60))
    
    if (diffHours < 1) return 'Just now'
    if (diffHours < 24) return `${diffHours}h ago`
    const diffDays = Math.ceil(diffHours / 24)
    return `${diffDays}d ago`
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {voucher.voucher_type === 'purchase' ? (
              <ShoppingCart className="h-5 w-5 text-blue-600" />
            ) : (
              <Package className="h-5 w-5 text-green-600" />
            )}
            {voucher.voucher_number} - {voucher.voucher_type === 'purchase' ? 'Purchase' : 'Issuance'} Voucher
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Status and Basic Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                {getStatusIcon(voucher.status)}
                Voucher Status & Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Status</Label>
                  <div className="mt-1">
                    <Badge className={getStatusColor(voucher.status)}>
                      {voucher.status.replace('_', ' ')}
                    </Badge>
                  </div>
                </div>
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Type</Label>
                  <div className="mt-1">
                    <Badge variant="outline" className={
                      voucher.voucher_type === 'purchase' ? 'text-blue-600' : 'text-green-600'
                    }>
                      {voucher.voucher_type === 'purchase' ? 'Purchase' : 'Issuance'}
                    </Badge>
                  </div>
                </div>
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Amount</Label>
                  <p className="text-lg font-semibold flex items-center gap-1">
                    <DollarSign className="h-4 w-4" />
                    {formatCurrency(voucher.total_estimated_cost)}
                  </p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Requested By</Label>
                  <p className="flex items-center gap-1">
                    <User className="h-4 w-4" />
                    {voucher.requested_by_user?.full_name || 'Unknown'}
                  </p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Requested Date</Label>
                  <p className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {formatDate(voucher.requested_date)}
                  </p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Created</Label>
                  <p className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {formatDateTime(voucher.created_at)}
                  </p>
                </div>
              </div>

              {voucher.description && (
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Description</Label>
                  <p className="mt-1">{voucher.description}</p>
                </div>
              )}

              {voucher.notes && (
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Notes</Label>
                  <p className="mt-1">{voucher.notes}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Purchase Details */}
          {voucher.voucher_type === 'purchase' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Purchase Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">Vendor</Label>
                    <p>{voucher.vendor_name || 'Not specified'}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">Contact</Label>
                    <p>{voucher.vendor_contact || 'Not specified'}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">PO Number</Label>
                    <p>{voucher.purchase_order_number || 'Not specified'}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">Expected Delivery</Label>
                    <p>{voucher.expected_delivery_date ? formatDate(voucher.expected_delivery_date) : 'Not specified'}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">Payment Type</Label>
                    <p className="capitalize">{voucher.payment_type.replace('_', ' ')}</p>
                  </div>
                  {voucher.deposit_amount && voucher.deposit_amount > 0 && (
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">Deposit Amount</Label>
                      <p>{formatCurrency(voucher.deposit_amount)}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Issuance Details */}
          {voucher.voucher_type === 'issuance' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Issuance Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Purpose</Label>
                  <p className="mt-1">{voucher.purpose || 'Not specified'}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">Destination</Label>
                    <p>{voucher.destination || 'Not specified'}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">Cost Center</Label>
                    <p>{voucher.cost_center || 'Not specified'}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">Project Code</Label>
                    <p>{voucher.project_code || 'Not specified'}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">Destination Account</Label>
                    <p>{voucher.destination_account?.name || 'Not specified'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Line Items */}
          {voucher.lines && voucher.lines.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Line Items</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Item</TableHead>
                      <TableHead>SKU</TableHead>
                      <TableHead>Quantity Requested</TableHead>
                      <TableHead>Quantity Approved</TableHead>
                      <TableHead>Quantity Actual</TableHead>
                      <TableHead>Unit Cost</TableHead>
                      <TableHead>Total Cost</TableHead>
                      <TableHead>Notes</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {voucher.lines.map((line, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-medium">
                          {line.item?.name || 'Unknown Item'}
                        </TableCell>
                        <TableCell>{line.item?.sku || '-'}</TableCell>
                        <TableCell>{line.quantity_requested}</TableCell>
                        <TableCell>{line.quantity_approved || '-'}</TableCell>
                        <TableCell>{line.quantity_actual || '-'}</TableCell>
                        <TableCell>
                          {line.unit_cost_estimated ? formatCurrency(line.unit_cost_estimated) : '-'}
                        </TableCell>
                        <TableCell className="font-medium">
                          {formatCurrency(line.total_cost)}
                        </TableCell>
                        <TableCell>{line.notes || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {/* Approval Timeline */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Approval Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Submitted */}
                {voucher.submitted_at && (
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-yellow-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Clock className="h-3 w-3 text-yellow-600" />
                    </div>
                    <div>
                      <p className="font-medium">Submitted for Approval</p>
                      <p className="text-sm text-muted-foreground">
                        {formatDateTime(voucher.submitted_at)} ({getTimeSinceEvent(voucher.submitted_at)})
                      </p>
                      {voucher.approval_deadline && (
                        <p className="text-sm text-muted-foreground">
                          Deadline: {formatDateTime(voucher.approval_deadline)} ({getTimeUntilDeadline(voucher.approval_deadline)})
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {/* Approved */}
                {voucher.finance_approved_at && (
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    </div>
                    <div>
                      <p className="font-medium">Approved by Finance</p>
                      <p className="text-sm text-muted-foreground">
                        {voucher.finance_approved_by_user?.full_name || 'Unknown'} • 
                        {formatDateTime(voucher.finance_approved_at)} ({getTimeSinceEvent(voucher.finance_approved_at)})
                      </p>
                      {voucher.finance_approval_notes && (
                        <p className="text-sm text-muted-foreground mt-1">
                          Notes: {voucher.finance_approval_notes}
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {/* Rejected */}
                {voucher.rejected_at && (
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <XCircle className="h-3 w-3 text-red-600" />
                    </div>
                    <div>
                      <p className="font-medium">Rejected</p>
                      <p className="text-sm text-muted-foreground">
                        {voucher.rejected_by_user?.full_name || 'Unknown'} • 
                        {formatDateTime(voucher.rejected_at)} ({getTimeSinceEvent(voucher.rejected_at)})
                      </p>
                      {voucher.rejection_reason && (
                        <p className="text-sm text-muted-foreground mt-1">
                          Reason: {voucher.rejection_reason}
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {/* Executed */}
                {voucher.executed_at && (
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-primary-container/50 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <FileText className="h-3 w-3 text-on-primary-container" />
                    </div>
                    <div>
                      <p className="font-medium">Executed</p>
                      <p className="text-sm text-muted-foreground">
                        {voucher.executed_by_user?.full_name || 'Unknown'} • 
                        {formatDateTime(voucher.executed_at)} ({getTimeSinceEvent(voucher.executed_at)})
                      </p>
                    </div>
                  </div>
                )}

                {/* Expired */}
                {voucher.expired_at && (
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <AlertTriangle className="h-3 w-3 text-red-600" />
                    </div>
                    <div>
                      <p className="font-medium">Expired</p>
                      <p className="text-sm text-muted-foreground">
                        {formatDateTime(voucher.expired_at)} ({getTimeSinceEvent(voucher.expired_at)})
                      </p>
                      {voucher.renewal_count > 0 && (
                        <p className="text-sm text-muted-foreground">
                          Renewed {voucher.renewal_count} time(s)
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Attachments */}
          {voucher.attachments && voucher.attachments.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Attachments</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {voucher.attachments.map((attachment) => (
                    <div key={attachment.id} className="flex items-center gap-2 p-2 border rounded">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <div className="flex-1">
                        <p className="font-medium">{attachment.file_name}</p>
                        <p className="text-sm text-muted-foreground">
                          {attachment.file_size && `${(attachment.file_size / 1024).toFixed(1)} KB`} • 
                          Uploaded {formatDateTime(attachment.uploaded_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

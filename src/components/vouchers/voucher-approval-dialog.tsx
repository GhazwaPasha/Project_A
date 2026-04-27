'use client'

import React, { useState } from 'react'
import { InventoryVoucher } from '@/types'
import { useApproveVoucher, useRejectVoucher } from '@/hooks/use-vouchers'
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogFooter 
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
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
  CheckCircle, 
  XCircle, 
  DollarSign, 
  User, 
  Calendar,
  Clock,
  AlertTriangle
} from 'lucide-react'
import { useOrganizationFormatters } from '@/hooks/use-organization-formatters'

interface VoucherApprovalDialogProps {
  voucher: InventoryVoucher
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}

export function VoucherApprovalDialog({ 
  voucher, 
  open, 
  onOpenChange, 
  onSuccess 
}: VoucherApprovalDialogProps) {
  const [action, setAction] = useState<'approve' | 'reject' | null>(null)
  const [comments, setComments] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const approveVoucher = useApproveVoucher()
  const rejectVoucher = useRejectVoucher()
  const { formatCurrency } = useOrganizationFormatters()

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

  const handleSubmit = async () => {
    if (!action) return

    setIsSubmitting(true)
    try {
      if (action === 'approve') {
        await approveVoucher.mutateAsync({
          id: voucher.id,
          notes: comments.trim() || undefined
        })
      } else {
        if (!comments.trim()) {
          alert('Please provide a reason for rejection')
          return
        }
        await rejectVoucher.mutateAsync({
          id: voucher.id,
          reason: comments.trim()
        })
      }
      onSuccess()
    } catch (error) {
      console.error('Error processing voucher:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    setAction(null)
    setComments('')
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {action === 'approve' ? (
              <CheckCircle className="h-5 w-5 text-green-600" />
            ) : action === 'reject' ? (
              <XCircle className="h-5 w-5 text-red-600" />
            ) : (
              <AlertTriangle className="h-5 w-5 text-yellow-600" />
            )}
            {action ? `${action === 'approve' ? 'Approve' : 'Reject'} Voucher` : 'Review Voucher'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Voucher Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Voucher Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Voucher Number</Label>
                  <p className="text-lg font-semibold">{voucher.voucher_number}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Type</Label>
                  <div className="flex items-center gap-2">
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
                  <Label className="text-sm font-medium text-muted-foreground">Deadline</Label>
                  <p className={`flex items-center gap-1 ${
                    voucher.approval_deadline && new Date(voucher.approval_deadline) < new Date() 
                      ? 'text-red-600' 
                      : 'text-yellow-600'
                  }`}>
                    <Clock className="h-4 w-4" />
                    {voucher.approval_deadline ? getTimeUntilDeadline(voucher.approval_deadline) : 'No deadline'}
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
                      <TableHead>Quantity</TableHead>
                      <TableHead>Unit Cost</TableHead>
                      <TableHead>Total</TableHead>
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

          {/* Action Selection */}
          {!action && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Choose Action</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4">
                  <Button
                    onClick={() => setAction('approve')}
                    className="bg-green-600 hover:bg-green-700 flex-1"
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Approve Voucher
                  </Button>
                  <Button
                    onClick={() => setAction('reject')}
                    variant="destructive"
                    className="flex-1"
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Reject Voucher
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Comments */}
          {action && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  {action === 'approve' ? 'Approval Comments' : 'Rejection Reason'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Label htmlFor="comments">
                    {action === 'approve' 
                      ? 'Add any comments about this approval (optional)'
                      : 'Please provide a reason for rejection (required)'
                    }
                  </Label>
                  <Textarea
                    id="comments"
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    placeholder={
                      action === 'approve' 
                        ? 'Add approval comments...'
                        : 'Explain why this voucher is being rejected...'
                    }
                    rows={4}
                  />
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          {action && (
            <Button 
              onClick={handleSubmit}
              disabled={isSubmitting || (action === 'reject' && !comments.trim())}
              className={
                action === 'approve' 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-red-600 hover:bg-red-700'
              }
            >
              {isSubmitting ? 'Processing...' : `${action === 'approve' ? 'Approve' : 'Reject'} Voucher`}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

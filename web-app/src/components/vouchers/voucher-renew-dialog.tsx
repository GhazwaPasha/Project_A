'use client'

import React, { useState } from 'react'
import { InventoryVoucher } from '@/types'
import { useRenewVoucher } from '@/hooks/use-vouchers'
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
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  RotateCcw, 
  AlertTriangle, 
  Clock,
  DollarSign,
  User,
  Calendar
} from 'lucide-react'

interface VoucherRenewDialogProps {
  voucher: InventoryVoucher
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}

export function VoucherRenewDialog({ 
  voucher, 
  open, 
  onOpenChange, 
  onSuccess 
}: VoucherRenewDialogProps) {
  const [renewalReason, setRenewalReason] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const renewVoucher = useRenewVoucher()

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

  const getTimeSinceExpiration = (expiredAt: string) => {
    const now = new Date()
    const expiredDate = new Date(expiredAt)
    const diffMs = now.getTime() - expiredDate.getTime()
    const diffHours = Math.ceil(diffMs / (1000 * 60 * 60))
    
    if (diffHours < 24) return `${diffHours}h ago`
    const diffDays = Math.ceil(diffHours / 24)
    return `${diffDays}d ago`
  }

  const handleSubmit = async () => {
    if (!renewalReason.trim()) {
      alert('Please provide a reason for renewal')
      return
    }

    setIsSubmitting(true)
    try {
      await renewVoucher.mutateAsync({
        id: voucher.id,
        reason: renewalReason.trim()
      })
      onSuccess()
    } catch (error) {
      console.error('Error renewing voucher:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    setRenewalReason('')
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RotateCcw className="h-5 w-5 text-primary" />
            Renew Expired Voucher
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Warning Alert */}
          <Alert className="border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              <strong>This voucher has expired.</strong> Renewing it will reset it to draft status 
              and you'll need to resubmit it for approval. The inventory items will become visible again.
            </AlertDescription>
          </Alert>

          {/* Voucher Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Expired Voucher Details</CardTitle>
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
                      voucher.voucher_type === 'purchase' ? 'text-primary' : 'text-tertiary'
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
                  <Label className="text-sm font-medium text-muted-foreground">Original Deadline</Label>
                  <p className="flex items-center gap-1 text-red-600">
                    <Clock className="h-4 w-4" />
                    {voucher.approval_deadline ? formatDateTime(voucher.approval_deadline) : 'Unknown'}
                  </p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Expired</Label>
                  <p className="flex items-center gap-1 text-red-600">
                    <AlertTriangle className="h-4 w-4" />
                    {voucher.expired_at ? getTimeSinceExpiration(voucher.expired_at) : 'Unknown'}
                  </p>
                </div>
              </div>

              {voucher.description && (
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Description</Label>
                  <p className="mt-1">{voucher.description}</p>
                </div>
              )}

              {/* Renewal History */}
              {voucher.renewal_count > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-yellow-800">
                    <RotateCcw className="h-4 w-4" />
                    <span className="font-medium">Renewal History</span>
                  </div>
                  <p className="text-sm text-yellow-700 mt-1">
                    This voucher has been renewed {voucher.renewal_count} time(s) before.
                    {voucher.renewal_reason && (
                      <span className="block mt-1">
                        Last reason: {voucher.renewal_reason}
                      </span>
                    )}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Renewal Reason */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Renewal Reason</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="renewal-reason">
                  Please explain why you want to renew this voucher:
                </Label>
                <Textarea
                  id="renewal-reason"
                  value={renewalReason}
                  onChange={(e) => setRenewalReason(e.target.value)}
                  placeholder="e.g., The vendor was delayed but we still need these items, or The project requirements changed..."
                  rows={4}
                />
                <p className="text-sm text-muted-foreground">
                  This reason will be recorded in the voucher history.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* What Happens Next */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">What Happens Next</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-primary-container/50 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-on-primary-container font-medium text-xs">1</span>
                  </div>
                  <div>
                    <p className="font-medium">Voucher Reset to Draft</p>
                    <p className="text-muted-foreground">
                      The voucher status will be reset to "Draft" and you can edit it if needed.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-primary-container/50 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-on-primary-container font-medium text-xs">2</span>
                  </div>
                  <div>
                    <p className="font-medium">Inventory Items Restored</p>
                    <p className="text-muted-foreground">
                      All inventory items related to this voucher will become visible again.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-primary-container/50 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-on-primary-container font-medium text-xs">3</span>
                  </div>
                  <div>
                    <p className="font-medium">Resubmit for Approval</p>
                    <p className="text-muted-foreground">
                      You'll need to resubmit the voucher for approval with a new 48-hour deadline.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit}
            disabled={isSubmitting || !renewalReason.trim()}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isSubmitting ? 'Renewing...' : 'Renew Voucher'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

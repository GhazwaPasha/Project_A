'use client'

import React, { useState } from 'react'
import { InventoryVoucher } from '@/types'
import { 
  useVoucherStatusColor, 
  useVoucherStatusIcon,
  useApproveVoucher,
  useRejectVoucher,
  useRenewVoucher,
  useDeleteVoucher,
  useSubmitForApproval
} from '@/hooks/use-vouchers'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { 
  MoreHorizontal, 
  Eye, 
  Edit, 
  Trash2, 
  Check, 
  X, 
  RotateCcw,
  Clock,
  AlertTriangle,
  Send,
  FileText,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { VoucherApprovalDialog } from './voucher-approval-dialog'
import { VoucherRenewDialog } from './voucher-renew-dialog'
import { VoucherViewDialog } from './voucher-view-dialog'

interface VoucherListProps {
  vouchers: InventoryVoucher[]
  isLoading?: boolean
  showActions?: boolean
  showApprovalActions?: boolean
  showRenewActions?: boolean
  showViewActions?: boolean
  organizationId?: string
  compact?: boolean
}

export function VoucherList({ 
  vouchers, 
  isLoading = false,
  showActions = true,
  showApprovalActions = false,
  showRenewActions = false,
  showViewActions = false,
  compact = false,
  organizationId = ''
}: VoucherListProps) {
  const safeVouchers = vouchers ?? []
  const [selectedVoucher, setSelectedVoucher] = useState<InventoryVoucher | null>(null)
  const [showApprovalDialog, setShowApprovalDialog] = useState(false)
  const [showRenewDialog, setShowRenewDialog] = useState(false)
  const [showViewDialog, setShowViewDialog] = useState(false)

  const getStatusColor = useVoucherStatusColor
  const getStatusIcon = useVoucherStatusIcon

  // Mutations
  const approveVoucher = useApproveVoucher()
  const rejectVoucher = useRejectVoucher()
  const renewVoucher = useRenewVoucher()
  const deleteVoucher = useDeleteVoucher()
  const submitForApproval = useSubmitForApproval(organizationId)

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
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

  const handleApprove = (voucher: InventoryVoucher) => {
    setSelectedVoucher(voucher)
    setShowApprovalDialog(true)
  }

  const handleReject = (voucher: InventoryVoucher) => {
    setSelectedVoucher(voucher)
    setShowApprovalDialog(true)
  }

  const handleSubmitForApproval = async (voucher: InventoryVoucher) => {
    try {
      await submitForApproval.mutateAsync(voucher.id)
      // The mutation will automatically refresh the data
    } catch (error) {
      console.error('Error submitting for approval:', error)
    }
  }

  const handleRenew = (voucher: InventoryVoucher) => {
    setSelectedVoucher(voucher)
    setShowRenewDialog(true)
  }

  const handleView = (voucher: InventoryVoucher) => {
    setSelectedVoucher(voucher)
    setShowViewDialog(true)
  }

  const handleDelete = async (voucher: InventoryVoucher) => {
    if (window.confirm(`Are you sure you want to delete voucher ${voucher.voucher_number}?`)) {
      try {
        await deleteVoucher.mutateAsync(voucher.id)
      } catch (error) {
        console.error('Error deleting voucher:', error)
      }
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-6">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (safeVouchers.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium">No vouchers found</p>
            <p className="text-sm">Create your first voucher to get started</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (compact) {
    return (
      <div className="space-y-2">
        {safeVouchers.map((voucher) => (
          <Card key={voucher.id} className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="text-lg">{getStatusIcon(voucher.status)}</div>
                <div>
                  <div className="font-medium">{voucher.voucher_number}</div>
                  <div className="text-sm text-muted-foreground">
                    {voucher.voucher_type === 'purchase' ? 'Purchase' : 'Issuance'} • 
                    {formatCurrency(voucher.total_estimated_cost)} • 
                    {formatDate(voucher.requested_date)}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge className={getStatusColor(voucher.status)}>
                  {voucher.status.replace('_', ' ')}
                </Badge>
                {showViewActions && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleView(voucher)}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <>
      <div className="space-y-4">
        {safeVouchers.map((voucher) => (
          <Card key={voucher.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="text-2xl">{getStatusIcon(voucher.status)}</div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold">{voucher.voucher_number}</h3>
                      <Badge className={getStatusColor(voucher.status)}>
                        {voucher.status.replace('_', ' ')}
                      </Badge>
                      {voucher.voucher_type === 'purchase' ? (
                        <Badge variant="outline" className="text-blue-600">
                          Purchase
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-green-600">
                          Issuance
                        </Badge>
                      )}
                    </div>
                    
                    <div className="text-sm text-muted-foreground">
                      <div className="flex items-center gap-4">
                        <span>
                          <strong>Amount:</strong> {formatCurrency(voucher.total_estimated_cost)}
                        </span>
                        <span>
                          <strong>Requested:</strong> {formatDate(voucher.requested_date)}
                        </span>
                        <span>
                          <strong>By:</strong> {voucher.requested_by_user?.full_name || 'Unknown'}
                        </span>
                      </div>
                      
                      {voucher.voucher_type === 'purchase' && voucher.vendor_name && (
                        <div className="mt-1">
                          <strong>Vendor:</strong> {voucher.vendor_name}
                        </div>
                      )}
                      
                      {voucher.voucher_type === 'issuance' && voucher.purpose && (
                        <div className="mt-1">
                          <strong>Purpose:</strong> {voucher.purpose}
                        </div>
                      )}
                      
                      {voucher.description && (
                        <div className="mt-1">
                          <strong>Description:</strong> {voucher.description}
                        </div>
                      )}
                    </div>

                    {/* Deadline warning */}
                    {voucher.approval_deadline && voucher.status === 'pending_finance' && (
                      <div className="flex items-center gap-2 mt-2">
                        <Clock className="h-4 w-4 text-yellow-600" />
                        <span className="text-sm text-yellow-700">
                          {getTimeUntilDeadline(voucher.approval_deadline)}
                        </span>
                      </div>
                    )}

                    {/* Expiration info */}
                    {voucher.status === 'expired' && voucher.expired_at && (
                      <div className="flex items-center gap-2 mt-2">
                        <AlertTriangle className="h-4 w-4 text-red-600" />
                        <span className="text-sm text-red-700">
                          Expired {formatDateTime(voucher.expired_at)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  {showViewActions && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleView(voucher)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  )}

                  {showApprovalActions && voucher.status === 'pending_finance' && (
                    <>
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => handleApprove(voucher)}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        <Check className="h-4 w-4 mr-1" />
                        Approve
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleReject(voucher)}
                      >
                        <X className="h-4 w-4 mr-1" />
                        Reject
                      </Button>
                    </>
                  )}

                  {showRenewActions && voucher.status === 'expired' && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRenew(voucher)}
                    >
                      <RotateCcw className="h-4 w-4 mr-1" />
                      Renew
                    </Button>
                  )}

                  {showActions && (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleView(voucher)}>
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        
                        {voucher.status === 'draft' && (
                          <>
                            <DropdownMenuItem>
                              <Edit className="h-4 w-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              onClick={() => handleSubmitForApproval(voucher)}
                              className="text-blue-600"
                            >
                              <Send className="h-4 w-4 mr-2" />
                              Submit for Approval
                            </DropdownMenuItem>
                          </>
                        )}

                        {voucher.status === 'pending_finance' && (
                          <>
                            <DropdownMenuItem 
                              onClick={() => handleApprove(voucher)}
                              className="text-green-600"
                            >
                              <CheckCircle className="h-4 w-4 mr-2" />
                              Approve
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              onClick={() => handleReject(voucher)}
                              className="text-red-600"
                            >
                              <XCircle className="h-4 w-4 mr-2" />
                              Reject
                            </DropdownMenuItem>
                          </>
                        )}
                        
                        {voucher.status === 'expired' && (
                          <DropdownMenuItem onClick={() => handleRenew(voucher)}>
                            <RotateCcw className="h-4 w-4 mr-2" />
                            Renew
                          </DropdownMenuItem>
                        )}
                        
                        {voucher.status === 'draft' && (
                          <DropdownMenuItem 
                            onClick={() => handleDelete(voucher)}
                            className="text-red-600"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Dialogs */}
      {selectedVoucher && (
        <>
          <VoucherApprovalDialog
            voucher={selectedVoucher}
            open={showApprovalDialog}
            onOpenChange={setShowApprovalDialog}
            onSuccess={() => {
              setShowApprovalDialog(false)
              setSelectedVoucher(null)
            }}
          />
          
          <VoucherRenewDialog
            voucher={selectedVoucher}
            open={showRenewDialog}
            onOpenChange={setShowRenewDialog}
            onSuccess={() => {
              setShowRenewDialog(false)
              setSelectedVoucher(null)
            }}
          />
          
          <VoucherViewDialog
            voucher={selectedVoucher}
            open={showViewDialog}
            onOpenChange={setShowViewDialog}
          />
        </>
      )}
    </>
  )
}

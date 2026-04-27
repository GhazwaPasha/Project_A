'use client'

import React from 'react'
import { InventoryVoucher } from '@/types'
import { useVoucherStatusColor, useVoucherStatusIcon } from '@/hooks/use-vouchers'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Clock, 
  DollarSign, 
  User, 
  Calendar,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react'

interface VoucherApprovalDashboardProps {
  vouchers: InventoryVoucher[]
}

export function VoucherApprovalDashboard({ vouchers }: VoucherApprovalDashboardProps) {
  const getStatusColor = useVoucherStatusColor
  const getStatusIcon = useVoucherStatusIcon

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

  const getPriority = (voucher: InventoryVoucher) => {
    const now = new Date()
    const deadline = new Date(voucher.approval_deadline!)
    const diffHours = (deadline.getTime() - now.getTime()) / (1000 * 60 * 60)
    
    if (diffHours <= 0) return 'expired'
    if (diffHours <= 6) return 'urgent'
    if (diffHours <= 24) return 'high'
    if (voucher.total_estimated_cost > 10000) return 'high'
    return 'normal'
  }

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      expired: 'text-on-error-container bg-error-container/50',
      urgent: 'text-on-error-container bg-error-container/50',
      high: 'text-on-tertiary-container bg-tertiary-container/50',
      normal: 'text-on-primary-container bg-primary-container/50'
    }
    return colors[priority] || 'text-on-surface-variant bg-surface-container-highest'
  }

  const getPriorityIcon = (priority: string) => {
    const icons: Record<string, React.ReactNode> = {
      expired: <AlertTriangle className="h-4 w-4" />,
      urgent: <AlertTriangle className="h-4 w-4" />,
      high: <Clock className="h-4 w-4" />,
      normal: <Clock className="h-4 w-4" />
    }
    return icons[priority] || <Clock className="h-4 w-4" />
  }

  if (vouchers.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <CheckCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p className="text-lg font-medium">No pending approvals</p>
        <p className="text-sm">All vouchers have been processed</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {vouchers.map((voucher) => {
        const priority = getPriority(voucher)
        const isExpired = priority === 'expired'
        
        return (
          <Card 
            key={voucher.id} 
            className={`transition-all hover:shadow-md ${
              isExpired ? 'border-red-200 bg-red-50' : 
              priority === 'urgent' ? 'border-red-200 bg-red-50' :
              priority === 'high' ? 'border-orange-200 bg-orange-50' : 
              'border-yellow-200 bg-yellow-50'
            }`}
          >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="text-2xl">{getStatusIcon(voucher.status)}</div>
                  
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold">{voucher.voucher_number}</h3>
                      <Badge className={getStatusColor(voucher.status)}>
                        {voucher.status.replace('_', ' ')}
                      </Badge>
                      <Badge className={getPriorityColor(priority)}>
                        {getPriorityIcon(priority)}
                        <span className="ml-1 capitalize">{priority}</span>
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
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div className="flex items-center gap-2">
                        <DollarSign className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">
                          {formatCurrency(voucher.total_estimated_cost)}
                        </span>
                        {voucher.total_estimated_cost > 10000 && (
                          <Badge variant="outline" className="text-orange-600">
                            Large Amount
                          </Badge>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span>{voucher.requested_by_user?.full_name || 'Unknown'}</span>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span>Submitted {formatDate(voucher.requested_date)}</span>
                      </div>
                    </div>

                    {/* Description */}
                    {voucher.description && (
                      <div className="text-sm text-muted-foreground">
                        <strong>Description:</strong> {voucher.description}
                      </div>
                    )}

                    {/* Purchase details */}
                    {voucher.voucher_type === 'purchase' && voucher.vendor_name && (
                      <div className="text-sm text-muted-foreground">
                        <strong>Vendor:</strong> {voucher.vendor_name}
                        {voucher.vendor_contact && ` (${voucher.vendor_contact})`}
                      </div>
                    )}

                    {/* Issuance details */}
                    {voucher.voucher_type === 'issuance' && voucher.purpose && (
                      <div className="text-sm text-muted-foreground">
                        <strong>Purpose:</strong> {voucher.purpose}
                        {voucher.destination && ` → ${voucher.destination}`}
                      </div>
                    )}

                    {/* Line items summary */}
                    {voucher.lines && voucher.lines.length > 0 && (
                      <div className="text-sm text-muted-foreground">
                        <strong>Items:</strong> {voucher.lines.length} line(s)
                        {voucher.lines.slice(0, 2).map((line, index) => (
                          <span key={index}>
                            {index > 0 && ', '}
                            {line.item?.name} ({line.quantity_requested} units)
                          </span>
                        ))}
                        {voucher.lines.length > 2 && ` and ${voucher.lines.length - 2} more...`}
                      </div>
                    )}

                    {/* Deadline warning */}
                    {voucher.approval_deadline && (
                      <div className={`flex items-center gap-2 ${
                        isExpired ? 'text-red-700' : 
                        priority === 'urgent' ? 'text-red-700' :
                        priority === 'high' ? 'text-orange-700' : 
                        'text-yellow-700'
                      }`}>
                        <Clock className="h-4 w-4" />
                        <span className="font-medium">
                          {isExpired ? 'EXPIRED' : getTimeUntilDeadline(voucher.approval_deadline)}
                        </span>
                        <span className="text-xs">
                          (Deadline: {formatDateTime(voucher.approval_deadline)})
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex items-center gap-2">
                  <Button
                    variant="default"
                    size="sm"
                    className="bg-green-600 hover:bg-green-700"
                    onClick={() => {
                      // This would open the approval dialog
                      console.log('Approve voucher:', voucher.id)
                    }}
                  >
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Quick Approve
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      // This would open the detailed approval dialog
                      console.log('View details for voucher:', voucher.id)
                    }}
                  >
                    View Details
                  </Button>
                  
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => {
                      // This would open the rejection dialog
                      console.log('Reject voucher:', voucher.id)
                    }}
                  >
                    <XCircle className="h-4 w-4 mr-1" />
                    Reject
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}

'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { 
  Search, 
  Filter, 
  Download,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Calendar,
  User,
  Flag,
  Eye,
  ChevronRight,
  MoreVertical,
  ShoppingCart,
  Package,
  DollarSign,
  FileText,
  CheckSquare
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { useOrganization } from '@/hooks/use-organization'
import { 
  useVouchers, 
  useVoucherStats, 
  usePendingApprovals, 
  useExpiredVouchers,
  useApproveVoucher,
  useRejectVoucher,
  useRenewVoucher
} from '@/hooks/use-vouchers'
import { VoucherApprovalDialog } from '@/components/vouchers/voucher-approval-dialog'
import { VoucherRenewDialog } from '@/components/vouchers/voucher-renew-dialog'
import { VoucherViewDialog } from '@/components/vouchers/voucher-view-dialog'
import { InventoryVoucher } from '@/types'

export function Win11ApprovalsPage() {
  const { currentOrganization } = useOrganization()
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterType, setFilterType] = useState('all')
  const [selectedVoucher, setSelectedVoucher] = useState<InventoryVoucher | null>(null)
  const [showApprovalDialog, setShowApprovalDialog] = useState(false)
  const [showRenewDialog, setShowRenewDialog] = useState(false)
  const [showViewDialog, setShowViewDialog] = useState(false)

  // Fetch data
  const { data: vouchers = [], isLoading: vouchersLoading } = useVouchers()
  const { data: stats } = useVoucherStats()
  const { data: pendingApprovals = [] } = usePendingApprovals()
  const { data: expiredVouchers = [] } = useExpiredVouchers()

  // Debug logging
  useEffect(() => {
    console.log('Approvals Page - Debug Info:')
    console.log('Current Organization:', currentOrganization?.id)
    console.log('Vouchers:', vouchers)
    console.log('Vouchers Loading:', vouchersLoading)
    console.log('Pending Approvals:', pendingApprovals)
    console.log('Expired Vouchers:', expiredVouchers)
  }, [currentOrganization, vouchers, vouchersLoading, pendingApprovals, expiredVouchers])

  // Mutations
  const approveVoucher = useApproveVoucher()
  const rejectVoucher = useRejectVoucher()
  const renewVoucher = useRenewVoucher()

  const filteredVouchers = vouchers.filter(voucher => {
    const matchesSearch = voucher.voucher_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         voucher.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         voucher.vendor_name?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = filterStatus === 'all' || voucher.status === filterStatus
    const matchesType = filterType === 'all' || voucher.voucher_type === filterType
    return matchesSearch && matchesStatus && matchesType
  })

  // Debug filtered results
  useEffect(() => {
    console.log('Filtered Vouchers:', filteredVouchers)
    console.log('Filter Status:', filterStatus)
    console.log('Filter Type:', filterType)
    console.log('Search Term:', searchTerm)
  }, [filteredVouchers, filterStatus, filterType, searchTerm])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'text-gray-600 bg-gray-50'
      case 'pending_finance': return 'text-orange-600 bg-orange-50'
      case 'approved': return 'text-green-600 bg-green-50'
      case 'receiving': return 'text-blue-600 bg-blue-50'
      case 'issuing': return 'text-blue-600 bg-blue-50'
      case 'posted': return 'text-purple-600 bg-purple-50'
      case 'completed': return 'text-green-600 bg-green-50'
      case 'rejected': return 'text-red-600 bg-red-50'
      case 'expired': return 'text-red-600 bg-red-50'
      case 'cancelled': return 'text-gray-600 bg-gray-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'draft': return <FileText className="w-4 h-4" />
      case 'pending_finance': return <Clock className="w-4 h-4" />
      case 'approved': return <CheckCircle className="w-4 h-4" />
      case 'receiving': return <Package className="w-4 h-4" />
      case 'issuing': return <Package className="w-4 h-4" />
      case 'posted': return <CheckSquare className="w-4 h-4" />
      case 'completed': return <CheckCircle className="w-4 h-4" />
      case 'rejected': return <XCircle className="w-4 h-4" />
      case 'expired': return <AlertTriangle className="w-4 h-4" />
      case 'cancelled': return <XCircle className="w-4 h-4" />
      default: return <FileText className="w-4 h-4" />
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'purchase': return <ShoppingCart className="w-4 h-4" />
      case 'issuance': return <Package className="w-4 h-4" />
      default: return <FileText className="w-4 h-4" />
    }
  }

  const getPriorityColor = (voucher: InventoryVoucher) => {
    if (voucher.status === 'expired') return 'text-red-600 bg-red-50'
    if (voucher.status === 'pending_finance') {
      const deadline = new Date(voucher.approval_deadline || '')
      const now = new Date()
      const hoursLeft = (deadline.getTime() - now.getTime()) / (1000 * 60 * 60)
      
      if (hoursLeft < 0) return 'text-red-600 bg-red-50' // Overdue
      if (hoursLeft < 24) return 'text-orange-600 bg-orange-50' // Due soon
      if (hoursLeft < 48) return 'text-yellow-600 bg-yellow-50' // Due in 2 days
      return 'text-green-600 bg-green-50' // Plenty of time
    }
    return 'text-gray-600 bg-gray-50'
  }

  const getPriorityText = (voucher: InventoryVoucher) => {
    if (voucher.status === 'expired') return 'Expired'
    if (voucher.status === 'pending_finance') {
      const deadline = new Date(voucher.approval_deadline || '')
      const now = new Date()
      const hoursLeft = (deadline.getTime() - now.getTime()) / (1000 * 60 * 60)
      
      if (hoursLeft < 0) return 'Overdue'
      if (hoursLeft < 24) return 'Due Soon'
      if (hoursLeft < 48) return 'Due in 2 Days'
      return 'On Track'
    }
    return 'Normal'
  }

  const handleApprove = (voucher: InventoryVoucher) => {
    setSelectedVoucher(voucher)
    setShowApprovalDialog(true)
  }

  const handleReject = (voucher: InventoryVoucher) => {
    setSelectedVoucher(voucher)
    setShowApprovalDialog(true)
  }

  const handleRenew = (voucher: InventoryVoucher) => {
    setSelectedVoucher(voucher)
    setShowRenewDialog(true)
  }

  const handleView = (voucher: InventoryVoucher) => {
    setSelectedVoucher(voucher)
    setShowViewDialog(true)
  }

  const renderVoucherCard = (voucher: InventoryVoucher) => {
    return (
      <Card 
        key={voucher.id}
        className="md-card-expressive group hover:md-elevation-1 transition-all duration-200 cursor-pointer"
        onClick={() => handleView(voucher)}
      >
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-primary-container rounded-xl flex items-center justify-center">
                {getTypeIcon(voucher.voucher_type)}
              </div>
              <div>
                <h3 className="md-title-medium text-on-surface">{voucher.voucher_number}</h3>
                <p className="md-body-small text-on-surface-variant">
                  {voucher.voucher_type === 'purchase' ? 'Purchase Voucher' : 'Issuance Voucher'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium ${getPriorityColor(voucher)}`}>
                {getPriorityText(voucher)}
              </span>
              <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium ${getStatusColor(voucher.status)}`}>
                {voucher.status.replace('_', ' ')}
              </span>
            </div>
          </div>
          
          <p className="md-body-medium text-on-surface-variant mb-4">
            {voucher.description || 'No description provided'}
          </p>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-on-surface-variant">Amount</span>
              <span className="text-on-surface font-medium">{formatCurrency(voucher.total_estimated_cost || 0)}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-on-surface-variant">Requested</span>
              <span className="text-on-surface">{formatDate(voucher.requested_date)}</span>
            </div>
            {voucher.approval_deadline && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-on-surface-variant">Deadline</span>
                <span className={`font-medium ${getPriorityColor(voucher)}`}>
                  {formatDate(voucher.approval_deadline)}
                </span>
              </div>
            )}
            {voucher.vendor_name && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-on-surface-variant">Vendor</span>
                <span className="text-on-surface">{voucher.vendor_name}</span>
              </div>
            )}
          </div>
          
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-outline-variant">
            <div className="flex items-center space-x-1">
              <button 
                className="p-1 hover:bg-surface-container-highest rounded"
                onClick={(e) => {
                  e.stopPropagation()
                  handleView(voucher)
                }}
              >
                <Eye className="w-4 h-4" />
              </button>
              {voucher.status === 'pending_finance' && (
                <>
                  <button 
                    className="p-1 hover:bg-surface-container-highest rounded text-green-600"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleApprove(voucher)
                    }}
                  >
                    <CheckCircle className="w-4 h-4" />
                  </button>
                  <button 
                    className="p-1 hover:bg-surface-container-highest rounded text-red-600"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleReject(voucher)
                    }}
                  >
                    <XCircle className="w-4 h-4" />
                  </button>
                </>
              )}
              {voucher.status === 'expired' && (
                <button 
                  className="p-1 hover:bg-surface-container-highest rounded text-blue-600"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleRenew(voucher)
                  }}
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              )}
            </div>
            <div className="flex items-center space-x-1">
              <button className="p-1 hover:bg-surface-container-highest rounded">
                <MoreVertical className="w-4 h-4" />
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
      {/* Fixed Header */}
      <div className="sticky top-0 z-30 backdrop-blur-sm border-b border-outline-variant" style={{ backgroundColor: 'var(--md-sys-color-surface)' }}>
        <div className="px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="md-headline-small text-on-background">Approvals</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                Review and approve pending vouchers and requests
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Button 
                onClick={() => window.location.reload()}
                variant="outline"
                className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Button variant="outline" className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
              <input
                type="text"
                placeholder="Search vouchers by number, description, or vendor..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-12 pl-12 pr-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                aria-label="Search vouchers"
              />
            </div>
            
            <div className="flex gap-3">
              <div className="relative">
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="h-12 pl-4 pr-12 py-3 bg-surface-container border border-outline rounded-2xl text-sm text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200 appearance-none cursor-pointer min-w-[140px]"
                >
                  <option value="all">All Status</option>
                  <option value="pending_finance">Pending Approval</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                  <option value="expired">Expired</option>
                </select>
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
                  <svg className="w-4 h-4 text-on-surface-variant" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
              <div className="relative">
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="h-12 pl-4 pr-12 py-3 bg-surface-container border border-outline rounded-2xl text-sm text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200 appearance-none cursor-pointer min-w-[140px]"
                >
                  <option value="all">All Types</option>
                  <option value="purchase">Purchase</option>
                  <option value="issuance">Issuance</option>
                </select>
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
                  <svg className="w-4 h-4 text-on-surface-variant" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
              <Button variant="outline" className="h-12 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container">
                <Filter className="w-4 h-4 mr-2" />
                Filter
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-6 py-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card className="md-card-expressive">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-on-surface-variant">Total Vouchers</p>
                  <p className="text-2xl font-bold text-on-surface">{vouchers.length}</p>
                </div>
                <FileText className="w-8 h-8 text-primary" />
              </div>
            </CardContent>
          </Card>
          <Card className="md-card-expressive">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-on-surface-variant">Pending Approval</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {pendingApprovals.length}
                  </p>
                </div>
                <Clock className="w-8 h-8 text-orange-600" />
              </div>
            </CardContent>
          </Card>
          <Card className="md-card-expressive">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-on-surface-variant">Approved</p>
                  <p className="text-2xl font-bold text-green-600">
                    {vouchers.filter(v => v.status === 'approved').length}
                  </p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
          <Card className="md-card-expressive">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-on-surface-variant">Expired</p>
                  <p className="text-2xl font-bold text-red-600">
                    {expiredVouchers.length}
                  </p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {vouchersLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : filteredVouchers.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-20 h-20 bg-primary-container rounded-3xl flex items-center justify-center mb-6">
              <CheckSquare className="w-10 h-10 text-on-primary-container" />
            </div>
            <h3 className="md-headline-small text-on-surface mb-3">No vouchers found</h3>
            <p className="md-body-large text-on-surface-variant text-center mb-8 max-w-md">
              {searchTerm || filterStatus !== 'all' || filterType !== 'all'
                ? 'Try adjusting your search or filter criteria.'
                : 'No vouchers have been created yet.'
              }
            </p>
          </div>
        ) : (
          /* Vouchers Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredVouchers.map(voucher => renderVoucherCard(voucher))}
          </div>
        )}
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
    </div>
  )
}

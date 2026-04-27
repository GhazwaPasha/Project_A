'use client'

import React from 'react'
import { VoucherStats } from '@/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  FileText, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  DollarSign,
  TrendingUp,
  Timer
} from 'lucide-react'

interface VoucherStatsCardsProps {
  stats: VoucherStats
}

export function VoucherStatsCards({ stats }: VoucherStatsCardsProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const formatHours = (hours: number) => {
    if (hours < 1) {
      return `${Math.round(hours * 60)}m`
    } else if (hours < 24) {
      return `${hours.toFixed(1)}h`
    } else {
      return `${(hours / 24).toFixed(1)}d`
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'text-yellow-600',
      approved: 'text-green-600',
      rejected: 'text-red-600',
      expired: 'text-red-600',
      completed: 'text-green-600',
    }
    return colors[status] || 'text-gray-600'
  }

  const getStatusIcon = (status: string) => {
    const icons: Record<string, React.ReactNode> = {
      pending: <Clock className="h-4 w-4" />,
      approved: <CheckCircle className="h-4 w-4" />,
      rejected: <XCircle className="h-4 w-4" />,
      expired: <AlertTriangle className="h-4 w-4" />,
      completed: <CheckCircle className="h-4 w-4" />,
    }
    return icons[status] || <FileText className="h-4 w-4" />
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Vouchers */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Vouchers</CardTitle>
          <FileText className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.total_vouchers}</div>
          <p className="text-xs text-muted-foreground">
            All time vouchers created
          </p>
        </CardContent>
      </Card>

      {/* Pending Approval */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
          <Clock className="h-4 w-4 text-yellow-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-yellow-600">
            {stats.pending_approval}
          </div>
          <p className="text-xs text-muted-foreground">
            Awaiting finance approval
          </p>
        </CardContent>
      </Card>

      {/* Approved */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Approved</CardTitle>
          <CheckCircle className="h-4 w-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">
            {stats.approved}
          </div>
          <p className="text-xs text-muted-foreground">
            Finance approved vouchers
          </p>
        </CardContent>
      </Card>

      {/* Completed */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Completed</CardTitle>
          <CheckCircle className="h-4 w-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">
            {stats.completed}
          </div>
          <p className="text-xs text-muted-foreground">
            Fully processed vouchers
          </p>
        </CardContent>
      </Card>

      {/* Total Value */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Value</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {formatCurrency(stats.total_value)}
          </div>
          <p className="text-xs text-muted-foreground">
            All vouchers combined
          </p>
        </CardContent>
      </Card>

      {/* Approval Rate */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Approval Rate</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {stats.approval_rate_percent.toFixed(1)}%
          </div>
          <p className="text-xs text-muted-foreground">
            Success rate
          </p>
        </CardContent>
      </Card>

      {/* Average Approval Time */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Approval Time</CardTitle>
          <Timer className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {formatHours(stats.average_approval_time_hours)}
          </div>
          <p className="text-xs text-muted-foreground">
            From submission to approval
          </p>
        </CardContent>
      </Card>

      {/* Status Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Status Breakdown</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getStatusIcon('pending')}
              <span className="text-sm">Pending</span>
            </div>
            <Badge variant="outline" className={getStatusColor('pending')}>
              {stats.pending_approval}
            </Badge>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getStatusIcon('approved')}
              <span className="text-sm">Approved</span>
            </div>
            <Badge variant="outline" className={getStatusColor('approved')}>
              {stats.approved}
            </Badge>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getStatusIcon('rejected')}
              <span className="text-sm">Rejected</span>
            </div>
            <Badge variant="outline" className={getStatusColor('rejected')}>
              {stats.rejected}
            </Badge>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getStatusIcon('expired')}
              <span className="text-sm">Expired</span>
            </div>
            <Badge variant="outline" className={getStatusColor('expired')}>
              {stats.expired}
            </Badge>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getStatusIcon('completed')}
              <span className="text-sm">Completed</span>
            </div>
            <Badge variant="outline" className={getStatusColor('completed')}>
              {stats.completed}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

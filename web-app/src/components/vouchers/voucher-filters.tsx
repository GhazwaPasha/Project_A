'use client'

import React from 'react'
import { VoucherFilters, VoucherType, VoucherStatus } from '@/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Calendar } from '@/components/ui/calendar'
import { 
  Popover, 
  PopoverContent, 
  PopoverTrigger 
} from '@/components/ui/popover'
import { CalendarIcon, Filter, X } from 'lucide-react'
import { format } from 'date-fns'

interface VoucherFiltersProps {
  filters: VoucherFilters
  onFiltersChange: (filters: VoucherFilters) => void
}

export function VoucherFilters({ filters, onFiltersChange }: VoucherFiltersProps) {
  const handleFilterChange = (key: keyof VoucherFilters, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value
    })
  }

  const handleStatusToggle = (status: VoucherStatus) => {
    const currentStatuses = filters.status || []
    const newStatuses = currentStatuses.includes(status)
      ? currentStatuses.filter(s => s !== status)
      : [...currentStatuses, status]
    
    handleFilterChange('status', newStatuses.length > 0 ? newStatuses : undefined)
  }

  const handleTypeToggle = (type: VoucherType) => {
    const currentTypes = filters.voucher_type || []
    const newTypes = currentTypes.includes(type)
      ? currentTypes.filter(t => t !== type)
      : [...currentTypes, type]
    
    handleFilterChange('voucher_type', newTypes.length > 0 ? newTypes : undefined)
  }

  const clearFilters = () => {
    onFiltersChange({})
  }

  const hasActiveFilters = Object.values(filters).some(value => 
    value !== undefined && value !== null && 
    (Array.isArray(value) ? value.length > 0 : true)
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Filter className="h-5 w-5" />
          Filters
          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearFilters}
              className="ml-auto"
            >
              <X className="h-4 w-4 mr-1" />
              Clear All
            </Button>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search */}
        <div className="space-y-2">
          <Label htmlFor="search">Search</Label>
          <Input
            id="search"
            placeholder="Search vouchers, vendors, purposes..."
            value={filters.search || ''}
            onChange={(e) => handleFilterChange('search', e.target.value || undefined)}
          />
        </div>

        {/* Status Filters */}
        <div className="space-y-2">
          <Label>Status</Label>
          <div className="grid grid-cols-2 gap-2">
            {[
              { value: 'draft', label: 'Draft' },
              { value: 'pending_finance', label: 'Pending Finance' },
              { value: 'approved', label: 'Approved' },
              { value: 'receiving', label: 'Receiving' },
              { value: 'issuing', label: 'Issuing' },
              { value: 'posted', label: 'Posted' },
              { value: 'completed', label: 'Completed' },
              { value: 'rejected', label: 'Rejected' },
              { value: 'expired', label: 'Expired' },
              { value: 'cancelled', label: 'Cancelled' }
            ].map((status) => (
              <div key={status.value} className="flex items-center space-x-2">
                <Checkbox
                  id={`status-${status.value}`}
                  checked={filters.status?.includes(status.value as VoucherStatus) || false}
                  onCheckedChange={() => handleStatusToggle(status.value as VoucherStatus)}
                />
                <Label 
                  htmlFor={`status-${status.value}`}
                  className="text-sm font-normal"
                >
                  {status.label}
                </Label>
              </div>
            ))}
          </div>
        </div>

        {/* Type Filters */}
        <div className="space-y-2">
          <Label>Type</Label>
          <div className="flex space-x-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="type-purchase"
                checked={filters.voucher_type?.includes('purchase') || false}
                onCheckedChange={() => handleTypeToggle('purchase')}
              />
              <Label htmlFor="type-purchase" className="text-sm font-normal">
                Purchase
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="type-issuance"
                checked={filters.voucher_type?.includes('issuance') || false}
                onCheckedChange={() => handleTypeToggle('issuance')}
              />
              <Label htmlFor="type-issuance" className="text-sm font-normal">
                Issuance
              </Label>
            </div>
          </div>
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>From Date</Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className="w-full justify-start text-left font-normal"
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {filters.date_from ? format(new Date(filters.date_from), 'PPP') : 'Select date'}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={filters.date_from ? new Date(filters.date_from) : undefined}
                  onSelect={(date) => handleFilterChange('date_from', date ? format(date, 'yyyy-MM-dd') : undefined)}
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>

          <div className="space-y-2">
            <Label>To Date</Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className="w-full justify-start text-left font-normal"
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {filters.date_to ? format(new Date(filters.date_to), 'PPP') : 'Select date'}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={filters.date_to ? new Date(filters.date_to) : undefined}
                  onSelect={(date) => handleFilterChange('date_to', date ? format(date, 'yyyy-MM-dd') : undefined)}
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>
        </div>

        {/* Amount Range */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="amount-min">Min Amount</Label>
            <Input
              id="amount-min"
              type="number"
              placeholder="0"
              value={filters.amount_min || ''}
              onChange={(e) => handleFilterChange('amount_min', e.target.value ? parseFloat(e.target.value) : undefined)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="amount-max">Max Amount</Label>
            <Input
              id="amount-max"
              type="number"
              placeholder="No limit"
              value={filters.amount_max || ''}
              onChange={(e) => handleFilterChange('amount_max', e.target.value ? parseFloat(e.target.value) : undefined)}
            />
          </div>
        </div>

        {/* Active Filters Summary */}
        {hasActiveFilters && (
          <div className="pt-4 border-t">
            <div className="text-sm text-muted-foreground mb-2">Active Filters:</div>
            <div className="flex flex-wrap gap-2">
              {filters.search && (
                <Badge variant="secondary">
                  Search: {filters.search}
                </Badge>
              )}
              {filters.status && filters.status.length > 0 && (
                <Badge variant="secondary">
                  Status: {filters.status.length} selected
                </Badge>
              )}
              {filters.voucher_type && filters.voucher_type.length > 0 && (
                <Badge variant="secondary">
                  Type: {filters.voucher_type.length} selected
                </Badge>
              )}
              {filters.date_from && (
                <Badge variant="secondary">
                  From: {format(new Date(filters.date_from), 'MMM dd, yyyy')}
                </Badge>
              )}
              {filters.date_to && (
                <Badge variant="secondary">
                  To: {format(new Date(filters.date_to), 'MMM dd, yyyy')}
                </Badge>
              )}
              {filters.amount_min && (
                <Badge variant="secondary">
                  Min: ${filters.amount_min.toLocaleString()}
                </Badge>
              )}
              {filters.amount_max && (
                <Badge variant="secondary">
                  Max: ${filters.amount_max.toLocaleString()}
                </Badge>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

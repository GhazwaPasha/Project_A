'use client'

import React, { useState, useEffect } from 'react'
import { Calendar, X, ChevronDown, Clock, CalendarDays } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

export interface DateRange {
  startDate: Date | null
  endDate: Date | null
}

export interface DateFilterProps {
  onDateRangeChange: (dateRange: DateRange) => void
  initialDateRange?: DateRange
  className?: string
  placeholder?: string
}

const PRESET_RANGES = [
  {
    label: 'Today',
    value: 'today',
    getRange: () => {
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const endOfDay = new Date(today)
      endOfDay.setHours(23, 59, 59, 999)
      return { startDate: today, endDate: endOfDay }
    }
  },
  {
    label: 'Yesterday',
    value: 'yesterday',
    getRange: () => {
      const yesterday = new Date()
      yesterday.setDate(yesterday.getDate() - 1)
      yesterday.setHours(0, 0, 0, 0)
      const endOfDay = new Date(yesterday)
      endOfDay.setHours(23, 59, 59, 999)
      return { startDate: yesterday, endDate: endOfDay }
    }
  },
  {
    label: 'This Week',
    value: 'thisWeek',
    getRange: () => {
      const today = new Date()
      const startOfWeek = new Date(today)
      startOfWeek.setDate(today.getDate() - today.getDay())
      startOfWeek.setHours(0, 0, 0, 0)
      const endOfWeek = new Date(startOfWeek)
      endOfWeek.setDate(startOfWeek.getDate() + 6)
      endOfWeek.setHours(23, 59, 59, 999)
      return { startDate: startOfWeek, endDate: endOfWeek }
    }
  },
  {
    label: 'Last Week',
    value: 'lastWeek',
    getRange: () => {
      const today = new Date()
      const lastWeekStart = new Date(today)
      lastWeekStart.setDate(today.getDate() - today.getDay() - 7)
      lastWeekStart.setHours(0, 0, 0, 0)
      const lastWeekEnd = new Date(lastWeekStart)
      lastWeekEnd.setDate(lastWeekStart.getDate() + 6)
      lastWeekEnd.setHours(23, 59, 59, 999)
      return { startDate: lastWeekStart, endDate: lastWeekEnd }
    }
  },
  {
    label: 'This Month',
    value: 'thisMonth',
    getRange: () => {
      const today = new Date()
      const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
      startOfMonth.setHours(0, 0, 0, 0)
      const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0)
      endOfMonth.setHours(23, 59, 59, 999)
      return { startDate: startOfMonth, endDate: endOfMonth }
    }
  },
  {
    label: 'Last Month',
    value: 'lastMonth',
    getRange: () => {
      const today = new Date()
      const lastMonthStart = new Date(today.getFullYear(), today.getMonth() - 1, 1)
      lastMonthStart.setHours(0, 0, 0, 0)
      const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0)
      lastMonthEnd.setHours(23, 59, 59, 999)
      return { startDate: lastMonthStart, endDate: lastMonthEnd }
    }
  },
  {
    label: 'This Year',
    value: 'thisYear',
    getRange: () => {
      const today = new Date()
      const startOfYear = new Date(today.getFullYear(), 0, 1)
      startOfYear.setHours(0, 0, 0, 0)
      const endOfYear = new Date(today.getFullYear(), 11, 31)
      endOfYear.setHours(23, 59, 59, 999)
      return { startDate: startOfYear, endDate: endOfYear }
    }
  },
  {
    label: 'Last 30 Days',
    value: 'last30Days',
    getRange: () => {
      const today = new Date()
      const thirtyDaysAgo = new Date(today)
      thirtyDaysAgo.setDate(today.getDate() - 30)
      thirtyDaysAgo.setHours(0, 0, 0, 0)
      today.setHours(23, 59, 59, 999)
      return { startDate: thirtyDaysAgo, endDate: today }
    }
  },
  {
    label: 'Last 90 Days',
    value: 'last90Days',
    getRange: () => {
      const today = new Date()
      const ninetyDaysAgo = new Date(today)
      ninetyDaysAgo.setDate(today.getDate() - 90)
      ninetyDaysAgo.setHours(0, 0, 0, 0)
      today.setHours(23, 59, 59, 999)
      return { startDate: ninetyDaysAgo, endDate: today }
    }
  }
]

export function DateFilter({ 
  onDateRangeChange, 
  initialDateRange = { startDate: null, endDate: null },
  className,
  placeholder = "Select date range"
}: DateFilterProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null)
  const [dateRange, setDateRange] = useState<DateRange>(initialDateRange)
  const [tempStartDate, setTempStartDate] = useState<string>('')
  const [tempEndDate, setTempEndDate] = useState<string>('')

  // Initialize temp dates when component mounts or dateRange changes
  useEffect(() => {
    if (dateRange.startDate) {
      setTempStartDate(dateRange.startDate.toISOString().split('T')[0])
    } else {
      setTempStartDate('')
    }
    if (dateRange.endDate) {
      setTempEndDate(dateRange.endDate.toISOString().split('T')[0])
    } else {
      setTempEndDate('')
    }
  }, [dateRange.startDate, dateRange.endDate])

  const formatDateRange = (range: DateRange): string => {
    if (!range.startDate || !range.endDate) return placeholder

    const start = range.startDate.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
    const end = range.endDate.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })

    if (start === end) return start
    return `${start} - ${end}`
  }

  const handlePresetSelect = (preset: typeof PRESET_RANGES[0]) => {
    const range = preset.getRange()
    setDateRange(range)
    setSelectedPreset(preset.value)
    setTempStartDate(range.startDate.toISOString().split('T')[0])
    setTempEndDate(range.endDate.toISOString().split('T')[0])
    onDateRangeChange(range)
    setIsOpen(false)
  }

  const handleCustomDateApply = () => {
    if (tempStartDate && tempEndDate) {
      const startDate = new Date(tempStartDate)
      startDate.setHours(0, 0, 0, 0)
      const endDate = new Date(tempEndDate)
      endDate.setHours(23, 59, 59, 999)
      
      const range = { startDate, endDate }
      setDateRange(range)
      setSelectedPreset(null)
      onDateRangeChange(range)
      setIsOpen(false)
    }
  }

  const handleClear = () => {
    const emptyRange = { startDate: null, endDate: null }
    setDateRange(emptyRange)
    setSelectedPreset(null)
    setTempStartDate('')
    setTempEndDate('')
    onDateRangeChange(emptyRange)
    setIsOpen(false)
  }

  const isCustomRange = !selectedPreset && (dateRange.startDate || dateRange.endDate)

  return (
    <div className={cn("relative", className)}>
      {/* Date Filter Trigger Button */}
      <Button
        variant="outline"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "h-10 min-w-[160px] justify-between rounded-2xl px-4 transition-all duration-200 sm:min-w-[200px]",
          /* beat outline: bg-background + hover:accent; use M3 surfaces + primary tint on hover in light and dark */
          "!border !border-[var(--md-sys-color-outline)] !bg-[var(--md-sys-color-surface-container-highest)]",
          "!text-on-surface",
          "hover:!border-[var(--md-sys-color-outline)]",
          "hover:!bg-[color-mix(in_srgb,var(--md-sys-color-primary)_12%,var(--md-sys-color-surface-container-highest))] hover:!text-on-surface",
          isOpen &&
            "!border-[var(--md-sys-color-primary)] !bg-primary !text-on-primary"
        )}
      >
        <div className="flex min-w-0 items-center gap-2">
          <Calendar className="h-4 w-4 shrink-0 text-inherit" />
          <span className="md-body-medium truncate text-inherit">
            {formatDateRange(dateRange)}
          </span>
        </div>
        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 text-inherit transition-transform duration-200",
            isOpen && "rotate-180"
          )}
        />
      </Button>

      {/* Date Filter Dropdown */}
      {isOpen && (
        <Card className="absolute top-12 left-0 z-50 w-80 sm:w-96 md-card-expressive border-outline shadow-lg">
          <CardContent className="p-0">
            {/* Header */}
            <div className="p-4 border-b border-outline-variant">
              <div className="flex items-center justify-between">
                <h3 className="md-title-medium text-on-surface">Select Date Range</h3>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setIsOpen(false)}
                  className="h-8 w-8 rounded-full text-on-surface hover:!bg-[var(--md-sys-color-surface-container)]"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Preset Ranges */}
            <div className="p-4 border-b border-outline-variant">
              <h4 className="md-body-large text-on-surface font-medium mb-3 flex items-center gap-2">
                <Clock className="w-4 h-4" />
                Quick Select
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {PRESET_RANGES.map((preset) => (
                  <Button
                    key={preset.value}
                    variant={selectedPreset === preset.value ? "default" : "ghost"}
                    onClick={() => handlePresetSelect(preset)}
                    className={cn(
                      "h-9 rounded-xl px-3 text-sm font-medium text-on-surface transition-all duration-200",
                      selectedPreset === preset.value
                        ? "bg-primary text-on-primary"
                        : "hover:!bg-[color-mix(in_srgb,var(--md-sys-color-primary)_10%,var(--md-sys-color-surface-container-highest))] hover:!text-on-surface"
                    )}
                  >
                    {preset.label}
                  </Button>
                ))}
              </div>
            </div>

            {/* Custom Date Range */}
            <div className="p-4">
              <h4 className="md-body-large text-on-surface font-medium mb-3 flex items-center gap-2">
                <CalendarDays className="w-4 h-4" />
                Custom Range
              </h4>
              <div className="space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="md-body-small text-on-surface-variant mb-1 block">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={tempStartDate}
                      onChange={(e) => setTempStartDate(e.target.value)}
                      className="md-text-field-input h-9 text-sm"
                    />
                  </div>
                  <div>
                    <label className="md-body-small text-on-surface-variant mb-1 block">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={tempEndDate}
                      onChange={(e) => setTempEndDate(e.target.value)}
                      className="md-text-field-input h-9 text-sm"
                    />
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <Button
                    onClick={handleCustomDateApply}
                    disabled={!tempStartDate || !tempEndDate}
                    className="flex-1 h-9 rounded-xl"
                  >
                    Apply Range
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleClear}
                    className="h-9 rounded-xl !border !border-[var(--md-sys-color-outline)] px-4 text-on-surface hover:!bg-[var(--md-sys-color-surface-container)]"
                  >
                    Clear
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  )
}

export default DateFilter

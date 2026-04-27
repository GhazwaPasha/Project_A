'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  ArrowLeft, 
  Download, 
  Printer, 
  RefreshCw,
  BarChart3,
  Loader2
} from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { useOrganizationFormatters } from '@/hooks/use-organization-formatters'
import { useAgedPayables } from '@/hooks/use-organization-data'
import { useCurrentOrganization } from '@/hooks/use-current-organization'
import { useToast } from '@/hooks/use-toast'

interface AgedPayablesData {
  payables: Array<{
    vendorName: string
    current: number
    days30: number
    days60: number
    days90: number
    total: number
  }>
  totals: {
    current: number
    days30: number
    days60: number
    days90: number
    total: number
  }
  generatedAt: string
}

interface AgedPayablesReportProps {
  onBack: () => void
  asOfDate?: string
}

export function AgedPayablesReport({ onBack, asOfDate }: AgedPayablesReportProps) {
  const currentOrganization = useCurrentOrganization()
  const { formatCurrency } = useOrganizationFormatters()
  const { toast } = useToast()
  
  // Use optimized hook instead of manual data loading
  const { 
    data, 
    isLoading: loading, 
    error, 
    refetch 
  } = useAgedPayables(asOfDate)

  const handlePrint = () => {
    window.print()
  }

  const handleExport = () => {
    toast({
      title: 'PDF export',
      description: 'Not available yet. Use Print and choose “Save as PDF” in the print dialog.',
    })
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-lg">Loading Aged Payables...</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <BarChart3 className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Error Loading Aged Payables</h2>
          <p className="text-gray-600 mb-4">
            {error instanceof Error ? error.message : error ? String(error) : 'No data available'}
          </p>
          <div className="space-x-2">
            <Button onClick={() => refetch()}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
            <Button variant="outline" onClick={onBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Reports
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
      {/* Fixed Header */}
      <div className="app-page-header sticky top-0 z-30">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button 
                onClick={onBack}
                className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Back to Reports</span>
                <span className="sm:hidden">Back</span>
              </Button>
              <div>
                <h1 className="md-headline-small text-on-background">Aged Payables</h1>
                <p className="md-body-medium text-on-surface-variant mt-1">
                  As of {formatDate(asOfDate || new Date().toISOString())}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button 
                className="md-button"
                onClick={() => refetch()}
                title="Refresh"
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
              <Button 
                className="md-button"
                onClick={handlePrint}
                title="Print"
              >
                <Printer className="w-4 h-4" />
              </Button>
              <Button 
                className="md-button"
                onClick={handleExport}
                title="Export"
              >
                <Download className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Report Content */}
      <div className="px-6 py-6">
        <div className="max-w-6xl mx-auto">
          {/* Company Header */}
          <div className="text-center mb-8">
            <h2 className="md-headline-large text-on-background mb-2">
              {currentOrganization?.name || 'Company Name'}
            </h2>
            <h3 className="md-title-large text-on-surface-variant">Aged Payables Report</h3>
            <p className="md-body-large text-on-surface-variant">
              As of {formatDate(asOfDate || new Date().toISOString())}
            </p>
          </div>

          {/* Aged Payables Table */}
          <Card className="mb-6">
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Vendor
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Current
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        1-30 Days
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        31-60 Days
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        61-90 Days
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Over 90 Days
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Total
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {data.payables.map((payable, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 font-medium text-gray-900">
                          {payable.vendorName}
                        </td>
                        <td className="px-6 py-4 text-right font-mono">
                          {formatCurrency(payable.current)}
                        </td>
                        <td className="px-6 py-4 text-right font-mono">
                          {formatCurrency(payable.days30)}
                        </td>
                        <td className="px-6 py-4 text-right font-mono">
                          {formatCurrency(payable.days60)}
                        </td>
                        <td className="px-6 py-4 text-right font-mono">
                          {formatCurrency(payable.days90)}
                        </td>
                        <td className="px-6 py-4 text-right font-mono font-bold">
                          {formatCurrency(payable.total)}
                        </td>
                      </tr>
                    ))}
                    <tr className="bg-gray-50 font-bold border-t-2 border-gray-300">
                      <td className="px-6 py-4 text-gray-900">Total</td>
                      <td className="px-6 py-4 text-right font-mono">
                        {formatCurrency(data.totals.current)}
                      </td>
                      <td className="px-6 py-4 text-right font-mono">
                        {formatCurrency(data.totals.days30)}
                      </td>
                      <td className="px-6 py-4 text-right font-mono">
                        {formatCurrency(data.totals.days60)}
                      </td>
                      <td className="px-6 py-4 text-right font-mono">
                        {formatCurrency(data.totals.days90)}
                      </td>
                      <td className="px-6 py-4 text-right font-mono">
                        {formatCurrency(data.totals.total)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-green-600">{formatCurrency(data.totals.current)}</div>
                <div className="text-sm text-gray-600">Current (0-30 days)</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-yellow-600">{formatCurrency(data.totals.days30)}</div>
                <div className="text-sm text-gray-600">1-30 Days</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-orange-600">{formatCurrency(data.totals.days60)}</div>
                <div className="text-sm text-gray-600">31-60 Days</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-red-600">{formatCurrency(data.totals.days90)}</div>
                <div className="text-sm text-gray-600">Over 90 Days</div>
              </CardContent>
            </Card>
          </div>

          {/* Footer */}
          <div className="text-center text-sm text-gray-500">
            <p>Generated on {formatDate(data.generatedAt)}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

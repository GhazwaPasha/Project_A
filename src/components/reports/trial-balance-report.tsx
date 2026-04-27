'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  ArrowLeft, 
  Download, 
  Printer, 
  RefreshCw,
  Calculator,
  Loader2
} from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { useOrganizationFormatters } from '@/hooks/use-organization-formatters'
import { useTrialBalance } from '@/hooks/use-organization-data'
import { useCurrentOrganization } from '@/hooks/use-current-organization'
import { useToast } from '@/hooks/use-toast'

interface TrialBalanceData {
  accounts: Array<{
    accountId: number
    accountName: string
    accountType: string
    debitBalance: number
    creditBalance: number
  }>
  totalDebits: number
  totalCredits: number
  isBalanced: boolean
  generatedAt: string
}

interface TrialBalanceReportProps {
  onBack: () => void
  asOfDate?: string
}

export function TrialBalanceReport({ onBack, asOfDate }: TrialBalanceReportProps) {
  const currentOrganization = useCurrentOrganization()
  const { formatCurrency } = useOrganizationFormatters()
  const { toast } = useToast()

  // Use optimized hook instead of manual data loading
  const { 
    data, 
    isLoading: loading, 
    error, 
    refetch 
  } = useTrialBalance(asOfDate)

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
          <p className="text-lg">Loading Trial Balance...</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Calculator className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Error Loading Trial Balance</h2>
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
                <h1 className="md-headline-small text-on-background">Trial Balance</h1>
                <p className="md-body-medium text-on-surface-variant mt-1">
                  As of {formatDate(asOfDate || new Date().toISOString())}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button 
                className="md-button-outlined"
                onClick={() => refetch()}
                title="Refresh"
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
              <Button 
                className="md-button-outlined"
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
            <h3 className="md-title-large text-on-surface-variant">Trial Balance</h3>
            <p className="md-body-large text-on-surface-variant">
              As of {formatDate(asOfDate || new Date().toISOString())}
            </p>
          </div>

          {/* Trial Balance Table */}
          <Card className="md-card-expressive mb-6">
            <CardHeader>
              <CardTitle className="md-title-large text-on-surface">Trial Balance</CardTitle>
              <CardDescription className="md-body-medium text-on-surface-variant">
                All account balances as of {formatDate(asOfDate || new Date().toISOString())}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-outline-variant">
                    <tr>
                      <th className="text-left p-4 md-body-large text-on-surface font-medium">
                        Account
                      </th>
                      <th className="text-left p-4 md-body-large text-on-surface font-medium">
                        Type
                      </th>
                      <th className="text-right p-4 md-body-large text-on-surface font-medium">
                        Debit
                      </th>
                      <th className="text-right p-4 md-body-large text-on-surface font-medium">
                        Credit
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant">
                    {data.accounts.map((account) => (
                      <tr key={account.accountId}>
                        <td className="p-4 md-body-large text-on-surface font-medium">
                          {account.accountName}
                        </td>
                        <td className="p-4 md-body-large text-on-surface-variant capitalize">
                          {account.accountType}
                        </td>
                        <td className="p-4 text-right font-mono md-body-large text-on-surface">
                          {account.debitBalance > 0 ? formatCurrency(account.debitBalance) : '-'}
                        </td>
                        <td className="p-4 text-right font-mono md-body-large text-on-surface">
                          {account.creditBalance > 0 ? formatCurrency(account.creditBalance) : '-'}
                        </td>
                      </tr>
                    ))}
                    <tr className="bg-surface-container font-bold border-t-2 border-outline">
                      <td className="p-4 md-title-medium text-on-surface" colSpan={2}>
                        Total
                      </td>
                      <td className="p-4 text-right font-mono md-title-medium text-on-surface">
                        {formatCurrency(data.totalDebits)}
                      </td>
                      <td className="p-4 text-right font-mono md-title-medium text-on-surface">
                        {formatCurrency(data.totalCredits)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Balance Verification */}
          <Card className="mb-6">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Balance Verification</h3>
                  <p className="text-gray-600">
                    Total Debits = Total Credits
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-600 mb-1">
                    {formatCurrency(data.totalDebits)} = {formatCurrency(data.totalCredits)}
                  </div>
                  <div className={`text-lg font-bold ${data.isBalanced ? 'text-green-600' : 'text-red-600'}`}>
                    {data.isBalanced ? '✓ Balanced' : '✗ Not Balanced'}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-gray-900">{data.accounts.length}</div>
                <div className="text-sm text-gray-600">Total Accounts</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-blue-600">{formatCurrency(data.totalDebits)}</div>
                <div className="text-sm text-gray-600">Total Debits</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-green-600">{formatCurrency(data.totalCredits)}</div>
                <div className="text-sm text-gray-600">Total Credits</div>
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

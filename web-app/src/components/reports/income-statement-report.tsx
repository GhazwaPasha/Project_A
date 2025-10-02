'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  ArrowLeft, 
  Download, 
  Printer, 
  RefreshCw,
  TrendingUp,
  Loader2
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { DataService } from '@/lib/data-service'
import { useOrganization } from '@/hooks/use-organization'

interface IncomeStatementData {
  revenue: { total: number; breakdown: Array<{ account: string; amount: number }> }
  expenses: { total: number; breakdown: Array<{ account: string; amount: number }> }
  netIncome: number
  grossProfit: number
  operatingIncome: number
  generatedAt: string
}

interface IncomeStatementReportProps {
  onBack: () => void
  fromDate?: string
  toDate?: string
}

export function IncomeStatementReport({ onBack, fromDate, toDate }: IncomeStatementReportProps) {
  const [data, setData] = useState<IncomeStatementData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { currentOrganization } = useOrganization()

  useEffect(() => {
    if (currentOrganization) {
      loadIncomeStatement()
    }
  }, [currentOrganization, fromDate, toDate])

  const loadIncomeStatement = async () => {
    if (!currentOrganization) return

    setLoading(true)
    setError(null)

    try {
      const incomeStatementData = await DataService.generateIncomeStatement(
        currentOrganization.id, 
        fromDate,
        toDate
      )
      setData(incomeStatementData)
    } catch (error) {
      console.error('Error loading income statement:', error)
      setError('Failed to load income statement data')
    } finally {
      setLoading(false)
    }
  }

  const handlePrint = () => {
    if (!data) return

    const printWindow = window.open('', '_blank')
    if (!printWindow) return

    const printContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Income Statement - ${currentOrganization?.name || 'Company'}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
            .header { text-align: center; margin-bottom: 30px; }
            .header h1 { color: #1976D2; margin: 0; }
            .header h2 { color: #666; margin: 5px 0; }
            .header p { color: #888; margin: 0; }
            .section { margin-bottom: 30px; }
            .section h3 { color: #1976D2; border-bottom: 2px solid #1976D2; padding-bottom: 5px; margin-bottom: 15px; }
            .revenue h3 { color: #2E7D32; }
            .expenses h3 { color: #C62828; }
            .totals { margin-top: 30px; display: flex; gap: 20px; }
            .total-card { 
              flex: 1; 
              border: 2px solid #1976D2; 
              padding: 20px; 
              text-align: center; 
              background-color: #f8f9fa;
            }
            .total-card h3 { margin: 0 0 10px 0; color: #1976D2; }
            .total-card .amount { font-size: 24px; font-weight: bold; font-family: monospace; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            .text-right { text-align: right; }
            .revenue-row { color: #2E7D32; }
            .expense-row { color: #C62828; }
            .total-row { font-weight: bold; background-color: #f5f5f5; }
            .print-button { 
              position: fixed; 
              top: 20px; 
              right: 20px; 
              padding: 10px 20px; 
              background-color: #007bff; 
              color: white; 
              border: none; 
              border-radius: 5px; 
              cursor: pointer; 
              font-size: 14px;
            }
            .print-button:hover { background-color: #0056b3; }
            @media print {
              .print-button { display: none; }
              body { margin: 0; }
            }
          </style>
        </head>
        <body>
          <button class="print-button" onclick="window.print()">Print Report</button>
          
          <div class="header">
            <h1>${currentOrganization?.name || 'Company Name'}</h1>
            <h2>Income Statement</h2>
            <p>${fromDate && toDate 
              ? `For the period ${formatDate(fromDate)} to ${formatDate(toDate)}`
              : 'For the current period'
            }</p>
          </div>

          <div class="section revenue">
            <h3>REVENUE</h3>
            <table>
              <thead>
                <tr>
                  <th>Account</th>
                  <th class="text-right">Amount</th>
                </tr>
              </thead>
              <tbody>
                ${data.revenue.breakdown.map(item => `
                  <tr>
                    <td>${item.account}</td>
                    <td class="text-right revenue-row">${formatCurrency(item.amount)}</td>
                  </tr>
                `).join('')}
                <tr class="total-row">
                  <td><strong>Total Revenue</strong></td>
                  <td class="text-right revenue-row"><strong>${formatCurrency(data.revenue.total)}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="section expenses">
            <h3>EXPENSES</h3>
            <table>
              <thead>
                <tr>
                  <th>Account</th>
                  <th class="text-right">Amount</th>
                </tr>
              </thead>
              <tbody>
                ${data.expenses.breakdown.map(item => `
                  <tr>
                    <td>${item.account}</td>
                    <td class="text-right expense-row">${formatCurrency(item.amount)}</td>
                  </tr>
                `).join('')}
                <tr class="total-row">
                  <td><strong>Total Expenses</strong></td>
                  <td class="text-right expense-row"><strong>${formatCurrency(data.expenses.total)}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="section">
            <h3>NET INCOME</h3>
            <table>
              <tbody>
                <tr>
                  <td><strong>Total Revenue</strong></td>
                  <td class="text-right revenue-row"><strong>${formatCurrency(data.revenue.total)}</strong></td>
                </tr>
                <tr>
                  <td><strong>Total Expenses</strong></td>
                  <td class="text-right expense-row"><strong>${formatCurrency(data.expenses.total)}</strong></td>
                </tr>
                <tr class="total-row" style="border-top: 2px solid #333;">
                  <td><strong>Net Income</strong></td>
                  <td class="text-right" style="color: ${data.netIncome >= 0 ? '#2E7D32' : '#C62828'};">
                    <strong>${formatCurrency(data.netIncome)}</strong>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="totals">
            <div class="total-card">
              <h3>TOTAL REVENUE</h3>
              <div class="amount" style="color: #2E7D32;">${formatCurrency(data.revenue.total)}</div>
            </div>
            <div class="total-card">
              <h3>TOTAL EXPENSES</h3>
              <div class="amount" style="color: #C62828;">${formatCurrency(data.expenses.total)}</div>
            </div>
            <div class="total-card">
              <h3>NET INCOME</h3>
              <div class="amount" style="color: ${data.netIncome >= 0 ? '#2E7D32' : '#C62828'};">
                ${formatCurrency(data.netIncome)}
              </div>
            </div>
          </div>

          <div style="margin-top: 30px; text-align: center; color: #666;">
            <p>Generated on ${new Date().toLocaleDateString()}</p>
          </div>
        </body>
      </html>
    `

    printWindow.document.write(printContent)
    printWindow.document.close()
    printWindow.focus()
  }

  const handleExport = () => {
    // TODO: Implement PDF export
    console.log('Export functionality to be implemented')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-lg">Loading Income Statement...</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <TrendingUp className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Error Loading Income Statement</h2>
          <p className="text-gray-600 mb-4">{error || 'No data available'}</p>
          <div className="space-x-2">
            <Button onClick={loadIncomeStatement}>
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
      <div className="sticky top-0 z-30 backdrop-blur-sm border-b border-outline-variant" style={{ backgroundColor: 'var(--md-sys-color-surface)' }}>
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
                <h1 className="md-headline-small text-on-background">Income Statement</h1>
                <p className="md-body-medium text-on-surface-variant mt-1">
                  {fromDate && toDate 
                    ? `${formatDate(fromDate)} - ${formatDate(toDate)}`
                    : 'Current Period'
                  }
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button 
                className="md-button-outlined"
                onClick={loadIncomeStatement}
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
        <div className="max-w-4xl mx-auto">
          {/* Company Header */}
          <div className="text-center mb-8">
            <h2 className="md-headline-large text-on-background mb-2">
              {currentOrganization?.name || 'Company Name'}
            </h2>
            <h3 className="md-title-large text-on-surface-variant">Income Statement</h3>
            <p className="md-body-large text-on-surface-variant">
              {fromDate && toDate 
                ? `For the period ${formatDate(fromDate)} to ${formatDate(toDate)}`
                : 'For the current period'
              }
            </p>
          </div>

          {/* Revenue Section */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-lg text-green-600">Revenue</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <tbody className="divide-y divide-gray-200">
                    {data.revenue.breakdown.map((item, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 font-medium text-gray-900">
                          {item.account}
                        </td>
                        <td className="px-6 py-4 text-right font-mono text-green-600">
                          {formatCurrency(item.amount)}
                        </td>
                      </tr>
                    ))}
                    <tr className="bg-green-50 font-bold border-t-2 border-green-200">
                      <td className="px-6 py-4 text-gray-900">Total Revenue</td>
                      <td className="px-6 py-4 text-right font-mono text-green-600">
                        {formatCurrency(data.revenue.total)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Expenses Section */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-lg text-red-600">Expenses</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <tbody className="divide-y divide-gray-200">
                    {data.expenses.breakdown.map((item, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 font-medium text-gray-900">
                          {item.account}
                        </td>
                        <td className="px-6 py-4 text-right font-mono text-red-600">
                          {formatCurrency(item.amount)}
                        </td>
                      </tr>
                    ))}
                    <tr className="bg-red-50 font-bold border-t-2 border-red-200">
                      <td className="px-6 py-4 text-gray-900">Total Expenses</td>
                      <td className="px-6 py-4 text-right font-mono text-red-600">
                        {formatCurrency(data.expenses.total)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Net Income */}
          <Card className="mb-6">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Net Income</h3>
                  <p className="text-gray-600">
                    Revenue - Expenses
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-600 mb-1">
                    {formatCurrency(data.revenue.total)} - {formatCurrency(data.expenses.total)}
                  </div>
                  <div className={`text-2xl font-bold ${data.netIncome >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(data.netIncome)}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-green-600">{formatCurrency(data.revenue.total)}</div>
                <div className="text-sm text-gray-600">Total Revenue</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-red-600">{formatCurrency(data.expenses.total)}</div>
                <div className="text-sm text-gray-600">Total Expenses</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className={`text-2xl font-bold ${data.netIncome >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(data.netIncome)}
                </div>
                <div className="text-sm text-gray-600">Net Income</div>
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

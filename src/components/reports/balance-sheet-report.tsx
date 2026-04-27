'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  ArrowLeft, 
  Download, 
  Printer, 
  RefreshCw,
  Building2,
  Loader2,
  AlertCircle,
  ChevronRight,
  ChevronDown
} from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { useOrganizationFormatters } from '@/hooks/use-organization-formatters'
import { useBalanceSheet } from '@/hooks/use-organization-data'
import { useCurrentOrganization } from '@/contexts/organization-context'
import { useComponentLoadingState } from '@/hooks/use-loading-state'
import { useToast } from '@/hooks/use-toast'

interface Account {
  id: number
  code: string
  name: string
  account_type: string
  balance: number
  parent_id: number | null
  children: Account[]
}

interface Section {
  name: string
  group: string
  accounts: Account[]
  total: number
}

interface BalanceSheetData {
  isGroupBased: boolean
  assetSections: Section[]
  liabilitySections: Section[]
  equitySections: Section[]
  totalAssets: number
  totalLiabilities: number
  totalEquity: number
  isBalanced: boolean
  generatedAt: string
}

interface BalanceSheetReportProps {
  onBack: () => void
  asOfDate?: string
}

export function BalanceSheetReport({ onBack, asOfDate }: BalanceSheetReportProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())
  const [expandedAccounts, setExpandedAccounts] = useState<Set<number>>(new Set())
  const currentOrganization = useCurrentOrganization()
  const { formatCurrency } = useOrganizationFormatters()
  const { toast } = useToast()
  
  // Use component loading state for better UX
  const { isLoading: componentLoading } = useComponentLoadingState('balance-sheet', ['organization', 'accounts'])
  
  // Use optimized hook instead of manual data loading
  const { 
    data, 
    isLoading: queryLoading, 
    error, 
    refetch 
  } = useBalanceSheet(asOfDate)
  
  const loading = componentLoading || queryLoading

  const handlePrint = () => {
    if (!data) return

    const printWindow = window.open('', '_blank')
    if (!printWindow) return

    // Generate HTML content for printing
    const generateAccountRows = (accounts: Account[], level: number = 0): string => {
      let html = ''
      accounts.forEach(account => {
        const indent = '&nbsp;'.repeat(level * 4)
        const hasChildren = account.children && account.children.length > 0
        const balance = account.balance !== 0 ? formatCurrency(account.balance) : '-'
        
        html += `
          <tr>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">
              ${indent}${hasChildren ? '▼' : '&nbsp;&nbsp;&nbsp;'} ${account.name}
              <br><small style="color: #666;">${account.code}</small>
            </td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right; font-family: monospace;">
              ${balance}
            </td>
          </tr>
        `
        
        if (hasChildren && account.children) {
          html += generateAccountRows(account.children, level + 1)
        }
      })
      return html
    }

    const generateSectionHTML = (sections: Section[], title: string): string => {
      let html = `
        <div style="margin-bottom: 30px;">
          <h3 style="color: #1976D2; border-bottom: 2px solid #1976D2; padding-bottom: 5px; margin-bottom: 15px;">${title}</h3>
      `
      
      sections.forEach(section => {
        html += `
          <div style="margin-bottom: 20px;">
            <h4 style="background-color: #f5f5f5; padding: 10px; margin: 0; font-weight: bold;">
              ${section.name} - ${formatCurrency(section.total)}
            </h4>
            <table style="width: 100%; border-collapse: collapse;">
              <thead>
                <tr style="background-color: #f9f9f9;">
                  <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Account</th>
                  <th style="padding: 8px; border: 1px solid #ddd; text-align: right;">Balance</th>
                </tr>
              </thead>
              <tbody>
                ${generateAccountRows(section.accounts)}
              </tbody>
            </table>
          </div>
        `
      })
      
      html += '</div>'
      return html
    }

    const printContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Balance Sheet - ${currentOrganization?.name || 'Company'}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
            .header { text-align: center; margin-bottom: 30px; }
            .header h1 { color: #1976D2; margin: 0; }
            .header h2 { color: #666; margin: 5px 0; }
            .header p { color: #888; margin: 0; }
            .balance-sheet { display: flex; gap: 30px; }
            .column { flex: 1; }
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
            <h2>Balance Sheet</h2>
            <p>As of ${formatDate(asOfDate || new Date().toISOString())}</p>
          </div>

          <div class="balance-sheet">
            <div class="column">
              <h2 style="color: #1976D2; text-align: center; margin-bottom: 20px;">ASSETS</h2>
              ${generateSectionHTML(data.assetSections, 'Assets')}
            </div>
            
            <div class="column">
              <h2 style="color: #1976D2; text-align: center; margin-bottom: 20px;">LIABILITIES & EQUITY</h2>
              ${generateSectionHTML(data.liabilitySections, 'Liabilities')}
              ${generateSectionHTML(data.equitySections, 'Equity')}
            </div>
          </div>

          <div class="totals">
            <div class="total-card">
              <h3>TOTAL ASSETS</h3>
              <div class="amount">${formatCurrency(data.totalAssets)}</div>
            </div>
            <div class="total-card">
              <h3>TOTAL LIABILITIES</h3>
              <div class="amount">${formatCurrency(data.totalLiabilities)}</div>
            </div>
            <div class="total-card">
              <h3>TOTAL EQUITY</h3>
              <div class="amount">${formatCurrency(data.totalEquity)}</div>
            </div>
          </div>

          <div style="margin-top: 30px; text-align: center; color: #666;">
            <p>Generated on ${new Date().toLocaleDateString()}</p>
            <p>Assets = Liabilities + Equity: ${data.isBalanced ? '✓ Balanced' : '✗ Not Balanced'}</p>
          </div>
        </body>
      </html>
    `

    printWindow.document.write(printContent)
    printWindow.document.close()
    printWindow.focus()
  }

  const handleExport = () => {
    toast({
      title: 'PDF export',
      description: 'Not available yet. Use Print and choose “Save as PDF” in the print dialog.',
    })
  }

  const toggleSection = (sectionName: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(sectionName)) {
      newExpanded.delete(sectionName)
    } else {
      newExpanded.add(sectionName)
    }
    setExpandedSections(newExpanded)
  }

  const toggleAccount = (accountId: number) => {
    const newExpanded = new Set(expandedAccounts)
    if (newExpanded.has(accountId)) {
      newExpanded.delete(accountId)
    } else {
      newExpanded.add(accountId)
    }
    setExpandedAccounts(newExpanded)
  }

  const renderAccount = (account: Account, level: number = 0): JSX.Element[] => {
    const indentClass = level > 0 ? `ml-${level * 4}` : ''
    const isParent = account.children && account.children.length > 0
    const isExpanded = expandedAccounts.has(account.id)
    
    const rows: JSX.Element[] = []
    
    // Render the current account
    rows.push(
      <tr key={account.id} className={`${isParent ? 'bg-surface-container/20' : ''} hover:bg-surface-container/10`}>
        <td className={`p-3 ${indentClass}`}>
          <div className="flex items-center space-x-2">
            {level > 0 && (
              <div className="flex items-center space-x-1">
                <div className="w-3 h-px bg-outline-variant"></div>
                <div className="w-1.5 h-1.5 border-l border-b border-outline-variant rounded-bl"></div>
              </div>
            )}
            
            {/* Expand/Collapse Chevron */}
            {isParent ? (
              <div
                onClick={() => toggleAccount(account.id)}
                className="mr-2 p-0.5 rounded cursor-pointer hover:bg-surface-container transition-colors"
                title={isExpanded ? 'Collapse' : 'Expand'}
              >
                {isExpanded ? (
                  <ChevronDown className="w-3 h-3" />
                ) : (
                  <ChevronRight className="w-3 h-3" />
                )}
              </div>
            ) : (
              <div className="w-5 mr-2" />
            )}
            
            <div className="flex-1 min-w-0">
              <div className={`md-body-medium ${isParent ? 'font-semibold' : ''} text-on-surface truncate`}>
                {account.name}
              </div>
              <div className="md-body-small text-on-surface-variant">
                {account.code}
              </div>
            </div>
          </div>
        </td>
        <td className="p-3 text-right font-mono md-body-medium text-on-surface">
          {account.balance !== 0 ? formatCurrency(account.balance) : '-'}
        </td>
      </tr>
    )
    
    // Render children recursively only if expanded
    if (isParent && isExpanded && account.children && account.children.length > 0) {
      account.children.forEach(child => {
        rows.push(...renderAccount(child, level + 1))
      })
    }
    
    return rows
  }

  const renderSection = (section: Section) => {
    const isExpanded = expandedSections.has(section.name)
    const hasAccounts = section.accounts && section.accounts.length > 0
    
    return (
      <div key={section.name} className="mb-4">
        <div className="border border-outline-variant rounded-lg overflow-hidden">
          {/* Section Header */}
          <div 
            className="cursor-pointer hover:bg-surface-container/30 transition-colors px-4 py-3 border-b border-outline-variant"
            onClick={() => toggleSection(section.name)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {hasAccounts && (
                  <div
                    onClick={(e) => {
                      e.stopPropagation()
                      toggleSection(section.name)
                    }}
                    className="mr-2 p-1 rounded cursor-pointer hover:bg-surface-container transition-colors"
                    title={isExpanded ? 'Collapse section' : 'Expand section'}
                  >
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </div>
                )}
                <div>
                  <h4 className="md-title-medium text-on-surface font-semibold">{section.name}</h4>
                  <p className="md-body-small text-on-surface-variant">
                    {section.accounts.length} accounts
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="md-title-medium text-on-surface font-mono">
                  {formatCurrency(section.total)}
                </div>
              </div>
            </div>
          </div>
          
          {/* Section Content */}
          {isExpanded && hasAccounts && (
            <div className="bg-surface/50">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-outline-variant bg-surface-container/30">
                    <tr>
                      <th className="text-left p-3 md-body-medium text-on-surface font-medium">Account</th>
                      <th className="text-right p-3 md-body-medium text-on-surface font-medium">Balance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant">
                    {section.accounts.flatMap((account) => renderAccount(account, 0))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
        <div className="text-center">
          <div className="w-20 h-20 bg-primary-container rounded-3xl flex items-center justify-center mb-6 mx-auto">
            <RefreshCw className="w-10 h-10 text-on-primary-container animate-spin" />
          </div>
          <h3 className="md-headline-small text-on-surface mb-3">Loading Balance Sheet</h3>
          <p className="md-body-large text-on-surface-variant">
            Please wait while we generate your balance sheet report...
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
        <div className="text-center">
          <div className="w-20 h-20 bg-error-container rounded-3xl flex items-center justify-center mb-6 mx-auto">
            <AlertCircle className="w-10 h-10 text-on-error-container" />
          </div>
          <h3 className="md-headline-small text-on-surface mb-3">Error Loading Balance Sheet</h3>
          <p className="md-body-large text-on-surface-variant mb-8 max-w-md">
            Failed to load balance sheet data
          </p>
          <Button onClick={() => refetch()} className="md-button">
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
        <div className="text-center">
          <div className="w-20 h-20 bg-error-container rounded-3xl flex items-center justify-center mb-6 mx-auto">
            <AlertCircle className="w-10 h-10 text-on-error-container" />
          </div>
          <h3 className="md-headline-small text-on-surface mb-3">No Data Available</h3>
          <p className="md-body-large text-on-surface-variant mb-8 max-w-md">
            No balance sheet data available for the selected date
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button 
              className="md-button"
              onClick={() => refetch()}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
            <Button 
              className="md-button"
              onClick={onBack}
            >
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
                <h1 className="md-headline-small text-on-background">Balance Sheet</h1>
                <p className="md-body-medium text-on-surface-variant mt-1">
                  As of {formatDate(asOfDate || new Date().toISOString())}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div
                onClick={() => {
                  // Expand all sections and accounts
                  const allSections = new Set<string>([
                    ...(data?.assetSections.map((s) => s.name) ?? []),
                    ...(data?.liabilitySections.map((s) => s.name) ?? []),
                    ...(data?.equitySections.map((s) => s.name) ?? []),
                  ])
                  setExpandedSections(allSections)
                  
                  // Expand all parent accounts
                  const allParentAccounts = new Set<number>()
                  const collectParentAccounts = (accounts: Account[]) => {
                    accounts.forEach(acc => {
                      if (acc.children && acc.children.length > 0) {
                        allParentAccounts.add(acc.id)
                        collectParentAccounts(acc.children)
                      }
                    })
                  }
                  data?.assetSections.forEach(s => collectParentAccounts(s.accounts))
                  data?.liabilitySections.forEach(s => collectParentAccounts(s.accounts))
                  data?.equitySections.forEach(s => collectParentAccounts(s.accounts))
                  setExpandedAccounts(allParentAccounts)
                }}
                className="p-2 rounded cursor-pointer hover:bg-surface-container transition-colors"
                title="Expand All"
              >
                <ChevronDown className="w-4 h-4" />
              </div>
              <div
                onClick={() => {
                  setExpandedSections(new Set())
                  setExpandedAccounts(new Set())
                }}
                className="p-2 rounded cursor-pointer hover:bg-surface-container transition-colors"
                title="Collapse All"
              >
                <ChevronRight className="w-4 h-4" />
              </div>
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
        <div className="max-w-7xl mx-auto">
          {/* Company Header */}
          <div className="text-center mb-8">
            <h2 className="md-headline-large text-on-background mb-2">
              {currentOrganization?.name || 'Company Name'}
            </h2>
            <h3 className="md-title-large text-on-surface-variant">Balance Sheet</h3>
            <p className="md-body-large text-on-surface-variant">
              As of {formatDate(asOfDate || new Date().toISOString())}
            </p>
          </div>

          {/* Balance Sheet Layout - Two Column */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
            {/* Left Column - Assets */}
            <div className="space-y-6">
              <div className="text-center mb-6">
                <h2 className="md-headline-medium text-on-background">ASSETS</h2>
              </div>
              
              {data.assetSections.map((section) => renderSection(section))}
            </div>

            {/* Right Column - Liabilities and Equity */}
            <div className="space-y-6">
              <div className="text-center mb-6">
                <h2 className="md-headline-medium text-on-background">LIABILITIES & EQUITY</h2>
              </div>
              
              {/* Liabilities */}
              <div className="space-y-4">
                {data.liabilitySections.map((section) => renderSection(section))}
              </div>

              {/* Equity */}
              <div className="space-y-4">
                {data.equitySections.map((section) => renderSection(section))}
              </div>
            </div>
          </div>

          {/* Main Totals - Always at Bottom */}
          <div className="mt-8">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Total Assets */}
              <Card className="md-card-expressive">
                <CardContent className="p-6">
                  <div className="text-center">
                    <h3 className="md-title-large text-on-surface font-bold mb-2">TOTAL ASSETS</h3>
                    <div className="md-headline-small text-on-surface font-mono font-bold">
                      {formatCurrency(data.totalAssets)}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Total Liabilities */}
              <Card className="md-card-expressive">
                <CardContent className="p-6">
                  <div className="text-center">
                    <h3 className="md-title-large text-on-surface font-bold mb-2">TOTAL LIABILITIES</h3>
                    <div className="md-headline-small text-on-surface font-mono font-bold">
                      {formatCurrency(data.totalLiabilities)}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Total Equity */}
              <Card className="md-card-expressive">
                <CardContent className="p-6">
                  <div className="text-center">
                    <h3 className="md-title-large text-on-surface font-bold mb-2">TOTAL EQUITY</h3>
                    <div className="md-headline-small text-on-surface font-mono font-bold">
                      {formatCurrency(data.totalEquity)}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Balance Verification */}
          <Card className="md-card-expressive mt-6">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="md-title-large text-on-surface">Balance Verification</h3>
                  <p className="md-body-medium text-on-surface-variant">
                    Assets = Liabilities + Equity
                  </p>
                </div>
                <div className="text-right">
                  <div className="md-body-small text-on-surface-variant mb-1">
                    {formatCurrency(data.totalAssets)} = {formatCurrency(data.totalLiabilities)} + {formatCurrency(data.totalEquity)}
                  </div>
                  <div className={`md-title-medium font-bold ${data.isBalanced ? 'text-green-600' : 'text-red-600'}`}>
                    {data.isBalanced ? '✓ Balanced' : '✗ Not Balanced'}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Footer */}
          <div className="mt-8 text-center md-body-small text-on-surface-variant">
            <p>Generated on {formatDate(data.generatedAt)}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

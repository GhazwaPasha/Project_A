'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Search, 
  Filter, 
  Download,
  RefreshCw,
  Plus,
  FileText,
  BarChart3,
  PieChart,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Calendar,
  Eye,
  Settings,
  ChevronRight,
  Calculator,
  Building2,
  CreditCard,
  PiggyBank
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'

// Mock data for financial reports
const mockReports = [
  {
    id: '1',
    name: 'Balance Sheet',
    type: 'Financial Statement',
    description: 'Assets, liabilities, and equity as of a specific date',
    icon: Building2,
    lastGenerated: '2024-12-19',
    status: 'Ready',
    totalAssets: 36670.50,
    totalLiabilities: 4700.75,
    totalEquity: 31969.75,
    isBalanced: true
  },
  {
    id: '2',
    name: 'Income Statement',
    type: 'Financial Statement',
    description: 'Revenue, expenses, and net income for a period',
    icon: TrendingUp,
    lastGenerated: '2024-12-19',
    status: 'Ready',
    totalRevenue: 45000.00,
    totalExpenses: 5300.50,
    netIncome: 39699.50,
    isProfitable: true
  },
  {
    id: '3',
    name: 'Cash Flow Statement',
    type: 'Financial Statement',
    description: 'Cash inflows and outflows from operations, investing, and financing',
    icon: CreditCard,
    lastGenerated: '2024-12-18',
    status: 'Ready',
    operatingCashFlow: 12500.00,
    investingCashFlow: -12500.00,
    financingCashFlow: 25000.00,
    netCashFlow: 25000.00
  },
  {
    id: '4',
    name: 'Trial Balance',
    type: 'Verification Report',
    description: 'List of all accounts with their debit and credit balances',
    icon: Calculator,
    lastGenerated: '2024-12-19',
    status: 'Ready',
    totalDebits: 68320.25,
    totalCredits: 68320.25,
    isBalanced: true
  },
  {
    id: '5',
    name: 'Aged Receivables',
    type: 'Analysis Report',
    description: 'Customer receivables broken down by age',
    icon: PieChart,
    lastGenerated: '2024-12-17',
    status: 'Ready',
    current: 5000.00,
    days30: 2500.00,
    days60: 1000.00,
    days90: 250.00,
    total: 8750.00
  },
  {
    id: '6',
    name: 'Aged Payables',
    type: 'Analysis Report',
    description: 'Vendor payables broken down by age',
    icon: BarChart3,
    lastGenerated: '2024-12-17',
    status: 'Ready',
    current: 2000.00,
    days30: 1000.00,
    days60: 200.75,
    days90: 0.00,
    total: 3200.75
  }
]

const mockCustomReports = [
  {
    id: '7',
    name: 'Monthly Revenue Summary',
    type: 'Custom Report',
    description: 'Revenue breakdown by service category',
    icon: FileText,
    lastGenerated: '2024-12-19',
    status: 'Ready',
    customFields: ['Service Category', 'Revenue Amount', 'Percentage']
  },
  {
    id: '8',
    name: 'Expense Analysis',
    type: 'Custom Report',
    description: 'Detailed expense analysis by department',
    icon: PieChart,
    lastGenerated: '2024-12-18',
    status: 'Ready',
    customFields: ['Department', 'Expense Type', 'Amount', 'Variance']
  }
]

export function Win11ReportsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [selectedReport, setSelectedReport] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)

  const allReports = [...mockReports, ...mockCustomReports]
  
  const filteredReports = allReports.filter(report => {
    const matchesSearch = report.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         report.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = filterType === 'all' || report.type.toLowerCase().includes(filterType.toLowerCase())
    return matchesSearch && matchesType
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Ready': return 'text-green-600 bg-green-50'
      case 'Generating': return 'text-blue-600 bg-blue-50'
      case 'Error': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getReportIcon = (report: any) => {
    const IconComponent = report.icon
    return <IconComponent className="w-6 h-6" />
  }

  const renderReportCard = (report: any) => {
    const isSelected = selectedReport === report.id
    
    return (
      <Card 
        key={report.id}
        className={`md-card-expressive group hover:md-elevation-1 transition-all duration-200 cursor-pointer ${
          isSelected ? 'ring-2 ring-primary' : ''
        }`}
        onClick={() => setSelectedReport(report.id)}
      >
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-primary-container rounded-2xl flex items-center justify-center">
                {getReportIcon(report)}
              </div>
              <div>
                <h3 className="md-title-medium text-on-surface">{report.name}</h3>
                <p className="md-body-small text-on-surface-variant">{report.type}</p>
              </div>
            </div>
            <ChevronRight className={`w-5 h-5 text-on-surface-variant transition-transform ${
              isSelected ? 'rotate-90' : ''
            }`} />
          </div>
          
          <p className="md-body-medium text-on-surface-variant mb-4">
            {report.description}
          </p>
          
          <div className="flex items-center justify-between mb-4">
            <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium ${getStatusColor(report.status)}`}>
              {report.status}
            </span>
            <span className="text-xs text-on-surface-variant">
              Last generated: {formatDate(report.lastGenerated)}
            </span>
          </div>
          
          {/* Report-specific metrics */}
          <div className="space-y-2">
            {report.isBalanced !== undefined && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-on-surface-variant">Balanced</span>
                <span className={`font-medium ${report.isBalanced ? 'text-green-600' : 'text-red-600'}`}>
                  {report.isBalanced ? 'Yes' : 'No'}
                </span>
              </div>
            )}
            {report.isProfitable !== undefined && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-on-surface-variant">Profitable</span>
                <span className={`font-medium ${report.isProfitable ? 'text-green-600' : 'text-red-600'}`}>
                  {report.isProfitable ? 'Yes' : 'No'}
                </span>
              </div>
            )}
            {report.totalAssets && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-on-surface-variant">Total Assets</span>
                <span className="font-medium text-on-surface">
                  {formatCurrency(report.totalAssets)}
                </span>
              </div>
            )}
            {report.netIncome && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-on-surface-variant">Net Income</span>
                <span className={`font-medium ${report.netIncome >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(report.netIncome)}
                </span>
              </div>
            )}
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
              <h1 className="md-headline-small text-on-background">Financial Reports</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                Generate and analyze your financial statements
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Button 
                onClick={() => setShowCreateModal(true)}
                className="md-button"
              >
                <Plus className="w-4 h-4 mr-2" />
                New Report
              </Button>
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
                Export All
              </Button>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
              <input
                type="text"
                placeholder="Search reports by name or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-12 pl-12 pr-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                aria-label="Search reports"
              />
            </div>
            
            <div className="flex gap-3">
              <div className="relative">
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="h-12 pl-4 pr-12 py-3 bg-surface-container border border-outline rounded-2xl text-sm text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200 appearance-none cursor-pointer min-w-[160px]"
                >
                  <option value="all">All Types</option>
                  <option value="financial statement">Financial Statement</option>
                  <option value="verification report">Verification Report</option>
                  <option value="analysis report">Analysis Report</option>
                  <option value="custom report">Custom Report</option>
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
        {filteredReports.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-20 h-20 bg-primary-container rounded-3xl flex items-center justify-center mb-6">
              <BarChart3 className="w-10 h-10 text-on-primary-container" />
            </div>
            <h3 className="md-headline-small text-on-surface mb-3">No reports found</h3>
            <p className="md-body-large text-on-surface-variant text-center mb-8 max-w-md">
              {searchTerm || filterType !== 'all' 
                ? 'Try adjusting your search or filter criteria.'
                : 'Get started by generating your first financial report.'
              }
            </p>
            <Button onClick={() => setShowCreateModal(true)} className="md-button">
              <Plus className="w-4 h-4 mr-2" />
              Generate Report
            </Button>
          </div>
        ) : (
          /* Reports Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredReports.map(report => renderReportCard(report))}
          </div>
        )}

        {/* Report Details Modal/Preview */}
        {selectedReport && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
            <Card className="md-card-expressive max-w-2xl w-full max-h-[80vh] overflow-y-auto">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="md-title-large text-on-surface">
                      {allReports.find(r => r.id === selectedReport)?.name}
                    </CardTitle>
                    <CardDescription className="md-body-medium text-on-surface-variant">
                      {allReports.find(r => r.id === selectedReport)?.description}
                    </CardDescription>
                  </div>
                  <Button 
                    variant="outline" 
                    onClick={() => setSelectedReport(null)}
                    className="h-8 w-8 p-0"
                  >
                    ×
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-surface-container rounded-lg">
                      <h4 className="font-medium text-on-surface mb-2">Report Status</h4>
                      <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium ${getStatusColor(allReports.find(r => r.id === selectedReport)?.status || '')}`}>
                        {allReports.find(r => r.id === selectedReport)?.status}
                      </span>
                    </div>
                    <div className="p-4 bg-surface-container rounded-lg">
                      <h4 className="font-medium text-on-surface mb-2">Last Generated</h4>
                      <p className="text-sm text-on-surface-variant">
                        {formatDate(allReports.find(r => r.id === selectedReport)?.lastGenerated || '')}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2">
                    <Button className="flex-1">
                      <Eye className="w-4 h-4 mr-2" />
                      View Report
                    </Button>
                    <Button variant="outline" className="flex-1">
                      <Download className="w-4 h-4 mr-2" />
                      Export
                    </Button>
                    <Button variant="outline" className="flex-1">
                      <Settings className="w-4 h-4 mr-2" />
                      Settings
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}

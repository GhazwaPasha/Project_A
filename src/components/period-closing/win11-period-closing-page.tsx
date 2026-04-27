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
  Lock,
  Unlock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Calendar,
  Shield,
  Database,
  FileText,
  BarChart3,
  Settings,
  ChevronRight,
  Clock,
  Play,
  Pause,
  RotateCcw,
  Save
} from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { useOrganizationFormatters } from '@/hooks/use-organization-formatters'

// Mock data for period closing
const mockClosingSteps = [
  {
    id: '1',
    name: 'Bank Reconciliation',
    description: 'Reconcile all bank accounts for the period',
    category: 'Reconciliation',
    status: 'Completed',
    completedAt: '2024-12-19T10:30:00Z',
    completedBy: 'John Doe',
    isRequired: true,
    estimatedTime: '2 hours',
    priority: 'High'
  },
  {
    id: '2',
    name: 'Accounts Receivable Review',
    description: 'Review and age all outstanding receivables',
    category: 'Receivables',
    status: 'Completed',
    completedAt: '2024-12-19T14:15:00Z',
    completedBy: 'Jane Smith',
    isRequired: true,
    estimatedTime: '1.5 hours',
    priority: 'High'
  },
  {
    id: '3',
    name: 'Accounts Payable Review',
    description: 'Review and verify all outstanding payables',
    category: 'Payables',
    status: 'In Progress',
    completedAt: null,
    completedBy: 'Mike Johnson',
    isRequired: true,
    estimatedTime: '1 hour',
    priority: 'High'
  },
  {
    id: '4',
    name: 'Inventory Count',
    description: 'Perform physical inventory count and valuation',
    category: 'Inventory',
    status: 'Pending',
    completedAt: null,
    completedBy: 'Sarah Wilson',
    isRequired: true,
    estimatedTime: '4 hours',
    priority: 'Medium'
  },
  {
    id: '5',
    name: 'Depreciation Calculation',
    description: 'Calculate and record monthly depreciation',
    category: 'Fixed Assets',
    status: 'Pending',
    completedAt: null,
    completedBy: 'Tom Brown',
    isRequired: true,
    estimatedTime: '1 hour',
    priority: 'Medium'
  },
  {
    id: '6',
    name: 'Accrual Adjustments',
    description: 'Record all necessary accrual adjustments',
    category: 'Adjustments',
    status: 'Pending',
    completedAt: null,
    completedBy: 'Lisa Davis',
    isRequired: true,
    estimatedTime: '2 hours',
    priority: 'High'
  },
  {
    id: '7',
    name: 'Trial Balance Verification',
    description: 'Generate and verify trial balance',
    category: 'Verification',
    status: 'Pending',
    completedAt: null,
    completedBy: 'Admin',
    isRequired: true,
    estimatedTime: '30 minutes',
    priority: 'High'
  },
  {
    id: '8',
    name: 'Financial Statements',
    description: 'Generate final financial statements',
    category: 'Reporting',
    status: 'Pending',
    completedAt: null,
    completedBy: 'Admin',
    isRequired: true,
    estimatedTime: '1 hour',
    priority: 'High'
  },
  {
    id: '9',
    name: 'Backup Creation',
    description: 'Create backup of period data',
    category: 'Backup',
    status: 'Pending',
    completedAt: null,
    completedBy: 'System',
    isRequired: true,
    estimatedTime: '15 minutes',
    priority: 'High'
  },
  {
    id: '10',
    name: 'Period Lock',
    description: 'Lock the period to prevent further changes',
    category: 'Security',
    status: 'Pending',
    completedAt: null,
    completedBy: 'Admin',
    isRequired: true,
    estimatedTime: '5 minutes',
    priority: 'High'
  }
]

const mockClosingStatus = {
  period: 'December 2024',
  startDate: '2024-12-01',
  endDate: '2024-12-31',
  isLocked: false,
  canClose: false,
  completedSteps: 2,
  totalSteps: 10,
  progress: 20,
  lastBackup: '2024-12-18T16:30:00Z',
  nextScheduledBackup: '2024-12-20T16:30:00Z'
}

export function Win11PeriodClosingPage() {
  const { formatCurrency } = useOrganizationFormatters()
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterCategory, setFilterCategory] = useState('all')
  const [selectedStep, setSelectedStep] = useState<string | null>(null)
  const [isClosing, setIsClosing] = useState(false)
  const [showBackupModal, setShowBackupModal] = useState(false)

  const filteredSteps = mockClosingSteps.filter(step => {
    const matchesSearch = step.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         step.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         step.category.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = filterStatus === 'all' || step.status.toLowerCase() === filterStatus.toLowerCase()
    const matchesCategory = filterCategory === 'all' || step.category.toLowerCase() === filterCategory.toLowerCase()
    return matchesSearch && matchesStatus && matchesCategory
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Completed': return 'text-green-600 bg-green-50'
      case 'In Progress': return 'text-blue-600 bg-blue-50'
      case 'Pending': return 'text-orange-600 bg-orange-50'
      case 'Failed': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Completed': return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'In Progress': return <Clock className="w-4 h-4 text-blue-600" />
      case 'Pending': return <AlertTriangle className="w-4 h-4 text-orange-600" />
      case 'Failed': return <XCircle className="w-4 h-4 text-red-600" />
      default: return <Clock className="w-4 h-4 text-gray-600" />
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'High': return 'text-red-600 bg-red-50'
      case 'Medium': return 'text-yellow-600 bg-yellow-50'
      case 'Low': return 'text-green-600 bg-green-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'Reconciliation': return <BarChart3 className="w-4 h-4" />
      case 'Receivables': return <FileText className="w-4 h-4" />
      case 'Payables': return <FileText className="w-4 h-4" />
      case 'Inventory': return <Database className="w-4 h-4" />
      case 'Fixed Assets': return <Settings className="w-4 h-4" />
      case 'Adjustments': return <Settings className="w-4 h-4" />
      case 'Verification': return <CheckCircle className="w-4 h-4" />
      case 'Reporting': return <BarChart3 className="w-4 h-4" />
      case 'Backup': return <Database className="w-4 h-4" />
      case 'Security': return <Shield className="w-4 h-4" />
      default: return <FileText className="w-4 h-4" />
    }
  }

  const renderStepCard = (step: any) => {
    const isSelected = selectedStep === step.id
    
    return (
      <Card 
        key={step.id}
        className={`md-card-expressive group hover:md-elevation-1 transition-all duration-200 cursor-pointer ${
          isSelected ? 'ring-2 ring-primary' : ''
        }`}
        onClick={() => setSelectedStep(step.id)}
      >
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-primary-container rounded-xl flex items-center justify-center">
                {getCategoryIcon(step.category)}
              </div>
              <div>
                <h3 className="md-title-medium text-on-surface">{step.name}</h3>
                <p className="md-body-small text-on-surface-variant">{step.category}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {getStatusIcon(step.status)}
              <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium ${getStatusColor(step.status)}`}>
                {step.status}
              </span>
            </div>
          </div>
          
          <p className="md-body-medium text-on-surface-variant mb-4">
            {step.description}
          </p>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-on-surface-variant">Priority</span>
              <span className={`inline-block px-2 py-0.5 rounded-md text-xs font-medium ${getPriorityColor(step.priority)}`}>
                {step.priority}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-on-surface-variant">Estimated Time</span>
              <span className="text-on-surface font-medium">{step.estimatedTime}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-on-surface-variant">Assigned to</span>
              <span className="text-on-surface">{step.completedBy}</span>
            </div>
            {step.completedAt && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-on-surface-variant">Completed</span>
                <span className="text-green-600 font-medium">{formatDate(step.completedAt)}</span>
              </div>
            )}
            {step.isRequired && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-on-surface-variant">Required</span>
                <span className="text-red-600 font-medium">Yes</span>
              </div>
            )}
          </div>
          
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-outline-variant">
            <div className="flex items-center space-x-1">
              {step.status === 'Completed' ? (
                <CheckCircle className="w-5 h-5 text-green-600" />
              ) : step.status === 'In Progress' ? (
                <Pause className="w-5 h-5 text-blue-600" />
              ) : (
                <Play className="w-5 h-5 text-gray-400" />
              )}
            </div>
            <div className="flex items-center space-x-1">
              <button className="p-1 hover:bg-surface-container-highest rounded">
                <Settings className="w-4 h-4" />
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
      <div className="app-page-header sticky top-0 z-30">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="md-headline-small text-on-background">Period Closing</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                {mockClosingStatus.period} • {mockClosingStatus.completedSteps}/{mockClosingStatus.totalSteps} steps completed
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Button 
                onClick={() => setShowBackupModal(true)}
                variant="outline"
                className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container"
              >
                <Database className="w-4 h-4 mr-2" />
                Backup
              </Button>
              <Button 
                onClick={() => setIsClosing(true)}
                disabled={!mockClosingStatus.canClose || isClosing}
                className="md-button"
              >
                {isClosing ? (
                  <>
                    <Clock className="w-4 h-4 mr-2" />
                    Closing...
                  </>
                ) : (
                  <>
                    <Lock className="w-4 h-4 mr-2" />
                    Close Period
                  </>
                )}
              </Button>
              <Button 
                onClick={() => window.location.reload()}
                variant="outline"
                className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-on-surface">Closing Progress</span>
              <span className="text-sm text-on-surface-variant">{mockClosingStatus.progress}%</span>
            </div>
            <div className="w-full bg-surface-container rounded-full h-2">
              <div 
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{ width: `${mockClosingStatus.progress}%` }}
              ></div>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
              <input
                type="text"
                placeholder="Search closing steps..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-12 pl-12 pr-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                aria-label="Search closing steps"
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
                  <option value="pending">Pending</option>
                  <option value="in progress">In Progress</option>
                  <option value="completed">Completed</option>
                </select>
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
                  <svg className="w-4 h-4 text-on-surface-variant" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
              <div className="relative">
                <select
                  value={filterCategory}
                  onChange={(e) => setFilterCategory(e.target.value)}
                  className="h-12 pl-4 pr-12 py-3 bg-surface-container border border-outline rounded-2xl text-sm text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200 appearance-none cursor-pointer min-w-[160px]"
                >
                  <option value="all">All Categories</option>
                  <option value="reconciliation">Reconciliation</option>
                  <option value="receivables">Receivables</option>
                  <option value="payables">Payables</option>
                  <option value="inventory">Inventory</option>
                  <option value="fixed assets">Fixed Assets</option>
                  <option value="adjustments">Adjustments</option>
                  <option value="verification">Verification</option>
                  <option value="reporting">Reporting</option>
                  <option value="backup">Backup</option>
                  <option value="security">Security</option>
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
        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card className="md-card-expressive">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-on-surface-variant">Period Status</p>
                  <p className="text-lg font-bold text-on-surface">
                    {mockClosingStatus.isLocked ? 'Locked' : 'Open'}
                  </p>
                </div>
                {mockClosingStatus.isLocked ? (
                  <Lock className="w-8 h-8 text-red-600" />
                ) : (
                  <Unlock className="w-8 h-8 text-green-600" />
                )}
              </div>
            </CardContent>
          </Card>
          <Card className="md-card-expressive">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-on-surface-variant">Completed Steps</p>
                  <p className="text-2xl font-bold text-green-600">
                    {mockClosingStatus.completedSteps}
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
                  <p className="text-sm text-on-surface-variant">Remaining Steps</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {mockClosingStatus.totalSteps - mockClosingStatus.completedSteps}
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
                  <p className="text-sm text-on-surface-variant">Last Backup</p>
                  <p className="text-sm font-bold text-on-surface">
                    {formatDate(mockClosingStatus.lastBackup)}
                  </p>
                </div>
                <Database className="w-8 h-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {filteredSteps.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-20 h-20 bg-primary-container rounded-3xl flex items-center justify-center mb-6">
              <Lock className="w-10 h-10 text-on-primary-container" />
            </div>
            <h3 className="md-headline-small text-on-surface mb-3">No closing steps found</h3>
            <p className="md-body-large text-on-surface-variant text-center mb-8 max-w-md">
              {searchTerm || filterStatus !== 'all' || filterCategory !== 'all'
                ? 'Try adjusting your search or filter criteria.'
                : 'All closing steps are ready to be executed.'
              }
            </p>
          </div>
        ) : (
          /* Closing Steps Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredSteps.map(step => renderStepCard(step))}
          </div>
        )}
      </div>
    </div>
  )
}

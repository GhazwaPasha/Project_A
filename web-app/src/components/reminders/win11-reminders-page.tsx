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
  CheckSquare,
  Clock,
  AlertTriangle,
  Calendar,
  User,
  Flag,
  Edit,
  Trash2,
  Eye,
  ChevronRight,
  CheckCircle,
  XCircle,
  MoreVertical
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'

// Mock data for reminders
const mockReminders = [
  {
    id: '1',
    title: 'Month-End Closing',
    description: 'Complete month-end closing procedures for December 2024',
    type: 'Closing',
    priority: 'High',
    status: 'Pending',
    dueDate: '2024-12-31',
    assignedTo: 'John Doe',
    createdBy: 'Admin',
    createdAt: '2024-12-15',
    completedAt: null,
    isOverdue: false,
    daysUntilDue: 12
  },
  {
    id: '2',
    title: 'Bank Reconciliation',
    description: 'Reconcile bank statements for November 2024',
    type: 'Reconciliation',
    priority: 'Medium',
    status: 'In Progress',
    dueDate: '2024-12-25',
    assignedTo: 'Jane Smith',
    createdBy: 'John Doe',
    createdAt: '2024-12-10',
    completedAt: null,
    isOverdue: false,
    daysUntilDue: 6
  },
  {
    id: '3',
    title: 'Tax Filing Preparation',
    description: 'Prepare documents for quarterly tax filing',
    type: 'Tax',
    priority: 'High',
    status: 'Pending',
    dueDate: '2024-12-20',
    assignedTo: 'Mike Johnson',
    createdBy: 'Admin',
    createdAt: '2024-12-01',
    completedAt: null,
    isOverdue: true,
    daysUntilDue: -1
  },
  {
    id: '4',
    title: 'Invoice #INV-2024-001',
    description: 'Follow up on overdue payment for Invoice #INV-2024-001',
    type: 'Collection',
    priority: 'Medium',
    status: 'Completed',
    dueDate: '2024-12-15',
    assignedTo: 'Sarah Wilson',
    createdBy: 'Jane Smith',
    createdAt: '2024-11-20',
    completedAt: '2024-12-18',
    isOverdue: false,
    daysUntilDue: 0
  },
  {
    id: '5',
    title: 'Equipment Depreciation',
    description: 'Calculate and record monthly equipment depreciation',
    type: 'Accounting',
    priority: 'Low',
    status: 'Pending',
    dueDate: '2024-12-30',
    assignedTo: 'Tom Brown',
    createdBy: 'Mike Johnson',
    createdAt: '2024-12-05',
    completedAt: null,
    isOverdue: false,
    daysUntilDue: 11
  },
  {
    id: '6',
    title: 'Vendor Payment Review',
    description: 'Review and approve pending vendor payments',
    type: 'Payments',
    priority: 'Medium',
    status: 'In Progress',
    dueDate: '2024-12-22',
    assignedTo: 'Lisa Davis',
    createdBy: 'Admin',
    createdAt: '2024-12-12',
    completedAt: null,
    isOverdue: false,
    daysUntilDue: 3
  }
]

export function Win11RemindersPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterPriority, setFilterPriority] = useState('all')
  const [selectedReminder, setSelectedReminder] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)

  const filteredReminders = mockReminders.filter(reminder => {
    const matchesSearch = reminder.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         reminder.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         reminder.assignedTo.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = filterStatus === 'all' || reminder.status.toLowerCase() === filterStatus.toLowerCase()
    const matchesPriority = filterPriority === 'all' || reminder.priority.toLowerCase() === filterPriority.toLowerCase()
    return matchesSearch && matchesStatus && matchesPriority
  })

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'High': return 'text-red-600 bg-red-50'
      case 'Medium': return 'text-yellow-600 bg-yellow-50'
      case 'Low': return 'text-green-600 bg-green-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Completed': return 'text-green-600 bg-green-50'
      case 'In Progress': return 'text-blue-600 bg-blue-50'
      case 'Pending': return 'text-orange-600 bg-orange-50'
      case 'Overdue': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'Closing': return <Calendar className="w-4 h-4" />
      case 'Reconciliation': return <CheckSquare className="w-4 h-4" />
      case 'Tax': return <Flag className="w-4 h-4" />
      case 'Collection': return <User className="w-4 h-4" />
      case 'Accounting': return <CheckCircle className="w-4 h-4" />
      case 'Payments': return <Clock className="w-4 h-4" />
      default: return <AlertTriangle className="w-4 h-4" />
    }
  }

  const getDueDateColor = (reminder: any) => {
    if (reminder.isOverdue) return 'text-red-600'
    if (reminder.daysUntilDue <= 3) return 'text-orange-600'
    if (reminder.daysUntilDue <= 7) return 'text-yellow-600'
    return 'text-green-600'
  }

  const getDueDateText = (reminder: any) => {
    if (reminder.isOverdue) return `${Math.abs(reminder.daysUntilDue)} days overdue`
    if (reminder.daysUntilDue === 0) return 'Due today'
    if (reminder.daysUntilDue === 1) return 'Due tomorrow'
    return `Due in ${reminder.daysUntilDue} days`
  }

  const renderReminderCard = (reminder: any) => {
    const isSelected = selectedReminder === reminder.id
    
    return (
      <Card 
        key={reminder.id}
        className={`md-card-expressive group hover:md-elevation-1 transition-all duration-200 cursor-pointer ${
          isSelected ? 'ring-2 ring-primary' : ''
        } ${reminder.isOverdue ? 'border-l-4 border-l-red-500' : ''}`}
        onClick={() => setSelectedReminder(reminder.id)}
      >
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-primary-container rounded-xl flex items-center justify-center">
                {getTypeIcon(reminder.type)}
              </div>
              <div>
                <h3 className="md-title-medium text-on-surface">{reminder.title}</h3>
                <p className="md-body-small text-on-surface-variant">{reminder.type}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium ${getPriorityColor(reminder.priority)}`}>
                {reminder.priority}
              </span>
              <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium ${getStatusColor(reminder.status)}`}>
                {reminder.status}
              </span>
            </div>
          </div>
          
          <p className="md-body-medium text-on-surface-variant mb-4">
            {reminder.description}
          </p>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-on-surface-variant">Assigned to</span>
              <span className="text-on-surface font-medium">{reminder.assignedTo}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-on-surface-variant">Due Date</span>
              <span className={`font-medium ${getDueDateColor(reminder)}`}>
                {formatDate(reminder.dueDate)} ({getDueDateText(reminder)})
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-on-surface-variant">Created by</span>
              <span className="text-on-surface">{reminder.createdBy}</span>
            </div>
            {reminder.completedAt && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-on-surface-variant">Completed</span>
                <span className="text-green-600 font-medium">{formatDate(reminder.completedAt)}</span>
              </div>
            )}
          </div>
          
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-outline-variant">
            <div className="flex items-center space-x-1">
              <button className="p-1 hover:bg-surface-container-highest rounded">
                <Eye className="w-4 h-4" />
              </button>
              <button className="p-1 hover:bg-surface-container-highest rounded">
                <Edit className="w-4 h-4" />
              </button>
              <button className="p-1 hover:bg-surface-container-highest rounded text-red-600">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
            <div className="flex items-center space-x-1">
              {reminder.status === 'Completed' ? (
                <CheckCircle className="w-5 h-5 text-green-600" />
              ) : (
                <button className="p-1 hover:bg-surface-container-highest rounded">
                  <CheckCircle className="w-5 h-5 text-gray-400" />
                </button>
              )}
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
              <h1 className="md-headline-small text-on-background">Reminders & Tasks</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                Manage deadlines and track task progress
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Button 
                onClick={() => setShowCreateModal(true)}
                className="md-button"
              >
                <Plus className="w-4 h-4 mr-2" />
                New Reminder
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
                placeholder="Search reminders by title, description, or assignee..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-12 pl-12 pr-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                aria-label="Search reminders"
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
                  <option value="overdue">Overdue</option>
                </select>
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
                  <svg className="w-4 h-4 text-on-surface-variant" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
              <div className="relative">
                <select
                  value={filterPriority}
                  onChange={(e) => setFilterPriority(e.target.value)}
                  className="h-12 pl-4 pr-12 py-3 bg-surface-container border border-outline rounded-2xl text-sm text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200 appearance-none cursor-pointer min-w-[140px]"
                >
                  <option value="all">All Priority</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
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
                  <p className="text-sm text-on-surface-variant">Total Tasks</p>
                  <p className="text-2xl font-bold text-on-surface">{mockReminders.length}</p>
                </div>
                <CheckSquare className="w-8 h-8 text-primary" />
              </div>
            </CardContent>
          </Card>
          <Card className="md-card-expressive">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-on-surface-variant">Pending</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {mockReminders.filter(r => r.status === 'Pending').length}
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
                  <p className="text-sm text-on-surface-variant">Completed</p>
                  <p className="text-2xl font-bold text-green-600">
                    {mockReminders.filter(r => r.status === 'Completed').length}
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
                  <p className="text-sm text-on-surface-variant">Overdue</p>
                  <p className="text-2xl font-bold text-red-600">
                    {mockReminders.filter(r => r.isOverdue).length}
                  </p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {filteredReminders.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-20 h-20 bg-primary-container rounded-3xl flex items-center justify-center mb-6">
              <CheckSquare className="w-10 h-10 text-on-primary-container" />
            </div>
            <h3 className="md-headline-small text-on-surface mb-3">No reminders found</h3>
            <p className="md-body-large text-on-surface-variant text-center mb-8 max-w-md">
              {searchTerm || filterStatus !== 'all' || filterPriority !== 'all'
                ? 'Try adjusting your search or filter criteria.'
                : 'Get started by creating your first reminder.'
              }
            </p>
            <Button onClick={() => setShowCreateModal(true)} className="md-button">
              <Plus className="w-4 h-4 mr-2" />
              Create Reminder
            </Button>
          </div>
        ) : (
          /* Reminders Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredReminders.map(reminder => renderReminderCard(reminder))}
          </div>
        )}
      </div>
    </div>
  )
}

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
  Users,
  UserPlus,
  Shield,
  Crown,
  User,
  Mail,
  Phone,
  Calendar,
  Settings,
  Edit,
  Trash2,
  Eye,
  ChevronRight,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  MoreVertical,
  Lock,
  Unlock,
  Ban,
  CheckSquare,
  UserCheck,
  UserX
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'

// Mock data for users
const mockUsers = [
  {
    id: '1',
    name: 'John Doe',
    email: 'john.doe@company.com',
    role: 'Admin',
    department: 'Finance',
    status: 'Active',
    lastActive: '2024-12-19T14:30:00Z',
    joinDate: '2024-01-15',
    permissions: ['Full Access', 'User Management', 'Financial Reports', 'System Settings'],
    avatar: 'JD',
    phone: '+1 (555) 123-4567',
    isOnline: true,
    loginCount: 156,
    lastLogin: '2024-12-19T14:30:00Z',
    failedLogins: 0,
    isLocked: false
  },
  {
    id: '2',
    name: 'Jane Smith',
    email: 'jane.smith@company.com',
    role: 'Manager',
    department: 'Accounting',
    status: 'Active',
    lastActive: '2024-12-19T13:45:00Z',
    joinDate: '2024-03-20',
    permissions: ['Financial Reports', 'Journal Entries', 'Ledger Access', 'Reports'],
    avatar: 'JS',
    phone: '+1 (555) 234-5678',
    isOnline: true,
    loginCount: 89,
    lastLogin: '2024-12-19T13:45:00Z',
    failedLogins: 1,
    isLocked: false
  },
  {
    id: '3',
    name: 'Mike Johnson',
    email: 'mike.johnson@company.com',
    role: 'Accountant',
    department: 'Accounting',
    status: 'Active',
    lastActive: '2024-12-19T12:15:00Z',
    joinDate: '2024-06-10',
    permissions: ['Journal Entries', 'Ledger Access', 'Basic Reports'],
    avatar: 'MJ',
    phone: '+1 (555) 345-6789',
    isOnline: false,
    loginCount: 67,
    lastLogin: '2024-12-18T17:20:00Z',
    failedLogins: 0,
    isLocked: false
  },
  {
    id: '4',
    name: 'Sarah Wilson',
    email: 'sarah.wilson@company.com',
    role: 'Accountant',
    department: 'Accounting',
    status: 'Pending',
    lastActive: '2024-12-18T16:20:00Z',
    joinDate: '2024-12-01',
    permissions: ['Journal Entries', 'Ledger Access'],
    avatar: 'SW',
    phone: '+1 (555) 456-7890',
    isOnline: false,
    loginCount: 0,
    lastLogin: null,
    failedLogins: 0,
    isLocked: false
  },
  {
    id: '5',
    name: 'Tom Brown',
    email: 'tom.brown@company.com',
    role: 'Viewer',
    department: 'Management',
    status: 'Active',
    lastActive: '2024-12-19T10:30:00Z',
    joinDate: '2024-08-15',
    permissions: ['Basic Reports', 'Dashboard Access'],
    avatar: 'TB',
    phone: '+1 (555) 567-8901',
    isOnline: true,
    loginCount: 34,
    lastLogin: '2024-12-19T10:30:00Z',
    failedLogins: 0,
    isLocked: false
  },
  {
    id: '6',
    name: 'Lisa Davis',
    email: 'lisa.davis@company.com',
    role: 'Accountant',
    department: 'Accounting',
    status: 'Suspended',
    lastActive: '2024-11-30T17:45:00Z',
    joinDate: '2024-02-28',
    permissions: ['Journal Entries', 'Ledger Access', 'Basic Reports'],
    avatar: 'LD',
    phone: '+1 (555) 678-9012',
    isOnline: false,
    loginCount: 45,
    lastLogin: '2024-11-30T17:45:00Z',
    failedLogins: 3,
    isLocked: true
  },
  {
    id: '7',
    name: 'Alex Chen',
    email: 'alex.chen@company.com',
    role: 'Accountant',
    department: 'Accounting',
    status: 'Inactive',
    lastActive: '2024-12-10T14:20:00Z',
    joinDate: '2024-04-15',
    permissions: ['Journal Entries', 'Ledger Access', 'Basic Reports'],
    avatar: 'AC',
    phone: '+1 (555) 789-0123',
    isOnline: false,
    loginCount: 78,
    lastLogin: '2024-12-10T14:20:00Z',
    failedLogins: 0,
    isLocked: false
  },
  {
    id: '8',
    name: 'Maria Garcia',
    email: 'maria.garcia@company.com',
    role: 'Manager',
    department: 'Operations',
    status: 'Active',
    lastActive: '2024-12-19T11:15:00Z',
    joinDate: '2024-07-01',
    permissions: ['Financial Reports', 'Team Management', 'Reports', 'Dashboard Access'],
    avatar: 'MG',
    phone: '+1 (555) 890-1234',
    isOnline: false,
    loginCount: 92,
    lastLogin: '2024-12-19T11:15:00Z',
    failedLogins: 0,
    isLocked: false
  }
]

export function Win11UserManagementPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterRole, setFilterRole] = useState('all')
  const [filterStatus, setFilterStatus] = useState('all')
  const [selectedUser, setSelectedUser] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showBulkActions, setShowBulkActions] = useState(false)

  const filteredUsers = mockUsers.filter(user => {
    const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.department.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesRole = filterRole === 'all' || user.role.toLowerCase() === filterRole.toLowerCase()
    const matchesStatus = filterStatus === 'all' || user.status.toLowerCase() === filterStatus.toLowerCase()
    return matchesSearch && matchesRole && matchesStatus
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Active': return 'text-green-600 bg-green-50'
      case 'Pending': return 'text-yellow-600 bg-yellow-50'
      case 'Inactive': return 'text-gray-600 bg-gray-50'
      case 'Suspended': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Active': return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'Pending': return <Clock className="w-4 h-4 text-yellow-600" />
      case 'Inactive': return <XCircle className="w-4 h-4 text-gray-600" />
      case 'Suspended': return <AlertTriangle className="w-4 h-4 text-red-600" />
      default: return <Clock className="w-4 h-4 text-gray-600" />
    }
  }

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'Admin': return <Crown className="w-4 h-4 text-red-600" />
      case 'Manager': return <Shield className="w-4 h-4 text-blue-600" />
      case 'Accountant': return <User className="w-4 h-4 text-green-600" />
      case 'Viewer': return <Eye className="w-4 h-4 text-gray-600" />
      default: return <User className="w-4 h-4 text-gray-600" />
    }
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'Admin': return 'text-red-600 bg-red-50'
      case 'Manager': return 'text-blue-600 bg-blue-50'
      case 'Accountant': return 'text-green-600 bg-green-50'
      case 'Viewer': return 'text-gray-600 bg-gray-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const renderUserCard = (user: any) => {
    const isSelected = selectedUser === user.id
    
    return (
      <Card 
        key={user.id}
        className={`md-card-expressive group hover:md-elevation-1 transition-all duration-200 cursor-pointer ${
          isSelected ? 'ring-2 ring-primary' : ''
        } ${user.isLocked ? 'border-l-4 border-l-red-500' : ''}`}
        onClick={() => setSelectedUser(user.id)}
      >
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="w-12 h-12 bg-primary-container rounded-full flex items-center justify-center">
                  <span className="text-sm font-semibold text-on-primary-container">
                    {user.avatar}
                  </span>
                </div>
                {user.isOnline && (
                  <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-primary rounded-full border-2 border-background" />
                )}
                {user.isLocked && (
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-error rounded-full border-2 border-background flex items-center justify-center">
                    <Lock className="w-2 h-2 text-on-error" />
                  </div>
                )}
              </div>
              <div>
                <h3 className="md-title-medium text-on-surface">{user.name}</h3>
                <p className="md-body-small text-on-surface-variant">{user.department}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {getStatusIcon(user.status)}
              <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium ${getStatusColor(user.status)}`}>
                {user.status}
              </span>
            </div>
          </div>
          
          <div className="space-y-2 mb-4">
            <div className="flex items-center space-x-2 text-sm">
              <Mail className="w-4 h-4 text-on-surface-variant" />
              <span className="text-on-surface-variant">{user.email}</span>
            </div>
            <div className="flex items-center space-x-2 text-sm">
              <Phone className="w-4 h-4 text-on-surface-variant" />
              <span className="text-on-surface-variant">{user.phone}</span>
            </div>
            <div className="flex items-center space-x-2 text-sm">
              <Calendar className="w-4 h-4 text-on-surface-variant" />
              <span className="text-on-surface-variant">Joined {formatDate(user.joinDate)}</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              {getRoleIcon(user.role)}
              <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium ${getRoleColor(user.role)}`}>
                {user.role}
              </span>
            </div>
            <span className="text-xs text-on-surface-variant">
              Last active: {formatDate(user.lastActive)}
            </span>
          </div>

          {/* User Statistics */}
          <div className="grid grid-cols-2 gap-4 mb-4 p-3 bg-surface-container rounded-lg">
            <div>
              <p className="text-xs text-on-surface-variant">Login Count</p>
              <p className="text-sm font-semibold text-on-surface">{user.loginCount}</p>
            </div>
            <div>
              <p className="text-xs text-on-surface-variant">Failed Logins</p>
              <p className={`text-sm font-semibold ${user.failedLogins > 0 ? 'text-red-600' : 'text-on-surface'}`}>
                {user.failedLogins}
              </p>
            </div>
          </div>
          
          <div className="space-y-1">
            <p className="text-xs text-on-surface-variant">Permissions:</p>
            <div className="flex flex-wrap gap-1">
              {user.permissions.slice(0, 2).map((permission: string, index: number) => (
                <span key={index} className="text-xs bg-surface-container text-on-surface-variant px-2 py-1 rounded">
                  {permission}
                </span>
              ))}
              {user.permissions.length > 2 && (
                <span className="text-xs bg-surface-container text-on-surface-variant px-2 py-1 rounded">
                  +{user.permissions.length - 2} more
                </span>
              )}
            </div>
          </div>
          
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-outline-variant">
            <div className="flex items-center space-x-1">
              <button className="p-1 hover:bg-surface-container-highest rounded">
                <Eye className="w-4 h-4" />
              </button>
              <button className="p-1 hover:bg-surface-container-highest rounded">
                <Edit className="w-4 h-4" />
              </button>
              {user.isLocked ? (
                <button className="p-1 hover:bg-surface-container-highest rounded text-green-600">
                  <Unlock className="w-4 h-4" />
                </button>
              ) : (
                <button className="p-1 hover:bg-surface-container-highest rounded text-red-600">
                  <Lock className="w-4 h-4" />
                </button>
              )}
              <button className="p-1 hover:bg-surface-container-highest rounded text-red-600">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
            <button className="p-1 hover:bg-surface-container-highest rounded">
              <MoreVertical className="w-4 h-4" />
            </button>
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
              <h1 className="md-headline-small text-on-background">User Management</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                Manage user accounts, roles, and permissions
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Button 
                onClick={() => setShowCreateModal(true)}
                className="md-button"
              >
                <UserPlus className="w-4 h-4 mr-2" />
                Add User
              </Button>
              <Button 
                onClick={() => setShowBulkActions(true)}
                variant="outline"
                className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container"
              >
                <CheckSquare className="w-4 h-4 mr-2" />
                Bulk Actions
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
                placeholder="Search users by name, email, or department..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-12 pl-12 pr-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                aria-label="Search users"
              />
            </div>
            
            <div className="flex gap-3">
              <div className="relative">
                <select
                  value={filterRole}
                  onChange={(e) => setFilterRole(e.target.value)}
                  className="h-12 pl-4 pr-12 py-3 bg-surface-container border border-outline rounded-2xl text-sm text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200 appearance-none cursor-pointer min-w-[140px]"
                >
                  <option value="all">All Roles</option>
                  <option value="admin">Admin</option>
                  <option value="manager">Manager</option>
                  <option value="accountant">Accountant</option>
                  <option value="viewer">Viewer</option>
                </select>
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
                  <svg className="w-4 h-4 text-on-surface-variant" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
              <div className="relative">
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="h-12 pl-4 pr-12 py-3 bg-surface-container border border-outline rounded-2xl text-sm text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200 appearance-none cursor-pointer min-w-[140px]"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="pending">Pending</option>
                  <option value="inactive">Inactive</option>
                  <option value="suspended">Suspended</option>
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
                  <p className="text-sm text-on-surface-variant">Total Users</p>
                  <p className="text-2xl font-bold text-on-surface">{mockUsers.length}</p>
                </div>
                <Users className="w-8 h-8 text-primary" />
              </div>
            </CardContent>
          </Card>
          <Card className="md-card-expressive">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-on-surface-variant">Active Users</p>
                  <p className="text-2xl font-bold text-green-600">
                    {mockUsers.filter(u => u.status === 'Active').length}
                  </p>
                </div>
                <UserCheck className="w-8 h-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
          <Card className="md-card-expressive">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-on-surface-variant">Online Now</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {mockUsers.filter(u => u.isOnline).length}
                  </p>
                </div>
                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                  <div className="w-3 h-3 bg-white rounded-full"></div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="md-card-expressive">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-on-surface-variant">Locked Accounts</p>
                  <p className="text-2xl font-bold text-red-600">
                    {mockUsers.filter(u => u.isLocked).length}
                  </p>
                </div>
                <Lock className="w-8 h-8 text-red-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {filteredUsers.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-20 h-20 bg-primary-container rounded-3xl flex items-center justify-center mb-6">
              <Users className="w-10 h-10 text-on-primary-container" />
            </div>
            <h3 className="md-headline-small text-on-surface mb-3">No users found</h3>
            <p className="md-body-large text-on-surface-variant text-center mb-8 max-w-md">
              {searchTerm || filterRole !== 'all' || filterStatus !== 'all'
                ? 'Try adjusting your search or filter criteria.'
                : 'Get started by adding your first user.'
              }
            </p>
            <Button onClick={() => setShowCreateModal(true)} className="md-button">
              <UserPlus className="w-4 h-4 mr-2" />
              Add User
            </Button>
          </div>
        ) : (
          /* Users Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredUsers.map(user => renderUserCard(user))}
          </div>
        )}
      </div>
    </div>
  )
}

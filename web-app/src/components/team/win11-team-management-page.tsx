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
  MoreVertical
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'

// Mock data for team members
const mockTeamMembers = [
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
    isOnline: true
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
    isOnline: true
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
    isOnline: false
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
    isOnline: false
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
    isOnline: true
  },
  {
    id: '6',
    name: 'Lisa Davis',
    email: 'lisa.davis@company.com',
    role: 'Accountant',
    department: 'Accounting',
    status: 'Inactive',
    lastActive: '2024-11-30T17:45:00Z',
    joinDate: '2024-02-28',
    permissions: ['Journal Entries', 'Ledger Access', 'Basic Reports'],
    avatar: 'LD',
    phone: '+1 (555) 678-9012',
    isOnline: false
  }
]

const mockRoles = [
  {
    id: '1',
    name: 'Admin',
    description: 'Full system access and user management',
    permissions: ['Full Access', 'User Management', 'Financial Reports', 'System Settings', 'Backup & Restore'],
    memberCount: 1,
    color: 'text-red-600 bg-red-50'
  },
  {
    id: '2',
    name: 'Manager',
    description: 'Financial reports and team oversight',
    permissions: ['Financial Reports', 'Journal Entries', 'Ledger Access', 'Reports', 'Team Overview'],
    memberCount: 1,
    color: 'text-blue-600 bg-blue-50'
  },
  {
    id: '3',
    name: 'Accountant',
    description: 'Daily accounting operations',
    permissions: ['Journal Entries', 'Ledger Access', 'Basic Reports', 'Trial Balance'],
    memberCount: 3,
    color: 'text-green-600 bg-green-50'
  },
  {
    id: '4',
    name: 'Viewer',
    description: 'Read-only access to reports',
    permissions: ['Basic Reports', 'Dashboard Access', 'Read-only Ledger'],
    memberCount: 1,
    color: 'text-gray-600 bg-gray-50'
  }
]

export function Win11TeamManagementPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterRole, setFilterRole] = useState('all')
  const [filterStatus, setFilterStatus] = useState('all')
  const [selectedMember, setSelectedMember] = useState<string | null>(null)
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [activeTab, setActiveTab] = useState('members') // 'members' or 'roles'

  const filteredMembers = mockTeamMembers.filter(member => {
    const matchesSearch = member.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         member.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         member.department.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesRole = filterRole === 'all' || member.role.toLowerCase() === filterRole.toLowerCase()
    const matchesStatus = filterStatus === 'all' || member.status.toLowerCase() === filterStatus.toLowerCase()
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

  const renderMemberCard = (member: any) => {
    const isSelected = selectedMember === member.id
    
    return (
      <Card 
        key={member.id}
        className={`md-card-expressive group hover:md-elevation-1 transition-all duration-200 cursor-pointer ${
          isSelected ? 'ring-2 ring-primary' : ''
        }`}
        onClick={() => setSelectedMember(member.id)}
      >
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="w-12 h-12 bg-primary-container rounded-full flex items-center justify-center">
                  <span className="text-sm font-semibold text-on-primary-container">
                    {member.avatar}
                  </span>
                </div>
                {member.isOnline && (
                  <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white"></div>
                )}
              </div>
              <div>
                <h3 className="md-title-medium text-on-surface">{member.name}</h3>
                <p className="md-body-small text-on-surface-variant">{member.department}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {getStatusIcon(member.status)}
              <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium ${getStatusColor(member.status)}`}>
                {member.status}
              </span>
            </div>
          </div>
          
          <div className="space-y-2 mb-4">
            <div className="flex items-center space-x-2 text-sm">
              <Mail className="w-4 h-4 text-on-surface-variant" />
              <span className="text-on-surface-variant">{member.email}</span>
            </div>
            <div className="flex items-center space-x-2 text-sm">
              <Phone className="w-4 h-4 text-on-surface-variant" />
              <span className="text-on-surface-variant">{member.phone}</span>
            </div>
            <div className="flex items-center space-x-2 text-sm">
              <Calendar className="w-4 h-4 text-on-surface-variant" />
              <span className="text-on-surface-variant">Joined {formatDate(member.joinDate)}</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              {getRoleIcon(member.role)}
              <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium ${getRoleColor(member.role)}`}>
                {member.role}
              </span>
            </div>
            <span className="text-xs text-on-surface-variant">
              Last active: {formatDate(member.lastActive)}
            </span>
          </div>
          
          <div className="space-y-1">
            <p className="text-xs text-on-surface-variant">Permissions:</p>
            <div className="flex flex-wrap gap-1">
              {member.permissions.slice(0, 3).map((permission: string, index: number) => (
                <span key={index} className="text-xs bg-surface-container text-on-surface-variant px-2 py-1 rounded">
                  {permission}
                </span>
              ))}
              {member.permissions.length > 3 && (
                <span className="text-xs bg-surface-container text-on-surface-variant px-2 py-1 rounded">
                  +{member.permissions.length - 3} more
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

  const renderRoleCard = (role: any) => {
    return (
      <Card key={role.id} className="md-card-expressive group hover:md-elevation-1 transition-all duration-200">
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-primary-container rounded-xl flex items-center justify-center">
                {getRoleIcon(role.name)}
              </div>
              <div>
                <h3 className="md-title-medium text-on-surface">{role.name}</h3>
                <p className="md-body-small text-on-surface-variant">{role.memberCount} members</p>
              </div>
            </div>
            <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium ${role.color}`}>
              {role.name}
            </span>
          </div>
          
          <p className="md-body-medium text-on-surface-variant mb-4">
            {role.description}
          </p>
          
          <div className="space-y-2">
            <p className="text-sm font-medium text-on-surface">Permissions:</p>
            <div className="space-y-1">
              {role.permissions.map((permission: string, index: number) => (
                <div key={index} className="flex items-center space-x-2 text-sm">
                  <CheckCircle className="w-3 h-3 text-green-600" />
                  <span className="text-on-surface-variant">{permission}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-outline-variant">
            <div className="flex items-center space-x-1">
              <button className="p-1 hover:bg-surface-container-highest rounded">
                <Edit className="w-4 h-4" />
              </button>
              <button className="p-1 hover:bg-surface-container-highest rounded">
                <Settings className="w-4 h-4" />
              </button>
            </div>
            <span className="text-sm text-on-surface-variant">
              {role.memberCount} member{role.memberCount !== 1 ? 's' : ''}
            </span>
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
              <h1 className="md-headline-small text-on-background">Team Management</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                Manage team members, roles, and permissions
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Button 
                onClick={() => setShowInviteModal(true)}
                className="md-button"
              >
                <UserPlus className="w-4 h-4 mr-2" />
                Invite Member
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

          {/* Tabs */}
          <div className="flex space-x-1 mb-4">
            <button
              onClick={() => setActiveTab('members')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'members'
                  ? 'bg-primary text-on-primary'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              <Users className="w-4 h-4 mr-2 inline" />
              Team Members ({mockTeamMembers.length})
            </button>
            <button
              onClick={() => setActiveTab('roles')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'roles'
                  ? 'bg-primary text-on-primary'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              <Shield className="w-4 h-4 mr-2 inline" />
              Roles & Permissions ({mockRoles.length})
            </button>
          </div>

          {/* Search and Filters */}
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
              <input
                type="text"
                placeholder={activeTab === 'members' ? 'Search team members...' : 'Search roles...'}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-12 pl-12 pr-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                aria-label="Search"
              />
            </div>
            
            <div className="flex gap-3">
              {activeTab === 'members' && (
                <>
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
                    </select>
                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
                      <svg className="w-4 h-4 text-on-surface-variant" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                </>
              )}
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
                  <p className="text-sm text-on-surface-variant">Total Members</p>
                  <p className="text-2xl font-bold text-on-surface">{mockTeamMembers.length}</p>
                </div>
                <Users className="w-8 h-8 text-primary" />
              </div>
            </CardContent>
          </Card>
          <Card className="md-card-expressive">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-on-surface-variant">Active Members</p>
                  <p className="text-2xl font-bold text-green-600">
                    {mockTeamMembers.filter(m => m.status === 'Active').length}
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
                  <p className="text-sm text-on-surface-variant">Pending Invites</p>
                  <p className="text-2xl font-bold text-yellow-600">
                    {mockTeamMembers.filter(m => m.status === 'Pending').length}
                  </p>
                </div>
                <Clock className="w-8 h-8 text-yellow-600" />
              </div>
            </CardContent>
          </Card>
          <Card className="md-card-expressive">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-on-surface-variant">Online Now</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {mockTeamMembers.filter(m => m.isOnline).length}
                  </p>
                </div>
                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                  <div className="w-3 h-3 bg-white rounded-full"></div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {activeTab === 'members' ? (
          filteredMembers.length === 0 ? (
            /* Empty State */
            <div className="flex flex-col items-center justify-center py-20">
              <div className="w-20 h-20 bg-primary-container rounded-3xl flex items-center justify-center mb-6">
                <Users className="w-10 h-10 text-on-primary-container" />
              </div>
              <h3 className="md-headline-small text-on-surface mb-3">No team members found</h3>
              <p className="md-body-large text-on-surface-variant text-center mb-8 max-w-md">
                {searchTerm || filterRole !== 'all' || filterStatus !== 'all'
                  ? 'Try adjusting your search or filter criteria.'
                  : 'Get started by inviting your first team member.'
                }
              </p>
              <Button onClick={() => setShowInviteModal(true)} className="md-button">
                <UserPlus className="w-4 h-4 mr-2" />
                Invite Member
              </Button>
            </div>
          ) : (
            /* Team Members Grid */
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredMembers.map(member => renderMemberCard(member))}
            </div>
          )
        ) : (
          /* Roles Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {mockRoles.map(role => renderRoleCard(role))}
          </div>
        )}
      </div>
    </div>
  )
}

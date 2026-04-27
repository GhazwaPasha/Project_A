'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Search,
  Filter,
  Download,
  RefreshCw,
  Users,
  UserPlus,
  Shield,
  Crown,
  User,
  Mail,
  Calendar,
  Eye,
  CheckCircle,
  CheckSquare,
  UserCheck,
} from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { useCurrentOrganization } from '@/hooks/use-current-organization'
import { orgRoleLabel, orgRolePermissionsForDisplay } from '@/lib/organization-role-definitions'

type ApiMember = {
  id: string
  user_id: string
  email: string
  full_name: string | null
  role: string
  joined_at: string | null
}

type UserDirectoryRow = ApiMember & {
  displayName: string
  initials: string
  permissions: string[]
}

function initialsFor(email: string, name: string | null): string {
  if (name?.trim()) {
    const parts = name.trim().split(/\s+/)
    if (parts.length >= 2) return (parts[0]![0]! + parts[1]![0]!).toUpperCase()
    return parts[0]!.slice(0, 2).toUpperCase()
  }
  return (email.split('@')[0] || email).slice(0, 2).toUpperCase()
}

export function Win11UserManagementPage() {
  const currentOrganization = useCurrentOrganization()
  const [members, setMembers] = useState<ApiMember[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterRole, setFilterRole] = useState('all')
  const [selectedUser, setSelectedUser] = useState<string | null>(null)

  const loadUsers = useCallback(async () => {
    if (!currentOrganization?.id) {
      setMembers([])
      setLoading(false)
      return
    }

    setLoading(true)
    setLoadError(null)
    try {
      const res = await fetch(`/api/organizations/${currentOrganization.id}/members`, {
        credentials: 'include',
      })
      const data = (await res.json().catch(() => ({}))) as {
        error?: string
        members?: ApiMember[]
      }
      if (!res.ok) {
        setLoadError(typeof data.error === 'string' ? data.error : 'Could not load users')
        setMembers([])
        return
      }
      setMembers(data.members ?? [])
    } catch {
      setLoadError('Could not load users')
      setMembers([])
    } finally {
      setLoading(false)
    }
  }, [currentOrganization?.id])

  useEffect(() => {
    void loadUsers()
  }, [loadUsers])

  const users = useMemo<UserDirectoryRow[]>(
    () =>
      members.map((member) => ({
        ...member,
        displayName: member.full_name?.trim() || member.email,
        initials: initialsFor(member.email, member.full_name),
        permissions: orgRolePermissionsForDisplay(member.role),
      })),
    [members]
  )

  const filteredUsers = useMemo(() => {
    const query = searchTerm.toLowerCase()
    return users.filter((userRow) => {
      const matchesSearch =
        !query ||
        userRow.displayName.toLowerCase().includes(query) ||
        userRow.email.toLowerCase().includes(query) ||
        orgRoleLabel(userRow.role).toLowerCase().includes(query)
      const matchesRole =
        filterRole === 'all' ||
        userRow.role === filterRole ||
        (filterRole === 'owner' && userRow.role === 'organization_owner')
      return matchesSearch && matchesRole
    })
  }, [filterRole, searchTerm, users])

  const getRoleIcon = (role: string) => {
    if (role === 'organization_owner') return <Crown className="w-4 h-4 text-red-600" />
    if (role === 'accountant') return <User className="w-4 h-4 text-green-600" />
    if (role === 'observer') return <Eye className="w-4 h-4 text-slate-600" />
    return <Shield className="w-4 h-4 text-blue-600" />
  }

  const getRoleColor = (role: string) => {
    if (role === 'organization_owner') return 'text-red-600 bg-red-50'
    if (role === 'accountant') return 'text-green-600 bg-green-50'
    if (role === 'observer') return 'text-slate-600 bg-slate-50'
    if (role === 'super_admin') return 'text-amber-600 bg-amber-50'
    return 'text-blue-600 bg-blue-50'
  }

  const renderUserCard = (userRow: UserDirectoryRow) => {
    const isSelected = selectedUser === userRow.id

    return (
      <Card
        key={userRow.id}
        className={`md-card-expressive group hover:md-elevation-1 transition-all duration-200 cursor-pointer ${
          isSelected ? 'ring-2 ring-primary' : ''
        }`}
        onClick={() => setSelectedUser(userRow.id)}
      >
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-primary-container rounded-full flex items-center justify-center">
                <span className="text-sm font-semibold text-on-primary-container">
                  {userRow.initials}
                </span>
              </div>
              <div>
                <h3 className="md-title-medium text-on-surface">{userRow.displayName}</h3>
                <p className="md-body-small text-on-surface-variant">
                  {currentOrganization?.name ?? 'Current organization'}
                </p>
              </div>
            </div>
            <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium text-green-600 bg-green-50">
              <CheckCircle className="w-4 h-4" />
              Active
            </span>
          </div>

          <div className="space-y-2 mb-4">
            <div className="flex items-center space-x-2 text-sm">
              <Mail className="w-4 h-4 text-on-surface-variant" />
              <span className="text-on-surface-variant">{userRow.email}</span>
            </div>
            {userRow.joined_at && (
              <div className="flex items-center space-x-2 text-sm">
                <Calendar className="w-4 h-4 text-on-surface-variant" />
                <span className="text-on-surface-variant">Joined {formatDate(userRow.joined_at)}</span>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              {getRoleIcon(userRow.role)}
              <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium ${getRoleColor(userRow.role)}`}>
                {orgRoleLabel(userRow.role)}
              </span>
            </div>
            <span className="text-xs text-on-surface-variant">Org role</span>
          </div>

          <div className="space-y-1">
            <p className="text-xs text-on-surface-variant">Permissions:</p>
            <div className="flex flex-wrap gap-1">
              {userRow.permissions.slice(0, 3).map((permission) => (
                <span
                  key={permission}
                  className="text-xs bg-surface-container text-on-surface-variant px-2 py-1 rounded"
                >
                  {permission}
                </span>
              ))}
              {userRow.permissions.length > 3 && (
                <span className="text-xs bg-surface-container text-on-surface-variant px-2 py-1 rounded">
                  +{userRow.permissions.length - 3} more
                </span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!currentOrganization) {
    return (
      <div
        className="min-h-screen flex items-center justify-center p-6"
        style={{ backgroundColor: 'var(--md-sys-color-background)' }}
      >
        <p className="md-body-large text-on-surface-variant">Select an organization in the header first.</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
      <div className="app-page-header sticky top-0 z-30">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="md-headline-small text-on-background">User Management</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                Manage real users in <span className="text-on-surface font-medium">{currentOrganization.name}</span>
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Button className="md-button" onClick={() => window.location.assign('/team')}>
                <UserPlus className="w-4 h-4 mr-2" />
                Add User
              </Button>
              <Button
                variant="outline"
                className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container"
                onClick={() => window.location.assign('/team')}
              >
                <CheckSquare className="w-4 h-4 mr-2" />
                Manage Roles
              </Button>
              <Button
                onClick={() => void loadUsers()}
                variant="outline"
                className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Button
                variant="outline"
                className="h-10 px-4 rounded-2xl border-outline"
                onClick={() => {
                  const blob = new Blob([JSON.stringify(users, null, 2)], { type: 'application/json' })
                  const a = document.createElement('a')
                  a.href = URL.createObjectURL(blob)
                  a.download = 'users-export.json'
                  a.click()
                }}
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>

          {loadError && (
            <p className="md-body-small text-on-error-container bg-error-container/30 p-2 rounded mb-4">
              {loadError}
            </p>
          )}

          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
              <input
                type="text"
                placeholder="Search users by name, email, or role..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-12 pl-12 pr-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                aria-label="Search users"
              />
            </div>

            <div className="flex gap-3">
              <select
                value={filterRole}
                onChange={(e) => setFilterRole(e.target.value)}
                className="h-12 pl-4 pr-12 py-3 bg-surface-container border border-outline rounded-2xl text-sm text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200 appearance-none cursor-pointer min-w-[160px]"
              >
                <option value="all">All Roles</option>
                <option value="owner">Owner</option>
                <option value="accountant">Accountant</option>
                <option value="member">Member</option>
                <option value="observer">Observer</option>
                <option value="super_admin">Platform admin</option>
              </select>
              <Button variant="outline" className="h-12 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container">
                <Filter className="w-4 h-4 mr-2" />
                Filter
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card className="md-card-expressive">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-on-surface-variant">Total Users</p>
                  <p className="text-2xl font-bold text-on-surface">{users.length}</p>
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
                  <p className="text-2xl font-bold text-green-600">{users.length}</p>
                </div>
                <UserCheck className="w-8 h-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
          <Card className="md-card-expressive">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-on-surface-variant">Owners</p>
                  <p className="text-2xl font-bold text-red-600">
                    {users.filter((u) => u.role === 'organization_owner').length}
                  </p>
                </div>
                <Crown className="w-8 h-8 text-red-600" />
              </div>
            </CardContent>
          </Card>
          <Card className="md-card-expressive">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-on-surface-variant">Visible Results</p>
                  <p className="text-2xl font-bold text-blue-600">{filteredUsers.length}</p>
                </div>
                <Eye className="w-8 h-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {loading ? (
          <p className="md-body-large text-on-surface-variant">Loading users...</p>
        ) : filteredUsers.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-20 h-20 bg-primary-container rounded-3xl flex items-center justify-center mb-6">
              <Users className="w-10 h-10 text-on-primary-container" />
            </div>
            <h3 className="md-headline-small text-on-surface mb-3">No users found</h3>
            <p className="md-body-large text-on-surface-variant text-center mb-8 max-w-md">
              {searchTerm || filterRole !== 'all'
                ? 'Try adjusting your search or role filter.'
                : 'Add users from Team Management to include them in this organization.'}
            </p>
            <Button onClick={() => window.location.assign('/team')} className="md-button">
              <UserPlus className="w-4 h-4 mr-2" />
              Add User
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredUsers.map((userRow) => renderUserCard(userRow))}
          </div>
        )}
      </div>
    </div>
  )
}

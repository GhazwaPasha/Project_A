'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Building2,
  Crown,
  RefreshCw,
  Search,
  Shield,
  UserCheck,
  Users,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatDate } from '@/lib/utils'
import { INVITABLE_ORG_ROLES, orgRoleLabel } from '@/lib/organization-role-definitions'
import { useAuthStore, useUser } from '@/stores/auth-store'
import type { InvitableOrgRole } from '@/lib/organization-role-definitions'

type AdminUser = {
  id: string
  email: string
  full_name: string | null
  is_super_admin: boolean
  created_at: string
  updated_at: string
  last_sign_in_at: string | null
  membership_count: number
}

type AdminOrganization = {
  id: string
  name: string
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  member_count: number
  owner_emails: string[]
}

type AdminMembership = {
  id: string
  organization_id: string
  organization_name: string
  user_id: string
  email: string
  full_name: string | null
  role: string
  joined_at: string | null
  is_active: boolean
}

type AdminOverview = {
  stats: {
    totalUsers: number
    totalOrganizations: number
    superAdmins: number
    activeMemberships: number
  }
  users: AdminUser[]
  organizations: AdminOrganization[]
  memberships: AdminMembership[]
}

type AdminTab = 'users' | 'organizations' | 'memberships'

function displayName(email: string, name: string | null) {
  return name?.trim() || email
}

export function Win11SuperAdminPage() {
  const sessionUser = useUser()
  const isSuper = useAuthStore((s) => s.profile?.is_super_admin) === true
  const [data, setData] = useState<AdminOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<AdminTab>('users')
  const [searchTerm, setSearchTerm] = useState('')
  const [organizationFilter, setOrganizationFilter] = useState('all')
  const [updatingKey, setUpdatingKey] = useState<string | null>(null)

  const loadOverview = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/super-admin/overview', {
        cache: 'no-store',
        credentials: 'include',
      })
      const json = (await res.json().catch(() => ({}))) as AdminOverview & { error?: string }
      if (!res.ok) {
        setError(typeof json.error === 'string' ? json.error : 'Could not load Super Admin data')
        setData(null)
        return
      }
      setData(json)
    } catch {
      setError('Could not load Super Admin data')
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (isSuper) void loadOverview()
    else setLoading(false)
  }, [isSuper, loadOverview])

  const query = searchTerm.toLowerCase()
  const filteredUsers = useMemo(() => {
    return (data?.users ?? []).filter((u) => {
      return (
        !query ||
        u.email.toLowerCase().includes(query) ||
        displayName(u.email, u.full_name).toLowerCase().includes(query)
      )
    })
  }, [data?.users, query])

  const filteredOrganizations = useMemo(() => {
    return (data?.organizations ?? []).filter((o) => {
      return (
        !query ||
        o.name.toLowerCase().includes(query) ||
        o.owner_emails.some((email) => email.toLowerCase().includes(query))
      )
    })
  }, [data?.organizations, query])

  const filteredMemberships = useMemo(() => {
    return (data?.memberships ?? []).filter((m) => {
      const matchesOrg = organizationFilter === 'all' || m.organization_id === organizationFilter
      const matchesSearch =
        !query ||
        m.organization_name.toLowerCase().includes(query) ||
        m.email.toLowerCase().includes(query) ||
        displayName(m.email, m.full_name).toLowerCase().includes(query) ||
        orgRoleLabel(m.role).toLowerCase().includes(query)
      return matchesOrg && matchesSearch
    })
  }, [data?.memberships, organizationFilter, query])

  async function updateSuperAdmin(userId: string, isSuperAdmin: boolean) {
    setUpdatingKey(`user:${userId}`)
    setError(null)
    try {
      const res = await fetch('/api/super-admin/users', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ userId, isSuperAdmin }),
      })
      const json = (await res.json().catch(() => ({}))) as { error?: string }
      if (!res.ok) {
        setError(typeof json.error === 'string' ? json.error : 'Could not update user')
        return
      }
      await loadOverview()
    } finally {
      setUpdatingKey(null)
    }
  }

  async function updateMembershipRole(membershipId: string, role: InvitableOrgRole) {
    setUpdatingKey(`membership:${membershipId}`)
    setError(null)
    try {
      const res = await fetch('/api/super-admin/memberships', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ membershipId, role }),
      })
      const json = (await res.json().catch(() => ({}))) as { error?: string }
      if (!res.ok) {
        setError(typeof json.error === 'string' ? json.error : 'Could not update membership')
        return
      }
      setData((current) => {
        if (!current) return current
        return {
          ...current,
          memberships: current.memberships.map((m) =>
            m.id === membershipId ? { ...m, role } : m
          ),
        }
      })
    } finally {
      setUpdatingKey(null)
    }
  }

  if (!isSuper) {
    return (
      <div
        className="min-h-screen flex items-center justify-center p-6"
        style={{ backgroundColor: 'var(--md-sys-color-background)' }}
      >
        <Card className="md-card-expressive max-w-lg">
          <CardContent className="p-8 text-center">
            <Shield className="w-12 h-12 mx-auto mb-4 text-on-surface-variant" />
            <h1 className="md-headline-small text-on-surface">Super Admin only</h1>
            <p className="md-body-medium text-on-surface-variant mt-2">
              Your profile does not have platform super admin access.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
      <div className="app-page-header sticky top-0 z-30">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="md-headline-small text-on-background">Super Admin</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                Necessary platform controls for users, organizations, and memberships.
              </p>
            </div>
            <Button
              onClick={() => void loadOverview()}
              variant="outline"
              className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>

          {error && (
            <p className="md-body-small text-on-error-container bg-error-container/30 p-2 rounded mb-4">
              {error}
            </p>
          )}

          <div className="flex space-x-1 mb-4">
            {(['users', 'organizations', 'memberships'] as AdminTab[]).map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab ? 'bg-primary text-on-primary' : 'text-on-surface-variant'
                }`}
              >
                {tab === 'users' ? 'Users' : tab === 'organizations' ? 'Organizations' : 'Memberships'}
              </button>
            ))}
          </div>

          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search users, organizations, emails, or roles..."
                className="w-full h-12 pl-12 pr-4 bg-surface-container rounded-2xl border border-outline text-sm"
                aria-label="Search super admin data"
              />
            </div>
            {activeTab === 'memberships' && (
              <select
                value={organizationFilter}
                onChange={(e) => setOrganizationFilter(e.target.value)}
                className="h-12 px-4 bg-surface-container border border-outline rounded-2xl text-sm min-w-[240px]"
                aria-label="Filter memberships by organization"
              >
                <option value="all">All organizations</option>
                {(data?.organizations ?? []).map((org) => (
                  <option key={org.id} value={org.id}>
                    {org.name}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card className="md-card-expressive">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-on-surface-variant">Users</p>
                <p className="text-2xl font-bold text-on-surface">{data?.stats.totalUsers ?? 0}</p>
              </div>
              <Users className="w-8 h-8 text-primary" />
            </CardContent>
          </Card>
          <Card className="md-card-expressive">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-on-surface-variant">Organizations</p>
                <p className="text-2xl font-bold text-on-surface">
                  {data?.stats.totalOrganizations ?? 0}
                </p>
              </div>
              <Building2 className="w-8 h-8 text-primary" />
            </CardContent>
          </Card>
          <Card className="md-card-expressive">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-on-surface-variant">Super Admins</p>
                <p className="text-2xl font-bold text-amber-600">{data?.stats.superAdmins ?? 0}</p>
              </div>
              <Crown className="w-8 h-8 text-amber-600" />
            </CardContent>
          </Card>
          <Card className="md-card-expressive">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-on-surface-variant">Active Memberships</p>
                <p className="text-2xl font-bold text-green-600">
                  {data?.stats.activeMemberships ?? 0}
                </p>
              </div>
              <UserCheck className="w-8 h-8 text-green-600" />
            </CardContent>
          </Card>
        </div>

        {loading ? (
          <p className="md-body-large text-on-surface-variant">Loading Super Admin data...</p>
        ) : activeTab === 'users' ? (
          <UsersTable
            users={filteredUsers}
            currentUserId={sessionUser?.id ?? null}
            updatingKey={updatingKey}
            onSuperAdminChange={updateSuperAdmin}
          />
        ) : activeTab === 'organizations' ? (
          <OrganizationsTable organizations={filteredOrganizations} />
        ) : (
          <MembershipsTable
            memberships={filteredMemberships}
            currentUserId={sessionUser?.id ?? null}
            updatingKey={updatingKey}
            onRoleChange={updateMembershipRole}
          />
        )}
      </div>
    </div>
  )
}

function UsersTable({
  users,
  currentUserId,
  updatingKey,
  onSuperAdminChange,
}: {
  users: AdminUser[]
  currentUserId: string | null
  updatingKey: string | null
  onSuperAdminChange: (userId: string, isSuperAdmin: boolean) => Promise<void>
}) {
  return (
    <Card className="md-card-expressive">
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User</TableHead>
              <TableHead>Memberships</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Super Admin</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((u) => {
              const isSelf = currentUserId === u.id
              return (
                <TableRow key={u.id}>
                  <TableCell>
                    <div className="font-medium text-on-surface">{displayName(u.email, u.full_name)}</div>
                    <div className="text-xs text-on-surface-variant">{u.email}</div>
                  </TableCell>
                  <TableCell>{u.membership_count}</TableCell>
                  <TableCell>{formatDate(u.created_at)}</TableCell>
                  <TableCell>
                    <select
                      value={u.is_super_admin ? 'true' : 'false'}
                      disabled={isSelf || updatingKey === `user:${u.id}`}
                      onChange={(e) => void onSuperAdminChange(u.id, e.target.value === 'true')}
                      className="h-9 rounded-md border border-outline bg-surface-container px-3 text-sm"
                      aria-label={`Set super admin access for ${u.email}`}
                    >
                      <option value="false">No</option>
                      <option value="true">Yes</option>
                    </select>
                    {isSelf && <span className="ml-2 text-xs text-on-surface-variant">You</span>}
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
        {users.length === 0 && (
          <p className="p-6 text-center text-on-surface-variant">No users match your search.</p>
        )}
      </CardContent>
    </Card>
  )
}

function OrganizationsTable({ organizations }: { organizations: AdminOrganization[] }) {
  return (
    <Card className="md-card-expressive">
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Organization</TableHead>
              <TableHead>Owners</TableHead>
              <TableHead>Members</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {organizations.map((org) => (
              <TableRow key={org.id}>
                <TableCell>
                  <div className="font-medium text-on-surface">{org.name}</div>
                  {org.description && (
                    <div className="text-xs text-on-surface-variant">{org.description}</div>
                  )}
                </TableCell>
                <TableCell>{org.owner_emails.join(', ') || 'No owner'}</TableCell>
                <TableCell>{org.member_count}</TableCell>
                <TableCell>{org.is_active ? 'Active' : 'Inactive'}</TableCell>
                <TableCell>{formatDate(org.created_at)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {organizations.length === 0 && (
          <p className="p-6 text-center text-on-surface-variant">No organizations match your search.</p>
        )}
      </CardContent>
    </Card>
  )
}

function MembershipsTable({
  memberships,
  currentUserId,
  updatingKey,
  onRoleChange,
}: {
  memberships: AdminMembership[]
  currentUserId: string | null
  updatingKey: string | null
  onRoleChange: (membershipId: string, role: InvitableOrgRole) => Promise<void>
}) {
  return (
    <Card className="md-card-expressive">
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Organization</TableHead>
              <TableHead>Member</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Joined</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {memberships.map((m) => {
              const isSelf = currentUserId === m.user_id
              const canChange =
                !isSelf && m.role !== 'organization_owner' && m.role !== 'super_admin'
              return (
                <TableRow key={m.id}>
                  <TableCell>{m.organization_name}</TableCell>
                  <TableCell>
                    <div className="font-medium text-on-surface">{displayName(m.email, m.full_name)}</div>
                    <div className="text-xs text-on-surface-variant">{m.email}</div>
                  </TableCell>
                  <TableCell>
                    {canChange ? (
                      <select
                        value={m.role}
                        disabled={updatingKey === `membership:${m.id}`}
                        onChange={(e) => void onRoleChange(m.id, e.target.value as InvitableOrgRole)}
                        className="h-9 rounded-md border border-outline bg-surface-container px-3 text-sm"
                        aria-label={`Change role for ${m.email} in ${m.organization_name}`}
                      >
                        {INVITABLE_ORG_ROLES.map((role) => (
                          <option key={role.value} value={role.value}>
                            {role.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span>{orgRoleLabel(m.role)}</span>
                    )}
                    {isSelf && <span className="ml-2 text-xs text-on-surface-variant">You</span>}
                  </TableCell>
                  <TableCell>{m.joined_at ? formatDate(m.joined_at) : '-'}</TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
        {memberships.length === 0 && (
          <p className="p-6 text-center text-on-surface-variant">No memberships match your search.</p>
        )}
      </CardContent>
    </Card>
  )
}

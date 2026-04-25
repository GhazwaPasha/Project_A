'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
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
  CheckCircle,
  Eye,
} from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { useUser } from '@/stores/auth-store'
import { useAuthStore } from '@/stores/auth-store'
import { useCurrentOrganization } from '@/stores/auth-store'
import {
  ORGANIZATION_ROLE_CATALOG,
  INVITABLE_ORG_ROLES,
  orgRoleLabel,
  orgRolePermissionsForDisplay,
  type InvitableOrgRole,
} from '@/lib/organization-role-definitions'

type ApiMember = {
  id: string
  user_id: string
  email: string
  full_name: string | null
  role: string
  joined_at: string | null
}

function initialsFor(email: string, name: string | null): string {
  if (name?.trim()) {
    const p = name.trim().split(/\s+/)
    if (p.length >= 2) return (p[0]![0]! + p[1]![0]!).toUpperCase()
    return p[0]!.slice(0, 2).toUpperCase()
  }
  const e = email.split('@')[0] || email
  return e.slice(0, 2).toUpperCase()
}

export function Win11TeamManagementPage() {
  const currentOrganization = useCurrentOrganization()
  const user = useUser()
  const profile = useAuthStore((s) => s.profile)

  const [members, setMembers] = useState<ApiMember[]>([])
  const [loadError, setLoadError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const [searchTerm, setSearchTerm] = useState('')
  const [filterRole, setFilterRole] = useState('all')
  const [selectedMember, setSelectedMember] = useState<string | null>(null)
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [activeTab, setActiveTab] = useState<'members' | 'roles'>('members')

  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState<InvitableOrgRole>('accountant')
  const [inviteError, setInviteError] = useState<string | null>(null)
  const [inviteLoading, setInviteLoading] = useState(false)
  const [roleUpdateError, setRoleUpdateError] = useState<string | null>(null)
  const [updatingMemberId, setUpdatingMemberId] = useState<string | null>(null)

  const loadMembers = useCallback(async () => {
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
        setLoadError(typeof data.error === 'string' ? data.error : 'Could not load team')
        setMembers([])
        return
      }
      setMembers(data.members ?? [])
    } catch {
      setLoadError('Could not load team')
      setMembers([])
    } finally {
      setLoading(false)
    }
  }, [currentOrganization?.id])

  useEffect(() => {
    void loadMembers()
  }, [loadMembers])

  const myRow = useMemo(
    () => (user ? members.find((m) => m.user_id === user.id) : undefined),
    [members, user]
  )
  const canInvite =
    myRow?.role === 'organization_owner' || profile?.is_super_admin === true

  const roleCatalogForTab = useMemo(
    () => ORGANIZATION_ROLE_CATALOG.filter((r) => r.role !== 'super_admin'),
    []
  )

  const roleCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const m of members) {
      c[m.role] = (c[m.role] || 0) + 1
    }
    return c
  }, [members])

  const filteredMembers = useMemo(() => {
    return members.filter((m) => {
      const displayName = m.full_name?.trim() || m.email
      const q = searchTerm.toLowerCase()
      const matchSearch =
        !q || displayName.toLowerCase().includes(q) || m.email.toLowerCase().includes(q)
      if (filterRole === 'all') return matchSearch
      if (filterRole === 'owner') return matchSearch && m.role === 'organization_owner'
      return matchSearch && m.role === filterRole
    })
  }, [members, searchTerm, filterRole])

  const getRoleIcon = (dbRole: string) => {
    if (dbRole === 'organization_owner') return <Crown className="w-4 h-4 text-red-600" />
    if (dbRole === 'accountant') return <User className="w-4 h-4 text-green-600" />
    if (dbRole === 'observer') return <Eye className="w-4 h-4 text-slate-600" />
    return <Shield className="w-4 h-4 text-blue-600" />
  }

  const getRoleColor = (dbRole: string) => {
    if (dbRole === 'organization_owner') return 'text-red-600 bg-red-50'
    if (dbRole === 'accountant') return 'text-green-600 bg-green-50'
    if (dbRole === 'observer') return 'text-slate-600 bg-slate-50'
    if (dbRole === 'super_admin') return 'text-amber-600 bg-amber-50'
    return 'text-gray-600 bg-gray-50'
  }

  async function submitInvite(e: React.FormEvent) {
    e.preventDefault()
    if (!currentOrganization?.id) return
    setInviteError(null)
    setInviteLoading(true)
    try {
      const res = await fetch(`/api/organizations/${currentOrganization.id}/members`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email: inviteEmail.trim(), role: inviteRole }),
      })
      const data = (await res.json().catch(() => ({}))) as { error?: string }
      if (!res.ok) {
        setInviteError(typeof data.error === 'string' ? data.error : 'Could not add member')
        return
      }
      setShowInviteModal(false)
      setInviteEmail('')
      setInviteRole('accountant')
      await loadMembers()
    } finally {
      setInviteLoading(false)
    }
  }

  async function changeMemberRole(memberId: string, role: InvitableOrgRole) {
    if (!currentOrganization?.id) return
    setRoleUpdateError(null)
    setUpdatingMemberId(memberId)
    try {
      const res = await fetch(`/api/organizations/${currentOrganization.id}/members`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ memberId, role }),
      })
      const data = (await res.json().catch(() => ({}))) as { error?: string }
      if (!res.ok) {
        setRoleUpdateError(typeof data.error === 'string' ? data.error : 'Could not update role')
        return
      }
      setMembers((current) =>
        current.map((m) => (m.id === memberId ? { ...m, role } : m))
      )
    } finally {
      setUpdatingMemberId(null)
    }
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
              <h1 className="md-headline-small text-on-background">Team Management</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                Members of <span className="text-on-surface font-medium">{currentOrganization.name}</span> — add
                people who have already registered. Owner and Accountant can use the books, reports, and ledger; Members
                use only inventory and related flows; Observers are read-only in inventory (see Roles tab).
              </p>
            </div>
            <div className="flex items-center space-x-3">
              {canInvite && (
                <Button
                  onClick={() => {
                    setInviteError(null)
                    setShowInviteModal(true)
                  }}
                  className="md-button"
                >
                  <UserPlus className="w-4 h-4 mr-2" />
                  Add member
                </Button>
              )}
              <Button
                onClick={() => void loadMembers()}
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
                  const blob = new Blob([JSON.stringify(members, null, 2)], { type: 'application/json' })
                  const a = document.createElement('a')
                  a.href = URL.createObjectURL(blob)
                  a.download = 'team-export.json'
                  a.click()
                }}
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>

          <div className="flex space-x-1 mb-4">
            <button
              type="button"
              onClick={() => setActiveTab('members')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'members' ? 'bg-primary text-on-primary' : 'text-on-surface-variant'
              }`}
            >
              <Users className="w-4 h-4 mr-2 inline" />
              Team members ({members.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('roles')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'roles' ? 'bg-primary text-on-primary' : 'text-on-surface-variant'
              }`}
            >
              <Shield className="w-4 h-4 mr-2 inline" />
              Roles &amp; permissions ({roleCatalogForTab.length})
            </button>
          </div>

          {loadError && (
            <p className="md-body-small text-on-error-container bg-error-container/30 p-2 rounded mb-2">
              {loadError}
            </p>
          )}
          {roleUpdateError && (
            <p className="md-body-small text-on-error-container bg-error-container/30 p-2 rounded mb-2">
              {roleUpdateError}
            </p>
          )}

          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
              <input
                type="text"
                name="search"
                placeholder={activeTab === 'members' ? 'Search by name or email' : 'Search roles'}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-12 pl-12 pr-4 bg-surface-container rounded-2xl border border-outline text-sm"
                aria-label="Search"
              />
            </div>
            {activeTab === 'members' && (
              <div className="flex gap-3">
                <div className="relative">
                  <select
                    name="filterRole"
                    value={filterRole}
                    onChange={(e) => setFilterRole(e.target.value)}
                    className="h-12 pl-4 pr-10 bg-surface-container border border-outline rounded-2xl text-sm min-w-[160px]"
                  >
                    <option value="all">All roles</option>
                    <option value="owner">Owner</option>
                    <option value="accountant">Accountant</option>
                    <option value="member">Member</option>
                    <option value="observer">Observer</option>
                    <option value="super_admin">Platform admin</option>
                  </select>
                </div>
                <Button variant="outline" className="h-12 rounded-2xl" type="button">
                  <Filter className="w-4 h-4 mr-2" />
                  Filter
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {loading ? (
          <p className="md-body-large text-on-surface-variant">Loading team…</p>
        ) : activeTab === 'members' ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <Card className="md-card-expressive">
                <CardContent className="p-4">
                  <p className="text-sm text-on-surface-variant">Total members</p>
                  <p className="text-2xl font-bold text-on-surface">{members.length}</p>
                </CardContent>
              </Card>
              <Card className="md-card-expressive">
                <CardContent className="p-4">
                  <p className="text-sm text-on-surface-variant">Your role</p>
                  <p className="text-lg font-semibold text-on-surface">
                    {myRow ? orgRoleLabel(myRow.role) : '—'}
                  </p>
                </CardContent>
              </Card>
            </div>
            {filteredMembers.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <Users className="w-12 h-12 text-on-surface-variant mb-3" />
                <h3 className="md-title-medium text-on-surface">No members match</h3>
                <p className="md-body-medium text-on-surface-variant max-w-md mt-2">
                  {canInvite
                    ? 'Add someone who already has an Accountuitive profile (signed up) using their email.'
                    : 'You can view this list; only the organization owner can add members.'}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredMembers.map((m) => {
                  const display = m.full_name?.trim() || m.email
                  const perm = orgRolePermissionsForDisplay(m.role)
                  const isSelf = user?.id === m.user_id
                  const canChangeRole =
                    canInvite && !isSelf && m.role !== 'organization_owner' && m.role !== 'super_admin'
                  return (
                    <Card
                      key={m.id}
                      className={`md-card-expressive cursor-pointer ${
                        selectedMember === m.id ? 'ring-2 ring-primary' : ''
                      }`}
                      onClick={() => setSelectedMember(m.id)}
                    >
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-primary-container rounded-full flex items-center justify-center text-sm font-semibold text-on-primary-container">
                              {initialsFor(m.email, m.full_name)}
                            </div>
                            <div>
                              <h3 className="md-title-medium text-on-surface">{display}</h3>
                              {isSelf && (
                                <span className="text-xs text-on-surface-variant">You</span>
                              )}
                            </div>
                          </div>
                          <span
                            className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium ${getRoleColor(
                              m.role
                            )}`}
                          >
                            {getRoleIcon(m.role)}
                            {orgRoleLabel(m.role)}
                          </span>
                        </div>
                        <div className="space-y-2 text-sm text-on-surface-variant mb-3">
                          <div className="flex items-center gap-2">
                            <Mail className="w-4 h-4" />
                            {m.email}
                          </div>
                          {m.joined_at && (
                            <div className="flex items-center gap-2">
                              <Calendar className="w-4 h-4" />
                              Joined {formatDate(m.joined_at)}
                            </div>
                          )}
                        </div>
                        {perm.length > 0 && (
                          <div>
                            <p className="text-xs text-on-surface-variant mb-1">Role scope</p>
                            <div className="flex flex-wrap gap-1">
                              {perm.map((p) => (
                                <span
                                  key={p}
                                  className="text-xs bg-surface-container px-2 py-0.5 rounded"
                                >
                                  {p}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        {canChangeRole && (
                          <div className="mt-4 pt-4 border-t border-outline-variant">
                            <label className="block text-xs text-on-surface-variant mb-1">
                              Change role
                            </label>
                            <select
                              className="w-full h-10 rounded-md border border-outline bg-surface-container px-3 text-sm"
                              value={m.role}
                              disabled={updatingMemberId === m.id}
                              onClick={(e) => e.stopPropagation()}
                              onChange={(e) => {
                                e.stopPropagation()
                                void changeMemberRole(m.id, e.target.value as InvitableOrgRole)
                              }}
                              aria-label={`Change role for ${display}`}
                            >
                              {INVITABLE_ORG_ROLES.map((o) => (
                                <option key={o.value} value={o.value}>
                                  {o.label}
                                </option>
                              ))}
                            </select>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            )}
          </>
        ) : (
          <div className="space-y-4">
            {roleCatalogForTab
              .filter(
                (r) =>
                  !searchTerm ||
                  r.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                  r.description.toLowerCase().includes(searchTerm.toLowerCase())
              )
              .map((r) => (
                <Card key={r.id} className="md-card-expressive">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="md-title-medium text-on-surface">{r.name}</h3>
                        <p className="md-body-small text-on-surface-variant mt-1">{r.description}</p>
                        <p className="md-body-small text-on-surface mt-2">
                          {roleCounts[r.id] ?? roleCounts[r.role] ?? 0} member
                          {(roleCounts[r.id] ?? roleCounts[r.role] ?? 0) === 1 ? '' : 's'}
                        </p>
                      </div>
                    </div>
                    <ul className="mt-4 space-y-1 text-sm text-on-surface-variant">
                      {r.permissions.map((p) => (
                        <li key={p} className="flex items-center gap-2">
                          <CheckCircle className="w-3 h-3 text-green-600" />
                          {p}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              ))}
          </div>
        )}
      </div>

      <Dialog
        open={showInviteModal}
        onOpenChange={(o) => {
          if (!o) setInviteError(null)
          setShowInviteModal(o)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add team member</DialogTitle>
            <DialogDescription>
              They need an Accountuitive profile first (sign up and complete profile), then you can
              add them with the work email below.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={submitInvite} className="space-y-4">
            {inviteError && (
              <div
                className="text-sm p-3 rounded border"
                style={{
                  borderColor: 'var(--md-sys-color-error)',
                  color: 'var(--md-sys-color-on-error-container)',
                }}
              >
                {inviteError}
              </div>
            )}
            <div>
              <Label htmlFor="invite-email">Work email</Label>
              <Input
                id="invite-email"
                name="email"
                type="email"
                required
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="teammate@company.com"
                className="mt-1 h-12"
                autoComplete="email"
              />
            </div>
            <div>
              <Label htmlFor="invite-role">Role in this org</Label>
              <select
                id="invite-role"
                name="role"
                className="mt-1 w-full h-12 rounded-md border border-input bg-background px-3"
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value as InvitableOrgRole)}
              >
                {INVITABLE_ORG_ROLES.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label} — {o.hint}
                  </option>
                ))}
              </select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowInviteModal(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={inviteLoading}>
                {inviteLoading ? 'Adding…' : 'Add to team'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

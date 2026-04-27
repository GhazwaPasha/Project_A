'use client'

import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Search,
  Download,
  RefreshCw,
  Save,
  Building2,
  FileText,
  Shield,
  Globe,
  Database,
  Bell,
  Edit,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { useCurrentOrganization } from '@/hooks/use-current-organization'
import { useOrganization } from '@/hooks/use-organization'
import { useOrganizationContext } from '@/contexts/organization-context'
import { useAuthStore } from '@/stores/auth-store'
import { queryKeys } from '@/lib/query-keys'
import {
  type OrganizationSettingsView,
  buildOrganizationSettingsView,
  parseOrganizationSettingsValue,
} from '@/lib/organization-settings-defaults'
import { cn } from '@/lib/utils'
import type { Organization } from '@/types'

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

const CURRENCIES = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF', 'INR', 'PKR', 'AED', 'SAR']

const settingsCategories = [
  {
    id: 'company',
    name: 'Company Information',
    description: 'Name, contact details, and business address for this organization',
    icon: Building2,
    color: 'text-blue-600 bg-blue-50',
    settingsCount: 9,
  },
  {
    id: 'accounting',
    name: 'Accounting Settings',
    description: 'Fiscal year, currency, number formats, and book preferences',
    icon: FileText,
    color: 'text-green-600 bg-green-50',
    settingsCount: 10,
  },
  {
    id: 'security',
    name: 'Security & Access',
    description: 'Session policy, 2FA expectations, and optional IP allow list',
    icon: Shield,
    color: 'text-red-600 bg-red-50',
    settingsCount: 8,
  },
  {
    id: 'notifications',
    name: 'Notifications',
    description: 'Alert and report delivery preferences (stored for your team; delivery depends on app email/SMS support)',
    icon: Bell,
    color: 'text-yellow-600 bg-yellow-50',
    settingsCount: 7,
  },
  {
    id: 'integrations',
    name: 'Integrations',
    description: 'Planned or configured external tools (labels only — wire API keys in future)',
    icon: Globe,
    color: 'text-purple-600 bg-purple-50',
    settingsCount: 6,
  },
  {
    id: 'backup',
    name: 'Backup & recovery',
    description: 'Schedule preferences and your own notes (e.g. off-site copy)',
    icon: Database,
    color: 'text-gray-600 bg-gray-50',
    settingsCount: 4,
  },
] as const

type CategoryId = (typeof settingsCategories)[number]['id']

type DraftSetter = (fn: (prev: OrganizationSettingsView) => OrganizationSettingsView) => void

export function Win11OrganizationSettingsPage() {
  const org = useCurrentOrganization()
  const { isLoading, hasOrganizations } = useOrganization()
  const { refreshOrganizations } = useOrganizationContext()
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const user = useAuthStore((s) => s.user)
  const profile = useAuthStore((s) => s.profile)
  const orgMemberRole = useAuthStore((s) => s.currentOrgMemberRole)
  const orgMemberRoleResolved = useAuthStore((s) => s.orgMemberRoleResolved)

  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<CategoryId | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [draft, setDraft] = useState<OrganizationSettingsView | null>(null)
  const [saving, setSaving] = useState(false)

  const view = useMemo(() => buildOrganizationSettingsView(org), [org])
  const canEdit = Boolean(
    orgMemberRoleResolved &&
    (profile?.is_super_admin ||
      orgMemberRole === 'organization_owner' ||
      orgMemberRole === 'accountant')
  )

  const display = isEditing && draft ? draft : view

  useEffect(() => {
    if (!isEditing) {
      setDraft(null)
    }
  }, [isEditing, org?.updated_at])

  const startEdit = () => {
    if (!org || !canEdit) return
    setDraft(buildOrganizationSettingsView(org))
    setIsEditing(true)
  }

  const cancelEdit = () => {
    setIsEditing(false)
    setDraft(null)
  }

  const setDraftP: DraftSetter = (fn) => {
    setDraft((prev) => (prev ? fn(prev) : prev))
  }

  const save = useCallback(async () => {
    if (!user?.id || !org?.id || !draft) return
    if (!draft.name.trim()) {
      toast({ title: 'Name required', description: 'The organization name cannot be empty.', variant: 'destructive' })
      return
    }
    setSaving(true)
    try {
      const baseSettings = parseOrganizationSettingsValue(org?.settings) as Record<string, unknown>
      const mergedSettings: Record<string, unknown> = {
        ...baseSettings,
        companyInfo: draft.companyInfo,
        accountingSettings: { ...draft.accountingSettings },
        securitySettings: draft.securitySettings,
        notificationSettings: draft.notificationSettings,
        integrations: draft.integrations,
        backup: {
          ...draft.backup,
          autoBackup: draft.accountingSettings.autoBackup,
          backupFrequency: draft.accountingSettings.backupFrequency,
          retentionPeriod: draft.accountingSettings.retentionPeriod,
        },
      }
      const res = await fetch(`/api/organizations/${org.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: draft.name.trim(),
          description: draft.description.trim() || null,
          settings: mergedSettings,
        }),
      })
      const data = (await res.json().catch(() => ({}))) as { error?: unknown; organization?: Organization }
      if (!res.ok) {
        const msg = typeof data.error === 'string' ? data.error : 'Could not save settings'
        toast({ title: 'Save failed', description: msg, variant: 'destructive' })
        return
      }
      if (data.organization) {
        const up = data.organization
        queryClient.setQueryData(queryKeys.currentOrganization(up.id), up)
        const { organizations, currentOrganization, setCurrentOrganization, setOrganizations, syncOrgQueries } =
          useAuthStore.getState()
        if (currentOrganization?.id === up.id) {
          setCurrentOrganization(up)
        }
        setOrganizations(organizations.map((o) => (o.id === up.id ? up : o)))
        syncOrgQueries(user.id)
      }
      toast({ title: 'Saved', description: 'Organization settings were updated.' })
      setIsEditing(false)
      setDraft(null)
      await queryClient.invalidateQueries({ queryKey: queryKeys.currentOrganization(org.id) })
      await queryClient.invalidateQueries({ queryKey: queryKeys.userOrganizations(user.id) })
      await refreshOrganizations()
    } catch (e) {
      toast({
        title: 'Save failed',
        description: e instanceof Error ? e.message : 'Network error',
        variant: 'destructive',
      })
    } finally {
      setSaving(false)
    }
  }, [draft, org, queryClient, refreshOrganizations, toast, user?.id])

  const onExport = () => {
    if (!org) return
    const v = buildOrganizationSettingsView(org)
    const payload = {
      id: org.id,
      name: v.name,
      description: v.description,
      companyInfo: v.companyInfo,
      accountingSettings: v.accountingSettings,
      securitySettings: v.securitySettings,
      notificationSettings: v.notificationSettings,
      integrations: v.integrations,
      backup: v.backup,
      updated_at: org.updated_at,
    }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `organization-${org.id.slice(0, 8)}-settings.json`
    a.click()
    URL.revokeObjectURL(a.href)
    toast({ title: 'Export started', description: 'A JSON file was downloaded.' })
  }

  const onRefresh = () => {
    if (!user?.id || !org?.id) return
    void queryClient.invalidateQueries({ queryKey: queryKeys.currentOrganization(org.id) })
    void refreshOrganizations()
    toast({ title: 'Refreshed', description: 'Latest organization data loaded.' })
  }

  const filteredCategories = useMemo(
    () =>
      settingsCategories.filter(
        (category) =>
          category.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          category.description.toLowerCase().includes(searchTerm.toLowerCase())
      ),
    [searchTerm]
  )

  const getCategoryIcon = (category: (typeof settingsCategories)[number]) => {
    const IconComponent = category.icon
    return <IconComponent className="w-6 h-6" />
  }

  const renderCategoryCard = (category: (typeof settingsCategories)[number]) => (
    <Card
      key={category.id}
      className="md-card-expressive group hover:md-elevation-1 transition-all duration-200 cursor-pointer"
      onClick={() => {
        setSelectedCategory(category.id)
        setIsEditing(false)
        setDraft(null)
      }}
    >
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div
              className={cn(
                'w-12 h-12 rounded-2xl flex items-center justify-center',
                category.color
              )}
            >
              {getCategoryIcon(category)}
            </div>
            <div>
              <h3 className="md-title-medium text-on-surface">{category.name}</h3>
              <p className="md-body-small text-on-surface-variant">
                {category.settingsCount} fields
              </p>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-on-surface-variant transition-transform group-hover:translate-x-0.5" />
        </div>
        <p className="md-body-medium text-on-surface-variant mb-4">{category.description}</p>
        <div className="flex items-center justify-between">
          <span
            className={cn('inline-block px-2 py-1 rounded-md text-xs font-medium', category.color)}
          >
            {category.name}
          </span>
        </div>
      </CardContent>
    </Card>
  )

  if (!hasOrganizations) {
    return (
      <div
        className="min-h-screen flex items-center justify-center p-6"
        style={{ backgroundColor: 'var(--md-sys-color-background)' }}
      >
        <p className="text-on-surface-variant">Create or join an organization to see settings.</p>
      </div>
    )
  }

  if (isLoading && !org) {
    return (
      <div
        className="min-h-screen flex items-center justify-center p-6"
        style={{ backgroundColor: 'var(--md-sys-color-background)' }}
      >
        <p className="text-on-surface-variant">Loading organization…</p>
      </div>
    )
  }

  if (!org) {
    return (
      <div
        className="min-h-screen flex items-center justify-center p-6"
        style={{ backgroundColor: 'var(--md-sys-color-background)' }}
      >
        <p className="text-on-surface-variant">Select an organization in the header.</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
      <div className="app-page-header sticky top-0 z-30">
        <div className="px-6 py-4">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-4">
            <div>
              <h1 className="md-headline-small text-on-background">Organization Settings</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                {display.name} — {orgMemberRole ? `Your role: ${orgMemberRole.replace('organization_', '')}` : 'Role loading…'}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {isEditing && canEdit ? (
                <>
                  <Button
                    onClick={cancelEdit}
                    variant="outline"
                    className="h-10 rounded-2xl"
                    disabled={saving}
                  >
                    Cancel
                  </Button>
                  <Button onClick={() => void save()} className="md-button" disabled={saving}>
                    <Save className="w-4 h-4 mr-2" />
                    {saving ? 'Saving…' : 'Save changes'}
                  </Button>
                </>
              ) : (
                <>
                  {canEdit && (
                    <Button
                      onClick={startEdit}
                      className="md-button"
                      disabled={!selectedCategory}
                    >
                      <Edit className="w-4 h-4 mr-2" />
                      {selectedCategory ? 'Edit this section' : 'Pick a section first'}
                    </Button>
                  )}
                  <Button
                    onClick={onRefresh}
                    variant="outline"
                    className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Refresh
                  </Button>
                  <Button
                    onClick={onExport}
                    variant="outline"
                    className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Export
                  </Button>
                </>
              )}
            </div>
          </div>
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
              <input
                type="text"
                placeholder="Search settings categories…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-12 pl-12 pr-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                aria-label="Search settings"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {selectedCategory ? (
          <div className="w-full max-w-4xl">
            <CategoryDetail
              categoryId={selectedCategory}
              getCategoryIcon={getCategoryIcon}
              display={display}
              isEditing={isEditing}
              setDraft={setDraftP}
              onBack={() => {
                setSelectedCategory(null)
                setIsEditing(false)
                setDraft(null)
              }}
              onEdit={startEdit}
              canEdit={canEdit}
            />
          </div>
        ) : (
          <div>
            <h2 className="text-lg font-semibold text-on-surface mb-4">Settings categories</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
              {filteredCategories.map((c) => renderCategoryCard(c))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function CategoryDetail({
  categoryId,
  getCategoryIcon,
  display,
  isEditing,
  setDraft,
  onBack,
  onEdit,
  canEdit,
}: {
  categoryId: CategoryId
  getCategoryIcon: (c: (typeof settingsCategories)[number]) => ReactNode
  display: OrganizationSettingsView
  isEditing: boolean
  setDraft: DraftSetter
  onBack: () => void
  onEdit: () => void
  canEdit: boolean
}) {
  const category = settingsCategories.find((c) => c.id === categoryId)
  if (!category) return null

  return (
    <Card className="md-card-expressive">
      <CardHeader className="space-y-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
          <Button
            type="button"
            variant="ghost"
            className="md-surface-nav-button h-10 w-fit -ml-2 px-3 text-on-surface hover:bg-surface-container-highest rounded-2xl"
            onClick={onBack}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            All settings
          </Button>
        </div>
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center space-x-3 min-w-0">
            <div
              className={cn(
                'w-10 h-10 rounded-xl flex items-center justify-center shrink-0',
                category.color
              )}
            >
              {getCategoryIcon(category)}
            </div>
            <div className="min-w-0">
              <CardTitle className="md-title-large text-on-surface">{category.name}</CardTitle>
              <CardDescription className="md-body-medium text-on-surface-variant">
                {category.description}
              </CardDescription>
            </div>
          </div>
          {canEdit && !isEditing && (
            <Button onClick={onEdit} className="md-button shrink-0">
              <Edit className="w-4 h-4 mr-2" />
              Edit
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {categoryId === 'company' && (
          <CompanySection display={display} isEditing={isEditing} setDraft={setDraft} />
        )}
        {categoryId === 'accounting' && (
          <AccountingSection
            display={display}
            isEditing={isEditing}
            setDraft={setDraft}
            months={MONTHS}
            currencies={CURRENCIES}
          />
        )}
        {categoryId === 'security' && <SecuritySection display={display} isEditing={isEditing} setDraft={setDraft} />}
        {categoryId === 'notifications' && (
          <NotificationsSection display={display} isEditing={isEditing} setDraft={setDraft} />
        )}
        {categoryId === 'integrations' && (
          <IntegrationsSection display={display} isEditing={isEditing} setDraft={setDraft} />
        )}
        {categoryId === 'backup' && <BackupSection display={display} isEditing={isEditing} setDraft={setDraft} />}
      </CardContent>
    </Card>
  )
}

function readLabel(className?: string) {
  return cn('text-sm font-medium text-on-surface-variant', className)
}

function valBox(children: React.ReactNode) {
  return <p className="text-lg text-on-surface min-h-[1.5rem]">{children}</p>
}

function CompanySection({
  display,
  isEditing,
  setDraft,
}: {
  display: OrganizationSettingsView
  isEditing: boolean
  setDraft: DraftSetter
}) {
  const c = display.companyInfo
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="md:col-span-2 space-y-2">
          <Label className={readLabel()}>Display name</Label>
          {isEditing ? (
            <Input
              value={display.name}
              onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))}
              className="rounded-2xl"
            />
          ) : (
            valBox(display.name || '—')
          )}
        </div>
        <div className="md:col-span-2 space-y-2">
          <Label className={readLabel()}>Description</Label>
          {isEditing ? (
            <Textarea
              value={display.description}
              onChange={(e) => setDraft((d) => ({ ...d, description: e.target.value }))}
              className="rounded-2xl min-h-[80px]"
            />
          ) : (
            valBox(display.description || '—')
          )}
        </div>
        {(['legalName', 'taxId', 'registrationNumber', 'industry'] as const).map((k) => (
          <div key={k} className="space-y-2">
            <Label className={readLabel()}>
              {k === 'legalName' ? 'Legal name' : k === 'taxId' ? 'Tax ID' : k === 'registrationNumber' ? 'Registration #' : 'Industry'}
            </Label>
            {isEditing ? (
              <Input
                value={c[k]}
                onChange={(e) =>
                  setDraft((d) => ({
                    ...d,
                    companyInfo: { ...d.companyInfo, [k]: e.target.value },
                  }))
                }
                className="rounded-2xl"
              />
            ) : (
              valBox(c[k] || '—')
            )}
          </div>
        ))}
        <div className="space-y-2">
          <Label className={readLabel()}>Website</Label>
          {isEditing ? (
            <Input
              value={c.website}
              onChange={(e) =>
                setDraft((d) => ({ ...d, companyInfo: { ...d.companyInfo, website: e.target.value } }))
              }
              className="rounded-2xl"
            />
          ) : (
            valBox(c.website || '—')
          )}
        </div>
        <div className="space-y-2">
          <Label className={readLabel()}>Email</Label>
          {isEditing ? (
            <Input
              type="email"
              value={c.email}
              onChange={(e) =>
                setDraft((d) => ({ ...d, companyInfo: { ...d.companyInfo, email: e.target.value } }))
              }
              className="rounded-2xl"
            />
          ) : (
            valBox(c.email || '—')
          )}
        </div>
        <div className="space-y-2">
          <Label className={readLabel()}>Phone</Label>
          {isEditing ? (
            <Input
              value={c.phone}
              onChange={(e) =>
                setDraft((d) => ({ ...d, companyInfo: { ...d.companyInfo, phone: e.target.value } }))
              }
              className="rounded-2xl"
            />
          ) : (
            valBox(c.phone || '—')
          )}
        </div>
        {(['street', 'city', 'state', 'zipCode', 'country'] as const).map((k) => (
          <div key={k} className="space-y-2">
            <Label className={readLabel()}>
              {k === 'zipCode' ? 'ZIP / postal' : k.charAt(0).toUpperCase() + k.slice(1)}
            </Label>
            {isEditing ? (
              <Input
                value={c.address[k]}
                onChange={(e) =>
                  setDraft((d) => ({
                    ...d,
                    companyInfo: {
                      ...d.companyInfo,
                      address: { ...d.companyInfo.address, [k]: e.target.value },
                    },
                  }))
                }
                className="rounded-2xl"
              />
            ) : (
              valBox(c.address[k] || '—')
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function AccountingSection({
  display,
  isEditing,
  setDraft,
  months,
  currencies,
}: {
  display: OrganizationSettingsView
  isEditing: boolean
  setDraft: DraftSetter
  months: string[]
  currencies: string[]
}) {
  const a = display.accountingSettings
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label className={readLabel()}>Fiscal year start</Label>
          {isEditing ? (
            <select
              className="w-full h-10 rounded-2xl border border-outline bg-surface-container px-3 text-sm"
              value={a.fiscalYearStart}
              onChange={(e) =>
                setDraft((d) => ({
                  ...d,
                  accountingSettings: { ...d.accountingSettings, fiscalYearStart: e.target.value },
                }))
              }
            >
              {months.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          ) : (
            valBox(a.fiscalYearStart)
          )}
        </div>
        <div className="space-y-2">
          <Label className={readLabel()}>Reporting currency</Label>
          {isEditing ? (
            <select
              className="w-full h-10 rounded-2xl border border-outline bg-surface-container px-3 text-sm"
              value={a.reportingCurrency}
              onChange={(e) =>
                setDraft((d) => ({
                  ...d,
                  accountingSettings: { ...d.accountingSettings, reportingCurrency: e.target.value },
                }))
              }
            >
              {currencies.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          ) : (
            valBox(a.reportingCurrency)
          )}
        </div>
        {(['dateFormat', 'numberFormat', 'retentionPeriod', 'chartOfAccounts', 'inventoryMethod', 'depreciationMethod'] as const).map(
          (k) => (
            <div key={k} className="space-y-2">
              <Label className={readLabel()}>
                {k === 'dateFormat' ? 'Date format' : k === 'numberFormat' ? 'Number format' : k === 'retentionPeriod' ? 'Record retention' : k === 'chartOfAccounts' ? 'Chart of accounts' : k === 'inventoryMethod' ? 'Inventory' : 'Depreciation'}
              </Label>
              {isEditing ? (
                <Input
                  value={a[k]}
                  onChange={(e) =>
                    setDraft((d) => ({
                      ...d,
                      accountingSettings: { ...d.accountingSettings, [k]: e.target.value },
                    }))
                  }
                  className="rounded-2xl"
                />
              ) : (
                valBox(a[k])
              )}
            </div>
          )
        )}
        <div className="space-y-2">
          <Label className={readLabel()}>Decimal places</Label>
          {isEditing ? (
            <Input
              type="number"
              min={0}
              max={6}
              value={a.decimalPlaces}
              onChange={(e) =>
                setDraft((d) => ({
                  ...d,
                  accountingSettings: {
                    ...d.accountingSettings,
                    decimalPlaces: Math.min(6, Math.max(0, parseInt(e.target.value, 10) || 0)),
                  },
                }))
              }
              className="rounded-2xl"
            />
          ) : (
            valBox(String(a.decimalPlaces))
          )}
        </div>
        <div className="flex items-center justify-between gap-3 rounded-2xl border border-outline/60 p-3 md:col-span-2">
          <div>
            <p className="md-body-medium text-on-surface">Back up preferences (your process)</p>
            <p className="md-body-small text-on-surface-variant">Reminder label only — in-app export still manual.</p>
          </div>
          {isEditing ? (
            <Switch
              checked={a.autoBackup}
              onCheckedChange={(v) =>
                setDraft((d) => ({ ...d, accountingSettings: { ...d.accountingSettings, autoBackup: v } }))
              }
            />
          ) : (
            valBox(a.autoBackup ? 'Planned' : 'Off')
          )}
        </div>
        <div className="space-y-2">
          <Label className={readLabel()}>Backup frequency (label)</Label>
          {isEditing ? (
            <Input
              value={a.backupFrequency}
              onChange={(e) =>
                setDraft((d) => ({
                  ...d,
                  accountingSettings: { ...d.accountingSettings, backupFrequency: e.target.value },
                }))
              }
              className="rounded-2xl"
            />
          ) : (
            valBox(a.backupFrequency)
          )}
        </div>
      </div>
    </div>
  )
}

function SecuritySection({
  display,
  isEditing,
  setDraft,
}: {
  display: OrganizationSettingsView
  isEditing: boolean
  setDraft: DraftSetter
}) {
  const s = display.securitySettings
  const p = s.passwordPolicy
  return (
    <div className="space-y-6">
      <div>
        <h4 className="md-title-small text-on-surface mb-3">Password policy (documented for your team)</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(
            [
              ['minLength', 'Minimum length'],
              ['expirationDays', 'Password rotation (days)'],
            ] as const
          ).map(([k, label]) => (
            <div key={k} className="space-y-2">
              <Label className={readLabel()}>{label}</Label>
              {isEditing ? (
                <Input
                  type="number"
                  min={4}
                  max={128}
                  value={p[k]}
                  onChange={(e) =>
                    setDraft((d) => ({
                      ...d,
                      securitySettings: {
                        ...d.securitySettings,
                        passwordPolicy: {
                          ...d.securitySettings.passwordPolicy,
                          [k]: Math.max(4, parseInt(e.target.value, 10) || 0),
                        },
                      },
                    }))
                  }
                  className="rounded-2xl"
                />
              ) : (
                valBox(String(p[k]))
              )}
            </div>
          ))}
        </div>
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
          {(
            [
              ['requireUppercase', 'Require uppercase'],
              ['requireLowercase', 'Require lowercase'],
              ['requireNumbers', 'Require numbers'],
              ['requireSymbols', 'Require symbols'],
            ] as const
          ).map(([k, label]) => (
            <div
              key={k}
              className="flex items-center justify-between gap-2 rounded-2xl border border-outline/60 p-3"
            >
              <span className="md-body-medium text-on-surface">{label}</span>
              {isEditing ? (
                <Switch
                  checked={p[k]}
                  onCheckedChange={(v) =>
                    setDraft((d) => ({
                      ...d,
                      securitySettings: {
                        ...d.securitySettings,
                        passwordPolicy: { ...d.securitySettings.passwordPolicy, [k]: v },
                      },
                    }))
                  }
                />
              ) : (
                <span className="text-on-surface">{p[k] ? 'Yes' : 'No'}</span>
              )}
            </div>
          ))}
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label className={readLabel()}>Session timeout (minutes)</Label>
          {isEditing ? (
            <Input
              type="number"
              min={5}
              max={1440}
              value={s.sessionTimeout}
              onChange={(e) =>
                setDraft((d) => ({
                  ...d,
                  securitySettings: {
                    ...d.securitySettings,
                    sessionTimeout: Math.max(5, parseInt(e.target.value, 10) || 5),
                  },
                }))
              }
              className="rounded-2xl"
            />
          ) : (
            valBox(String(s.sessionTimeout))
          )}
        </div>
        <div className="flex items-center justify-between gap-2 rounded-2xl border border-outline/60 p-3">
          <span className="md-body-medium text-on-surface">Two-factor (expected for staff)</span>
          {isEditing ? (
            <Switch
              checked={s.twoFactorAuth}
              onCheckedChange={(v) =>
                setDraft((d) => ({ ...d, securitySettings: { ...d.securitySettings, twoFactorAuth: v } }))
              }
            />
          ) : (
            <span className="text-on-surface">{s.twoFactorAuth ? 'Required' : 'Not required'}</span>
          )}
        </div>
        {(
          [
            ['auditLogging', 'Audit logging'],
            ['dataEncryption', 'Data encryption (at rest in product)'],
            ['apiAccess', 'API access for integrations'],
          ] as const
        ).map(([k, label]) => (
          <div
            key={k}
            className="flex items-center justify-between gap-2 rounded-2xl border border-outline/60 p-3 md:col-span-2"
          >
            <span className="md-body-medium text-on-surface">{label}</span>
            {isEditing ? (
              <Switch
                checked={s[k]}
                onCheckedChange={(v) =>
                  setDraft((d) => ({ ...d, securitySettings: { ...d.securitySettings, [k]: v } }))
                }
              />
            ) : (
              <span className="text-on-surface">{s[k] ? 'On' : 'Off'}</span>
            )}
          </div>
        ))}
        <div className="md:col-span-2 space-y-2">
          <Label className={readLabel()}>
            IP allow list (CIDR or plain IPs, one per line)
          </Label>
          {isEditing ? (
            <Textarea
              value={s.ipWhitelist.join('\n')}
              onChange={(e) => {
                const list = e.target.value
                  .split(/[\n,]/)
                  .map((x) => x.trim())
                  .filter(Boolean)
                setDraft((d) => ({ ...d, securitySettings: { ...d.securitySettings, ipWhitelist: list } }))
              }}
              className="rounded-2xl min-h-[100px] font-mono text-sm"
              placeholder="192.168.0.0/16"
            />
          ) : (
            <p className="text-lg text-on-surface font-mono whitespace-pre-wrap">
              {s.ipWhitelist.length ? s.ipWhitelist.join('\n') : '—'}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

function NotificationsSection({
  display,
  isEditing,
  setDraft,
}: {
  display: OrganizationSettingsView
  isEditing: boolean
  setDraft: DraftSetter
}) {
  const n = display.notificationSettings
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {(
          [
            ['emailNotifications', 'Email'],
            ['smsNotifications', 'SMS'],
            ['systemAlerts', 'System alerts'],
            ['overdueInvoiceAlert', 'Overdue invoice alerts'],
            ['monthlyReport', 'Monthly summary'],
          ] as const
        ).map(([k, label]) => (
          <div
            key={k}
            className="flex items-center justify-between gap-2 rounded-2xl border border-outline/60 p-3"
          >
            <span className="md-body-medium text-on-surface">{label}</span>
            {isEditing ? (
              <Switch
                checked={n[k]}
                onCheckedChange={(v) =>
                  setDraft((d) => ({
                    ...d,
                    notificationSettings: { ...d.notificationSettings, [k]: v },
                  }))
                }
              />
            ) : (
              <span className="text-on-surface">{n[k] ? 'On' : 'Off'}</span>
            )}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(['reportDelivery', 'reminderFrequency'] as const).map((k) => (
          <div key={k} className="space-y-2">
            <Label className={readLabel()}>
              {k === 'reportDelivery' ? 'Default report delivery' : 'Reminder frequency'}
            </Label>
            {isEditing ? (
              <Input
                value={n[k]}
                onChange={(e) =>
                  setDraft((d) => ({
                    ...d,
                    notificationSettings: { ...d.notificationSettings, [k]: e.target.value },
                  }))
                }
                className="rounded-2xl"
              />
            ) : (
              valBox(n[k])
            )}
          </div>
        ))}
        <div className="space-y-2">
          <Label className={readLabel()}>Low cash alert threshold (same currency as reporting)</Label>
          {isEditing ? (
            <Input
              type="number"
              value={n.lowBalanceAlert}
              onChange={(e) =>
                setDraft((d) => ({
                  ...d,
                  notificationSettings: {
                    ...d.notificationSettings,
                    lowBalanceAlert: Math.max(0, parseFloat(e.target.value) || 0),
                  },
                }))
              }
              className="rounded-2xl"
            />
          ) : (
            valBox(String(n.lowBalanceAlert))
          )}
        </div>
      </div>
    </div>
  )
}

function IntegrationsSection({
  display,
  isEditing,
  setDraft,
}: {
  display: OrganizationSettingsView
  isEditing: boolean
  setDraft: DraftSetter
}) {
  const i = display.integrations
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2 rounded-2xl border border-outline/60 p-3">
        <span className="md-body-medium text-on-surface">Bank feeds (planned / manual import)</span>
        {isEditing ? (
          <Switch
            checked={i.bankFeeds}
            onCheckedChange={(v) => setDraft((d) => ({ ...d, integrations: { ...d.integrations, bankFeeds: v } }))}
          />
        ) : (
          <span className="text-on-surface">{i.bankFeeds ? 'On' : 'Off'}</span>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(['paymentGateway', 'taxSoftware', 'crmIntegration', 'emailProvider', 'cloudStorage'] as const).map(
          (k) => (
            <div key={k} className="space-y-2">
              <Label className={readLabel()}>
                {k === 'paymentGateway'
                  ? 'Payment provider'
                  : k === 'taxSoftware'
                    ? 'Tax / compliance tool'
                    : k === 'crmIntegration'
                      ? 'CRM'
                      : k === 'emailProvider'
                        ? 'Email provider'
                        : 'File storage'}
              </Label>
              {isEditing ? (
                <Input
                  value={i[k]}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, integrations: { ...d.integrations, [k]: e.target.value } }))
                  }
                  className="rounded-2xl"
                />
              ) : (
                valBox(i[k])
              )}
            </div>
          )
        )}
      </div>
    </div>
  )
}

function BackupSection({
  display,
  isEditing,
  setDraft,
}: {
  display: OrganizationSettingsView
  isEditing: boolean
  setDraft: DraftSetter
}) {
  const a = display.accountingSettings
  const b = display.backup
  return (
    <div className="space-y-4">
      <p className="md-body-small text-on-surface-variant">
        Schedule fields match <strong>Accounting</strong> and are saved together. Add notes for your off-site or
        IT process here.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label className={readLabel()}>Auto backup (intent)</Label>
          {valBox(a.autoBackup ? 'Yes' : 'No')}
        </div>
        <div>
          <Label className={readLabel()}>Frequency (label)</Label>
          {valBox(a.backupFrequency)}
        </div>
        <div>
          <Label className={readLabel()}>Retention (label)</Label>
          {valBox(a.retentionPeriod)}
        </div>
        <div>
          <Label className={readLabel()}>Last export / backup note</Label>
          {isEditing ? (
            <Textarea
              value={b.lastBackupNote}
              onChange={(e) =>
                setDraft((d) => ({
                  ...d,
                  backup: { ...d.backup, lastBackupNote: e.target.value },
                }))
              }
              placeholder="e.g. Nightly to S3 — 2026-01-15 verified"
              className="rounded-2xl min-h-[88px]"
            />
          ) : (
            valBox(b.lastBackupNote || '—')
          )}
        </div>
      </div>
    </div>
  )
}
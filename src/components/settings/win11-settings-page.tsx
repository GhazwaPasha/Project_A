'use client'

import { useMemo, useState } from 'react'
import { useAuthStore } from '@/stores/auth-store'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Search,
  RefreshCw,
  User,
  Palette,
  Monitor,
  ChevronLeft,
  ChevronRight,
  Bell,
  Shield,
  Eye,
  Globe,
} from 'lucide-react'
import { UserAccentSettingsContent } from '@/components/settings/user-accent-settings'
import { UserThemeSettingsContent } from '@/components/settings/user-theme-settings-card'
import { UserProfileSettingsContent } from '@/components/settings/user-profile-settings'
import type { LucideIcon } from 'lucide-react'

/** Sample values for categories that are not wired to the database yet. */
const placeholderUserSettings = {
  profile: {
    firstName: 'John',
    lastName: 'Doe',
    email: 'john.doe@company.com',
    phone: '+1 (555) 123-4567',
    title: 'Senior Accountant',
    department: 'Finance',
    timezone: 'America/New_York',
    language: 'English (US)',
    dateFormat: 'MM/DD/YYYY',
    timeFormat: '12 Hour',
    currency: 'USD',
  },
  preferences: {
    theme: 'System',
    fontSize: 'Medium',
    density: 'Comfortable',
    sidebarCollapsed: false,
    showNotifications: true,
    autoSave: true,
    confirmActions: true,
    showTooltips: true,
    animations: true,
  },
  notifications: {
    emailNotifications: true,
    pushNotifications: true,
    smsNotifications: false,
    desktopNotifications: true,
    reminderNotifications: true,
    reportNotifications: true,
    systemAlerts: true,
    marketingEmails: false,
    weeklyDigest: true,
    monthlyReport: true,
  },
  security: {
    twoFactorAuth: true,
    sessionTimeout: 30,
    passwordExpiry: 90,
    loginNotifications: true,
    deviceManagement: true,
    apiAccess: false,
    dataExport: true,
    accountRecovery: true,
  },
  privacy: {
    profileVisibility: 'Team',
    activityTracking: true,
    dataSharing: false,
    analytics: true,
    cookies: true,
    locationTracking: false,
    marketingData: false,
  },
}

type SettingsCategory = {
  id: string
  name: string
  description: string
  icon: LucideIcon
  color: string
  /** Live data and saves; otherwise preview-only copy. */
  kind: 'real' | 'placeholder'
  settingsCount?: number
}

const PERSONALIZATION_REAL: SettingsCategory[] = [
  {
    id: 'accent',
    name: 'Accent color',
    description: 'Primary color for buttons, focus rings, and highlights.',
    icon: Palette,
    color: 'text-fuchsia-600 bg-fuchsia-50',
    kind: 'real',
    settingsCount: 1,
  },
  {
    id: 'theme',
    name: 'Theme',
    description: 'Light, dark, or follow your system appearance.',
    icon: Monitor,
    color: 'text-amber-600 bg-amber-50',
    kind: 'real',
    settingsCount: 1,
  },
]

const PROFILE_REAL: SettingsCategory = {
  id: 'profile',
  name: 'Profile & Account',
  description: 'Personal information and account details',
  icon: User,
  color: 'text-blue-600 bg-blue-50',
  kind: 'real',
  settingsCount: 4,
}

const PLACEHOLDER_CATEGORIES: SettingsCategory[] = [
  {
    id: 'preferences',
    name: 'Appearance & Preferences',
    description: 'Layout, density, and other display preferences (preview)',
    icon: Palette,
    color: 'text-purple-600 bg-purple-50',
    kind: 'placeholder',
    settingsCount: 8,
  },
  {
    id: 'notifications',
    name: 'Notifications',
    description: 'Email, push, and system notifications (preview)',
    icon: Bell,
    color: 'text-yellow-600 bg-yellow-50',
    kind: 'placeholder',
    settingsCount: 10,
  },
  {
    id: 'security',
    name: 'Security & Privacy',
    description: 'Password, 2FA, and session controls (preview)',
    icon: Shield,
    color: 'text-red-600 bg-red-50',
    kind: 'placeholder',
    settingsCount: 7,
  },
  {
    id: 'privacy',
    name: 'Data & Privacy',
    description: 'Data sharing and privacy controls (preview)',
    icon: Eye,
    color: 'text-green-600 bg-green-50',
    kind: 'placeholder',
    settingsCount: 7,
  },
  {
    id: 'integrations',
    name: 'Integrations',
    description: 'Connected apps and services (preview)',
    icon: Globe,
    color: 'text-orange-600 bg-orange-50',
    kind: 'placeholder',
    settingsCount: 5,
  },
]

const ALL_SETTINGS_SECTIONS: SettingsCategory[] = [
  ...PERSONALIZATION_REAL,
  PROFILE_REAL,
  ...PLACEHOLDER_CATEGORIES,
]

function categoriesForUser(signedIn: boolean): SettingsCategory[] {
  if (signedIn) return ALL_SETTINGS_SECTIONS
  return [
    ...PERSONALIZATION_REAL.filter((c) => c.id !== 'accent'),
    PROFILE_REAL,
    ...PLACEHOLDER_CATEGORIES,
  ]
}

function PlaceholderBanner() {
  return (
    <p
      className="text-sm rounded-xl border border-outline bg-surface-container px-4 py-3 text-on-surface-variant"
      role="note"
    >
      <span className="font-medium text-on-surface">Preview only.</span> These values are not saved to your account.
      Use <strong className="font-medium">Accent</strong>, <strong className="font-medium">Theme</strong>, and{' '}
      <strong className="font-medium">Profile and Account</strong> (when signed in) for live settings.
    </p>
  )
}

function boolLabel(v: boolean) {
  return v ? 'Enabled' : 'Disabled'
}

export function Win11SettingsPage() {
  const user = useAuthStore((s) => s.user)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const q = searchTerm
  const allCategories = useMemo(() => {
    const rows = categoriesForUser(!!user)
    if (!user) {
      return rows.map((c) => (c.id === 'profile' ? { ...c, kind: 'placeholder' as const } : c))
    }
    return rows
  }, [user])
  const filteredCategories = useMemo(
    () =>
      allCategories.filter((category) => {
        const lower = q.toLowerCase()
        return (
          category.name.toLowerCase().includes(lower) || category.description.toLowerCase().includes(lower)
        )
      }),
    [allCategories, q]
  )

  const getCategoryIcon = (category: SettingsCategory) => {
    const IconComponent = category.icon
    return <IconComponent className="w-6 h-6" />
  }

  const renderCategoryCard = (category: SettingsCategory) => {
    return (
      <Card
        key={category.id}
        className="md-card-expressive group hover:md-elevation-1 transition-all duration-200 cursor-pointer"
        onClick={() => setSelectedCategory(category.id)}
      >
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3 min-w-0">
              <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${category.color}`}>
                {getCategoryIcon(category)}
              </div>
              <div className="min-w-0">
                <h3 className="md-title-medium text-on-surface">{category.name}</h3>
                {category.settingsCount != null && (
                  <p className="md-body-small text-on-surface-variant">{category.settingsCount} settings</p>
                )}
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-on-surface-variant shrink-0 transition-transform group-hover:translate-x-0.5" />
          </div>
          <p className="md-body-medium text-on-surface-variant mb-3">{category.description}</p>
          <div className="flex items-center justify-between gap-2">
            <span
              className={`inline-block max-w-[70%] truncate rounded-md px-2 py-1 text-xs font-medium ${category.color}`}
            >
              {category.kind === 'real' ? 'Live' : 'Preview'}
            </span>
          </div>
        </CardContent>
      </Card>
    )
  }

  const renderSettingsDetails = () => {
    const category = ALL_SETTINGS_SECTIONS.find((c) => c.id === selectedCategory)
    if (!category) return null

    return (
      <Card className="md-card-expressive">
        <CardHeader className="space-y-4">
          <Button
            type="button"
            variant="ghost"
            className="md-surface-nav-button h-10 w-fit -ml-2 px-3 text-on-surface hover:bg-surface-container-highest rounded-2xl"
            onClick={() => setSelectedCategory(null)}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            All settings
          </Button>
          <div className="flex items-center space-x-3 min-w-0">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${category.color}`}>
              {getCategoryIcon(category)}
            </div>
            <div className="min-w-0">
              <CardTitle className="md-title-large text-on-surface">{category.name}</CardTitle>
              <CardDescription className="md-body-medium text-on-surface-variant">
                {category.description}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {selectedCategory === 'accent' && <UserAccentSettingsContent />}
          {selectedCategory === 'theme' && <UserThemeSettingsContent />}
          {selectedCategory === 'profile' &&
            (user ? (
              <UserProfileSettingsContent />
            ) : (
              <>
                <PlaceholderBanner />
                <div className="space-y-4">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
                      <label className="text-sm font-medium text-on-surface-variant">First name</label>
                      <p className="text-lg text-on-surface">{placeholderUserSettings.profile.firstName}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-on-surface-variant">Last name</label>
                      <p className="text-lg text-on-surface">{placeholderUserSettings.profile.lastName}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-on-surface-variant">Email</label>
                      <p className="text-lg text-on-surface">{placeholderUserSettings.profile.email}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-on-surface-variant">Phone</label>
                      <p className="text-lg text-on-surface">{placeholderUserSettings.profile.phone}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-on-surface-variant">Title</label>
                      <p className="text-lg text-on-surface">{placeholderUserSettings.profile.title}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-on-surface-variant">Department</label>
                      <p className="text-lg text-on-surface">{placeholderUserSettings.profile.department}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-on-surface-variant">Timezone</label>
                      <p className="text-lg text-on-surface">{placeholderUserSettings.profile.timezone}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-on-surface-variant">Language</label>
                      <p className="text-lg text-on-surface">{placeholderUserSettings.profile.language}</p>
                    </div>
                  </div>
                </div>
              </>
            ))}

          {selectedCategory === 'preferences' && (
            <>
              <PlaceholderBanner />
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Theme (sample)</label>
                  <p className="text-lg text-on-surface">{placeholderUserSettings.preferences.theme}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Font size</label>
                  <p className="text-lg text-on-surface">{placeholderUserSettings.preferences.fontSize}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Density</label>
                  <p className="text-lg text-on-surface">{placeholderUserSettings.preferences.density}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Sidebar</label>
                  <p className="text-lg text-on-surface">
                    {placeholderUserSettings.preferences.sidebarCollapsed ? 'Collapsed' : 'Expanded'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Auto save</label>
                  <p className="text-lg text-on-surface">{boolLabel(placeholderUserSettings.preferences.autoSave)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Confirm actions</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.preferences.confirmActions)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Show tooltips</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.preferences.showTooltips)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Animations</label>
                  <p className="text-lg text-on-surface">{boolLabel(placeholderUserSettings.preferences.animations)}</p>
                </div>
              </div>
            </>
          )}

          {selectedCategory === 'notifications' && (
            <>
              <PlaceholderBanner />
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Email notifications</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.notifications.emailNotifications)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Push notifications</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.notifications.pushNotifications)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">SMS notifications</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.notifications.smsNotifications)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Desktop notifications</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.notifications.desktopNotifications)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Reminder notifications</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.notifications.reminderNotifications)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Report notifications</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.notifications.reportNotifications)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">System alerts</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.notifications.systemAlerts)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Marketing emails</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.notifications.marketingEmails)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Weekly digest</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.notifications.weeklyDigest)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Monthly report</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.notifications.monthlyReport)}
                  </p>
                </div>
              </div>
            </>
          )}

          {selectedCategory === 'security' && (
            <>
              <PlaceholderBanner />
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Two-factor authentication</label>
                  <p className="text-lg text-on-surface">{boolLabel(placeholderUserSettings.security.twoFactorAuth)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Session timeout</label>
                  <p className="text-lg text-on-surface">{placeholderUserSettings.security.sessionTimeout} minutes</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Password expiry</label>
                  <p className="text-lg text-on-surface">{placeholderUserSettings.security.passwordExpiry} days</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Login notifications</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.security.loginNotifications)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Device management</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.security.deviceManagement)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">API access</label>
                  <p className="text-lg text-on-surface">{boolLabel(placeholderUserSettings.security.apiAccess)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Data export</label>
                  <p className="text-lg text-on-surface">{boolLabel(placeholderUserSettings.security.dataExport)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Account recovery</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.security.accountRecovery)}
                  </p>
                </div>
              </div>
            </>
          )}

          {selectedCategory === 'privacy' && (
            <>
              <PlaceholderBanner />
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Profile visibility</label>
                  <p className="text-lg text-on-surface">{placeholderUserSettings.privacy.profileVisibility}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Activity tracking</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.privacy.activityTracking)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Data sharing</label>
                  <p className="text-lg text-on-surface">{boolLabel(placeholderUserSettings.privacy.dataSharing)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Analytics</label>
                  <p className="text-lg text-on-surface">{boolLabel(placeholderUserSettings.privacy.analytics)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Cookies</label>
                  <p className="text-lg text-on-surface">{boolLabel(placeholderUserSettings.privacy.cookies)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Location tracking</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.privacy.locationTracking)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Marketing data</label>
                  <p className="text-lg text-on-surface">
                    {boolLabel(placeholderUserSettings.privacy.marketingData)}
                  </p>
                </div>
              </div>
            </>
          )}

          {selectedCategory === 'integrations' && (
            <>
              <PlaceholderBanner />
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Google Drive</label>
                  <p className="text-lg text-on-surface">Connected (sample)</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Microsoft Office</label>
                  <p className="text-lg text-on-surface">Not connected (sample)</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Slack</label>
                  <p className="text-lg text-on-surface">Connected (sample)</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Zoom</label>
                  <p className="text-lg text-on-surface">Not connected (sample)</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Dropbox</label>
                  <p className="text-lg text-on-surface">Not connected (sample)</p>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
      <div className="app-page-header sticky top-0 z-30">
        <div className="px-6 py-4">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between mb-4">
            <div>
              <h1 className="md-headline-small text-on-background">Settings</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                Live settings for your account, plus previews of upcoming areas
              </p>
            </div>
            <Button
              type="button"
              onClick={() => window.location.reload()}
              variant="outline"
              className="h-10 px-4 rounded-2xl border-outline hover:bg-primary-container hover:text-on-primary-container shrink-0"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>

          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 text-on-surface-variant pointer-events-none" />
            <input
              type="text"
              placeholder="Search settings…"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full h-12 pl-12 pr-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
              aria-label="Search settings"
            />
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {selectedCategory ? (
          <div className="w-full">{renderSettingsDetails()}</div>
        ) : (
          <div>
            <h2 className="text-lg font-semibold text-on-surface mb-4">Personalization and categories</h2>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-3">
              {filteredCategories.map((category) => renderCategoryCard(category))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

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
  Save,
  Settings,
  User,
  Palette,
  Bell,
  Shield,
  Globe,
  Database,
  Monitor,
  Smartphone,
  Moon,
  Sun,
  Eye,
  EyeOff,
  Lock,
  Key,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Clock,
  ChevronRight,
  CheckCircle,
  AlertTriangle,
  Info,
  Edit,
  Trash2,
  Upload,
  Download as DownloadIcon
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'

// Mock data for settings
const mockUserSettings = {
  profile: {
    firstName: 'John',
    lastName: 'Doe',
    email: 'john.doe@company.com',
    phone: '+1 (555) 123-4567',
    title: 'Senior Accountant',
    department: 'Finance',
    avatar: 'JD',
    timezone: 'America/New_York',
    language: 'English (US)',
    dateFormat: 'MM/DD/YYYY',
    timeFormat: '12 Hour',
    currency: 'USD'
  },
  preferences: {
    theme: 'System', // Light, Dark, System
    fontSize: 'Medium', // Small, Medium, Large
    density: 'Comfortable', // Compact, Comfortable, Spacious
    sidebarCollapsed: false,
    showNotifications: true,
    autoSave: true,
    confirmActions: true,
    showTooltips: true,
    animations: true
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
    monthlyReport: true
  },
  security: {
    twoFactorAuth: true,
    sessionTimeout: 30, // minutes
    passwordExpiry: 90, // days
    loginNotifications: true,
    deviceManagement: true,
    apiAccess: false,
    dataExport: true,
    accountRecovery: true
  },
  privacy: {
    profileVisibility: 'Team', // Public, Team, Private
    activityTracking: true,
    dataSharing: false,
    analytics: true,
    cookies: true,
    locationTracking: false,
    marketingData: false
  }
}

const mockSettingsCategories = [
  {
    id: 'profile',
    name: 'Profile & Account',
    description: 'Personal information and account details',
    icon: User,
    color: 'text-blue-600 bg-blue-50',
    settingsCount: 8
  },
  {
    id: 'preferences',
    name: 'Appearance & Preferences',
    description: 'Theme, layout, and display preferences',
    icon: Palette,
    color: 'text-purple-600 bg-purple-50',
    settingsCount: 8
  },
  {
    id: 'notifications',
    name: 'Notifications',
    description: 'Email, push, and system notifications',
    icon: Bell,
    color: 'text-yellow-600 bg-yellow-50',
    settingsCount: 10
  },
  {
    id: 'security',
    name: 'Security & Privacy',
    description: 'Password, 2FA, and privacy settings',
    icon: Shield,
    color: 'text-red-600 bg-red-50',
    settingsCount: 7
  },
  {
    id: 'privacy',
    name: 'Data & Privacy',
    description: 'Data sharing and privacy controls',
    icon: Eye,
    color: 'text-green-600 bg-green-50',
    settingsCount: 7
  },
  {
    id: 'integrations',
    name: 'Integrations',
    description: 'Connected apps and services',
    icon: Globe,
    color: 'text-orange-600 bg-orange-50',
    settingsCount: 5
  }
]

export function Win11SettingsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingField, setEditingField] = useState<string | null>(null)

  const filteredCategories = mockSettingsCategories.filter(category => {
    const matchesSearch = category.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         category.description.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesSearch
  })

  const getCategoryIcon = (category: any) => {
    const IconComponent = category.icon
    return <IconComponent className="w-6 h-6" />
  }

  const renderCategoryCard = (category: any) => {
    const isSelected = selectedCategory === category.id
    
    return (
      <Card 
        key={category.id}
        className={`md-card-expressive group hover:md-elevation-1 transition-all duration-200 cursor-pointer ${
          isSelected ? 'ring-2 ring-primary' : ''
        }`}
        onClick={() => setSelectedCategory(category.id)}
      >
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${category.color}`}>
                {getCategoryIcon(category)}
              </div>
              <div>
                <h3 className="md-title-medium text-on-surface">{category.name}</h3>
                <p className="md-body-small text-on-surface-variant">{category.settingsCount} settings</p>
              </div>
            </div>
            <ChevronRight className={`w-5 h-5 text-on-surface-variant transition-transform ${
              isSelected ? 'rotate-90' : ''
            }`} />
          </div>
          
          <p className="md-body-medium text-on-surface-variant mb-4">
            {category.description}
          </p>
          
          <div className="flex items-center justify-between">
            <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium ${category.color}`}>
              {category.name}
            </span>
            <div className="flex items-center space-x-1">
              <button className="p-1 hover:bg-surface-container-highest rounded">
                <Edit className="w-4 h-4" />
              </button>
              <button className="p-1 hover:bg-surface-container-highest rounded">
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const renderSettingsDetails = () => {
    if (!selectedCategory) {
      return (
        <Card className="md-card-expressive">
          <CardContent className="p-12 text-center">
            <Settings className="w-16 h-16 text-on-surface-variant mx-auto mb-4" />
            <h3 className="md-title-large text-on-surface mb-2">Select a Category</h3>
            <p className="text-on-surface-variant">
              Choose a settings category from the left to view and configure options.
            </p>
          </CardContent>
        </Card>
      )
    }

    const category = mockSettingsCategories.find(c => c.id === selectedCategory)
    if (!category) return null

    return (
      <Card className="md-card-expressive">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${category.color}`}>
                {getCategoryIcon(category)}
              </div>
              <div>
                <CardTitle className="md-title-large text-on-surface">{category.name}</CardTitle>
                <CardDescription className="md-body-medium text-on-surface-variant">
                  {category.description}
                </CardDescription>
              </div>
            </div>
            <Button onClick={() => setShowEditModal(true)} className="md-button">
              <Edit className="w-4 h-4 mr-2" />
              Edit Settings
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {selectedCategory === 'profile' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">First Name</label>
                  <p className="text-lg text-on-surface">{mockUserSettings.profile.firstName}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Last Name</label>
                  <p className="text-lg text-on-surface">{mockUserSettings.profile.lastName}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Email</label>
                  <p className="text-lg text-on-surface">{mockUserSettings.profile.email}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Phone</label>
                  <p className="text-lg text-on-surface">{mockUserSettings.profile.phone}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Title</label>
                  <p className="text-lg text-on-surface">{mockUserSettings.profile.title}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Department</label>
                  <p className="text-lg text-on-surface">{mockUserSettings.profile.department}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Timezone</label>
                  <p className="text-lg text-on-surface">{mockUserSettings.profile.timezone}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Language</label>
                  <p className="text-lg text-on-surface">{mockUserSettings.profile.language}</p>
                </div>
              </div>
            </div>
          )}

          {selectedCategory === 'preferences' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Theme</label>
                  <p className="text-lg text-on-surface">{mockUserSettings.preferences.theme}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Font Size</label>
                  <p className="text-lg text-on-surface">{mockUserSettings.preferences.fontSize}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Density</label>
                  <p className="text-lg text-on-surface">{mockUserSettings.preferences.density}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Sidebar</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.preferences.sidebarCollapsed ? 'Collapsed' : 'Expanded'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Auto Save</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.preferences.autoSave ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Confirm Actions</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.preferences.confirmActions ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Show Tooltips</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.preferences.showTooltips ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Animations</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.preferences.animations ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {selectedCategory === 'notifications' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Email Notifications</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.notifications.emailNotifications ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Push Notifications</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.notifications.pushNotifications ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">SMS Notifications</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.notifications.smsNotifications ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Desktop Notifications</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.notifications.desktopNotifications ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Reminder Notifications</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.notifications.reminderNotifications ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Report Notifications</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.notifications.reportNotifications ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">System Alerts</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.notifications.systemAlerts ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Marketing Emails</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.notifications.marketingEmails ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Weekly Digest</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.notifications.weeklyDigest ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Monthly Report</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.notifications.monthlyReport ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {selectedCategory === 'security' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Two-Factor Authentication</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.security.twoFactorAuth ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Session Timeout</label>
                  <p className="text-lg text-on-surface">{mockUserSettings.security.sessionTimeout} minutes</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Password Expiry</label>
                  <p className="text-lg text-on-surface">{mockUserSettings.security.passwordExpiry} days</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Login Notifications</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.security.loginNotifications ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Device Management</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.security.deviceManagement ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">API Access</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.security.apiAccess ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Data Export</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.security.dataExport ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {selectedCategory === 'privacy' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Profile Visibility</label>
                  <p className="text-lg text-on-surface">{mockUserSettings.privacy.profileVisibility}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Activity Tracking</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.privacy.activityTracking ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Data Sharing</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.privacy.dataSharing ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Analytics</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.privacy.analytics ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Cookies</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.privacy.cookies ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Location Tracking</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.privacy.locationTracking ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Marketing Data</label>
                  <p className="text-lg text-on-surface">
                    {mockUserSettings.privacy.marketingData ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {selectedCategory === 'integrations' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Google Drive</label>
                  <p className="text-lg text-on-surface">Connected</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Microsoft Office</label>
                  <p className="text-lg text-on-surface">Not Connected</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Slack</label>
                  <p className="text-lg text-on-surface">Connected</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Zoom</label>
                  <p className="text-lg text-on-surface">Not Connected</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Dropbox</label>
                  <p className="text-lg text-on-surface">Not Connected</p>
                </div>
              </div>
            </div>
          )}
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
              <h1 className="md-headline-small text-on-background">Settings</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                Manage your personal preferences and application settings
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Button 
                onClick={() => setShowEditModal(true)}
                className="md-button"
              >
                <Save className="w-4 h-4 mr-2" />
                Save Changes
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
                <DownloadIcon className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>

          {/* Search */}
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
              <input
                type="text"
                placeholder="Search settings categories..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-12 pl-12 pr-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                aria-label="Search settings"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Settings Categories */}
          <div className="lg:col-span-1">
            <h2 className="text-lg font-semibold text-on-surface mb-4">Settings Categories</h2>
            <div className="space-y-4">
              {filteredCategories.map(category => renderCategoryCard(category))}
            </div>
          </div>

          {/* Settings Details */}
          <div className="lg:col-span-2">
            {renderSettingsDetails()}
          </div>
        </div>
      </div>
    </div>
  )
}

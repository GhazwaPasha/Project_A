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
  Building2,
  Settings,
  Shield,
  Globe,
  CreditCard,
  Calendar,
  FileText,
  Database,
  Bell,
  Lock,
  Eye,
  Edit,
  CheckCircle,
  AlertTriangle,
  Info,
  ChevronLeft,
  ChevronRight,
  Plus,
  Trash2,
  Upload
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'

// Mock data for organization settings
const mockOrganizationSettings = {
  companyInfo: {
    name: 'Acme Accounting Solutions',
    legalName: 'Acme Accounting Solutions LLC',
    taxId: '12-3456789',
    registrationNumber: 'REG-2024-001',
    industry: 'Professional Services',
    website: 'https://www.acmeaccounting.com',
    email: 'info@acmeaccounting.com',
    phone: '+1 (555) 123-4567',
    address: {
      street: '123 Business Plaza',
      city: 'New York',
      state: 'NY',
      zipCode: '10001',
      country: 'United States'
    }
  },
  accountingSettings: {
    fiscalYearStart: 'January',
    reportingCurrency: 'USD',
    dateFormat: 'MM/DD/YYYY',
    numberFormat: 'US (1,234.56)',
    decimalPlaces: 2,
    autoBackup: true,
    backupFrequency: 'Daily',
    retentionPeriod: '7 years',
    chartOfAccounts: 'Standard',
    inventoryMethod: 'FIFO',
    depreciationMethod: 'Straight Line'
  },
  securitySettings: {
    passwordPolicy: {
      minLength: 8,
      requireUppercase: true,
      requireLowercase: true,
      requireNumbers: true,
      requireSymbols: true,
      expirationDays: 90
    },
    sessionTimeout: 30, // minutes
    twoFactorAuth: true,
    ipWhitelist: ['192.168.1.0/24', '10.0.0.0/8'],
    auditLogging: true,
    dataEncryption: true,
    apiAccess: false
  },
  notificationSettings: {
    emailNotifications: true,
    smsNotifications: false,
    systemAlerts: true,
    reportDelivery: 'Email',
    reminderFrequency: 'Daily',
    lowBalanceAlert: 1000,
    overdueInvoiceAlert: true,
    monthlyReport: true
  },
  integrations: {
    bankFeeds: true,
    paymentGateway: 'Stripe',
    taxSoftware: 'QuickBooks Tax',
    crmIntegration: 'Salesforce',
    emailProvider: 'Gmail',
    cloudStorage: 'Google Drive'
  }
}

const mockSettingsCategories = [
  {
    id: 'company',
    name: 'Company Information',
    description: 'Basic company details and contact information',
    icon: Building2,
    color: 'text-blue-600 bg-blue-50',
    settingsCount: 8
  },
  {
    id: 'accounting',
    name: 'Accounting Settings',
    description: 'Fiscal year, currency, and accounting preferences',
    icon: FileText,
    color: 'text-green-600 bg-green-50',
    settingsCount: 10
  },
  {
    id: 'security',
    name: 'Security & Access',
    description: 'Password policies, 2FA, and access controls',
    icon: Shield,
    color: 'text-red-600 bg-red-50',
    settingsCount: 7
  },
  {
    id: 'notifications',
    name: 'Notifications',
    description: 'Email, SMS, and system alert preferences',
    icon: Bell,
    color: 'text-yellow-600 bg-yellow-50',
    settingsCount: 6
  },
  {
    id: 'integrations',
    name: 'Integrations',
    description: 'Third-party services and API connections',
    icon: Globe,
    color: 'text-purple-600 bg-purple-50',
    settingsCount: 6
  },
  {
    id: 'backup',
    name: 'Backup & Recovery',
    description: 'Data backup schedules and recovery options',
    icon: Database,
    color: 'text-gray-600 bg-gray-50',
    settingsCount: 4
  }
]

export function Win11OrganizationSettingsPage() {
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
    return (
      <Card
        key={category.id}
        className="md-card-expressive group hover:md-elevation-1 transition-all duration-200 cursor-pointer"
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
            <ChevronRight className="w-5 h-5 text-on-surface-variant transition-transform group-hover:translate-x-0.5" />
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
    const category = mockSettingsCategories.find(c => c.id === selectedCategory)
    if (!category) return null

    return (
      <Card className="md-card-expressive">
        <CardHeader className="space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
            <Button
              type="button"
              variant="ghost"
              className="md-surface-nav-button h-10 w-fit -ml-2 px-3 text-on-surface hover:bg-surface-container-highest rounded-2xl"
              onClick={() => setSelectedCategory(null)}
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              All settings
            </Button>
          </div>
          <div className="flex items-center justify-between gap-4">
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
            <Button onClick={() => setShowEditModal(true)} className="md-button shrink-0">
              <Edit className="w-4 h-4 mr-2" />
              Edit Settings
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {selectedCategory === 'company' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Company Name</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.companyInfo.name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Legal Name</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.companyInfo.legalName}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Tax ID</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.companyInfo.taxId}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Industry</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.companyInfo.industry}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Email</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.companyInfo.email}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Phone</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.companyInfo.phone}</p>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-on-surface-variant">Address</label>
                <p className="text-lg text-on-surface">
                  {mockOrganizationSettings.companyInfo.address.street}<br />
                  {mockOrganizationSettings.companyInfo.address.city}, {mockOrganizationSettings.companyInfo.address.state} {mockOrganizationSettings.companyInfo.address.zipCode}<br />
                  {mockOrganizationSettings.companyInfo.address.country}
                </p>
              </div>
            </div>
          )}

          {selectedCategory === 'accounting' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Fiscal Year Start</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.accountingSettings.fiscalYearStart}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Reporting Currency</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.accountingSettings.reportingCurrency}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Date Format</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.accountingSettings.dateFormat}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Number Format</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.accountingSettings.numberFormat}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Auto Backup</label>
                  <p className="text-lg text-on-surface">
                    {mockOrganizationSettings.accountingSettings.autoBackup ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Backup Frequency</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.accountingSettings.backupFrequency}</p>
                </div>
              </div>
            </div>
          )}

          {selectedCategory === 'security' && (
            <div className="space-y-4">
              <div>
                <h4 className="text-lg font-medium text-on-surface mb-3">Password Policy</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-on-surface-variant">Minimum Length</label>
                    <p className="text-lg text-on-surface">{mockOrganizationSettings.securitySettings.passwordPolicy.minLength} characters</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-on-surface-variant">Expiration</label>
                    <p className="text-lg text-on-surface">{mockOrganizationSettings.securitySettings.passwordPolicy.expirationDays} days</p>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Two-Factor Authentication</label>
                  <p className="text-lg text-on-surface">
                    {mockOrganizationSettings.securitySettings.twoFactorAuth ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Session Timeout</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.securitySettings.sessionTimeout} minutes</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Audit Logging</label>
                  <p className="text-lg text-on-surface">
                    {mockOrganizationSettings.securitySettings.auditLogging ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Data Encryption</label>
                  <p className="text-lg text-on-surface">
                    {mockOrganizationSettings.securitySettings.dataEncryption ? 'Enabled' : 'Disabled'}
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
                    {mockOrganizationSettings.notificationSettings.emailNotifications ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">SMS Notifications</label>
                  <p className="text-lg text-on-surface">
                    {mockOrganizationSettings.notificationSettings.smsNotifications ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Report Delivery</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.notificationSettings.reportDelivery}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Reminder Frequency</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.notificationSettings.reminderFrequency}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Low Balance Alert</label>
                  <p className="text-lg text-on-surface">
                    ${mockOrganizationSettings.notificationSettings.lowBalanceAlert}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Overdue Invoice Alert</label>
                  <p className="text-lg text-on-surface">
                    {mockOrganizationSettings.notificationSettings.overdueInvoiceAlert ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {selectedCategory === 'integrations' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Bank Feeds</label>
                  <p className="text-lg text-on-surface">
                    {mockOrganizationSettings.integrations.bankFeeds ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Payment Gateway</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.integrations.paymentGateway}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Tax Software</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.integrations.taxSoftware}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">CRM Integration</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.integrations.crmIntegration}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Email Provider</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.integrations.emailProvider}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Cloud Storage</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.integrations.cloudStorage}</p>
                </div>
              </div>
            </div>
          )}

          {selectedCategory === 'backup' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Auto Backup</label>
                  <p className="text-lg text-on-surface">
                    {mockOrganizationSettings.accountingSettings.autoBackup ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Backup Frequency</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.accountingSettings.backupFrequency}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Retention Period</label>
                  <p className="text-lg text-on-surface">{mockOrganizationSettings.accountingSettings.retentionPeriod}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-on-surface-variant">Last Backup</label>
                  <p className="text-lg text-on-surface">{formatDate(new Date().toISOString())}</p>
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
      <div className="app-page-header sticky top-0 z-30">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="md-headline-small text-on-background">Organization Settings</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                Configure company settings and preferences
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
                <Download className="w-4 h-4 mr-2" />
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
        {selectedCategory ? (
          <div className="w-full">{renderSettingsDetails()}</div>
        ) : (
          <div>
            <h2 className="text-lg font-semibold text-on-surface mb-4">Settings categories</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
              {filteredCategories.map((category) => renderCategoryCard(category))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

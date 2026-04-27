import type { Organization, OrganizationSettings } from '@/types'

/**
 * `organizations.settings` may come from Postgres as an object, or in some
 * environments as a JSON string after serialization. We always normalize to
 * a plain object so `reportingCurrency` and other keys are not lost.
 */
export function parseOrganizationSettingsValue(
  raw: unknown
): OrganizationSettings & Record<string, unknown> {
  if (raw == null) return {}
  if (typeof raw === 'string') {
    try {
      const p = JSON.parse(raw) as unknown
      if (p && typeof p === 'object' && !Array.isArray(p)) {
        return p as OrganizationSettings & Record<string, unknown>
      }
    } catch {
      return {}
    }
    return {}
  }
  if (typeof raw === 'object' && !Array.isArray(raw)) {
    return raw as OrganizationSettings & Record<string, unknown>
  }
  return {}
}

/** Stored under `organization.settings` and merged with DB row `name` / `description`. */
export type CompanyInfoSettings = {
  legalName: string
  taxId: string
  registrationNumber: string
  industry: string
  website: string
  email: string
  phone: string
  address: {
    street: string
    city: string
    state: string
    zipCode: string
    country: string
  }
}

export type AccountingInfoSettings = {
  fiscalYearStart: string
  reportingCurrency: string
  dateFormat: string
  numberFormat: string
  decimalPlaces: number
  autoBackup: boolean
  backupFrequency: string
  retentionPeriod: string
  chartOfAccounts: string
  inventoryMethod: string
  depreciationMethod: string
}

export type PasswordPolicySettings = {
  minLength: number
  requireUppercase: boolean
  requireLowercase: boolean
  requireNumbers: boolean
  requireSymbols: boolean
  expirationDays: number
}

export type SecurityInfoSettings = {
  passwordPolicy: PasswordPolicySettings
  sessionTimeout: number
  twoFactorAuth: boolean
  ipWhitelist: string[]
  auditLogging: boolean
  dataEncryption: boolean
  apiAccess: boolean
}

export type NotificationInfoSettings = {
  emailNotifications: boolean
  smsNotifications: boolean
  systemAlerts: boolean
  reportDelivery: string
  reminderFrequency: string
  lowBalanceAlert: number
  overdueInvoiceAlert: boolean
  monthlyReport: boolean
}

export type IntegrationsInfoSettings = {
  bankFeeds: boolean
  paymentGateway: string
  taxSoftware: string
  crmIntegration: string
  emailProvider: string
  cloudStorage: string
}

export type BackupInfoSettings = {
  autoBackup: boolean
  backupFrequency: string
  retentionPeriod: string
  lastBackupNote: string
}

export const DEFAULT_COMPANY: CompanyInfoSettings = {
  legalName: '',
  taxId: '',
  registrationNumber: '',
  industry: '',
  website: '',
  email: '',
  phone: '',
  address: { street: '', city: '', state: '', zipCode: '', country: '' },
}

export const DEFAULT_ACCOUNTING: AccountingInfoSettings = {
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
  depreciationMethod: 'Straight Line',
}

export const DEFAULT_PASSWORD_POLICY: PasswordPolicySettings = {
  minLength: 8,
  requireUppercase: true,
  requireLowercase: true,
  requireNumbers: true,
  requireSymbols: true,
  expirationDays: 90,
}

export const DEFAULT_SECURITY: SecurityInfoSettings = {
  passwordPolicy: DEFAULT_PASSWORD_POLICY,
  sessionTimeout: 30,
  twoFactorAuth: false,
  ipWhitelist: [],
  auditLogging: true,
  dataEncryption: true,
  apiAccess: false,
}

export const DEFAULT_NOTIFICATIONS: NotificationInfoSettings = {
  emailNotifications: true,
  smsNotifications: false,
  systemAlerts: true,
  reportDelivery: 'Email',
  reminderFrequency: 'Daily',
  lowBalanceAlert: 1000,
  overdueInvoiceAlert: true,
  monthlyReport: true,
}

export const DEFAULT_INTEGRATIONS: IntegrationsInfoSettings = {
  bankFeeds: false,
  paymentGateway: 'Not configured',
  taxSoftware: 'Not configured',
  crmIntegration: 'Not configured',
  emailProvider: 'Not configured',
  cloudStorage: 'Not configured',
}

export const DEFAULT_BACKUP: BackupInfoSettings = {
  autoBackup: true,
  backupFrequency: 'Daily',
  retentionPeriod: '7 years',
  lastBackupNote: '',
}

function mergeAddress(
  a: CompanyInfoSettings['address'],
  b?: Partial<CompanyInfoSettings['address']>
): CompanyInfoSettings['address'] {
  return { ...a, ...b }
}

export function buildOrganizationSettingsView(org: Organization | null) {
  const base = parseOrganizationSettingsValue(org?.settings)
  const raw = base as OrganizationSettings & {
    companyInfo?: Partial<CompanyInfoSettings> & { address?: Partial<CompanyInfoSettings['address']> }
    accountingSettings?: Partial<AccountingInfoSettings>
    securitySettings?: Partial<SecurityInfoSettings> & { passwordPolicy?: Partial<PasswordPolicySettings> }
    notificationSettings?: Partial<NotificationInfoSettings>
    integrations?: Partial<IntegrationsInfoSettings>
    backup?: Partial<BackupInfoSettings>
  }

  const c: CompanyInfoSettings = {
    ...DEFAULT_COMPANY,
    ...raw.companyInfo,
    address: mergeAddress(DEFAULT_COMPANY.address, raw.companyInfo?.address),
  }
  const sec: SecurityInfoSettings = {
    ...DEFAULT_SECURITY,
    ...raw.securitySettings,
    passwordPolicy: { ...DEFAULT_PASSWORD_POLICY, ...raw.securitySettings?.passwordPolicy },
  }

  return {
    name: org?.name ?? '',
    description: org?.description ?? '',
    companyInfo: c,
    accountingSettings: { ...DEFAULT_ACCOUNTING, ...raw.accountingSettings },
    securitySettings: sec,
    notificationSettings: { ...DEFAULT_NOTIFICATIONS, ...raw.notificationSettings },
    integrations: { ...DEFAULT_INTEGRATIONS, ...raw.integrations },
    backup: { ...DEFAULT_BACKUP, ...raw.backup },
  }
}

export type OrganizationSettingsView = ReturnType<typeof buildOrganizationSettingsView>

/** Reporting currency and decimals from the org row (same for every member in that org). */
export function getOrganizationAccountingDisplay(org: Organization | null) {
  const v = buildOrganizationSettingsView(org)
  return {
    reportingCurrency: v.accountingSettings.reportingCurrency,
    decimalPlaces: v.accountingSettings.decimalPlaces,
  }
}

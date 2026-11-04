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
  decimalPlaces: number
}

export type PasswordPolicySettings = {
  minLength: number
}

export type SecurityInfoSettings = {
  passwordPolicy: PasswordPolicySettings
  sessionTimeout: number
}

export type NotificationInfoSettings = {
  lowBalanceAlert: number
}

export type IntegrationsInfoSettings = {
}

export type BackupInfoSettings = {
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
  decimalPlaces: 2,
}

export const DEFAULT_PASSWORD_POLICY: PasswordPolicySettings = {
  minLength: 8,
}

export const DEFAULT_SECURITY: SecurityInfoSettings = {
  passwordPolicy: DEFAULT_PASSWORD_POLICY,
  sessionTimeout: 30,
}

export const DEFAULT_NOTIFICATIONS: NotificationInfoSettings = {
  lowBalanceAlert: 1000,
}

export const DEFAULT_INTEGRATIONS: IntegrationsInfoSettings = {
}

export const DEFAULT_BACKUP: BackupInfoSettings = {
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

import { appDataRequest } from '@/lib/app-data-request'
import type { Account, AccountReportCategory, AccountType } from '@/types'

/** Browser client: calls `/api/app-data` (server uses service role + membership checks). */
export class AccountService {
  static async getAccounts(
    organizationId: string,
    accountType?: AccountType,
    isActive: boolean = true
  ): Promise<Account[]> {
    return appDataRequest('AccountService', 'getAccounts', [organizationId, accountType, isActive])
  }

  static async getAccount(id: number): Promise<Account | null> {
    return appDataRequest('AccountService', 'getAccount', [id])
  }

  static async createAccount(accountData: {
    organization_id: string
    code: string
    name: string
    account_type: AccountType
    parent_id?: number
    description?: string
    group?: string | null
    report_category?: AccountReportCategory | null
    is_postable?: boolean
  }): Promise<Account> {
    return appDataRequest('AccountService', 'createAccount', [accountData])
  }

  static async updateAccount(id: number, accountData: Partial<Account>): Promise<Account> {
    return appDataRequest('AccountService', 'updateAccount', [id, accountData])
  }

  static async deleteAccount(id: number): Promise<void> {
    return appDataRequest('AccountService', 'deleteAccount', [id])
  }

  static async getAccountHierarchy(organizationId: string): Promise<Account[]> {
    return appDataRequest('AccountService', 'getAccountHierarchy', [organizationId])
  }

  static async getChildAccounts(parentId: number): Promise<Account[]> {
    return appDataRequest('AccountService', 'getChildAccounts', [parentId])
  }

  static async getParentAccounts(organizationId: string): Promise<Account[]> {
    return appDataRequest('AccountService', 'getParentAccounts', [organizationId])
  }

  static async searchAccounts(
    organizationId: string,
    searchTerm: string,
    accountType?: AccountType,
    limit: number = 50
  ): Promise<Account[]> {
    return appDataRequest('AccountService', 'searchAccounts', [organizationId, searchTerm, accountType, limit])
  }

  static async getAccountsByType(organizationId: string, accountType: AccountType): Promise<Account[]> {
    return appDataRequest('AccountService', 'getAccountsByType', [organizationId, accountType])
  }

  static async getPostableAccounts(organizationId: string): Promise<Account[]> {
    return appDataRequest('AccountService', 'getPostableAccounts', [organizationId])
  }

  static async validateAccountCode(organizationId: string, code: string, excludeId?: number): Promise<boolean> {
    return appDataRequest('AccountService', 'validateAccountCode', [organizationId, code, excludeId])
  }

  static async getAccountBalance(accountId: number, asOfDate?: string): Promise<number> {
    return appDataRequest('AccountService', 'getAccountBalance', [accountId, asOfDate])
  }

  static async getAccountStats(organizationId: string): Promise<{
    total_accounts: number
    accounts_by_type: Record<AccountType, number>
    active_accounts: number
    inactive_accounts: number
    postable_accounts: number
  }> {
    return appDataRequest('AccountService', 'getAccountStats', [organizationId])
  }

  static async getChartOfAccounts(organizationId: string): Promise<Account[]> {
    return appDataRequest('AccountService', 'getChartOfAccounts', [organizationId])
  }

  static async exportChartOfAccounts(organizationId: string): Promise<Account[]> {
    return appDataRequest('AccountService', 'exportChartOfAccounts', [organizationId])
  }

  static async importChartOfAccounts(
    organizationId: string,
    accounts: Omit<Account, 'id' | 'organization_id' | 'created_at' | 'updated_at' | 'created_by'>[]
  ): Promise<Account[]> {
    return appDataRequest('AccountService', 'importChartOfAccounts', [organizationId, accounts])
  }
}

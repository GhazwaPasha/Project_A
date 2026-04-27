import { useQuery, useQueryClient } from '@tanstack/react-query'
import { DataService } from '@/lib/data-service'
import { useCurrentOrganization } from '@/contexts/organization-context'
import { queryKeys } from '@/lib/query-keys'
import type {
  Account,
  AccountBalanceRow,
  AgedPayablesReportData,
  AgedReceivablesReportData,
  BalanceSheetReportData,
  FinancialMetricsData,
  IncomeStatementReportData,
  JournalEntry,
  JournalEntryLine,
  TrialBalanceReportData,
} from '@/types'

export type {
  FinancialMetricsData,
  AccountBalanceRow,
  AgedPayablesReportData,
  AgedReceivablesReportData,
  TrialBalanceReportData,
  IncomeStatementReportData,
  BalanceSheetReportData,
} from '@/types'

type DashboardBundleData = {
  financialMetrics: FinancialMetricsData
  accountBalances: AccountBalanceRow[]
}

/** One `/api/app-data` request for both metrics and balances (parallel on server). Prefer on dashboard. */
export const useDashboardBundle = (dateRange?: { fromDate?: string; toDate?: string }) => {
  const currentOrganization = useCurrentOrganization()
  return useQuery<DashboardBundleData>({
    queryKey: queryKeys.dashboardBundle(currentOrganization?.id || '', dateRange),
    queryFn: () =>
      DataService.getDashboardBundle(
        currentOrganization!.id,
        dateRange?.fromDate,
        dateRange?.toDate
      ),
    enabled: !!currentOrganization,
    staleTime: 3 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  })
}

// Financial metrics hook
export const useFinancialMetrics = (dateRange?: { fromDate?: string; toDate?: string }) => {
  const currentOrganization = useCurrentOrganization()

  return useQuery<FinancialMetricsData>({
    queryKey: queryKeys.financialMetrics(currentOrganization?.id || '', dateRange),
    queryFn: () => DataService.getFinancialMetrics(currentOrganization!.id),
    enabled: !!currentOrganization,
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  })
}

// Account balances hook
export const useAccountBalances = (dateRange?: { fromDate?: string; toDate?: string }) => {
  const currentOrganization = useCurrentOrganization()

  return useQuery<AccountBalanceRow[]>({
    queryKey: queryKeys.accountBalances(currentOrganization?.id || '', dateRange),
    queryFn: () =>
      DataService.getAccountBalances(
        currentOrganization!.id,
        dateRange?.fromDate,
        dateRange?.toDate
      ),
    enabled: !!currentOrganization,
    staleTime: 3 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })
}

// Journal entries hook
export const useJournalEntries = () => {
  const currentOrganization = useCurrentOrganization()

  return useQuery<(JournalEntry & { lines: JournalEntryLine[] })[]>({
    queryKey: queryKeys.journalEntries(currentOrganization?.id || ''),
    queryFn: () => DataService.getJournalEntriesWithLines(currentOrganization!.id),
    enabled: !!currentOrganization,
    staleTime: 2 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })
}

// Accounts hook
export const useAccounts = () => {
  const currentOrganization = useCurrentOrganization()

  return useQuery<Account[]>({
    queryKey: queryKeys.accounts(currentOrganization?.id || '', true),
    queryFn: () => DataService.getAccounts(currentOrganization!.id, true),
    enabled: !!currentOrganization,
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  })
}

// Reports hooks
export const useBalanceSheet = (asOfDate?: string) => {
  const currentOrganization = useCurrentOrganization()

  return useQuery<BalanceSheetReportData>({
    queryKey: queryKeys.balanceSheet(currentOrganization?.id || '', asOfDate),
    queryFn: () => DataService.generateBalanceSheet(currentOrganization!.id, asOfDate),
    enabled: !!currentOrganization,
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  })
}

export const useIncomeStatement = (fromDate?: string, toDate?: string) => {
  const currentOrganization = useCurrentOrganization()

  return useQuery<IncomeStatementReportData>({
    queryKey: queryKeys.incomeStatement(currentOrganization?.id || '', fromDate, toDate),
    queryFn: () => DataService.generateIncomeStatement(currentOrganization!.id, fromDate, toDate),
    enabled: !!currentOrganization,
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  })
}

export const useTrialBalance = (asOfDate?: string) => {
  const currentOrganization = useCurrentOrganization()

  return useQuery<TrialBalanceReportData>({
    queryKey: queryKeys.trialBalance(currentOrganization?.id || '', asOfDate),
    queryFn: () => DataService.generateTrialBalance(currentOrganization!.id, asOfDate),
    enabled: !!currentOrganization,
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  })
}

export const useAgedReceivables = (asOfDate?: string) => {
  const currentOrganization = useCurrentOrganization()

  return useQuery<AgedReceivablesReportData>({
    queryKey: queryKeys.agedReceivables(currentOrganization?.id || '', asOfDate),
    queryFn: () => DataService.generateAgedReceivables(currentOrganization!.id, asOfDate),
    enabled: !!currentOrganization,
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  })
}

export const useAgedPayables = (asOfDate?: string) => {
  const currentOrganization = useCurrentOrganization()

  return useQuery<AgedPayablesReportData>({
    queryKey: queryKeys.agedPayables(currentOrganization?.id || '', asOfDate),
    queryFn: () => DataService.generateAgedPayables(currentOrganization!.id, asOfDate),
    enabled: !!currentOrganization,
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  })
}

// Utility hook for invalidating organization data
export const useInvalidateOrganizationData = () => {
  const queryClient = useQueryClient()
  const currentOrganization = useCurrentOrganization()

  const invalidateAll = () => {
    if (currentOrganization) {
      queryClient.invalidateQueries({
        predicate: (query) => query.queryKey.includes(currentOrganization.id),
      })
    }
  }

  const invalidateFinancial = () => {
    if (currentOrganization) {
      const id = currentOrganization.id
      for (const qk of queryKeys.financialQueryPrefixes(id)) {
        queryClient.invalidateQueries({ queryKey: qk })
      }
    }
  }

  const invalidateReports = () => {
    if (currentOrganization) {
      const id = currentOrganization.id
      for (const qk of queryKeys.reportQueryPrefixes(id)) {
        queryClient.invalidateQueries({ queryKey: qk })
      }
    }
  }

  const invalidateInventory = () => {
    if (currentOrganization) {
      const id = currentOrganization.id
      for (const qk of queryKeys.inventoryQueryPrefixes(id)) {
        queryClient.invalidateQueries({ queryKey: qk })
      }
    }
  }

  const invalidateSpecific = (queryKey: string[]) => {
    queryClient.invalidateQueries({ queryKey })
  }

  return {
    invalidateAll,
    invalidateFinancial,
    invalidateReports,
    invalidateInventory,
    invalidateSpecific,
  }
}

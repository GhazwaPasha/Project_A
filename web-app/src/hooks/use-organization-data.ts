import { useQuery, useQueryClient } from '@tanstack/react-query'
import { DataService } from '@/lib/data-service'
import { useCurrentOrganization } from '@/stores/auth-store'

// Financial metrics hook
export const useFinancialMetrics = (dateRange?: { fromDate?: string; toDate?: string }) => {
  const currentOrganization = useCurrentOrganization()
  
  return useQuery({
    queryKey: ['financial-metrics', currentOrganization?.id, dateRange],
    queryFn: () => DataService.getFinancialMetrics(currentOrganization!.id),
    enabled: !!currentOrganization,
    staleTime: 5 * 60 * 1000,
    cacheTime: 15 * 60 * 1000,
  })
}

// Account balances hook
export const useAccountBalances = (dateRange?: { fromDate?: string; toDate?: string }) => {
  const currentOrganization = useCurrentOrganization()
  
  return useQuery({
    queryKey: ['account-balances', currentOrganization?.id, dateRange],
    queryFn: () => DataService.getAccountBalances(
      currentOrganization!.id, 
      dateRange?.fromDate, 
      dateRange?.toDate
    ),
    enabled: !!currentOrganization,
    staleTime: 3 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
  })
}

// Journal entries hook
export const useJournalEntries = () => {
  const currentOrganization = useCurrentOrganization()
  
  return useQuery({
    queryKey: ['journal-entries', currentOrganization?.id],
    queryFn: () => DataService.getJournalEntriesWithLines(currentOrganization!.id),
    enabled: !!currentOrganization,
    staleTime: 2 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
  })
}

// Accounts hook
export const useAccounts = () => {
  const currentOrganization = useCurrentOrganization()
  
  return useQuery({
    queryKey: ['accounts', currentOrganization?.id],
    queryFn: () => DataService.getAccounts(currentOrganization!.id, true),
    enabled: !!currentOrganization,
    staleTime: 10 * 60 * 1000, // Accounts change less frequently
    cacheTime: 30 * 60 * 1000,
  })
}

// Reports hooks
export const useBalanceSheet = (asOfDate?: string) => {
  const currentOrganization = useCurrentOrganization()
  
  return useQuery({
    queryKey: ['balance-sheet', currentOrganization?.id, asOfDate],
    queryFn: () => DataService.generateBalanceSheet(currentOrganization!.id, asOfDate),
    enabled: !!currentOrganization,
    staleTime: 5 * 60 * 1000,
    cacheTime: 15 * 60 * 1000,
  })
}

export const useIncomeStatement = (fromDate?: string, toDate?: string) => {
  const currentOrganization = useCurrentOrganization()
  
  return useQuery({
    queryKey: ['income-statement', currentOrganization?.id, fromDate, toDate],
    queryFn: () => DataService.generateIncomeStatement(currentOrganization!.id, fromDate, toDate),
    enabled: !!currentOrganization,
    staleTime: 5 * 60 * 1000,
    cacheTime: 15 * 60 * 1000,
  })
}

export const useTrialBalance = (asOfDate?: string) => {
  const currentOrganization = useCurrentOrganization()
  
  return useQuery({
    queryKey: ['trial-balance', currentOrganization?.id, asOfDate],
    queryFn: () => DataService.generateTrialBalance(currentOrganization!.id, asOfDate),
    enabled: !!currentOrganization,
    staleTime: 5 * 60 * 1000,
    cacheTime: 15 * 60 * 1000,
  })
}

export const useAgedReceivables = (asOfDate?: string) => {
  const currentOrganization = useCurrentOrganization()
  
  return useQuery({
    queryKey: ['aged-receivables', currentOrganization?.id, asOfDate],
    queryFn: () => DataService.generateAgedReceivables(currentOrganization!.id, asOfDate),
    enabled: !!currentOrganization,
    staleTime: 5 * 60 * 1000,
    cacheTime: 15 * 60 * 1000,
  })
}

export const useAgedPayables = (asOfDate?: string) => {
  const currentOrganization = useCurrentOrganization()
  
  return useQuery({
    queryKey: ['aged-payables', currentOrganization?.id, asOfDate],
    queryFn: () => DataService.generateAgedPayables(currentOrganization!.id, asOfDate),
    enabled: !!currentOrganization,
    staleTime: 5 * 60 * 1000,
    cacheTime: 15 * 60 * 1000,
  })
}

// Utility hook for invalidating organization data
export const useInvalidateOrganizationData = () => {
  const queryClient = useQueryClient()
  const currentOrganization = useCurrentOrganization()
  
  const invalidateAll = () => {
    if (currentOrganization) {
      queryClient.invalidateQueries({
        predicate: (query) => query.queryKey.includes(currentOrganization.id)
      })
    }
  }
  
  const invalidateSpecific = (queryKey: string) => {
    if (currentOrganization) {
      queryClient.invalidateQueries({
        queryKey: [queryKey, currentOrganization.id]
      })
    }
  }
  
  return { invalidateAll, invalidateSpecific }
}

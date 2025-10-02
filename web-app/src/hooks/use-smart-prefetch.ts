import { useQueryClient } from '@tanstack/react-query'
import { useCurrentOrganization } from '@/stores/auth-store'
import { useCallback } from 'react'
import { DataService } from '@/lib/data-service'

export const useSmartPrefetch = () => {
  const queryClient = useQueryClient()
  const currentOrganization = useCurrentOrganization()
  
  const prefetchReportData = useCallback(async (reportType: string) => {
    if (!currentOrganization) return
    
    const prefetchMap = {
      'balance-sheet': () => queryClient.prefetchQuery({
        queryKey: ['balance-sheet', currentOrganization.id],
        queryFn: () => DataService.generateBalanceSheet(currentOrganization.id),
        staleTime: 5 * 60 * 1000,
      }),
      'income-statement': () => queryClient.prefetchQuery({
        queryKey: ['income-statement', currentOrganization.id],
        queryFn: () => DataService.generateIncomeStatement(currentOrganization.id),
        staleTime: 5 * 60 * 1000,
      }),
      'trial-balance': () => queryClient.prefetchQuery({
        queryKey: ['trial-balance', currentOrganization.id],
        queryFn: () => DataService.generateTrialBalance(currentOrganization.id),
        staleTime: 5 * 60 * 1000,
      }),
      'aged-receivables': () => queryClient.prefetchQuery({
        queryKey: ['aged-receivables', currentOrganization.id],
        queryFn: () => DataService.generateAgedReceivables(currentOrganization.id),
        staleTime: 5 * 60 * 1000,
      }),
      'aged-payables': () => queryClient.prefetchQuery({
        queryKey: ['aged-payables', currentOrganization.id],
        queryFn: () => DataService.generateAgedPayables(currentOrganization.id),
        staleTime: 5 * 60 * 1000,
      }),
    }
    
    const prefetchFn = prefetchMap[reportType as keyof typeof prefetchMap]
    if (prefetchFn) {
      await prefetchFn()
    }
  }, [queryClient, currentOrganization])
  
  const prefetchOnHover = useCallback((reportType: string) => {
    // Prefetch when user hovers over report card
    const timeoutId = setTimeout(() => {
      prefetchReportData(reportType)
    }, 200) // 200ms delay
    
    return () => clearTimeout(timeoutId)
  }, [prefetchReportData])
  
  const prefetchCommonData = useCallback(async () => {
    if (!currentOrganization) return
    
    // Prefetch commonly accessed data
    const commonDataPromises = [
      queryClient.prefetchQuery({
        queryKey: ['financial-metrics', currentOrganization.id],
        queryFn: () => DataService.getFinancialMetrics(currentOrganization.id),
        staleTime: 5 * 60 * 1000,
      }),
      queryClient.prefetchQuery({
        queryKey: ['account-balances', currentOrganization.id],
        queryFn: () => DataService.getAccountBalances(currentOrganization.id),
        staleTime: 3 * 60 * 1000,
      }),
    ]
    
    await Promise.allSettled(commonDataPromises)
  }, [queryClient, currentOrganization])
  
  return { 
    prefetchReportData, 
    prefetchOnHover, 
    prefetchCommonData 
  }
}

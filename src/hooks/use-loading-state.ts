'use client'

import { useQuery } from '@tanstack/react-query'
import { useCurrentOrganization } from '@/contexts/organization-context'
import { queryKeys } from '@/lib/query-keys'

/**
 * Centralized loading state management hook
 * Provides consistent loading states across the application
 */
export function useLoadingState() {
  const currentOrganization = useCurrentOrganization()
  
  // Check if organization is loading
  const { isLoading: orgLoading } = useQuery({
    queryKey: queryKeys.currentOrganization(currentOrganization?.id || ''),
    queryFn: () => Promise.resolve(currentOrganization),
    enabled: false, // Don't actually fetch, just check loading state
  })

  // Check if critical data is loading
  const { isLoading: financialLoading } = useQuery({
    queryKey: queryKeys.financialMetrics(currentOrganization?.id || ''),
    queryFn: () => Promise.resolve(null),
    enabled: false,
  })

  const { isLoading: accountsLoading } = useQuery({
    queryKey: queryKeys.accounts(currentOrganization?.id || '', true),
    queryFn: () => Promise.resolve(null),
    enabled: false,
  })

  return {
    isOrganizationLoading: orgLoading,
    isFinancialDataLoading: financialLoading,
    isAccountsLoading: accountsLoading,
    isAnyLoading: orgLoading || financialLoading || accountsLoading,
  }
}

/**
 * Hook for page-level loading states
 * Provides loading states for specific page types
 */
export function usePageLoadingState(pageType: 'home' | 'reports' | 'inventory' | 'vouchers' | 'suppliers') {
  const currentOrganization = useCurrentOrganization()
  
  const getPageQueries = () => {
    if (!currentOrganization) return []
    
    const baseQueries = [
      queryKeys.financialMetrics(currentOrganization.id),
      queryKeys.accounts(currentOrganization.id, true),
    ]

    switch (pageType) {
      case 'home':
        return [
          ...baseQueries,
          queryKeys.accountBalances(currentOrganization.id),
          queryKeys.journalEntries(currentOrganization.id),
        ]
      case 'reports':
        return [
          ...baseQueries,
          queryKeys.balanceSheet(currentOrganization.id),
          queryKeys.incomeStatement(currentOrganization.id),
          queryKeys.trialBalance(currentOrganization.id),
        ]
      case 'inventory':
        return [
          ...baseQueries,
          queryKeys.inventoryItems(currentOrganization.id, true),
          queryKeys.inventoryCategories(currentOrganization.id, true),
        ]
      case 'vouchers':
        return [
          ...baseQueries,
          queryKeys.vouchers(currentOrganization.id),
          queryKeys.voucherStats(currentOrganization.id),
        ]
      case 'suppliers':
        return [
          ...baseQueries,
          queryKeys.suppliers(currentOrganization.id),
        ]
      default:
        return baseQueries
    }
  }

  const queries = getPageQueries()
  
  // Check loading state for all relevant queries
  const queryStates = queries.map(queryKey => 
    useQuery({
      queryKey,
      queryFn: () => Promise.resolve(null),
      enabled: false, // Don't actually fetch, just check loading state
    })
  )

  const isLoading = queryStates.some(state => state.isLoading)
  const hasError = queryStates.some(state => state.error)
  const isSuccess = queryStates.every(state => state.isSuccess)

  return {
    isLoading,
    hasError,
    isSuccess,
    queryStates,
  }
}

/**
 * Hook for component-level loading states
 * Provides loading states for specific components
 */
export function useComponentLoadingState(componentType: string, dependencies: string[] = []) {
  const currentOrganization = useCurrentOrganization()
  
  if (!currentOrganization) {
    return {
      isLoading: true,
      hasError: false,
      isSuccess: false,
    }
  }

  // Create query keys based on component type and dependencies
  const getComponentQueries = () => {
    const baseQueries = [
      queryKeys.accounts(currentOrganization.id, true),
    ]

    switch (componentType) {
      case 'financial-metrics':
        return [queryKeys.financialMetrics(currentOrganization.id)]
      case 'account-balances':
        return [queryKeys.accountBalances(currentOrganization.id)]
      case 'journal-entries':
        return [queryKeys.journalEntries(currentOrganization.id)]
      case 'balance-sheet':
        return [queryKeys.balanceSheet(currentOrganization.id)]
      case 'income-statement':
        return [queryKeys.incomeStatement(currentOrganization.id)]
      case 'trial-balance':
        return [queryKeys.trialBalance(currentOrganization.id)]
      case 'inventory-items':
        return [queryKeys.inventoryItems(currentOrganization.id, true)]
      case 'inventory-categories':
        return [queryKeys.inventoryCategories(currentOrganization.id, true)]
      case 'vouchers':
        return [queryKeys.vouchers(currentOrganization.id)]
      case 'voucher-stats':
        return [queryKeys.voucherStats(currentOrganization.id)]
      case 'suppliers':
        return [queryKeys.suppliers(currentOrganization.id)]
      default:
        return baseQueries
    }
  }

  const queries = getComponentQueries()
  
  // Add dependency queries
  const dependencyQueries = dependencies.map(dep => {
    switch (dep) {
      case 'organization':
        return queryKeys.currentOrganization(currentOrganization.id)
      case 'accounts':
        return queryKeys.accounts(currentOrganization.id, true)
      case 'financial-metrics':
        return queryKeys.financialMetrics(currentOrganization.id)
      default:
        return [dep, currentOrganization.id]
    }
  })

  const allQueries = [...queries, ...dependencyQueries]
  
  // Check loading state for all relevant queries
  const queryStates = allQueries.map(queryKey => 
    useQuery({
      queryKey,
      queryFn: () => Promise.resolve(null),
      enabled: false, // Don't actually fetch, just check loading state
    })
  )

  const isLoading = queryStates.some(state => state.isLoading)
  const hasError = queryStates.some(state => state.error)
  const isSuccess = queryStates.every(state => state.isSuccess)

  return {
    isLoading,
    hasError,
    isSuccess,
    queryStates,
  }
}

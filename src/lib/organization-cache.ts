import { QueryClient } from '@tanstack/react-query'
import { DataService } from '@/lib/data-service'
import { queryKeys } from '@/lib/query-keys'

export class OrganizationCacheManager {
  private queryClient: QueryClient
  private organizationData: Map<string, any> = new Map()
  
  constructor(queryClient: QueryClient) {
    this.queryClient = queryClient
  }
  
  // Cache organization-specific data
  setOrganizationData(orgId: string, key: string, data: any) {
    const orgKey = `${orgId}-${key}`
    this.organizationData.set(orgKey, {
      data,
      timestamp: Date.now()
    })
  }
  
  // Get cached organization data
  getOrganizationData(orgId: string, key: string) {
    const orgKey = `${orgId}-${key}`
    const cached = this.organizationData.get(orgKey)
    
    if (cached && Date.now() - cached.timestamp < 5 * 60 * 1000) {
      return cached.data
    }
    
    return null
  }
  
  // Invalidate organization data
  invalidateOrganizationData(orgId: string) {
    const prefix = `${orgId}-`
    Array.from(this.organizationData.keys()).forEach((key) => {
      if (key.startsWith(prefix)) {
        this.organizationData.delete(key)
      }
    })
    
    // Also invalidate React Query cache
    this.queryClient.invalidateQueries({
      predicate: (query) => {
        return query.queryKey.includes(orgId)
      }
    })
  }
  
  // Preload organization data
  async preloadOrganizationData(orgId: string) {
    const preloadPromises = [
      this.queryClient.prefetchQuery({
        queryKey: queryKeys.financialMetrics(orgId),
        queryFn: () => DataService.getFinancialMetrics(orgId),
        staleTime: 5 * 60 * 1000,
      }),
      this.queryClient.prefetchQuery({
        queryKey: queryKeys.accountBalances(orgId),
        queryFn: () => DataService.getAccountBalances(orgId),
        staleTime: 3 * 60 * 1000,
      }),
      this.queryClient.prefetchQuery({
        queryKey: queryKeys.accounts(orgId, true),
        queryFn: () => DataService.getAccounts(orgId, true),
        staleTime: 10 * 60 * 1000,
      }),
    ]
    
    await Promise.allSettled(preloadPromises)
  }
  
  // Clear all cached data
  clearAll() {
    this.organizationData.clear()
    this.queryClient.clear()
  }
  
  // Get cache statistics
  getCacheStats() {
    return {
      organizationDataSize: this.organizationData.size,
      queryCacheSize: this.queryClient.getQueryCache().getAll().length,
    }
  }
}

// Create singleton instance
let organizationCacheInstance: OrganizationCacheManager | null = null

export const getOrganizationCache = (queryClient: QueryClient) => {
  if (!organizationCacheInstance) {
    organizationCacheInstance = new OrganizationCacheManager(queryClient)
  }
  return organizationCacheInstance
}

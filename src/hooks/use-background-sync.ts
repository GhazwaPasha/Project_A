import { useQueryClient } from '@tanstack/react-query'
import { useCurrentOrganization } from '@/contexts/organization-context'
import { useAuthStore } from '@/stores/auth-store'
import { queryKeys } from '@/lib/query-keys'
import { useEffect, useRef } from 'react'

/** Throttle: avoid hammering `loadUserData` + `/api/app-data` on rapid tab flips. */
const USER_DATA_REFETCH_MIN_MS = 2 * 60 * 1000

export const useBackgroundSync = (options?: { enabled?: boolean }) => {
  const queryClient = useQueryClient()
  const currentOrganization = useCurrentOrganization()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const lastSyncTimeRef = useRef<number>(Date.now())
  const lastUserDataRefetchAtRef = useRef<number>(0)
  const enabled = options?.enabled !== false
  
  useEffect(() => {
    if (!enabled || !currentOrganization) return
    
    // Sync data every 5 minutes when tab is active
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        const now = Date.now()
        const timeSinceLastSync = now - lastSyncTimeRef.current
        
        // Only sync if it's been more than 5 minutes since last sync
        if (timeSinceLastSync > 5 * 60 * 1000) {
          const id = currentOrganization.id
          for (const qk of queryKeys.financialQueryPrefixes(id)) {
            queryClient.invalidateQueries({ queryKey: qk })
          }
          for (const qk of queryKeys.reportQueryPrefixes(id)) {
            queryClient.invalidateQueries({ queryKey: qk })
          }
          lastSyncTimeRef.current = now
        }
      }
    }, 5 * 60 * 1000)
    
    return () => clearInterval(interval)
  }, [queryClient, currentOrganization, enabled])
  
  // On tab focus: throttled `loadUserData` (org membership, profile) + throttled report/financial invalidation
  useEffect(() => {
    if (!enabled) return

    const handleVisibilityChange = () => {
      if (document.visibilityState !== 'visible') return
      const now = Date.now()

      if (isAuthenticated && now - lastUserDataRefetchAtRef.current >= USER_DATA_REFETCH_MIN_MS) {
        lastUserDataRefetchAtRef.current = now
        void useAuthStore.getState().loadUserData()
      }

      if (currentOrganization) {
        const timeSinceLastSync = now - lastSyncTimeRef.current
        if (timeSinceLastSync > 5 * 60 * 1000) {
          const id = currentOrganization.id
          for (const qk of queryKeys.financialQueryPrefixes(id)) {
            queryClient.invalidateQueries({ queryKey: qk })
          }
          for (const qk of queryKeys.reportQueryPrefixes(id)) {
            queryClient.invalidateQueries({ queryKey: qk })
          }
          lastSyncTimeRef.current = now
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [queryClient, currentOrganization, enabled, isAuthenticated])
  
  // Sync on network reconnection
  useEffect(() => {
    if (!enabled) return
    
    const handleOnline = () => {
      if (!currentOrganization) return
      const id = currentOrganization.id
      // Match interval/visibility: only financial + report prefixes — avoids
      // refetching inventory, vouchers, journal, etc. in one burst on reconnect.
      for (const qk of queryKeys.financialQueryPrefixes(id)) {
        queryClient.invalidateQueries({ queryKey: qk })
      }
      for (const qk of queryKeys.reportQueryPrefixes(id)) {
        queryClient.invalidateQueries({ queryKey: qk })
      }
      lastSyncTimeRef.current = Date.now()
    }
    
    window.addEventListener('online', handleOnline)
    return () => window.removeEventListener('online', handleOnline)
  }, [queryClient, currentOrganization, enabled])
}

import { useQueryClient } from '@tanstack/react-query'
import { useCurrentOrganization } from '@/contexts/organization-context'
import { queryKeys } from '@/lib/query-keys'
import { useEffect, useRef } from 'react'

export const useBackgroundSync = (options?: { enabled?: boolean }) => {
  const queryClient = useQueryClient()
  const currentOrganization = useCurrentOrganization()
  const lastSyncTimeRef = useRef<number>(Date.now())
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
  
  // Sync on window focus - but only if away for more than 5 minutes
  useEffect(() => {
    if (!enabled) return
    
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && currentOrganization) {
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
    }
    
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [queryClient, currentOrganization, enabled])
  
  // Sync on network reconnection
  useEffect(() => {
    if (!enabled) return
    
    const handleOnline = () => {
      if (currentOrganization) {
        queryClient.invalidateQueries({
          predicate: (query) => query.queryKey.includes(currentOrganization.id)
        })
        lastSyncTimeRef.current = Date.now()
      }
    }
    
    window.addEventListener('online', handleOnline)
    return () => window.removeEventListener('online', handleOnline)
  }, [queryClient, currentOrganization, enabled])
}
